# Added 2026-10 for GR-roboracer by Guilherme Rodrigues (see Readme.md, "GR-roboracer fork").
import numpy as np


def interp_speed_periodic(s_query, s_nodes, v_nodes, lap_length):
    """Interpolate a closed-lap speed profile, periodic in ``lap_length``.

    The min-time NLP has one speed per node, node k at s_nodes[k] and the last node
    short of the lap. ``np.interp`` holds the last speed flat from there to the wrap
    and then jumps to v[0]. Here the lap closes: v_nodes[0] is also the value at
    ``lap_length``, so the speed ramps across the seam.
    """
    s_nodes = np.asarray(s_nodes, dtype=float)
    v_nodes = np.asarray(v_nodes, dtype=float)
    return np.interp(
        s_query,
        np.append(s_nodes, lap_length),
        np.append(v_nodes, v_nodes[0]),
    )
