"""Shared finite native control; prepared resets are implemented separately."""
import numpy as np
from guitar_learning.native.paths import rebase_paths
from guitar_learning.runtime.prepared_reset_v1 import (load_prepared_reset_contract,
    _restore_once, _state_all, ControlPhaseView, CONTROL_PHASE_OFFSET_STEPS)






class NativeSession:
    """Original scene/controller, with only the final post-preparation target owner changed."""
    def __init__(self, config, out):
        # Do not import tab2body.env.base: its fixed-guitar state writes are incompatible.
        import isaacgym
        from guitar_learning.native.front_facing_ready_v1.runtime_v15 import Scene
        from guitar_learning.native.front_facing_ready_v1.runtime_v12 import Controller
        self.scene = None
        try:
            self.scene = Scene({**config, 'attempt_out': str(out)})
            self.controller = Controller(self.scene)
        except BaseException:
            self.close()
            raise

    def prepare_tick(self):
        return self.controller.targets()

    def submit_policy_target(self, target):
        from guitar_learning.native.lower_body_release_v1.scene_v8 import Scene as FinalTargetScene
        scene = self.scene
        named, diagnostic = self.controller.apply(dict(zip(scene.names, target.tolist())))
        lower_target = np.array([named[name] for name in scene.names])
        upper = [i for i in range(105) if i not in scene.lower_indices]
        if not np.array_equal(lower_target[upper], target[upper]):
            raise RuntimeError('Foot maintenance modified policy/held upper channels')
        # Bypass Motion/LH IK and scheduled target corrections. Original final limiter/
        # native POSITION submission is called once; existing effort controller follows.
        row = FinalTargetScene.command(scene, named)
        row['foot_world_target_IK'] = diagnostic
        row['stage'] = 'policy_handoff'
        self.controller.target_rows.append(row)
        return row

    def integrate(self):
        effort, diagnostic = self.controller.effort()
        scene = self.scene
        if not np.isfinite(effort).all() or np.any(np.abs(effort) > scene.pd_properties['effort'] + 1e-6):
            raise RuntimeError('Original finite effort cap violated')
        if np.any(effort[scene.zero_indices] != 0) or np.any(effort[scene.position_indices] != 0):
            raise RuntimeError('Mixed POSITION/effort ownership violated')
        scene.integrate105(effort)
        return diagnostic

    def close(self):
        if self.scene is not None:
            self.scene.close()
            self.scene = None


class PreparedSession(NativeSession):
    def __init__(self, config, out):
        contract = load_prepared_reset_contract()
        config = rebase_paths(dict(config))
        if dict(config) != contract['config']:
            raise ValueError('Prepared reset requires the exact original035 baseline config')
        super().__init__(config, out)
        try:
            # Original constructor references/FK are established before restoring q.
            description = _restore_once(self.scene, contract, _state_all())
            self.seed_target105 = contract['target105'].copy()
            self.controller.s = ControlPhaseView(self.scene)
            self.prepared_reset_description = dict(description, source_sha256=contract['source_sha256'], source_snapshot_step=CONTROL_PHASE_OFFSET_STEPS,
                actual_initial_physics_step=self.scene.steps, control_phase_offset_steps=CONTROL_PHASE_OFFSET_STEPS,
                control_phase_scope='Explicit mature support-control phase only; no22s physics replay or advancement of actual scene time',
                initialization_scope='One reset-only DOF/guitar/target submission; fixed root/chair unchanged; no per-step state injection')
        except BaseException:
            self.close()
            raise

    def prepare_tick(self):
        return self.submit_policy_target(self.seed_target105)

    def integrate(self):
        diagnostic = super().integrate()
        diagnostic['control_phase_step_before'] = self.scene.steps - 1 + CONTROL_PHASE_OFFSET_STEPS
        diagnostic['physics_step_before'] = self.scene.steps - 1
        diagnostic['legacy_nested_step_fields_scope'] = 'Original controller metadata nested step fields use mature control-phase coordinates; actual physics_step_before above uses real reset time'
        return diagnostic
