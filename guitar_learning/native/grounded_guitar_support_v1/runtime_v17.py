"""Observed R_Hip3 load compensation before the original finite lower effort cap."""
from pathlib import Path
from unittest.mock import patch
import numpy as np
from ..lower_body_release_v1 import controller_horizontal_v4 as original_controller
from ..lower_body_release_v1.control_math_v1 import stable_pd as original_stable_pd
from guitar_learning.native.paths import read, sha, verify
from .runtime_v14 import Controller as PreviousController


class Controller(PreviousController):
    def __init__(self, scene):
        super().__init__(scene)
        cfg = scene.cfg
        assert cfg['hip_load_bias_mode'] == 'finite_constant_native_RHip_load_bias_v1'
        self.load_spec = read(cfg['hip_load_bias_spec'])
        spec = self.load_spec
        report_path = Path(cfg['hip_load_bias_report'])
        report = read(report_path)
        assert report['eligible_for_finite_hip_load_bias'] and report['inputs_unchanged']
        assert verify(read(report_path.parent/'inputs_before.json'))
        assert sha(cfg['hip_load_bias_spec']) == cfg['hip_load_bias_spec_sha256'] == report['spec_sha256']
        assert spec['schema'] == 'finite_native_RHip_load_bias_v1'
        assert spec['joint_names'] == ['R_Hip_x', 'R_Hip_y', 'R_Hip_z']
        assert spec['joint_indices105'] == [scene.names.index(n) for n in spec['joint_names']]
        assert spec['ramp_s'] == [.15, .75] and spec['ramp'] == 'smoothstep'
        assert spec['apply_stage'] == 'lower_raw_before_original_native_cap' and spec['implicit_PD_RHS_unchanged'] is True
        assert spec['initial_candidate_sha256'] == cfg['candidate_sha256'] == sha(cfg['candidate'])
        assert sha(Path(spec['query_reference_run'])/'efforts240.json') == spec['reference_efforts_sha256']
        self.load_bias3 = np.array(spec['bias_Nm'], dtype=float)
        assert self.load_bias3.shape == (3,) and np.isfinite(self.load_bias3).all()
        assert spec['component_limit_Nm'] == 2. and spec['vector_norm_limit_Nm'] == 2.
        assert abs(self.load_bias3).max() <= 2. and np.linalg.norm(self.load_bias3) <= 2.
        assert all(j in scene.lower_indices and j not in scene.zero_indices for j in spec['joint_indices105'])
        assert np.array_equal(scene.pd_properties['effort'][spec['joint_indices105']], spec['native_effort_caps_Nm'])

    def lower_effort(self, state):
        s = self.s
        assert original_controller.stable_pd is original_stable_pd
        active_global = np.array([j for j in s.lower_indices if j not in s.zero_indices], dtype=int)
        assert len(active_global) == 16
        u = float(np.clip((s.steps/240-.15)/.6, 0., 1.))
        ramp = u*u*(3-2*u)
        bias = np.zeros(16)
        for j, value in zip(self.load_spec['joint_indices105'], self.load_bias3):
            bias[list(active_global).index(j)] = ramp*value
        captured = []
        def compensated(mass, error, velocity, kp, kd, gravity, dt):
            assert not captured and len(error) == 16 and dt == 1/240
            forcing = gravity+bias
            raw, predicted, feedback = original_stable_pd(mass, error, velocity, kp, kd, forcing, dt)
            captured.append(dict(human_gravity16_Nm=gravity.tolist(), observed_bias16_Nm=bias.tolist(),
                total_forcing16_Nm=forcing.tolist(), unbiased_raw_effort16_Nm=(gravity+feedback).tolist(),
                feedback16_Nm=feedback.tolist(), predicted_velocity16_rad_s=predicted.tolist(),
                raw_effort16_Nm=raw.tolist(), velocity16_rad_s=velocity.tolist(), error16_rad=error.tolist(),
                caps16_Nm=s.pd_properties['effort'][active_global].astype(float).tolist()))
            return raw, predicted, feedback
        with patch.object(original_controller, 'stable_pd', compensated):
            result, diagnostic = super().lower_effort(state)
        assert original_controller.stable_pd is original_stable_pd and len(captured) == 1
        record = captured[0]
        record.update(mode=s.cfg['hip_load_bias_mode'], spec_sha256=s.cfg['hip_load_bias_spec_sha256'],
            active_indices105=active_global.tolist(), active_joint_names=[s.names[j] for j in active_global],
            selected_joint_names=self.load_spec['joint_names'], selected_indices105=self.load_spec['joint_indices105'],
            observed_constant_bias3_Nm=self.load_bias3.tolist(), ramp_s=[.15, .75], ramp_fraction=ramp,
            apply_stage='lower_raw_before_original_native_cap', implicit_PD_RHS_unchanged=True,
            original_function_restored=True, submitted_lower24_Nm=result.astype(float).tolist(),
            scope='Observed steady actuator-load compensation, assumed external load approximately minus bias. Human gravity diagnosis and implicit predictor unchanged; original native cap and zero8 apply. Not a contact-force sensor or submitted-effort post-add.')
        diagnostic['observed_hip_load_bias'] = record
        assert s.native() == state
        return result, diagnostic
