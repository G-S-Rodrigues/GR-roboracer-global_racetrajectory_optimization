import os

import global_racetrajectory_optimization as tum


def test_tumfork_1000_package_imports_from_the_working_tree():
    # The editable install is the code under test, not site-packages.
    assert os.path.abspath(tum.__file__).startswith("/ws/"), tum.__file__
