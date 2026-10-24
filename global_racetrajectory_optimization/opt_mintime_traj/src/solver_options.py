"""IPOPT options for opt_mintime (moved out of opt_mintime.py's inline dict)."""


def ipopt_opts(base, options=None, warm_start=False):
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
    return opts
