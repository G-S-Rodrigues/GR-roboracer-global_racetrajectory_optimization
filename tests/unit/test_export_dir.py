import os

import pytest

import global_racetrajectory_optimization as tum
from global_racetrajectory_optimization.trajectory_optimizer import (
    trajectory_optimizer,
)

MODULE_DIR = os.path.dirname(os.path.abspath(tum.__file__))


def _run(case, **kwargs):
    return trajectory_optimizer(
        case["inputs"], case["track"], "shortest_path", 0.4, False, **kwargs
    )


def test_tumfork_1060_default_exports_under_the_module(oval_case):
    _run(oval_case)
    assert os.path.isdir(os.path.join(MODULE_DIR, "outputs"))


def test_tumfork_1060_export_dir_is_the_output_root(oval_case, tmp_path):
    # Only min-time and the lap-time matrix write files (TUM's own choice), so
    # for shortest_path the observable is the directory itself; the files under
    # it are asserted by TUMFORK-4020.
    out = str(tmp_path / "export" / "nested")
    _run(oval_case, export_dir=out)
    assert os.path.isdir(out)


def test_tumfork_1060_a_path_inside_the_package_is_refused(oval_case):
    inside = os.path.join(MODULE_DIR, "outputs_should_not_exist")
    with pytest.raises(ValueError):
        _run(oval_case, export_dir=inside)
    assert not os.path.exists(inside)
