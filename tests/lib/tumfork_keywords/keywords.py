"""Robot Framework adapter over runner.py (thin: logic lives in runner)."""

import json
import os
import shutil

import make_oval
import numpy as np
from robot.api.deco import keyword, library

from tumfork_keywords import runner

DATA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "third_party",
    "GR-roboracer-data",
    "fixtures",
    "tum-fork",
)


def _num(v):
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return v
    return v


def _truthy(v):
    return str(v).lower() in ("true", "1", "yes")


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

    # ---- min-time (tier 4) ------------------------------------------------

    @keyword
    def make_gym_case(self, case_dir):
        """Spielberg, gym vehicle, margin 0.40: copied from the data repo."""
        src = os.path.join(DATA, "spielberg-gym-0.40")
        if not os.path.isdir(src):
            raise AssertionError(
                "data submodule not initialised: git submodule update --init"
            )
        os.makedirs(case_dir, exist_ok=True)
        track = shutil.copyfile(
            os.path.join(src, "track.csv"), os.path.join(case_dir, "track.csv")
        )
        inputs = os.path.join(case_dir, "inputs")
        # always refresh: case_dir persists in the ws-log volume, and the data
        # submodule may have moved since the last run
        shutil.rmtree(inputs, ignore_errors=True)
        shutil.copytree(os.path.join(src, "inputs"), inputs)
        return {
            "track": track,
            "inputs": inputs,
            "seed": os.path.join(src, "seed", "gym-0.4.csv"),
            "data": src,
        }

    @keyword
    def run_mintime_solve(
        self, case, out_npz, export_dir, timeout=1800, seed=False, **options
    ):
        """One min-time solve in a subprocess; never raises on a bad exit.

        ``options`` are MintimeOptions fields (Robot passes strings, so
        numbers are converted here). Returns rc, wall_s, stdout/stderr tails,
        the parsed solver_status.json (or None) and, if rc == 0, the arrays.
        """
        opts = {k: _num(v) for k, v in options.items()}
        res = runner.run_solve(
            runner.BRANCH_PYTHON,
            case["track"],
            case["inputs"],
            "mintime",
            1.11,
            out_npz,
            export_dir=export_dir,
            timeout=float(timeout),
            threads=3,
            mintime=opts,
            seed_csv=case["seed"] if _truthy(seed) else None,
        )
        status_file = os.path.join(export_dir, "mintime", "solver_status.json")
        status = None
        if os.path.isfile(status_file):
            with open(status_file) as fh:
                status = json.load(fh)
        return {
            "rc": res.returncode,
            "wall_s": res.wall_s,
            "stdout": res.stdout[-3000:],
            "stderr": res.stderr[-3000:],
            "status": status,
            "arrays": res.arrays() if res.returncode == 0 else None,
            "state_dir": os.path.join(export_dir, "mintime"),
        }

    @keyword
    def closure_error(self, result):
        """max | ds - |dxy| | along the returned trajectory (s;x;y;...)."""
        traj = result["arrays"]["traj"]
        ds = np.diff(traj[:, 0])
        dxy = np.hypot(np.diff(traj[:, 1]), np.diff(traj[:, 2]))
        return float(np.max(np.abs(ds - dxy)))

    @keyword
    def ax_ratios(self, result, case):
        """(seam, max over the closed lap) of ax against the profile's limits.

        Driving (ax > 0) is held to ax_max_machines(vx), braking (ax < 0) to
        the ggv's ax_max(vx), as tph's velocity profile does. traj is
        s;x;y;psi;kappa;vx;ax and ends with the closing row (row 0 again), so
        the step across the wrap is in the last two rows.
        """
        veh = os.path.join(case["inputs"], "veh_dyn_info")
        mach = np.loadtxt(
            os.path.join(veh, "ax_max_machines.csv"),
            delimiter=",",
            comments="#",
        )
        ggv = np.loadtxt(
            os.path.join(veh, "ggv.csv"), delimiter=",", comments="#"
        )
        traj = result["arrays"]["traj"]
        vx, ax = traj[:, 5], traj[:, 6]
        drive = np.interp(vx, mach[:, 0], mach[:, 1])
        brake = np.interp(vx, ggv[:, 0], ggv[:, 1])
        ratio = np.where(ax > 0, ax / drive, -ax / brake)
        return float(np.max(ratio[-2:])), float(np.max(ratio))

    @keyword
    def make_oval_mintime_case(self, case_dir):
        """The oval with a min-time ini, and a min-curv line as its seed."""
        os.makedirs(case_dir, exist_ok=True)
        track = make_oval.write_oval_track(os.path.join(case_dir, "oval.csv"))
        inputs = make_oval.write_inputs(
            os.path.join(case_dir, "inputs"),
            make_oval.INI_MINTIME_GYM,
            "f1tenth_gym_limits",
        )
        seed = os.path.join(case_dir, "seed.csv")
        out = os.path.join(case_dir, "seed.npz")
        res = runner.run_solve(
            runner.BRANCH_PYTHON, track, inputs, "mincurv_iqp", 1.11, out
        )
        if res.returncode != 0:
            raise AssertionError(f"seed solve failed\n{res.stderr[-2000:]}")
        np.savetxt(seed, res.arrays()["traj"], delimiter=";")
        return {"track": track, "inputs": inputs, "seed": seed}

    @keyword
    def snapshot_package_outputs(self):
        """{path: mtime_ns} for everything under the package's outputs/."""
        import global_racetrajectory_optimization as tum

        root = os.path.join(
            os.path.dirname(os.path.abspath(tum.__file__)), "outputs"
        )
        snap = {}
        for base, _, files in os.walk(root):
            snap[base] = os.stat(base).st_mtime_ns
            for name in files:
                path = os.path.join(base, name)
                snap[path] = os.stat(path).st_mtime_ns
        return snap

    @keyword
    def package_outputs_should_be_unchanged(self, before):
        """A solve with export_dir must not touch the package's outputs/."""
        after = self.snapshot_package_outputs()
        if after != before:
            changed = sorted(set(after.items()) ^ set(before.items()))
            raise AssertionError(f"package outputs/ changed: {changed[:5]}")
