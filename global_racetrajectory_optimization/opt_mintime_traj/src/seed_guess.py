"""Initial guess for the min-time NLP from a known line (R-SEED).

Ported from the p8b-step1 harness (run_tum_w.py, seed 1). The layout is
opt_mintime's own: the initial state, then per interval the control, ``d``
collocation states and the end state.
"""

import numpy as np


def build_seed_x0(
    seed,
    size,
    s_opt,
    tau,
    wheelbase,
    mass,
    nx=5,
    nu=4,
    v_s=50.0,
    delta_s=0.5,
    f_drive_s=7500.0,
    f_brake_s=20000.0,
):
    """The seeded ``w0`` of length ``size``.

    ``seed``  : (M, 7) TUM trajectory ``s;x;y;psi;kappa;v;a_x`` (open).
    ``s_opt`` : the NLP's grid, N + 1 points; it is mapped proportionally
                onto the seed's length, ``s_seed = s_opt * Lc / s_opt[-1]``.
    ``tau``   : opt_mintime's collocation points, 0 first (length d + 1).
    State: ``[v/v_s, 0, v*kappa, 0, 0]``; control:
    ``[atan(wb*kappa)/delta_s, max(m*a,0)/f_drive_s, min(m*a,0)/f_brake_s, 0]``.
    """
    if nx != 5:
        raise ValueError(
            f"seed_line supports nx=5 only (pwr_behavior off), got {nx}"
        )
    seed = np.asarray(seed, dtype=float)
    # a closing row duplicating the first (TUM's traj_race_cl) is dropped
    if len(seed) > 2 and np.hypot(*(seed[0, 1:3] - seed[-1, 1:3])) < 1e-9:
        seed = seed[:-1]
    ds = np.diff(seed[:, 0])
    if np.any(ds <= 0.0):
        raise ValueError("seed_line s must be strictly increasing")
    gap = float(np.hypot(*(seed[0, 1:3] - seed[-1, 1:3])))
    if gap > 2.0 * float(np.median(ds)):
        raise ValueError(
            f"seed_line is not a loop: closing gap {gap:.3f} m exceeds twice "
            f"the median spacing {np.median(ds):.3f} m"
        )
    s_, kap_, v_, ax_ = seed[:, 0], seed[:, 4], seed[:, 5], seed[:, 6]
    lc = s_[-1] + np.hypot(*(seed[0, 1:3] - seed[-1, 1:3]))
    d = len(tau) - 1
    blk = nu + d * nx + nx
    if (size - nx) % blk:
        raise ValueError(f"w0 size {size} does not fit nx={nx}, nu={nu}, d={d}")
    n = (size - nx) // blk
    s_grid = np.asarray(s_opt, dtype=float)
    if len(s_grid) != n + 1:
        raise ValueError(f"s_opt has {len(s_grid)} points, w0 implies {n + 1}")
    scale = lc / s_grid[-1]
    s_ext = np.append(s_, lc)

    def per(y, s):
        return np.interp(s % lc, s_ext, np.append(y, y[0]))

    def state(s):
        v = per(v_, s)
        return np.array([v / v_s, 0.0, v * per(kap_, s), 0.0, 0.0])

    def ctrl(s):
        k, a = per(kap_, s), per(ax_, s)
        return np.array(
            [
                np.arctan(wheelbase * k) / delta_s,
                max(mass * a, 0.0) / f_drive_s,
                min(mass * a, 0.0) / f_brake_s,
                0.0,
            ]
        )

    w = np.zeros(size)
    w[0:nx] = state(0.0)
    pos = nx
    for k in range(n):
        s0 = s_grid[k] * scale
        hk = (s_grid[k + 1] - s_grid[k]) * scale
        w[pos : pos + nu] = ctrl(s0 + 0.5 * hk)
        pos += nu
        for j in range(d):
            w[pos : pos + nx] = state(s0 + tau[j + 1] * hk)
            pos += nx
        w[pos : pos + nx] = state(s0 + hk)
        pos += nx
    return w
