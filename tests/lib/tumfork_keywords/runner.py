"""Run one TUM solve in a subprocess and return what happened."""

import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass

import numpy as np

BRANCH_PYTHON = "/opt/venv/bin/python"
UPSTREAM_PYTHON = "/opt/upstream/bin/python"
LIB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class SolveResult:
    returncode: int
    stdout: str
    stderr: str
    wall_s: float
    out_npz: str

    def arrays(self):
        with np.load(self.out_npz) as z:
            return {k: z[k] for k in z.files}


def run_solve(
    python,
    track_csv,
    inputs_dir,
    curv_opt_type,
    safety_width,
    out_npz,
    export_dir=None,
    timeout=None,
    threads=1,
    mintime=None,
    seed_csv=None,
):
    """Run ``tumfork_keywords.solve`` under ``python``.

    The cwd is a fresh temp dir, never /ws: ``python -m`` puts the cwd first on
    sys.path, so from /ws an upstream run would import this branch.
    """
    cmd = [
        python,
        "-m",
        "tumfork_keywords.solve",
        str(track_csv),
        str(inputs_dir),
        curv_opt_type,
        str(safety_width),
        str(out_npz),
    ]
    if export_dir is not None:
        cmd += ["--export-dir", str(export_dir)]
    if mintime is not None:
        cmd += ["--mintime", json.dumps(mintime)]
    if seed_csv is not None:
        cmd += ["--seed-csv", str(seed_csv)]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.update(
        PYTHONPATH=LIB_DIR,
        MPLBACKEND="Agg",
        OPENBLAS_NUM_THREADS=str(threads),
        OMP_NUM_THREADS=str(threads),
        MKL_NUM_THREADS=str(threads),
    )
    with tempfile.TemporaryDirectory() as cwd:
        t0 = time.perf_counter()
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        wall = time.perf_counter() - t0
    return SolveResult(
        proc.returncode, proc.stdout, proc.stderr, wall, str(out_npz)
    )
