"""Subprocess body: one trajectory_optimizer call, results to an .npz.

usage: python -m tumfork_keywords.solve TRACK_CSV INPUTS_DIR CURV_OPT_TYPE
           SAFETY_WIDTH OUT_NPZ [EXPORT_DIR]

Records the imported package's __file__, so a caller can prove which code ran.
"""

import os
import sys

import numpy as np


def main(argv):
    track_csv, inputs_dir, curv_opt_type, safety_width, out_npz = argv[:5]
    export_dir = argv[5] if len(argv) > 5 else None
    import global_racetrajectory_optimization as tum
    from global_racetrajectory_optimization.trajectory_optimizer import (
        trajectory_optimizer,
    )

    kwargs = {}
    if export_dir is not None:
        kwargs["export_dir"] = export_dir
    track_name = os.path.splitext(os.path.abspath(track_csv))[0]
    traj, bound1, bound2, lap_time = trajectory_optimizer(
        os.path.abspath(inputs_dir),
        track_name,
        curv_opt_type,
        safety_width=float(safety_width),
        plot=False,
        **kwargs,
    )
    np.savez(
        out_npz,
        traj=traj,
        bound1=bound1,
        bound2=bound2,
        lap_time=np.array(lap_time),
        package_file=np.array(os.path.abspath(tum.__file__)),
    )


if __name__ == "__main__":
    main(sys.argv[1:])
