import numpy as np

from global_racetrajectory_optimization.helper_funcs_glob.src.periodic_speed import (  # noqa: E501
    interp_speed_periodic,
)


def test_tumfork_1080_seam_interpolates_toward_v0_not_clamped():
    nodes = np.array([0.0, 1.0, 2.0, 3.0])
    v = np.array([1.0, 2.0, 3.0, 4.0])
    got = interp_speed_periodic(np.array([3.25, 3.5, 3.75]), nodes, v, 4.0)
    assert np.allclose(got, [3.25, 2.5, 1.75])


def test_tumfork_1080_interior_matches_np_interp():
    nodes = np.array([0.0, 1.0, 2.0, 3.0])
    v = np.array([1.0, 2.0, 3.0, 4.0])
    q = np.linspace(0.0, 3.0, 13)
    assert np.array_equal(
        interp_speed_periodic(q, nodes, v, 4.0), np.interp(q, nodes, v)
    )


def test_tumfork_1080_closed_ax_is_continuous_across_the_seam():
    n = 40
    lap = 10.0
    nodes = np.arange(n) * (lap / n)
    v = 10.0 + 0.5 * np.sin(2 * np.pi * nodes / lap)
    # query grid finer than the nodes, last point short of the lap
    s = np.arange(0.0, lap, 0.1 * 0.9)
    s = s[s < lap]
    vp = interp_speed_periodic(s, nodes, v, lap)
    el = np.diff(np.append(s, lap))
    vcl = np.append(vp, vp[0])
    ax = (vcl[1:] ** 2 - vcl[:-1] ** 2) / (2 * el)
    assert np.max(np.abs(ax)) < 4.0  # analytic peak 3.1
