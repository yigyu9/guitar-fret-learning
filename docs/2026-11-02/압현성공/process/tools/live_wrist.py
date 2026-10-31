"""자유 기타를 따라가는 유한 손목 피드백을 기존 압현 진단에만 적용한다.

손가락 후보각·접촉 판정·물리 상태는 변경하지 않는다. 목표 손목은 원본
FK 후보에서 구하며, 패드 측정치는 손목 제어에 사용하지 않는다.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


def finalize_report(report_path, report, writer):
    """원본을 별도 보존하고 새 파일 생성 원칙으로 확장 보고서를 교체한다."""
    backup = report_path.with_name('base_report.json')
    temporary = report_path.with_name('report_extended.tmp.json')
    with backup.open('xb') as stream:
        stream.write(report_path.read_bytes())
    writer(temporary, report)
    temporary.replace(report_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--ramp-s', type=float, default=6.)
    parser.add_argument('--hold-s', type=float, default=6.)
    args = parser.parse_args()
    if args.ramp_s <= 0 or args.hold_s <= 0:
        parser.error('Positive ramp and hold durations required')
    # Isaac Gym은 Torch보다 먼저 초기화한다.
    import isaacgym
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    import guitar_learning.gpu.control as native
    import guitar_learning.gpu.environment as environment
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.tool.validation import press_acquisition as probe
    from guitar_learning.tool.experiments.short_finger_learning.wrist import (
        WRIST_CONTROL, _wrist_position_groups, interpolated_pose,
        wrist_error_and_jacobian, bounded_wrist_target)

    geometry, out = args.geometry.resolve(), args.out.resolve()
    candidates = json.loads((geometry/'candidates.json').read_text())
    instances = []
    original_class = native.BatchedController
    original_environment = environment.TensorSongEnvironment
    original_rows = probe.REPRESENTATIVE_ROWS
    holder = {}
    wrapper_path = Path(__file__).resolve()
    wrapper_sha = hashlib.sha256(wrapper_path.read_bytes()).hexdigest()

    class CapturedEnvironment(original_environment):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            holder['environment'] = self

    class LiveWristController(original_class):
        def __init__(self, scene, **kwargs):
            super().__init__(scene, **kwargs)
            names = scene.metadata['body_names']
            self.wrist = names.index('human/L_Wrist')
            self.guitar = names.index('guitar/guitar')
            self.arm_columns = self.active[:12]
            self.position_groups = _wrist_position_groups(self, names, self.arm_columns)
            fk = full_fk(SimpleNamespace(names=scene.names, human_bodies=scene.human_bodies,
                q_ref=scene.q[0].cpu().numpy().copy()), scene.contract['state'])
            prepared = scene.contract['state']['guitar_body_states'][0]['pose']
            gp = np.array([prepared['p'][a] for a in 'xyz'])
            gr = Rotation.from_quat([prepared['r'][a] for a in 'xyzw'])
            poses = [fk(np.asarray(goal['q_target105']))['L_Wrist'] for goal in candidates['goals']]
            self.goal_position = self.tensor(np.stack([gr.inv().apply(p-gp) for p, _ in poses]))
            self.goal_quaternion = self.tensor(np.stack([(gr.inv()*r).as_quat() for _, r in poses]))
            self.correction = self.reference.new_zeros((self.num_envs, 12))
            self.previous_arm = self.reference[self.arm_columns].expand(self.num_envs, -1).clone()
            self.initial_position = None
            self.tick = 0
            self.trace = []
            instances.append(self)

        def targets(self, action, snapshot):
            body = snapshot['body_state']
            instrument, current = body[:, self.guitar], body[:, self.wrist]
            position = native.apply(native.conjugate(instrument[:, 3:7]), current[:, :3]-instrument[:, :3])
            quaternion = native.multiply(native.conjugate(instrument[:, 3:7]), current[:, 3:7])
            if self.initial_position is None:
                self.initial_position, self.initial_quaternion = position.clone(), quaternion.clone()
            fraction = min(max(((self.tick+1)/60.-.5)/args.ramp_s, 0.), 1.)
            fraction = action.new_full((self.num_envs,), fraction)
            goal_p, goal_q = interpolated_pose(self.initial_position, self.initial_quaternion,
                self.goal_position, self.goal_quaternion, fraction)
            error, jacobian = wrist_error_and_jacobian(snapshot, self.wrist, self.guitar,
                self.scene.com[self.wrist], self.position_groups, goal_p, goal_q)
            active = ~snapshot['reset_body_snapshot'] & ~holder['environment'].tick_failure.any(-1)
            reference = self.reference[self.active]
            bounded_action = action.clamp(-1, 1)
            requested = reference+torch.where(bounded_action >= 0,
                self.action_high-reference, reference-self.action_low)*bounded_action
            arm, correction, delta, candidate = bounded_wrist_target(requested[:, :12], self.correction,
                self.previous_arm, snapshot['q'][:, self.arm_columns], jacobian, error, active,
                self.action_low[:12], self.action_high[:12], self.rate[self.arm_columns])
            # 원본의 실패 행 hold를 유지하며, 실패 이후 보정은 누적하지 않는다.
            arm = torch.where(active[:, None], arm, self.target[:, self.arm_columns])
            correction = arm-requested[:, :12]
            self.correction.copy_(correction)
            self.previous_arm.copy_(arm)
            requested[:, :12] = arm
            executed = probe.trajectory_actions(requested, reference, self.action_low, self.action_high)
            target = super().targets(executed, snapshot)
            self.trace.append(dict(time_s=np.asarray(self.tick/60.), active=active.cpu().numpy().copy(),
                goal_position_G_m=goal_p.cpu().numpy().copy(), goal_quaternion_G_xyzw=goal_q.cpu().numpy().copy(),
                actual_position_G_m=position.cpu().numpy().copy(), actual_quaternion_G_xyzw=quaternion.cpu().numpy().copy(),
                error_world_scaled=error.cpu().numpy().copy(), correction_rad=correction.cpu().numpy().copy(),
                delta_rad=delta.cpu().numpy().copy(), candidate_arm_rad=candidate.cpu().numpy().copy(),
                requested_arm_rad=arm.cpu().numpy().copy(), native_target_arm_rad=target[:, self.arm_columns].cpu().numpy().copy(),
                actual_arm_rad=snapshot['q'][:, self.arm_columns].cpu().numpy().copy()))
            self.tick += 1
            return target

    wrapper_settings = dict(mode='live_wrist_finite_feedback', source_sha256={str(wrapper_path): wrapper_sha},
        diagnostic_only=True, wrist_control=WRIST_CONTROL, initial_hold_s=.5,
        ramp_s=args.ramp_s, hold_s=args.hold_s,
        goal='Each unchanged candidate source-FK L_Wrist pose transformed into prepared guitar frame',
        control='Live guitar-relative wrist pose error; arm12 request correction only; no pad feedback',
        unchanged='Finger trajectories, native action bounds/rate/alpha, PD/force, contact and safety predicates',
        after_failure='Original cumulative safety failure mask disables arm feedback and retains original bounded target hold',
        limitation='Static diagnostic, not song achievement. Original replay censors each row at first safety failure; feedback traces after that censor are not valid outcomes.')
    succeeded = False
    try:
        native.BatchedController = LiveWristController
        environment.TensorSongEnvironment = CapturedEnvironment
        probe.REPRESENTATIVE_ROWS = tuple(range(16))
        probe.replay_geometry(geometry, 'free', out, ramp_s=args.ramp_s, hold_s=args.hold_s, feedback='none')
        succeeded = True
    finally:
        native.BatchedController = original_class
        environment.TensorSongEnvironment = original_environment
        probe.REPRESENTATIVE_ROWS = original_rows
        if out.exists():
            probe.write(out/'wrapper_settings.json', wrapper_settings)
            if instances and instances[0].trace:
                trace = instances[0].trace
                arrays = {key: np.stack([row[key] for row in trace]) for key in trace[0]}
                np.savez_compressed(out/'wrist_feedback60.npz', **arrays)
                summary = []
                valid_pose = np.load(out/'poses60.npz', allow_pickle=False)['valid'] if (out/'poses60.npz').exists() else None
                for row in range(16):
                    valid = arrays['active'][:, row].copy()
                    if valid_pose is not None:
                        valid[:min(len(valid), len(valid_pose))] &= valid_pose[:len(valid), row]
                        valid[len(valid_pose):] = False
                    errors = arrays['error_world_scaled'][valid, row]
                    position_error = np.linalg.norm(errors[:, :3], axis=-1)
                    rotation_error = np.linalg.norm(errors[:, 3:], axis=-1)/WRIST_CONTROL['rotation_length_scale_m']
                    summary.append(dict(row=row, valid_control_samples=int(valid.sum()),
                        final_position_error_m=float(position_error[-1]) if len(errors) else None,
                        final_rotation_error_rad=float(rotation_error[-1]) if len(errors) else None,
                        maximum_position_error_m=float(position_error.max()) if len(errors) else None))
                probe.write(out/'wrist_feedback_summary.json', dict(mode=wrapper_settings['mode'], goals=summary,
                    scope='60Hz pre-step snapshot errors; original valid-pose prefix censor applied'))
            if succeeded:
                if hashlib.sha256(wrapper_path.read_bytes()).hexdigest() != wrapper_sha:
                    raise RuntimeError('Diagnostic wrapper changed during replay')
                report_path = out/'report.json'
                report = json.loads(report_path.read_text())
                report['wrapper'] = wrapper_settings
                report['mode'] = wrapper_settings['mode']
                report['interpretation'] += '; live wrist feedback added by separately pinned diagnostic wrapper'
                finalize_report(report_path, report, probe.write)


if __name__ == '__main__':
    main()
