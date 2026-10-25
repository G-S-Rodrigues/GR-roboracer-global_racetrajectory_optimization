#!/usr/bin/env bash
# The fork's gate. Runs inside the dev container (docker/docker-compose.yaml).
#   --fast   ruff on the fork's own files, then tier 1 (pytest tests/unit)
#   --ready  --fast plus tier 4 Robot, tag `fast`
#   --full   --fast plus every Robot test, `heavy` included
set -euo pipefail

usage() {
    echo "Usage: check.sh --fast|--ready|--full" >&2
}

if [[ $# -ne 1 ]] || [[ "$1" != "--fast" && "$1" != "--ready" && "$1" != "--full" ]]; then
    usage
    exit 2
fi
mode="$1"
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# R9: data lives in a submodule. Name the problem instead of failing on a
# missing file deep inside a test.
if [[ -f .gitmodules ]]; then
    while read -r path; do
        if [[ -z "$(ls -A "$path" 2>/dev/null)" ]]; then
            echo "check.sh: submodule '$path' is not initialised." >&2
            echo "  run: git submodule update --init" >&2
            exit 1
        fi
    done < <(git config --file .gitmodules --get-regexp '\.path$' | awk '{print $2}')
fi

echo "== ruff =="
ruff check .
ruff format --check .

echo "== tier 1: pytest tests/unit =="
pytest tests/unit

if [[ "$mode" == "--fast" ]]; then
    exit 0
fi

echo "== tier 4: robot =="
if [[ "$mode" == "--ready" ]]; then
    robot --pythonpath tests/lib:tests/fixtures --outputdir log/robot --include fast tests/acceptance
else
    robot --pythonpath tests/lib:tests/fixtures --outputdir log/robot tests/acceptance
fi
