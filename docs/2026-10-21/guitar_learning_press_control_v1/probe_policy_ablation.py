"""Closed-loop final100 N4 policy/action ablation; root runs after completion.

Each row uses its own current observation. Fixed row IDs and the N1024→N4
change confound interpretation; this is not an exact causal/generalization test.
"""
import argparse
import copy
import faulthandler
import json
from pathlib import Path
import sys
import time
import traceback

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(PHASE))
from evaluate_checkpoints import json_io, require, sha, write

CASES = ('full_policy', 'left21_zero', 'left_arm12_zero', 'all_zero39')


def action_masks(order):
    import numpy as np
    require(len(order) == len(set(order)) == 39, 'Unique named action39 required')
    hand = [i for i, n in enumerate(order) if n.startswith('LH:')]
    arm = [i for i, n in enumerate(order) if n.startswith('L_')]
    require(len(hand) == 21 and len(arm) == 12, 'Left hand21/arm12 mapping required')
    result = np.ones((4, 39), dtype=np.float32)
    result[1, hand] = 0; result[2, arm] = 0; result[3] = 0
    return result


def audit_trace(arrays, mask, episode, control):
    import numpy as np
    count = episode['steps']+1
    shapes = dict(body_state=(count, 106, 13), q=(count, 105), qd=(count, 105),
        target=(count, 105), raw_action=(count, 39), applied_action=(count, 39),
        state=(count,512), policy_input_state=(count,512), clock=(count,), global_physics_step=(count,))
    require(set(arrays) == set(shapes), 'Capture field set differs')
    require(all(arrays[k].shape == s and np.isfinite(arrays[k]).all() for k, s in shapes.items()), 'Capture shape/nonfinite failure')
    require(np.array_equal(arrays['clock'], np.arange(count)*4) and
            np.array_equal(arrays['global_physics_step'], np.arange(count)*4), 'First-episode60Hz clock differs')
    require(bool((arrays['raw_action'][0] == 0).all()) and bool((arrays['applied_action'][0] == 0).all()), 'Frame0 is a command sentinel')
    require(bool((np.abs(arrays['raw_action']) <= 1).all()) and
            np.array_equal(arrays['applied_action'], arrays['raw_action']*mask), 'Applied action differs from prescribed row mask')
    require(np.max(np.abs(np.linalg.norm(arrays['body_state'][..., 3:7], axis=-1)-1)) < 1e-3, 'Invalid body quaternion')
    reference = np.array(control['reference105_rad'])
    hand = [control['joint_names'].index(n) for n in control['action_order'] if n.startswith('LH:')]
    arm = [control['joint_names'].index(n) for n in control['action_order'] if n.startswith('L_')]
    held = list(hand) if np.all(mask[[i for i,n in enumerate(control['action_order']) if n.startswith('LH:')]] == 0) else []
    if np.all(mask[[i for i,n in enumerate(control['action_order']) if n.startswith('L_')]] == 0):
        held += arm
    error = float(np.max(np.abs(arrays['target'][:, held]-reference[held]))) if held else None
    require(error is None or error <= 3e-6, 'Zeroed channels did not hold prepared targets')
    return dict(frames=count, control_steps=count-1, action_mask_exact=True,
        input_state_previous_endpoint_max_error=float(np.abs(arrays['policy_input_state'][1:]-arrays['state'][:-1]).max()),
        zeroed_channel_target_reference_max_error_rad=error,
        raw_action_mean_abs=np.abs(arrays['raw_action'][1:]).mean(0).tolist(),
        applied_action_mean_abs=np.abs(arrays['applied_action'][1:]).mean(0).tolist(),
        actual_left21_range_rad=np.ptp(arrays['q'][:, hand], axis=0).tolist(),
        target_left21_range_rad=np.ptp(arrays['target'][:, hand], axis=0).tolist())


