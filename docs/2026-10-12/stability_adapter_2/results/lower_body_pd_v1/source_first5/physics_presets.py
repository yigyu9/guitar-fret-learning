"""Approved lower-body PD/solver diagnostics; baseline preserves prior behavior."""
PRESETS = {
    'baseline':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.},
    'solver16':{'position_iterations':16,'velocity_iterations':8,'leg_kp_scale':1.,'leg_kd_scale':1.},
    'leg_pd01':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':.1,'leg_kd_scale':.1},
    'leg_kd01':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':.1},
    'solver16_leg_kd01':{'position_iterations':16,'velocity_iterations':8,'leg_kp_scale':1.,'leg_kd_scale':.1},
}


def leg_indices(names):
    prefixes = tuple(side+'_'+body+'_' for side in ('L','R') for body in ('Hip','Knee','Ankle','Toe'))
    return [i for i,name in enumerate(names) if name.startswith(prefixes)]
