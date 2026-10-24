import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
for sub in ("lib", "fixtures"):
    path = os.path.join(TESTS, sub)
    if path not in sys.path:
        sys.path.insert(0, path)


import pytest  # noqa: E402


@pytest.fixture
def oval_case(tmp_path):
    """The oval track and GR-roboracer's rendered gym-limits ini."""
    import make_oval

    track = make_oval.write_oval_track(str(tmp_path / "oval.csv"))
    inputs = make_oval.write_inputs(
        str(tmp_path / "inputs"),
        make_oval.INI_F1TENTH_GYM_LIMITS + make_oval.SHORTEST_PATH_LINE,
        "f1tenth_gym_limits",
    )
    return {"track": track[:-4], "inputs": inputs, "dir": tmp_path}
