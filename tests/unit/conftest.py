import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
for sub in ("lib", "fixtures"):
    path = os.path.join(TESTS, sub)
    if path not in sys.path:
        sys.path.insert(0, path)
