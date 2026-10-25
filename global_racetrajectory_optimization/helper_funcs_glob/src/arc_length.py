"""Exact arc length of cubic splines (closure option 1, Q11).

tph's ``calc_spline_lengths`` sums a 15-point polyline per spline, which is
short by ~2e-4 m on a 1.6 m spline, and ``create_raceline`` places points
linearly in t, so its s drifts from the arc along the line (2.6e-3 on the W1a
raceline). Here s is the Gauss-Legendre integral of |(x'(t), y'(t))| on the
same splines; the xy of the points is not touched. tph is a separate package
and R-FORK forks TUM, not tph, so this is a deliberate duplicate.
"""

import numpy as np

_NODES, _WEIGHTS = np.polynomial.legendre.leggauss(16)


def _speed(cx, cy, t):
    dx = cx[1] + 2.0 * cx[2] * t + 3.0 * cx[3] * t**2
    dy = cy[1] + 2.0 * cy[2] * t + 3.0 * cy[3] * t**2
    return np.hypot(dx, dy)


def _arc(cx, cy, t):
    """Length of one spline on [0, t] (16-node Gauss-Legendre)."""
    tt = 0.5 * t * (_NODES + 1.0)
    return 0.5 * t * float(np.sum(_WEIGHTS * _speed(cx, cy, tt)))


def exact_spline_lengths(coeffs_x, coeffs_y):
    return np.array([_arc(a, b, 1.0) for a, b in zip(coeffs_x, coeffs_y)])


def exact_arc_length(coeffs_x, coeffs_y, spline_inds, t_vals):
    """s of each point: the lengths of the splines before it plus its arc."""
    lengths = exact_spline_lengths(coeffs_x, coeffs_y)
    cum = np.concatenate([[0.0], np.cumsum(lengths)])
    return np.array(
        [
            cum[k] + _arc(coeffs_x[k], coeffs_y[k], t)
            for k, t in zip(spline_inds, t_vals)
        ]
    )


def exact_lengths(coeffs_x, coeffs_y, spline_inds, t_vals):
    """(s of each point, spline lengths, closed element lengths).

    The three arrays tph's ``create_raceline`` returns as
    ``s_points``, ``spline_lengths`` and ``el_lengths_cl``.
    """
    lengths = exact_spline_lengths(coeffs_x, coeffs_y)
    s = exact_arc_length(coeffs_x, coeffs_y, spline_inds, t_vals)
    el = np.append(np.diff(s), float(np.sum(lengths)) - s[-1])
    return s, lengths, el
