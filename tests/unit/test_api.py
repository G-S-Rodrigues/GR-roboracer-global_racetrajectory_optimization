import inspect

import pytest

from global_racetrajectory_optimization.mintime_options import (
    MintimeNotConverged,
    MintimeOptions,
)
from global_racetrajectory_optimization.trajectory_optimizer import (
    trajectory_optimizer,
)


def test_tumfork_1070_old_positional_call_still_works(oval_case):
    out = trajectory_optimizer(
        oval_case["inputs"], oval_case["track"], "shortest_path", 0.4, False
    )
    assert len(out) == 4


def test_tumfork_1070_new_arguments_are_keyword_only():
    params = inspect.signature(trajectory_optimizer).parameters
    for name in ("export_dir", "mintime"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert params[name].default is None


def test_tumfork_1070_mintime_options_need_a_mintime_run(oval_case):
    with pytest.raises(ValueError):
        trajectory_optimizer(
            oval_case["inputs"],
            oval_case["track"],
            "shortest_path",
            0.4,
            False,
            mintime=MintimeOptions(),
        )


def test_tumfork_1070_not_converged_is_system_exit_code_1():
    err = MintimeNotConverged(1, status="x", iterations=3, state_dir="/d")
    assert isinstance(err, SystemExit)
    assert err.code == 1
    assert (err.status, err.iterations, err.state_dir) == ("x", 3, "/d")
    with pytest.raises(SystemExit) as info:
        raise MintimeNotConverged()
    assert info.value.code == 1
