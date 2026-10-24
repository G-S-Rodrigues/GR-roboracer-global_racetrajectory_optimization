"""Options for the fork's min-time optimizer (all defaults reproduce upstream).

Pass an instance as ``trajectory_optimizer(..., mintime=MintimeOptions(...))``.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


class MintimeNotConverged(SystemExit):
    """The min-time NLP did not converge (exit code 1, as upstream's exit).

    Raised only when ``mintime`` was given; the default path keeps
    ``sys.exit(1)``. ``state_dir`` holds the saved warm-start files, if any.
    """

    def __init__(self, code=1, status=None, iterations=None, state_dir=None):
        super().__init__(code)
        self.status = status
        self.iterations = iterations
        self.state_dir = state_dir


@dataclass
class MintimeOptions:
    max_iter: int = 2000
    # None: IPOPT's own default (or 1e-3 under warm start, as upstream).
    mu_init: Optional[float] = None
    # Stop IPOPT after this many seconds from the solver call, saving state.
    max_wall_time_s: Optional[float] = None
    # Save w0/lam_x0/lam_g0 every N iterations (0: only at a stop).
    save_every: int = 0
    # Directory holding w0/lam_x0/lam_g0.csv to resume from.
    warm_start_dir: Optional[str] = None
    warm_start_bound_push: float = 1e-3
    # An (M, 7) TUM trajectory array (s;x;y;psi;kappa;v;a_x) to seed from.
    seed_line: Optional[np.ndarray] = None
    # Replace tph's 15-point polyline arc length by the exact one (Q11).
    exact_arc_length: bool = True


def require_wired(options):
    """Step 3 only: fields whose behaviour a later step wires refuse to run."""
    for name, step in (
        ("max_wall_time_s", 4),
        ("warm_start_dir", 4),
        ("seed_line", 5),
    ):
        if getattr(options, name) is not None:
            raise NotImplementedError(f"{name}: Step {step}")
    if options.save_every:
        raise NotImplementedError("save_every: Step 4")
