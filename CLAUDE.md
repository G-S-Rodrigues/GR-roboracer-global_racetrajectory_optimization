# GR-roboracer-global_racetrajectory_optimization

Owner's fork of ForzaETH/global_racetrajectory_optimization (TUM), pinned at b1b38ec upstream. It adds
min-time solver options, warm start/resume, an injectable seed, a caller-chosen export dir and an exact
arc length, all behind defaults that leave the upstream call unchanged. GR-roboracer pins this repo.

Everything runs in the `gr-tum-dev` container (Python 3.8.20, `/opt/venv`; unmodified upstream in
`/opt/upstream`): `docker compose -f docker/docker-compose.yaml up -d dev`.

Gate: `docker exec gr-tum-dev bash -lc 'cd /ws && ./scripts/check.sh --ready'` (`--fast` is tier 1 only,
`--full` adds the `heavy` Robot tests). Test IDs are `TUMFORK-<tier><nnn>`; see `docs/agents/testing.md`.
Data is the submodule `third_party/GR-roboracer-data`: no fixture CSV is committed here.

The one trap: min-curv output must stay byte-identical to upstream (TUMFORK-4010). Do not edit its
code path, and do not reformat upstream files.

Upstream's `.gitignore` has a bare `lib/` that would hide `tests/lib/`; `!tests/lib/` undoes it.