def main():
    faulthandler.enable(all_threads=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=PHASE/'smoke100')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve(); checkpoint = run/'final.pt'
    settings = json.loads((run/'settings.json').read_text())
    report = json.loads((run/'report.json').read_text())
    pins = json.loads((run/'inputs_before.json').read_text())
    require(report['completed'] and report['optimizer_updates'] == 100 and report['failure'] is None and
            not(report['cleanup_errors'] or report['changed_inputs'] or report['missing_import_pins']), 'Completed intact100 training required')
    require((settings['num_envs'], settings['horizon'], settings['updates'], settings['size'], settings['seed'], settings['device']) ==
            (1024, 32, 100, 'large', 7, 'cuda:0') and settings['specialist']['role'] == 'left', 'Expected frozen large1024/H32/seed7 left100 run')
    require(not [p for p,v in pins.items() if not Path(p).is_file() or sha(p) != v], 'Training input pins changed')
    manifest_path = PHASE/'training_source_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    require(manifest['active_python_count'] == len(manifest['source']) == 435 and
            all(pins.get(p) == v and sha(p) == v for p,v in manifest['source'].items()), 'Frozen source435 mismatch')
    baseline_path = PHASE/'contact_probe_n4/report.json'
    baseline = json.loads(baseline_path.read_text())
    require(baseline['completed'] and baseline['gpu_scene']['closed'] and
            baseline['PPO_updates'] == baseline['policy_inference_steps'] == 0, 'Closed zero-command baseline required')
    for path in (checkpoint, run/'report.json', run/'training_contract.json', manifest_path, baseline_path,
                 Path(__file__).resolve(), PHASE/'evaluate_checkpoints.py'):
        value = sha(path)
        require(str(path) not in pins or pins[str(path)] == value, 'Existing pin mismatch')
        pins[str(path)] = value
    # Native SDK first; all imports above are stdlib or the lazy JSON adapter.
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.training.gpu_pool import GpuPool, FIELDS
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer, PPOConfig
    from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.gpu.environment import CONTACT_CONTRACT
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    settings = copy.deepcopy(settings); settings['num_envs'] = 4
    write(out/'settings.json', settings); pins[str(out/'settings.json')] = sha(out/'settings.json')
    write(out/'inputs_before.json', pins)
    torch.set_num_threads(1); torch.backends.cuda.matmul.allow_tf32 = False
    pool, failure, cleanup, frozen, restored, stats = None, None, [], None, None, None
    frames, first_end = [{} for _ in CASES], [None]*4
    active = np.ones(4, bool); ticks, policy_calls, progress = 0, 0, None
    started = time.perf_counter()
    def status(stage):
        path = out/'lifecycle.json'
        path.with_suffix('.tmp').write_text(json_io.dumps(dict(stage=stage, control_ticks=ticks,
            completed_first_episodes=sum(e is not None for e in first_end), wall_s=time.perf_counter()-started), allow_nan=False)+'\n')
        path.with_suffix('.tmp').replace(path)
    def capture(raw, applied, input_state):
        sample = pool.environment.snapshot
        values = {k:sample[k].detach().cpu().numpy() for k in ('body_state','q','qd','target')}
        values.update(raw_action=raw.detach().cpu().numpy(), applied_action=applied.detach().cpu().numpy(),
            state=pool.observation['state'].detach().cpu().numpy(), policy_input_state=input_state.detach().cpu().numpy(),
            clock=pool.environment.clock.cpu().numpy())
        for index in np.flatnonzero(active):
            for key, value in values.items():
                frames[index].setdefault(key, []).append(value[index].copy())
            frames[index].setdefault('global_physics_step', []).append(pool.scene.physics_steps)
    try:
        status('creating_pool'); pool = GpuPool(settings, out)
        require(pool.contract == json.loads((run/'training_contract.json').read_text()), 'N4 changed strict training contract')
        require(pool.controller.contract['action_order'] == list(ACTIVE_NAMES), 'Canonical action order mismatch')
        policy = SpecialistPolicy(512, size='large', contract=pool.contract, role='left').to(settings['device'])
        coordinator = CurriculumCoordinator(policy, pool)
        trainer = PPOTrainer(policy, PPOConfig(**settings['ppo'])); trainer.load(checkpoint)
        require(trainer.updates == 100, 'Strict restored optimizer count differs')
        observation = coordinator.restore(); policy.eval()
        restored = policy.left_curriculum_state.clone()
        require(restored.numel() == 3331 and torch.isfinite(restored).all(), 'Finite3331 restored state required')
        frozen = {k:v.detach().clone() for k,v in policy.state_dict().items()}
        progress = coordinator.state.progress
        mask_array = action_masks(pool.controller.contract['action_order'])
        mask = torch.tensor(mask_array, device=pool.scene.device)
        active_device = torch.ones(4, dtype=torch.bool, device=pool.scene.device)
        env = pool.environment
        stats = dict(native_peak=torch.zeros(4, 11, device=env.device),
            loaded_s=torch.zeros(4, 11, dtype=torch.float64, device=env.device),
            geometry_s=torch.zeros(4, env.M, dtype=torch.float64, device=env.device),
            selected_load_s=torch.zeros(4, env.M, dtype=torch.float64, device=env.device),
            candidate_s=torch.zeros(4, env.M, dtype=torch.float64, device=env.device),
            geometry_selected_load_s=torch.zeros(4, env.M, dtype=torch.float64, device=env.device),
            contact_s=torch.zeros(4, env.M, dtype=torch.float64, device=env.device),
            candidate_without_any_designated_load=torch.zeros(4, dtype=torch.int64, device=env.device),
            samples=torch.zeros(4, dtype=torch.int64, device=env.device))
        previous = env.candidate.clone()
        native_ids = torch.cat((env.finger_indices, torch.tensor([len(pool.scene.human_bodies)], device=env.device)))
        original = env.substep
        def measured_substep(snapshot):
            nonlocal previous
            original(snapshot)
            force = torch.linalg.vector_norm(pool.scene._native_contact_force[:, native_ids], dim=-1)
            loaded = force >= CONTACT_CONTRACT['force_threshold_n']
            live = active_device[:, None]
            stats['native_peak'] = torch.maximum(stats['native_peak'], torch.where(live, force, 0.))
            stats['loaded_s'] += (loaded*live).to(torch.float64)/240.
            now = env.clock.to(torch.float64)/240.
            press_weight = (torch.minimum(now[:,None], env.end)-torch.maximum((now-1/240.)[:,None], env.press)).clamp_min(0)*live
            for key, flag in (('geometry_s',env.contact_geometry),('selected_load_s',env.surface_body_loaded),
                              ('candidate_s',env.candidate),('geometry_selected_load_s',env.contact_geometry & env.surface_body_loaded),
                              ('contact_s',env.candidate & previous)):
                stats[key] += press_weight*flag
            any_load = loaded[:, 2*env.finger] | loaded[:, 2*env.finger+1]
            stats['candidate_without_any_designated_load'] += ((env.candidate & ~any_load)*live).sum(-1)
            stats['samples'] += active_device
            previous = env.candidate.clone()
        env.substep = measured_substep
        zero = torch.zeros(4, 39, device=env.device); capture(zero, zero, observation['state'])
        write(out/'visual_initial.json', pool.scene.contract['initial'])
        write(out/'training_contract.json', pool.contract)
        pending = []
        with torch.no_grad():
            for _ in range(settings['song_training']['control_ticks']):
                if pending:
                    observation = pool.reset(pending)[0]
                input_state = observation['state'].detach().clone()
                raw = policy.act(*(observation[k] for k in FIELDS), deterministic=True)['action']
                require(raw.shape == (4,39) and torch.isfinite(raw).all() and (raw.abs() <= 1).all(), 'Finite bounded per-row raw policy action required')
                applied = torch.where(active_device[:,None], raw*mask, zero)
                observation, reward, cost, terminated, truncated, episodes = pool.step(applied)
                ticks += 1; policy_calls += 1; capture(raw, applied, input_state)
                require(torch.isfinite(reward).all() and torch.isfinite(cost).all() and not truncated.any(), 'Invalid diagnostic transition')
                for episode in episodes:
                    index = episode['env_id']
                    if active[index]:
                        first_end[index] = episode; active[index] = False; active_device[index] = False
                pending = (terminated|truncated).nonzero().flatten().cpu().tolist()
                if ticks%60 == 0:
                    status('stepping')
                if not active.any():
                    break
        require(not active.any(), 'All first episodes must end within full-song horizon')
        require(trainer.updates == 100 and coordinator.state.progress == progress and
                torch.equal(policy.left_curriculum_state, restored) and
                all(torch.equal(v, frozen[k]) for k,v in policy.state_dict().items()), 'Probe changed restored model/curriculum')
        require(not stats['candidate_without_any_designated_load'].any(), 'Candidate lacks native designated finger load')
        status('first_episodes_complete')
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
        traceback.print_exc()
    finally:
        summary = None
        try:
            summary = {k:v.detach().cpu().tolist() for k,v in stats.items()} if stats is not None else None
        except BaseException as error:
            cleanup.append('native summary readback: '+repr(error))
        if pool is not None:
            try:
                pool.close()
            except BaseException as error:
                cleanup.append(repr(error))
    captures = []
    for index, case in enumerate(CASES):
        if not frames[index]:
            continue
        arrays = {k:np.stack(v) for k,v in frames[index].items()}
        path = out/('case_%d_%s.npz'%(index,case)); np.savez_compressed(str(path), **arrays)
        proof = None
        if first_end[index] is not None:
            try:
                proof = audit_trace(arrays, mask_array[index], first_end[index], pool.controller.contract)
                require(summary['samples'][index] == first_end[index]['steps']*4, '240Hz first-episode sample count differs')
                ledger = first_end[index]['left_note_ledger']['values']
                for name,key in (('geometry_s','geometry_time'),('selected_load_s','body_load_time'),('contact_s','contact_time')):
                    require(np.allclose(summary[name][index], ledger[key], rtol=0,atol=1e-9), '240Hz summary/ledger mismatch: '+key)
            except BaseException as error:
                proof = dict(error=repr(error))
                if failure is None:
                    failure = dict(type='CaptureAuditError', message=repr(error))
        captures.append(dict(env_id=index,case=case,path=path.name,sha256=sha(path),first_episode=first_end[index],audit=proof,
            native240_summary={k:v[index] for k,v in summary.items()} if summary else None))
    scene = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
    changed = [p for p,v in pins.items() if not Path(p).is_file() or sha(p) != v]
    missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
    native_ok = bool(scene and scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and
        scene['simulator_count'] == 1 and scene['environment_count'] == 4 and scene['physics_steps'] == 4*ticks and
        all(device == 'cuda:0' for device in scene['tensor_devices'].values()))
    completed = failure is None and not(cleanup or changed or missing) and native_ok and all(first_end)
    zero_episode = first_end[3]
    baseline_zero = baseline['captures'][3]['first_episode']
    write(out/'capture_metadata.json',dict(schema='guitar_learning.policy_ablation_capture.v1',
        cases=list(CASES),action_masks=action_masks(list(ACTIVE_NAMES)).tolist(),action_order=list(ACTIVE_NAMES),
        body_names=pool.scene.body_names if pool and pool.scene else None,joint_names=pool.scene.names if pool and pool.scene else None,
        capture_hz=60,source_physics_hz=240,frame0='Prepared035/v14 reset; both action arrays are sentinel zeros',
        raw_action='Each row current observation, deterministic final100 policy; no shared recorded tape',
        state='Endpoint state512 at clock4k; policy_input_state is the pre-step state used for framek raw_action, normally clock4(k-1). Frame0 both states are reset observation. Event/priority tokens are not captured, so state alone does not reproduce the full policy input.',
        native240_summary='Native finger10+compound guitar root force norms; peak and loaded_s over first episode; note times exact press..end overlap, selected load uses closest source sample body',
        force_threshold_n=CONTACT_CONTRACT['force_threshold_n'],
        force_body_names=['human/LH:'+f+str(s) for f in ('thumb','index','middle','ring','pinky') for s in (2,3)]+['guitar/guitar'],
        captures=[{k:v for k,v in c.items() if k in ('env_id','case','path','sha256')} for c in captures]))
    write(out/'report.json',dict(completed=completed,failure=failure,cleanup_errors=cleanup,changed_inputs=changed,
        missing_import_pins=missing,gpu_scene=scene,control_ticks=ticks,policy_batched_calls=policy_calls,
        PPO_updates=0,source_optimizer_updates=100,checkpoint=str(checkpoint),checkpoint_sha256=pins[str(checkpoint)],
        restored_curriculum_progress=progress if restored is not None else None,curriculum_values=3331,
        model_and_curriculum_unchanged=failure is None,deterministic=True,captures=captures,
        zero_baseline_comparison=dict(source=str(baseline_path),sha256=pins[str(baseline_path)],source_env_id=3,
            baseline_success_count=baseline_zero['song']['left_success_count'],
            current_success_count=zero_episode['song']['left_success_count'] if zero_episode else None,
            baseline_reason=baseline_zero['reason'],current_reason=zero_episode['reason'] if zero_episode else None),
        wall_s=time.perf_counter()-started,
        limitations='Fixed case↔envID confounding; newN4 versus training/evaluationN1024; each closed-loop row evolves different observations. Zero commands hold targets, not actual state. Native body net loads are not pair/pressure witnesses. No precise causal isolation, population estimate, four-finger reachability or policy generalization claim.'))
    status('report_written')
    print(json_io.dumps(dict(completed=completed,steps=ticks,results=[e['song']['left_success_count'] if e else None for e in first_end]),allow_nan=False))
    return 0 if completed else 1


if __name__ == '__main__':
    sys.exit(main())
