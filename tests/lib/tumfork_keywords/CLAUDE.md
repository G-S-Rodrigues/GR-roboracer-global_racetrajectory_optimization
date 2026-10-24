# tumfork_keywords

Purpose: run full TUM solves in a subprocess and read the outcome back, for the tier-4 Robot suites in
`tests/acceptance/`.

A plain `PYTHONPATH` library (`scripts/check.sh` passes `--pythonpath tests/lib`), not a package.
`runner.py` starts `<python> -m tumfork_keywords.solve ...` so the exit code, wall time and a `sys.exit`
are observable; `<python>` is `/opt/venv/bin/python` (this tree, editable) or `/opt/upstream/bin/python`
(unmodified ForzaETH b1b38ec). `solve.py` is the subprocess body. `keywords.py` is a thin Robot adapter:
new capability goes in `runner.py` first.

The one trap: an upstream run must have a `cwd` outside `/ws`. `python -m` puts the cwd first on
`sys.path`, so from `/ws` the "upstream" run would import this branch and 4010 would compare it with
itself. `runner.run_solve` enforces it.

Test: `robot --pythonpath tests/lib:tests/fixtures --outputdir log/robot --include fast tests/acceptance`.
