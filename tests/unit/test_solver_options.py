import os

import casadi as ca
import numpy as np

from global_racetrajectory_optimization.mintime_options import MintimeOptions
from global_racetrajectory_optimization.opt_mintime_traj.src.solver_options import (  # noqa: E501
    StopAndSave,
    ipopt_opts,
)

BASE = {"expand": True, "verbose": True}
UPSTREAM = {
    "expand": True,
    "verbose": True,
    "ipopt.max_iter": 2000,
    "ipopt.tol": 1e-7,
}
UPSTREAM_WARM = {
    "ipopt.warm_start_init_point": "yes",
    "ipopt.warm_start_bound_push": 1e-3,
    "ipopt.warm_start_mult_bound_push": 1e-3,
    "ipopt.warm_start_slack_bound_push": 1e-3,
    "ipopt.mu_init": 1e-3,
}


def test_tumfork_1040_default_is_upstreams_dict():
    assert ipopt_opts(BASE, MintimeOptions()) == UPSTREAM
    assert ipopt_opts(BASE, None) == UPSTREAM


def test_tumfork_1040_warm_start_is_upstreams_dict():
    want = dict(UPSTREAM, **UPSTREAM_WARM)
    assert ipopt_opts(BASE, MintimeOptions(), warm_start=True) == want


def test_tumfork_1040_max_iter_override():
    got = ipopt_opts(BASE, MintimeOptions(max_iter=50))
    assert got == dict(UPSTREAM, **{"ipopt.max_iter": 50})


def test_tumfork_1040_mu_init_without_warm_start_sets_only_mu():
    got = ipopt_opts(BASE, MintimeOptions(mu_init=1e-3))
    assert got == dict(UPSTREAM, **{"ipopt.mu_init": 1e-3})


def test_tumfork_1040_mu_init_overrides_warm_start_mu():
    got = ipopt_opts(BASE, MintimeOptions(mu_init=1e-2), warm_start=True)
    assert got["ipopt.mu_init"] == 1e-2
    assert got["ipopt.warm_start_init_point"] == "yes"


def test_tumfork_1040_bound_push_override():
    got = ipopt_opts(
        BASE, MintimeOptions(warm_start_bound_push=1e-9), warm_start=True
    )
    for key in (
        "ipopt.warm_start_bound_push",
        "ipopt.warm_start_mult_bound_push",
        "ipopt.warm_start_slack_bound_push",
    ):
        assert got[key] == 1e-9


def test_tumfork_1040_a_callback_becomes_iteration_callback():
    sentinel = object()
    got = ipopt_opts(BASE, MintimeOptions(max_wall_time_s=5), callback=sentinel)
    assert got["iteration_callback"] is sentinel
    assert "iteration_callback" not in ipopt_opts(BASE, MintimeOptions())


# ---- TUMFORK-1050: StopAndSave with a fake clock --------------------------

NX, NG = 6, 4


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _arg(f=1.5):
    vals = {
        "x": np.arange(NX, dtype=float),
        "f": np.array([f]),
        "g": np.zeros(NG),
        "lam_x": np.arange(NX, dtype=float) * 10,
        "lam_g": np.ones(NG),
        "lam_p": np.zeros(0),
    }
    out = []
    for i in range(ca.nlpsol_n_out()):
        v = vals[ca.nlpsol_out(i)]
        out.append(ca.DM(v) if v.size else ca.DM(0, 0))
    return out


def _cb(tmp_path, clock, limit=10.0, every=0):
    cb = StopAndSave("cb", NX, NG, str(tmp_path), limit, every, clock=clock)
    cb.start()
    return cb


def test_tumfork_1050_no_stop_before_the_limit_then_stop(tmp_path):
    clock = FakeClock()
    cb = _cb(tmp_path, clock)
    clock.t = 9.9
    assert cb.eval(_arg()) == [0]
    assert not list(tmp_path.iterdir())
    clock.t = 10.1
    assert cb.eval(_arg()) == [1]
    assert cb.stopped


def test_tumfork_1050_timer_counts_from_start_not_construction(tmp_path):
    clock = FakeClock()
    clock.t = 1000.0
    cb = StopAndSave("cb2", NX, NG, str(tmp_path), 10.0, 0, clock=clock)
    clock.t = 5000.0
    cb.start()
    clock.t = 5009.0
    assert cb.eval(_arg()) == [0]


def test_tumfork_1050_saves_every_n_iterations_and_at_stop(tmp_path):
    clock = FakeClock()
    cb = _cb(tmp_path, clock, limit=100.0, every=3)
    for _ in range(2):
        cb.eval(_arg())
    assert not (tmp_path / "w0.csv").exists()
    cb.eval(_arg())
    assert (tmp_path / "w0.csv").exists()
    assert (tmp_path / "iter.txt").read_text().split()[0] == "3"
    cb.eval(_arg())
    assert (tmp_path / "iter.txt").read_text().split()[0] == "3"
    clock.t = 101.0
    cb.eval(_arg())
    assert (tmp_path / "iter.txt").read_text().split()[0] == "5"


def test_tumfork_1050_files_are_tums_names_sizes_and_atomic(
    tmp_path, monkeypatch
):
    replaced = []
    real = os.replace
    monkeypatch.setattr(
        os, "replace", lambda a, b: (replaced.append(b), real(a, b))[1]
    )
    clock = FakeClock()
    cb = _cb(tmp_path, clock, limit=1.0)
    clock.t = 2.0
    cb.eval(_arg())
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ["iter.txt", "lam_g0.csv", "lam_x0.csv", "w0.csv"]
    assert len(np.loadtxt(tmp_path / "w0.csv")) == NX
    assert len(np.loadtxt(tmp_path / "lam_x0.csv")) == NX
    assert len(np.loadtxt(tmp_path / "lam_g0.csv")) == NG
    assert len(replaced) >= 3
    assert not list(tmp_path.glob("*.tmp"))


def test_tumfork_1050_records_first_and_last_objective(tmp_path):
    clock = FakeClock()
    cb = _cb(tmp_path, clock, limit=100.0)
    cb.eval(_arg(f=7.0))
    cb.eval(_arg(f=3.0))
    assert (cb.first_f, cb.last_f) == (7.0, 3.0)
