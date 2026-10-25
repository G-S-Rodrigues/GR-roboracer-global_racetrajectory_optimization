"""IPOPT options for opt_mintime (moved out of opt_mintime.py's inline dict)."""

import dataclasses
import json
import os
import time

import casadi as ca
import numpy as np


def ipopt_opts(base, options=None, warm_start=False, callback=None):
    """The casadi ``nlpsol`` options dict.

    With ``options`` None (or a default ``MintimeOptions``) this is exactly
    upstream's dict: ``base`` plus ``ipopt.max_iter`` 2000 and ``ipopt.tol``
    1e-7, and under ``warm_start`` the five warm-start entries at 1e-3.
    """
    max_iter = 2000 if options is None else options.max_iter
    push = 1e-3 if options is None else options.warm_start_bound_push
    opts = dict(base)
    opts["ipopt.max_iter"] = max_iter
    opts["ipopt.tol"] = 1e-7
    if warm_start:
        opts.update(
            {
                "ipopt.warm_start_init_point": "yes",
                "ipopt.warm_start_bound_push": push,
                "ipopt.warm_start_mult_bound_push": push,
                "ipopt.warm_start_slack_bound_push": push,
                "ipopt.mu_init": 1e-3,
            }
        )
    if options is not None and options.mu_init is not None:
        opts["ipopt.mu_init"] = options.mu_init
    if callback is not None:
        opts["iteration_callback"] = callback
    return opts


STATE_FILES = ("w0", "lam_x0", "lam_g0")


def save_state(out_dir, x, lam_x, lam_g):
    """Atomically write TUM's warm-start files ``w0/lam_x0/lam_g0.csv``."""
    os.makedirs(out_dir, exist_ok=True)
    for name, vec in (("w0", x), ("lam_x0", lam_x), ("lam_g0", lam_g)):
        tmp = os.path.join(out_dir, name + ".tmp")
        np.savetxt(tmp, np.asarray(vec).ravel())
        os.replace(tmp, os.path.join(out_dir, name + ".csv"))


class StopAndSave(ca.Callback):
    """IPOPT iteration callback: stop after a wall time, save state.

    The state files are TUM's warm-start names (``w0``, ``lam_x0``, ``lam_g0``
    ``.csv``, one value per line) plus ``iter.txt``, written atomically
    (tmp + ``os.replace``) every ``save_every`` iterations and at the stop. The
    clock is injected, and the timer starts at ``start()`` (the solver call),
    not at construction or import. ``first_f`` / ``last_f`` are the objective
    at the first and the latest callback.
    """

    def __init__(
        self,
        name,
        nx,
        ng,
        out_dir,
        max_wall_time_s=None,
        save_every=0,
        clock=time.perf_counter,
        opts=None,
    ):
        ca.Callback.__init__(self)
        self.nx, self.ng = nx, ng
        self.out_dir = out_dir
        self.max_wall_time_s = max_wall_time_s
        self.save_every = save_every
        self.clock = clock
        self.it = 0
        self.stopped = False
        self.first_f = None
        self.last_f = None
        self._t0 = None
        self.construct(name, opts or {})

    def start(self):
        self._t0 = self.clock()

    def get_n_in(self):
        return ca.nlpsol_n_out()

    def get_n_out(self):
        return 1

    def get_name_in(self, i):
        return ca.nlpsol_out(i)

    def get_name_out(self, i):
        return "ret"

    def get_sparsity_in(self, i):
        name = ca.nlpsol_out(i)
        if name == "f":
            return ca.Sparsity.scalar()
        if name in ("x", "lam_x"):
            return ca.Sparsity.dense(self.nx)
        if name in ("g", "lam_g"):
            return ca.Sparsity.dense(self.ng)
        return ca.Sparsity(0, 0)

    def _save(self, values):
        save_state(self.out_dir, values["x"], values["lam_x"], values["lam_g"])
        tmp = os.path.join(self.out_dir, "iter.tmp")
        with open(tmp, "w") as fh:
            fh.write(f"{self.it} {self.clock() - self._t0:.3f}\n")
        os.replace(tmp, os.path.join(self.out_dir, "iter.txt"))

    def eval(self, arg):
        if self._t0 is None:
            self.start()
        self.it += 1
        values = {
            ca.nlpsol_out(i): arg[i].full() for i in range(ca.nlpsol_n_out())
        }
        self.last_f = float(values["f"].ravel()[0])
        if self.first_f is None:
            self.first_f = self.last_f
        stop = (
            self.max_wall_time_s is not None
            and self.clock() - self._t0 > self.max_wall_time_s
        )
        if stop:
            self.stopped = True
        if stop or (self.save_every and self.it % self.save_every == 0):
            self._save(values)
        return [1 if stop else 0]


def write_solver_status(
    export_path,
    status,
    iterations,
    wall_time_s,
    objective,
    first_f,
    options,
    x0_source,
):
    """``<export_dir>/mintime/solver_status.json``: how a min-time solve ended.

    ``export_path`` is the min-time directory, beside the state files."""
    used = dataclasses.asdict(options)
    seed = used.pop("seed_line")
    used["seed_line_shape"] = None if seed is None else list(seed.shape)
    record = {
        "status": status,
        "iterations": iterations,
        "wall_time_s": wall_time_s,
        "objective": objective,
        "iteration0_objective": first_f,
        "x0_source": x0_source,
        "options": used,
    }
    os.makedirs(export_path, exist_ok=True)
    tmp = os.path.join(export_path, "solver_status.tmp")
    with open(tmp, "w") as fh:
        json.dump(record, fh, indent=1)
    os.replace(tmp, os.path.join(export_path, "solver_status.json"))
