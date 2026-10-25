"""The oval track fixture and the TUM inputs the tests feed it (code, no data).

R9: nothing here is a data file. The oval is generated; the ini text is the
config GR-roboracer renders (kept as constants, with their source); the two
veh_dyn_info tables are generated from the formula in GR-roboracer's
config/vehicles/*/ (flat ax and ay limits, the gym's Param).

Python 3.8 and numpy only: it also runs in GR-roboracer's dev container.
"""

import os

import numpy as np

# GR-roboracer a61e5fa, raceline/raceline/optimize.py tum_ini(vehicle), rendered
# for config/vehicles/f1tenth_default.yaml and f1tenth_gym_limits.yaml.
INI_F1TENTH_DEFAULT = """\
[GENERAL_OPTIONS]
ggv_file="ggv.csv"
ax_max_machines_file="ax_max_machines.csv"
stepsize_opts={"stepsize_prep": 0.05,
               "stepsize_reg": 0.2,
               "stepsize_interp_after_opt": 0.1}
reg_smooth_opts={"k_reg": 3,
                 "s_reg": 1}
veh_params={"v_max": 3.0,
            "length": 0.58,
            "width": 0.300000,
            "mass": 3.74,
            "dragcoeff": 0.0,
            "curvlim": 1.281191572,
            "g": 9.81}
vel_calc_opts={"dyn_model_exp": 1.0,
               "vel_profile_conv_filt_window": null}

[OPTIMIZATION_OPTIONS]
optim_opts_mincurv={"width_opt": 0.8,
                    "iqp_iters_min": 5,
                    "iqp_curverror_allowed": 0.1}
"""
INI_F1TENTH_GYM_LIMITS = """\
[GENERAL_OPTIONS]
ggv_file="ggv.csv"
ax_max_machines_file="ax_max_machines.csv"
stepsize_opts={"stepsize_prep": 0.05,
               "stepsize_reg": 0.2,
               "stepsize_interp_after_opt": 0.1}
reg_smooth_opts={"k_reg": 3,
                 "s_reg": 1}
veh_params={"v_max": 20.0,
            "length": 0.58,
            "width": 0.310000,
            "mass": 3.74,
            "dragcoeff": 0.0,
            "curvlim": 1.348436777,
            "g": 9.81}
vel_calc_opts={"dyn_model_exp": 1.0,
               "vel_profile_conv_filt_window": null}

[OPTIMIZATION_OPTIONS]
optim_opts_mincurv={"width_opt": 0.8,
                    "iqp_iters_min": 5,
                    "iqp_curverror_allowed": 0.1}
"""

# GR-roboracer never renders optim_opts_shortest_path (it does not call
# shortest_path); TUM's ini parser needs it for that type. The line is
# upstream's own params/racecar.ini:65, appended for shortest_path only.
SHORTEST_PATH_LINE = 'optim_opts_shortest_path={"width_opt": 3.4}\n'

# GR-roboracer part 8b, .scratch/part8b-harness/p8b-step1/D/W1a-gym-from-
# defaultRB/inputs/racecar_f110.ini: the gym vehicle, tyre set B, scale 0.98,
# stepsize_reg (h) 0.5. The min-time ini of the S1c / W1a solves.
INI_MINTIME_GYM = """\
[GENERAL_OPTIONS]
ggv_file="ggv.csv"
ax_max_machines_file="ax_max_machines.csv"
stepsize_opts={"stepsize_prep": 0.05,
               "stepsize_reg": 0.5,
               "stepsize_interp_after_opt": 0.1}
reg_smooth_opts={"k_reg": 3,
                 "s_reg": 1}
veh_params={"v_max": 20.0,
            "length": 0.58,
            "width": 0.310000,
            "mass": 3.74,
            "dragcoeff": 0.0,
            "curvlim": 1.348436777,
            "g": 9.81}
vel_calc_opts={"dyn_model_exp": 1.0,
               "vel_profile_conv_filt_window": null}

curv_calc_opts={"d_preview_curv": 2.0, "d_review_curv": 2.0, "d_preview_head": 1.0, "d_review_head": 1.0}

[OPTIMIZATION_OPTIONS]
optim_opts_mincurv={"width_opt": 0.8,
                    "iqp_iters_min": 5,
                    "iqp_curverror_allowed": 0.1}
optim_opts_mintime={"width_opt": 1.11, "penalty_delta": 1.0, "penalty_F": 0.1, "mue": 1.027922, "n_gauss": 5, "dn": 0.025, "limit_energy": false, "energy_limit": 2.0, "safe_traj": false, "ax_pos_safe": null, "ax_neg_safe": null, "ay_safe": null, "w_tr_reopt": 1.0, "w_veh_reopt": 0.8, "w_add_spl_regr": 0.0, "step_non_reg": 0, "eps_kappa": 0.02}
vehicle_params_mintime={"wheelbase_front": 0.15875, "wheelbase_rear": 0.17145, "track_width_front": 0.281, "track_width_rear": 0.281, "cog_z": 0.074, "I_z": 0.04712, "liftcoeff_front": 0.0, "liftcoeff_rear": 0.0, "k_brake_front": 0.5, "k_drive_front": 0.0, "k_roll": 0.5, "t_delta": 0.1, "t_drive": 0.1, "t_brake": 0.1, "power_max": 255.1114885704, "f_drive_max": 34.856052, "f_brake_max": 34.856052, "delta_max": 0.4189}
tire_params_mintime={"c_roll": 0.0, "f_z0": 8.6, "B_front": 3.9316666666666666, "C_front": 1.2, "eps_front": -0.1, "E_front": 0.85, "B_rear": 4.546833333333334, "C_rear": 1.2, "eps_rear": -0.1, "E_rear": 0.85}
pwr_params_mintime={"pwr_behavior": false}
"""

