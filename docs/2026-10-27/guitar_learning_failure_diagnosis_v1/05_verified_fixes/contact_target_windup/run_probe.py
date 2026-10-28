"""Strict final300 fixed-tape target-memory diagnostic; original observer reused."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from projection import project, rounding_tolerance

HERE = Path(__file__).resolve().parent
OBSERVER = HERE.parent/'contact_load_probe'
MODES = ('tape_original', 'tape_no_new_inward', 'tape_no_new_inward_and_relax')
SCHEMA = dict(clock=('i4', ()), start_clock=('i4', ()), first_attempt=('?', ()),
    incoming_action4=('f4', (4,)), tape_action4=('f4', (4,)), old_target4=('f4', (4,)),
    raw_target4=('f4', (4,)), final_target4=('f4', (4,)), actual4=('f4', (4,)),
    lower_increment=('f8', (4,)), upper_increment=('f8', (4,)),
    fixed_point_W=('f4', (3,)), normal_W=('f4', (3,)), point_J=('f4', (3, 4)),
    normal_J=('f8', (4,)), point_velocity_W=('f4', (3,)), predicted_velocity_W=('f4', (3,)),
    signed_normal_force_N=('f4', ()), gate=('?', ()), stale_J=('?', ()),
    prior_failure=('?', ()), invalid_state=('?', ()), invalid_J=('?', ()), zero_J=('?', ()), post_failure=('?', ()),
    beta_m=('f8', ()), capacity_m=('f8', ()), old_normal_error_m=('f8', ()),
    final_normal_error_m=('f8', ()), raw_normal_increment_m=('f8', ()),
    filtered_normal_increment_m=('f8', ()), tangent_change_m=('f8', (3,)),
    halfspace_residual_m=('f8', ()), halfspace_tolerance_m=('f8', ()),
    box_excess_rad=('f8', ()), coordinate_tolerance_rad=('f8', ()),
    memory_submit_error_rad=('f4', ()), other_target_change_rad=('f4', ()),
    arm_request12=('f4', (12,)), wrist_error6=('f4', (6,)))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')


def observer():
    sys.path.insert(0, str(OBSERVER))
    try:
        spec = importlib.util.spec_from_file_location('preserved_contact_load_observer', OBSERVER/'probe.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(OBSERVER))


def measure(pool, snapshot, first, local_points, threshold):
    """Compute J only for eligible non-reset rows, before any projection."""
    import torch
    from guitar_learning.gpu.geometry import apply
    from guitar_learning.tool.validation.thumb_contact_probe import point_jacobian
    env, distal, guitar = pool.environment, pool.fixed_distal, pool.environment.guitar_index
    body, instrument = snapshot['body_state'][:, distal], snapshot['body_state'][:, guitar]
    force = snapshot['contact_force'][:, distal]
    finite = (torch.isfinite(body).all(-1) & torch.isfinite(instrument).all(-1) & torch.isfinite(force).all(-1)
        & torch.isfinite(snapshot['q']).all(-1) & torch.isfinite(snapshot['qd']).all(-1))
    prior = env.failure.any(-1) | env.wrist_failure | env.wrist_severe_failure
    normal, point = torch.zeros_like(force), torch.zeros_like(force)
    signed = force.new_zeros(first.shape)
    valid = (first & finite).nonzero().flatten()
    if valid.numel():
        unit = env.press_plane[:3]/torch.linalg.vector_norm(env.press_plane[:3])
        normal[valid] = apply(instrument[valid, 3:7], unit.expand(len(valid), -1))
        point[valid] = body[valid, :3]+apply(body[valid, 3:7], local_points[valid])
        signed[valid] = (force[valid]*normal[valid]).sum(-1)
    gate = first & (env.clock >= 480) & ~prior & ~snapshot['reset_body_snapshot'] & finite & (signed > threshold)
    jacobian = force.new_zeros((len(first), 3, 4))
    measured, predicted = torch.zeros_like(force), torch.zeros_like(force)
    invalid = torch.zeros_like(first)
    ids = gate.nonzero().flatten()
    if ids.numel():
        offset = apply(body[ids, 3:7], local_points[ids]-pool.scene.com[distal])
        native = snapshot['jacobian'][ids, distal-1]
        good = torch.isfinite(native).all(dim=(-1, -2))
        invalid[ids] = ~good
        ids, native, offset = ids[good], native[good], offset[good]
        if ids.numel():
            full = point_jacobian(native, offset)
            jacobian[ids] = full[:, :, pool.selected_native]
            measured[ids] = body[ids, 7:10]+torch.cross(body[ids, 10:13], offset, dim=-1)
            predicted[ids] = (full@snapshot['qd'][ids, :, None]).squeeze(-1)
    gate &= ~invalid
    return dict(gate=gate, prior=prior, invalid=invalid, invalid_state=first & ~finite, finite=finite, normal=normal, point=point,
        signed=signed, J=jacobian, g=torch.einsum('nc,ncj->nj', normal.double(), jacobian.double()),
        measured=measured, predicted=predicted)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=MODES, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); out = args.out.resolve()
    if out.exists(): raise FileExistsError(str(out))
    sealed = json.loads((HERE/'precommit.json').read_text())
    if any(not Path(p).is_file() or sha(p) != h for p, h in sealed['input_pins'].items()):
        raise ValueError('Fixed-tape preparation inputs changed')
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    observed = observer()
    from protocol import Trace
    with np.load(HERE/'fixed_inputs.npz', allow_pickle=False) as z:
        action_source, material_source = z['action4'].copy(), z['point_local'].copy()
    trace = Trace(SCHEMA, 218)
    original_pool, original_pins = runner.ShortPool, runner._pins
    pools, identity, failure = [], None, None

    class TapePool(original_pool):
        def __init__(self, settings, output):
            super().__init__(settings, output)
            try:
                self.replay_first = torch.ones(128, dtype=torch.bool, device=self.scene.device)
                self.selected_actions = self.spec['learned_action_indices']
                self.selected_native = self.controller.active[self.selected_actions]
                if [self.scene.names[i] for i in self.selected_native] != self.spec['learned_action_names']:
                    raise ValueError('Selected native/action name mapping differs')
                if not bool((self.controller.rate[self.selected_native] == 4).all()):
                    raise ValueError('Original selected4 rate must be4rad/s')
                self.fixed_distal = int(self.environment.pad_indices[self.spec['finger']-1])
                self.tape = torch.as_tensor(action_source, device=self.scene.device)
                self.material = torch.as_tensor(material_source, dtype=self.scene.q.dtype, device=self.scene.device)
                self.pending = None
                native_targets = self.controller.targets

                def targets(action, snapshot):
                    old = self.controller.target[:, self.selected_native].clone()
                    raw = native_targets(action, snapshot)
                    if raw.data_ptr() != self.controller.target.data_ptr():
                        raise ValueError('Original target return must alias controller memory')
                    proposed = raw[:, self.selected_native].clone()
                    other = torch.ones(105, dtype=torch.bool, device=raw.device); other[self.selected_native] = False
                    original_other = raw[:, other].clone()
                    m = measure(self, snapshot, self.replay_first, self.material, sealed['force_threshold_N'])
                    lower = torch.maximum(self.controller.lower[self.selected_native], self.controller.action_low[self.selected_actions])
                    upper = torch.minimum(self.controller.upper[self.selected_native], self.controller.action_high[self.selected_actions])
                    limit = self.controller.rate[self.selected_native].double()/60
                    L = torch.maximum(lower.double()-old.double(), -limit)
                    U = torch.minimum(upper.double()-old.double(), limit)
                    actual = torch.zeros_like(old)
                    actual[m['finite']] = snapshot['q'][m['finite']][:, self.selected_native]
                    final = proposed.clone()
                    beta, capacity, residual, tolerance = [old.new_zeros(128, dtype=torch.float64) for _ in range(4)]
                    ids = m['gate'].nonzero().flatten()
                    if args.mode != MODES[0] and ids.numel():
                        result = project(proposed[ids].double()-old[ids].double(), L[ids], U[ids], m['g'][ids],
                            old[ids].double()-actual[ids].double(), relax=args.mode == MODES[2])
                        final[ids] = (old[ids].double()+result['delta']).to(final)
                        _, tol = rounding_tolerance(old[ids], proposed[ids], final[ids], result['normal_scaled'], result['beta_scaled'])
                        actual_delta = final[ids].double()-old[ids].double()
                        remainder = (result['normal_scaled']*actual_delta).sum(-1)-result['beta_scaled']
                        if not bool((remainder >= -tol).all()): raise ValueError('Halfspace rounding violation')
                        beta[ids] = result['beta_scaled']*result['scale']
                        capacity[ids] = result['maximum_scaled']*result['scale']
                        residual[ids], tolerance[ids] = remainder*result['scale'], tol*result['scale']
                        self.controller.target[:, self.selected_native] = final
                    coordinates, _ = rounding_tolerance(old, proposed, final, m['g'], beta)
                    delta = final.double()-old.double()
                    excess = torch.maximum(torch.maximum(L-delta, delta-U), torch.zeros_like(delta))
                    if not bool((excess <= coordinates).all()): raise ValueError('Final native/rate box violation')
                    memory = (raw[:, self.selected_native]-final).abs().amax(-1)
                    changed_other = (raw[:, other]-original_other).abs().amax(-1)
                    if not bool(((memory == 0) & (changed_other == 0)).all()): raise ValueError('Target memory/other-column mutation')
                    change = torch.einsum('ncj,nj->nc', m['J'].double(), final.double()-proposed.double())
                    tangent = change-m['normal'].double()*(change*m['normal'].double()).sum(-1, keepdim=True)
                    self.pending = dict(first_attempt=self.replay_first.clone(), start_clock=self.environment.clock.clone(),
                        incoming_action4=self.incoming4, tape_action4=self.replayed4, old_target4=old,
                        raw_target4=proposed, final_target4=final, actual4=actual,
                        lower_increment=L, upper_increment=U, fixed_point_W=m['point'], normal_W=m['normal'],
                        point_J=m['J'], normal_J=m['g'], point_velocity_W=m['measured'], predicted_velocity_W=m['predicted'],
                        signed_normal_force_N=m['signed'], gate=m['gate'], stale_J=snapshot['reset_body_snapshot'],
                        prior_failure=m['prior'], invalid_state=m['invalid_state'], invalid_J=m['invalid'], zero_J=(m['g'].abs().amax(-1) == 0) & m['gate'],
                        beta_m=beta, capacity_m=capacity, old_normal_error_m=(m['g']*(old.double()-actual.double())).sum(-1),
                        final_normal_error_m=(m['g']*(final.double()-actual.double())).sum(-1),
                        raw_normal_increment_m=(m['g']*(proposed.double()-old.double())).sum(-1),
                        filtered_normal_increment_m=(m['g']*delta).sum(-1), tangent_change_m=tangent,
                        halfspace_residual_m=residual, halfspace_tolerance_m=tolerance,
                        box_excess_rad=excess.amax(-1), coordinate_tolerance_rad=coordinates.amax(-1),
                        memory_submit_error_rad=memory, other_target_change_rad=changed_other,
                        arm_request12=self.last_wrist_feedback['requested_arm_rad'], wrist_error6=self.last_wrist_feedback['pose_error_world'])
                    return raw

                self.controller.targets = targets
                pools.append(self)
            except BaseException:
                self.close(); raise

        def step(self, action):
            clock = self.environment.clock
            if not bool(((clock[self.replay_first] % 4 == 0) & (clock[self.replay_first] < 872)).all()):
                raise ValueError('Tape clock must index a first-attempt control')
            index = (clock//4).clamp(0, 217)
            self.incoming4 = action[:, self.selected_actions].detach().clone()
            self.replayed4 = self.tape[index, torch.arange(128, device=clock.device)]
            replay = action.clone()
            replay[:, self.selected_actions] = torch.where(self.replay_first[:, None], self.replayed4, self.incoming4)
            self.pending = None
            result = super().step(replay)
            row = self.pending
            row.update(clock=self.environment.clock, post_failure=self.environment.failure.any(-1) |
                self.environment.wrist_failure | self.environment.wrist_severe_failure)
            submitted = self.scene.target[:, self.selected_native]
            row['memory_submit_error_rad'] = torch.maximum(row['memory_submit_error_rad'], (submitted-row['final_target4']).abs().amax(-1))
            trace.append({k: v.detach().cpu().numpy() for k, v in row.items()})
            for episode in result[-1]: self.replay_first[episode['env_id']] = False
            return result

    def pins(settings, output, extra=()):
        nonlocal identity
        stat = out.stat(); identity = (stat.st_dev, stat.st_ino)
        return original_pins(settings, output, [*extra, HERE/'precommit.json', *map(Path, sealed['input_pins'])])

    previous_argv = sys.argv
    try:
        runner.ShortPool, runner._pins = TapePool, pins
        sys.argv = [str(OBSERVER/'probe.py'), '--checkpoint', sealed['checkpoint'], '--control', 'policy', '--out', str(out)]
        observed.main()
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error)); raise
    finally:
        runner.ShortPool, runner._pins = original_pool, original_pins
        sys.argv = previous_argv
        if identity is not None and out.is_dir() and (out.stat().st_dev, out.stat().st_ino) == identity:
            a = trace.values(); first = a['first_attempt']; prefix = first & (a['start_clock'] < 480)
            base = json.loads((out/'load_probe_report.json').read_text()) if (out/'load_probe_report.json').is_file() else {}
            prefix_checks, replay_checks = {}, {}
            for field in ('actual_LH21', 'target_LH21', 'distal_force_W', 'guitar_pose', 'selected_distal_pose', 'thumb3_pose'):
                raw_path = out/'physics240.npz'
                if raw_path.is_file():
                    with np.load(raw_path, allow_pickle=False) as new, np.load(sealed['source_physics'], allow_pickle=False) as old:
                        prefix_checks[field] = bool(np.array_equal(new[field][:480], old[field][:480]))
                        if args.mode == MODES[0]: replay_checks[field] = bool(np.array_equal(new[field], old[field]))
            if args.mode == MODES[0] and (out/'evaluation.json').is_file():
                replay_checks['evaluation_values'] = json.loads((out/'evaluation.json').read_text()) == json.loads(Path(sealed['source_evaluation']).read_text())
            action_exact = False
            if (out/'control60.npz').is_file():
                with np.load(out/'control60.npz', allow_pickle=False) as z:
                    action_exact = bool(np.array_equal(z['executed_action_selected4'][z['first_attempt']], action_source[:len(z['clock'])][z['first_attempt']]))
            checks = dict(original_observer_completed=base.get('completed') is True,
                prefix_unmodified=not bool(np.any(a['final_target4'][prefix] != a['raw_target4'][prefix])),
                original_mode_unmodified=args.mode != MODES[0] or not bool(np.any(a['final_target4'][first] != a['raw_target4'][first])),
                source_prefix_exact=len(prefix_checks) == 6 and all(prefix_checks.values()),
                no_intervention_replay_exact=args.mode != MODES[0] or (len(replay_checks) == 7 and all(replay_checks.values())),
                source_tape_exact=action_exact, records_bounded=trace.count <= 218,
                combined_array_budget=trace.nbytes+base.get('selected_output_uncompressed_bytes', 100_000_000) < 100_000_000,
                target_memory_submission_equal=not bool(a['memory_submit_error_rad'].any()),
                other_target_columns_equal=not bool(a['other_target_change_rad'].any()),
                own_pins_unchanged=all(Path(p).is_file() and sha(p) == h for p, h in sealed['input_pins'].items()))
            with (out/'target_control60.npz').open('xb') as stream: np.savez_compressed(stream, **a)
            write(out/'target_windup_report.json', dict(completed=failure is None and all(checks.values()),
                failure=failure, mode=args.mode, checks=checks, prefix_checks=prefix_checks,
                no_intervention_replay_checks=replay_checks, own_record_uncompressed_bytes=trace.nbytes,
                diagnostic_contract=sealed['contract'], observer_report_sha256=sha(out/'load_probe_report.json') if base else None,
                scope='Fixed selected4 tape replay with target override; not policy performance, pair pressure or isolated middle-only causality'))
            if failure is None and not all(checks.values()): raise RuntimeError('Fixed-tape target diagnostic audit failed')


if __name__ == '__main__': main()
