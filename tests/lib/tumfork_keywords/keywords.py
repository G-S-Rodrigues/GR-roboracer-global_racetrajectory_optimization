"""Robot Framework adapter over runner.py (thin: logic lives in runner)."""

import os

import make_oval
import numpy as np
from robot.api.deco import keyword, library

from tumfork_keywords import runner

_INI = {
    "f1tenth_default": make_oval.INI_F1TENTH_DEFAULT,
    "f1tenth_gym_limits": make_oval.INI_F1TENTH_GYM_LIMITS,
}


@library(scope="GLOBAL")
class keywords:  # noqa: N801 - Robot library name
    @keyword
    def make_oval_case(self, case_dir, vehicle):
        """Write the oval track and GR-roboracer's rendered ini for it."""
        os.makedirs(case_dir, exist_ok=True)
        track = make_oval.write_oval_track(os.path.join(case_dir, "oval.csv"))
        inputs = make_oval.write_inputs(
            os.path.join(case_dir, "inputs"),
            _INI[vehicle] + make_oval.SHORTEST_PATH_LINE,
            vehicle,
        )
        return {"track": track, "inputs": inputs}

    @keyword
    def run_branch_solve(self, case, curv_opt_type, out_npz, export_dir=None):
        return self._run(
            runner.BRANCH_PYTHON, case, curv_opt_type, out_npz, export_dir
        )

    @keyword
    def run_upstream_solve(self, case, curv_opt_type, out_npz):
        return self._run(
            runner.UPSTREAM_PYTHON, case, curv_opt_type, out_npz, None
        )

    @staticmethod
    def _run(python, case, curv_opt_type, out_npz, export_dir):
        res = runner.run_solve(
            python,
            case["track"],
            case["inputs"],
            curv_opt_type,
            0.4,
            out_npz,
            export_dir=export_dir or None,
        )
        if res.returncode != 0:
            raise AssertionError(
                f"solve exited {res.returncode}\n{res.stderr[-2000:]}"
            )
        return res.arrays()

    @keyword
    def solutions_should_be_identical(self, branch, upstream, label):
        for key in ("traj", "bound1", "bound2", "lap_time"):
            if not np.array_equal(branch[key], upstream[key]):
                diff = np.max(np.abs(branch[key] - upstream[key]))
                raise AssertionError(
                    f"arrays differ: {label} {key} (max abs diff {diff:.3g})"
                )

    @keyword
    def package_file_should_start_with(self, result, prefix):
        got = str(result["package_file"])
        if not got.startswith(prefix):
            raise AssertionError(f"imported {got}, expected under {prefix}")