# (v_mps, ax_max, ay_max) of the gym vehicle (Param @1b4eb3f): flat limits.
_GGV = {
    "f1tenth_default": (2.0, 10.289709),
    "f1tenth_gym_limits": (9.51, 10.289709),
}
# The gym vehicle's ax_max_machines.csv falls from 9.51 to 3.48 over 0-20 m/s;
# a 5-point table of the same shape is enough here (inputs are identical on
# both sides of a comparison, and no test asserts these values).
_AX_MACHINES = {
    "f1tenth_default": [(0.0, 2.0), (20.0, 2.0)],
    "f1tenth_gym_limits": [
        (0.0, 9.51),
        (5.0, 9.51),
        (10.0, 6.0),
        (15.0, 4.2),
        (20.0, 3.480185),
    ],
}


def oval_centerline(straight=8.0, radius=3.0, spacing=0.25):
    """A stadium centerline, counter-clockwise, open (last != first)."""
    perim = 2 * straight + 2 * np.pi * radius
    n = int(round(perim / spacing))
    s = np.arange(n) * (perim / n)
    seg = [straight, np.pi * radius, straight, np.pi * radius]
    edges = np.cumsum([0.0] + seg)
    xy = np.empty((n, 2))
    for i, si in enumerate(s):
        k = int(np.searchsorted(edges, si, side="right") - 1)
        u = si - edges[k]
        if k == 0:
            xy[i] = (u, 0.0)
        elif k == 1:
            a = -np.pi / 2 + u / radius
            xy[i] = (straight + radius * np.cos(a), radius + radius * np.sin(a))
        elif k == 2:
            xy[i] = (straight - u, 2 * radius)
        else:
            a = np.pi / 2 + u / radius
            xy[i] = (radius * np.cos(a), radius + radius * np.sin(a))
    return xy


def write_oval_track(path, half_width=1.5):
    """TUM's track format: x_m, y_m, w_tr_right_m, w_tr_left_m."""
    xy = oval_centerline()
    w = np.full(len(xy), half_width)
    np.savetxt(
        path,
        np.column_stack([xy, w, w]),
        delimiter=",",
        header="x_m,y_m,w_tr_right_m,w_tr_left_m",
        fmt="%.9f",
    )
    return path


def write_inputs(inputs_dir, ini_text, vehicle="f1tenth_gym_limits"):
    """TUM's inputs directory: the ini and veh_dyn_info/{ggv,ax_max_machines}."""
    vdi = os.path.join(inputs_dir, "veh_dyn_info")
    os.makedirs(vdi, exist_ok=True)
    ax, ay = _GGV[vehicle]
    with open(os.path.join(vdi, "ggv.csv"), "w") as fh:
        fh.write("# v_mps,ax_max_mps2,ay_max_mps2\n")
        for v in range(21):
            fh.write(f"{v:.1f},{ax:.6f},{ay:.6f}\n")
    with open(os.path.join(vdi, "ax_max_machines.csv"), "w") as fh:
        fh.write("#v_mps,ax_max_machines_mps2\n")
        for v, a in _AX_MACHINES[vehicle]:
            fh.write(f"{v:.2f},{a:.6f}\n")
    with open(os.path.join(inputs_dir, "racecar_f110.ini"), "w") as fh:
        fh.write(ini_text)
    return inputs_dir
