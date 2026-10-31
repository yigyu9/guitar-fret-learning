"""Approved lower-body PD/solver diagnostics; baseline preserves prior behavior."""
PRESETS = {
    'baseline':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.},
    'solver16':{'position_iterations':16,'velocity_iterations':8,'leg_kp_scale':1.,'leg_kd_scale':1.},
    'leg_pd01':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':.1,'leg_kd_scale':.1},
    'leg_kd01':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':.1},
    'solver16_leg_kd01':{'position_iterations':16,'velocity_iterations':8,'leg_kp_scale':1.,'leg_kd_scale':.1},
    'substeps4':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.,'substeps':4},
    'substeps8':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.,'substeps':8},
    'leg_effort_pd':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.,'leg_drive':'effort'},
    'leg_passive':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':0.,'leg_kd_scale':0.,'leg_drive':'none'},
    'depen01':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.,'max_depenetration_velocity':.1},
    'solver16_depen01':{'position_iterations':16,'velocity_iterations':8,'leg_kp_scale':1.,'leg_kd_scale':1.,'max_depenetration_velocity':.1},
    'leg_effort_depen01':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.,'leg_drive':'effort','max_depenetration_velocity':.1},
    'pgs':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':1.,'solver_type':0},
    'pgs16':{'position_iterations':16,'velocity_iterations':8,'leg_kp_scale':1.,'leg_kd_scale':1.,'solver_type':0},
    'leg_kd0':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':0.},
    'pgs_leg_kd0':{'position_iterations':4,'velocity_iterations':2,'leg_kp_scale':1.,'leg_kd_scale':0.,'solver_type':0},
}


def leg_indices(names):
    prefixes = tuple(side+'_'+body+'_' for side in ('L','R') for body in ('Hip','Knee','Ankle','Toe'))
    return [i for i,name in enumerate(names) if name.startswith(prefixes)]
