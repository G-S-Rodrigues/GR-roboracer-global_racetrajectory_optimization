from global_racetrajectory_optimization.mintime_options import MintimeOptions
from global_racetrajectory_optimization.opt_mintime_traj.src.solver_options import (  # noqa: E501
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
