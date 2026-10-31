"""Shared finite native control; prepared resets are implemented separately."""
import numpy as np


ZERO_RANGE_NAMES = frozenset(side + '_' + part + '_' + axis for side in ('L', 'R') for part in ('Knee', 'Toe') for axis in 'yz')


def target_rates(names):
    lower = tuple(side + '_' + part + '_' for side in ('L', 'R') for part in ('Hip', 'Knee', 'Ankle', 'Toe'))
    return np.array([.4 if name.startswith(lower) else .1 if name.startswith(('Torso_', 'Spine_', 'Chest_')) else .5 if name.startswith(('Neck_', 'Head_')) else 1.5 if name.startswith(('LH:', 'RH:')) else 3. for name in names])


class NativeSession:
    """Original scene/controller, with only the final post-preparation target owner changed."""
    def __init__(self, config, out):
        # Do not import tab2body.env.base: its fixed-guitar state writes are incompatible.
        import isaacgym
        from stability_adapter_2.front_facing_ready_v1.runtime_v15 import Scene
        from stability_adapter_2.front_facing_ready_v1.runtime_v12 import Controller
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
        from stability_adapter_2.lower_body_release_v1.scene_v8 import Scene as FinalTargetScene
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

