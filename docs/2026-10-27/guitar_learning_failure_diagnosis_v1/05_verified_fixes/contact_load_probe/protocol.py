"""Fixed observation contract; no native or numerical imports at module load."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DIAG = HERE.parents[1]
BASELINE = DIAG/'04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7'
REFERENCE = DIAG/'03_short_learning/reference_middle_row8_v2.json'
CONDITIONS = (('initial_zero', 'initial.pt', 'zero', 0),
              ('initial_reference', 'initial.pt', 'reference', 0),
              ('cp50_policy', 'evaluation_000050.pt', 'policy', 50),
              ('final300_policy', 'final.pt', 'policy', 300))
ENVIRONMENTS, CONTROLS, ENDPOINTS, BYTE_LIMIT = 128, 218, 872, 100_000_000
REWARDS = ('song_left_approach', 'song_left_contact', 'song_clean_hold',
           'song_left_success', 'song_wrong_press', 'song_performance_deficit',
           'song_finger_standby', 'song_thumb_support', 'action_change')
NOTE = ('contact_progress', 'clean', 'wrong', 'missing', 'clean_streak',
        'best_clean_streak', 'left', 'released', 'release_s')

# Per environment, bounded dense fields; inactive first-attempt rows are zero.
PHYSICS = dict(clock=('i4', ()), local_time_s=('f8', ()), source_time_s=('f8', ()),
    first_attempt=('?', ()), tick_physical_failure=('?', ()), tick_wrist_failure=('?', ()),
    failure_latched=('?', ()), candidate=('?', ()), wrong=('?', ()), positive=('?', ()),
    position_geometry_any=('?', ()), facing_geometry_any=('?', ()),
    nearest_position_geometry=('?', ()), nearest_facing_geometry=('?', ()),
    nearest_sample_index=('i2', ()), nearest_distance_m=('f4', ()), nearest_height_m=('f4', ()),
    nearest_normal_cos=('f4', ()), nearest_point_W=('f4', (3,)), nearest_normal_W=('f4', (3,)),
    actual_LH21=('f4', (21,)), target_LH21=('f4', (21,)), qd_selected4=('f4', (4,)),
    distal_force_W=('f4', (5, 3)), guitar_pose=('f4', (13,)),
    selected_distal_pose=('f4', (13,)), thumb3_pose=('f4', (13,)),
    point_jacobian_W=('f4', (3, 4)), point_velocity_W=('f4', (3,)),
    point_velocity_predicted_all_dof_W=('f4', (3,)))
CONTROL = dict(clock=('i4', ()), first_attempt=('?', ()), failure_latched=('?', ()),
    policy_action_selected4=('f4', (4,)), executed_action_selected4=('f4', (4,)),
    reward=('f4', ()), cost=('f4', ()), reward_increment=('f8', (9,)),
    reward_cumulative=('f8', (9,)), note_ledger=('f8', (9,)))


def condition(checkpoint, control):
    for name, filename, expected, update in CONDITIONS:
        if Path(checkpoint).resolve() == (BASELINE/'train'/filename).resolve() and control == expected:
            return dict(name=name, checkpoint=str(Path(checkpoint).resolve()), control=control, updates=update)
    raise ValueError('Only the four predeclared corrected-baseline checkpoint/control pairs are allowed')


def failure_latch(first, previous, physical, wrist):
    """Failure endpoint itself and every later first-attempt endpoint are censored."""
    return first & (previous | physical | wrist)


class Trace:
    """Fixed-size selected-field CPU capture, never an unbounded body trace."""
    def __init__(self, schema, maximum):
        import numpy as np
        self.schema, self.maximum, self.count = schema, maximum, 0
        self.arrays = {k: np.zeros((maximum, ENVIRONMENTS, *shape), dtype=dtype)
                       for k, (dtype, shape) in schema.items()}

    def append(self, row):
        import numpy as np
        if self.count >= self.maximum or set(row) != set(self.schema):
            raise ValueError('Capture endpoint/field budget exceeded')
        first = np.asarray(row['first_attempt'], dtype=bool)
        for key, target in self.arrays.items():
            value = np.asarray(row[key])
            if value.shape != target.shape[1:] or not np.isfinite(value).all():
                raise ValueError('Invalid selected capture field: '+key)
            target[self.count] = np.where(first.reshape((ENVIRONMENTS,)+(1,)*(value.ndim-1)), value, 0)
        self.count += 1

    def values(self):
        return {k: v[:self.count] for k, v in self.arrays.items()}

    @property
    def nbytes(self):
        return sum(v.nbytes for v in self.arrays.values())


def protocol():
    return dict(schema='diagnostic.contact_load_observation.v1', environments=ENVIRONMENTS,
        first_attempt_quota=[1]*ENVIRONMENTS, controls_max=CONTROLS, physics_endpoints_max=ENDPOINTS,
        physics_hz=240, control_hz=60, substeps=4, uncompressed_selected_output_limit_bytes=BYTE_LIMIT,
        conditions=[dict(name=n, checkpoint=str(BASELINE/'train'/p), control=c, updates=u)
                    for n, p, c, u in CONDITIONS],
        physics_fields=PHYSICS, control_fields=CONTROL, reward_order=REWARDS, note_order=NOTE,
        failure='post original substep tick_physical_failure includes native tick latch; tick_wrist_failure includes normal/severe latch; own first-attempt failure_latched includes this endpoint and later endpoints',
        point='nearest designated reward pad sample from original surface_sample; any-sample position/facing/positive gates can be witnessed by another sample; no same-point candidate claim',
        projection='world point Jacobian selected4 and qtarget-q/action projections are local linear diagnostics, not penetration, causal proof, contact-pair pressure or force caps',
        mutation='no actions, settings, native state, source, thresholds, rewards, failure or policy/trainer/RNG path changes')
