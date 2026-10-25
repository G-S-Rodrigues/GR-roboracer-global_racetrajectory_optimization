import importlib
import os

import numpy as np
import pytest

from global_racetrajectory_optimization.mintime_options import (
    MintimeNotConverged,
    MintimeOptions,
)
from global_racetrajectory_optimization.trajectory_optimizer import (
    trajectory_optimizer,
)


def _run(case, export_dir, **fields):
    return trajectory_optimizer(
        case["inputs"],
        case["track"],
        "mintime",
        1.11,
        False,
        export_dir=str(export_dir),
        mintime=MintimeOptions(**fields),
    )


def test_tumfork_1050_a_max_iter_stop_leaves_resumable_state(
    oval_mintime_case, tmp_path
):
    out = tmp_path / "export"
    with pytest.raises(MintimeNotConverged) as info:
        _run(oval_mintime_case, out, max_iter=5)
    state = info.value.state_dir
    assert state is not None
    for name in ("w0", "lam_x0", "lam_g0"):
        assert os.path.isfile(os.path.join(state, name + ".csv")), name
    assert len(np.loadtxt(os.path.join(state, "w0.csv"))) > 100
    assert os.path.isfile(os.path.join(state, "solver_status.json"))


def test_tumfork_1070_seed_with_warm_start_dir_is_refused_early(
    oval_mintime_case, tmp_path, monkeypatch
):
    om = importlib.import_module(
        "global_racetrajectory_optimization.opt_mintime_traj.src.opt_mintime"
    )

    def boom(*a, **k):
        raise AssertionError("reached the NLP: should have been refused")

    monkeypatch.setattr(om, "opt_mintime", boom)
    seed = np.zeros((10, 7))
    with pytest.raises(ValueError, match="seed_line"):
        _run(
            oval_mintime_case,
            tmp_path / "e",
            seed_line=seed,
            warm_start_dir=str(tmp_path),
        )
