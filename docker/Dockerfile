# The fork's development image: Python 3.8.20 (what TUM's pins need), the
# GR-roboracer tum_env closure, and two venvs:
#   /opt/venv      the working tree at /ws, installed editable (code under test)
#   /opt/upstream  unmodified ForzaETH b1b38ec, for the byte-identity test
#                  TUMFORK-4010. Same closure, so only the TUM code differs.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_LINK_MODE=copy \
    MPLBACKEND=Agg

# build-essential: quadprog 0.1.12 has no 3.8 wheel and builds from sdist.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

ARG UV_VERSION=0.13.2
RUN curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" \
        | env UV_INSTALL_DIR=/usr/local/bin sh

ARG PYTHON_VERSION=3.8.20
RUN uv python install "${PYTHON_VERSION}"

# The closure is pinned and installed --no-deps: nothing resolves at build
# time. `uv pip check` is deliberately absent: tph 0.78 requires quadprog==0.1.7,
# which does not import; GR-roboracer's tum_env overrides it to 0.1.12 and so
# do we (the one known disagreement).
COPY docker/requirements-lock.txt /tmp/requirements-lock.txt
ARG UPSTREAM_SHA=b1b38ecfefec7200d5bcb243f115af1d795b3766
RUN uv venv --python "${PYTHON_VERSION}" /opt/venv \
    && uv pip install --python /opt/venv/bin/python --no-deps \
        -r /tmp/requirements-lock.txt \
    && uv venv --python "${PYTHON_VERSION}" /opt/upstream \
    && uv pip install --python /opt/upstream/bin/python --no-deps \
        -r /tmp/requirements-lock.txt \
    && uv pip install --python /opt/upstream/bin/python --no-deps \
        "global-racetrajectory-optimization @ git+https://github.com/ForzaETH/global_racetrajectory_optimization@${UPSTREAM_SHA}" \
    && rm /tmp/requirements-lock.txt

# Editable install of the working tree. The compose file bind-mounts the repo
# over /ws, so edits are live; the .pth written here points at /ws.
COPY setup.py /ws/setup.py
COPY global_racetrajectory_optimization /ws/global_racetrajectory_optimization
RUN uv pip install --python /opt/venv/bin/python --no-deps -e /ws

ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin
WORKDIR /ws
