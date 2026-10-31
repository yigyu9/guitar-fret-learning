"""Shared dimensions and observable coordination history; no native imports."""
HAND_STATE_DIM = 563
COORDINATION_FIELDS = ('coupled_hit_count', 'uncoupled_hit_count', 'has_coupled_error',
                       'best_abs_error_s', 'safety_invalidated', 'coordination_awarded')
COORDINATION_SCALES = (1., 1., 1., 7., 1., 1.)
COORDINATION_DIM = len(COORDINATION_FIELDS)
ACTOR_STATE_DIM = HAND_STATE_DIM + COORDINATION_DIM
STATE_DIM = 2*HAND_STATE_DIM + COORDINATION_DIM
SCHEMA = 'guitar_learning.joint.v1'
