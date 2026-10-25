import os

import numpy as np
import pytest
import trajectory_planning_helpers as tph
from scipy.integrate import quad

from global_racetrajectory_optimization.helper_funcs_glob.src.arc_length import (  # noqa: E501
    exact_arc_length,
    exact_lengths,
    exact_spline_lengths,
)

DATA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "third_party",
    "GR-roboracer-data",
    "fixtures",
    "tum-fork",
    "spielberg-gym-0.40",
)


def _circle_splines(r=2.0, n=8):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.column_stack([r * np.cos(a), r * np.sin(a)])
    cl = np.vstack([pts, pts[0]])
    cx, cy = tph.calc_splines.calc_splines(path=cl, use_dist_scaling=False)[:2]
    return cx, cy


def test_tumfork_1010_straight_cubic_is_its_chord():
    cx = np.array([[1.0, 3.0, 0.0, 0.0]])
    cy = np.array([[2.0, 4.0, 0.0, 0.0]])
    assert abs(exact_spline_lengths(cx, cy)[0] - 5.0) < 1e-12
    s = exact_arc_length(cx, cy, [0, 0], [0.0, 0.5])
    assert abs(s[1] - 2.5) < 1e-12


def test_tumfork_1010_matches_quad_on_a_circle_spline_set():
    cx, cy = _circle_splines()
    got = exact_spline_lengths(cx, cy)
    for k in range(len(cx)):

        def speed(t, k=k):
            dx = cx[k, 1] + 2 * cx[k, 2] * t + 3 * cx[k, 3] * t**2
            dy = cy[k, 1] + 2 * cy[k, 2] * t + 3 * cy[k, 3] * t**2
            return np.hypot(dx, dy)

        ref = quad(speed, 0.0, 1.0, epsabs=1e-13)[0]
        assert abs(got[k] - ref) < 1e-10, (k, got[k], ref)


def test_tumfork_1010_t0_is_the_cumulative_length_and_s_is_monotonic():
    cx, cy = _circle_splines()
    lengths = exact_spline_lengths(cx, cy)
    cum = np.concatenate([[0.0], np.cumsum(lengths)])
    ks = np.arange(len(cx))
    s0 = exact_arc_length(cx, cy, ks, np.zeros(len(cx)))
    assert np.max(np.abs(s0 - cum[:-1])) < 1e-12
    inds = np.repeat(ks, 10)
    ts = np.tile(np.linspace(0, 0.9, 10), len(cx))
    s = exact_arc_length(cx, cy, inds, ts)
    assert np.all(np.diff(s) > 0)


def _closure(s, xy):
    return float(np.max(np.abs(np.diff(s) - np.hypot(*np.diff(xy, axis=0).T))))


def test_tumfork_1020_closure_on_the_w1a_raceline():
    if not os.path.isfile(os.path.join(DATA, "W1a", "frame.npz")):
        pytest.fail(
            "W1a fixture missing: git submodule update --init "
            "third_party/GR-roboracer-data"
        )
    f = np.load(os.path.join(DATA, "W1a", "frame.npz"))
    r, nv = f["r"], f["nv"]
    n = np.loadtxt(os.path.join(DATA, "W1a", "states.csv"), delimiter=";")
    n = n[:-1, 5]
    out = tph.create_raceline.create_raceline(
        refline=r[:, :2], normvectors=nv, alpha=-n, stepsize_interp=0.1
    )
    xy, _, cxo, cyo, inds, ts, s_tph = out[:7]
    pre = _closure(s_tph, xy)
    assert pre > 2e-3, pre
    s, lengths, el = exact_lengths(cxo, cyo, inds, ts)
    post = _closure(s, xy)
    assert post < 1e-4, post
    assert abs(float(np.sum(el)) - float(np.sum(lengths))) < 1e-9
