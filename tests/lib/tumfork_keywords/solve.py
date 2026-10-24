"""Subprocess body: one trajectory_optimizer call, results to an .npz.

usage: python -m tumfork_keywords.solve TRACK_CSV INPUTS_DIR CURV_OPT_TYPE
           SAFETY_WIDTH OUT_NPZ [--export-dir D] [--mintime JSON]
           [--seed-csv CSV]

``--mintime`` is a JSON object of MintimeOptions fields; ``--seed-csv`` loads a
TUM trajectory (``s;x;y;psi;kappa;v;a_x``) into ``seed_line``. Records the
imported package's __file__, so a caller can prove which code ran. On
MintimeNotConverged it prints one ``MINTIME_NOT_CONVERGED`` line and exits 1.
"""

import argparse
import json
import os
import sys

import numpy as np


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("track_csv")
    ap.add_argument("inputs_dir")
    ap.add_argument("curv_opt_type")
    ap.add_argument("safety_width", type=float)
    ap.add_argument("out_npz")
    ap.add_argument("--export-dir")
    ap.add_argument("--mintime")
    ap.add_argument("--seed-csv")
    a = ap.parse_args(argv)

    import global_racetrajectory_optimization as tum
    from global_racetrajectory_optimization.trajectory_optimizer import (
        trajectory_optimizer,
    )

    kwargs = {}
    if a.export_dir is not None:
        kwargs["export_dir"] = a.export_dir
    if a.mintime is not None or a.seed_csv is not None:
        from global_racetrajectory_optimization.mintime_options import (
            MintimeNotConverged,
            MintimeOptions,
        )

        fields = json.loads(a.mintime) if a.mintime else {}
        if a.seed_csv:
            fields["seed_line"] = np.loadtxt(a.seed_csv, delimiter=";")
        kwargs["mintime"] = MintimeOptions(**fields)
    else:
        MintimeNotConverged = ()  # nothing to catch
    track_name = os.path.splitext(os.path.abspath(a.track_csv))[0]
    try:
        traj, bound1, bound2, lap_time = trajectory_optimizer(
            os.path.abspath(a.inputs_dir),
            track_name,
            a.curv_opt_type,
            safety_width=a.safety_width,
            plot=False,
            **kwargs,
        )
    except MintimeNotConverged as err:
        print(
            "MINTIME_NOT_CONVERGED "
            + json.dumps(
                {
                    "status": err.status,
                    "iterations": err.iterations,
                    "state_dir": err.state_dir,
                }
            )
        )
        sys.exit(1)
    np.savez(
        a.out_npz,
        traj=traj,
        bound1=bound1,
        bound2=bound2,
        lap_time=np.array(lap_time),
        package_file=np.array(os.path.abspath(tum.__file__)),
    )


if __name__ == "__main__":
    main(sys.argv[1:])
