import os

import casadi as ca
import numpy as np
import pytest

from global_racetrajectory_optimization.opt_mintime_traj.src.seed_guess import (  # noqa: E501
    build_seed_x0,
)

FIX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "third_party",
    "GR-roboracer-data",
    "fixtures",
    "tum-fork",
    "spielberg-gym-0.40",
)
TAU = np.append(0.0, np.array(ca.collocation_points(3, "legendre")).ravel())
WB, MASS = 0.15875 + 0.17145, 3.74
NX, NU, D = 5, 4, 3
BLK = NU + D * NX + NX


def _circle(v=5.0, a=0.0, r=4.0, m=200):
    ang = np.linspace(0, 2 * np.pi, m, endpoint=False)
    s = ang * r
    psi = ang + np.pi / 2
    return np.column_stack(
        [
            s,
            r * np.cos(ang),
            r * np.sin(ang),
            psi,
            np.full(m, 1 / r),
            np.full(m, v),
            np.full(m, a),
        ]
    )


def _grid(n, seed):
    lc = seed[-1, 0] + np.hypot(*(seed[0, 1:3] - seed[-1, 1:3]))
    return np.arange(n + 1) * (lc / n)


def test_tumfork_1030_constant_curvature_state_and_control():
    seed = _circle(v=5.0, a=0.0)
    n = 50
    size = NX + n * BLK
    w = build_seed_x0(seed, size, _grid(n, seed), TAU, WB, MASS)
    assert w.size == size
    states = [w[0:NX]]
    pos = NX
    for _ in range(n):
        u = w[pos : pos + NU]
        pos += NU
        assert abs(u[0] - np.arctan(WB / 4.0) / 0.5) < 1e-12, u[0]
        assert u[1] == 0.0 and u[2] == 0.0 and u[3] == 0.0
        for _ in range(D + 1):
            states.append(w[pos : pos + NX])
            pos += NX
    for x in states:
        assert abs(x[0] - 5.0 / 50.0) < 1e-12
        assert abs(x[2] - 5.0 / 4.0) < 1e-12
        assert x[1] == 0.0 and x[3] == 0.0 and x[4] == 0.0


def test_tumfork_1030_acceleration_splits_into_drive_and_brake():
    n = 20
    for a, drive, brake in (
        (2.0, MASS * 2.0 / 7500.0, 0.0),
        (-3.0, 0.0, -MASS * 3.0 / 20000.0),
    ):
        seed = _circle(a=a)
        w = build_seed_x0(seed, NX + n * BLK, _grid(n, seed), TAU, WB, MASS)
        u = w[NX : NX + NU]
        assert abs(u[1] - drive) < 1e-12 and abs(u[2] - brake) < 1e-12


def test_tumfork_1030_size_that_does_not_fit_raises():
    seed = _circle()
    with pytest.raises(ValueError):
        build_seed_x0(seed, NX + 3 * BLK + 1, _grid(3, seed), TAU, WB, MASS)
    with pytest.raises(ValueError):
        build_seed_x0(seed, NX + 3 * BLK, _grid(4, seed), TAU, WB, MASS)


@pytest.mark.skipif(
    not os.path.isfile(os.path.join(FIX, "x0_seed.csv")),
    reason="x0 golden not in the data submodule",
)
def test_tumfork_1030_matches_the_step1_golden():
    golden = np.loadtxt(os.path.join(FIX, "x0_seed.csv"))
    with open(os.path.join(FIX, "x0_seed.frame.txt")) as fh:
        frame = dict(line.strip().split("=", 1) for line in fh)
    seed = np.loadtxt(os.path.join(FIX, "seed", "gym-0.4.csv"), delimiter=";")
    n, h = int(frame["N"]), float(frame["h"])
    w = build_seed_x0(
        seed, int(frame["size"]), np.arange(n + 1) * h, TAU, WB, MASS
    )
    err = float(np.max(np.abs(w - golden)))
    assert err < 1e-9, f"max |x0 - golden| = {err}"
