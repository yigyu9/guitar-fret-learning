"""Fresh E0 actor imitation from one fully verified native pair trajectory.

This is a new actor-initialization artifact, never a PPO resume checkpoint.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import torch

STUDY = Path(__file__).resolve().parents[1]
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))
from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.portability import portable, localize
from guitar_learning.training.policy import FingerSkillPolicy

SOURCE = STUDY/'로그/goal_nominal_v1'
SOURCE_MANIFEST = STUDY/'입력/goal_nominal_v1.json'
CHECKPOINT = STUDY.parent/'학습_인접2지_v1/로그/parallel_v1/pilot_env2/J/final.pt'
BUDGET = dict(steps=400, batch_size=64, actor_lr=.001, seed=7, size='medium', threads=1,
              loss='mean squared error of tanh(mean) on the original active33 axes')
ACTOR_PREFIXES = ('support_encoder.', 'support_head.', 'finger_encoder.', 'finger_heads.')
PROJECTION = {'task.finger_skill.planned_transitions': dict(source=1280, target=204800),
              'task.finger_skill.full_song_after': dict(source=320, target=51200)}
TARGET_IDS = ['event-000000/string-3/note-0', 'event-000001/string-2/note-1']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def verify_pins(pins):
    if not pins:
        raise ValueError('Nonempty teacher/source pins required')
    for name, expected in pins.items():
        path = Path(name).resolve(); path.relative_to(ROOT)
        if sha(path) != expected:
            raise ValueError('Teacher/source SHA mismatch: '+str(path))


def target_contract(source):
    contract = copy.deepcopy(source)
    if (contract['observation']['dimension'] != 557 or
            contract['action']['names'] != list(ACTIVE_NAMES) or
            'natural_preparation' in contract['reward']):
        raise ValueError('Original E0 full557/39 contract required; E4 is a separate condition')
    for path, change in PROJECTION.items():
        item = contract
        parts = path.split('.')
        for key in parts[:-1]:
            item = item[key]
        if item[parts[-1]] != change['source']:
            raise ValueError('Unexpected source exposure budget')
        item[parts[-1]] = change['target']
    return contract


def validate_evidence(report, guard, episode, metadata):
    pair = episode.get('simultaneous_press', {})
    if (not all(report.get(k) is True for k in ('completed', 'capture_completed',
            'protocol_completed', 'lifecycle_verified', 'teacher_eligible', 'actual_target_approach_diagnostic')) or
            report.get('failure') is not None or report.get('cleanup_errors') != [] or
            report.get('geometry_failure') is not None or report.get('outcome') != 'simultaneous_clean_success' or
            report.get('episode') != episode or
            not all(guard.get(k) is True for k in ('completed', 'capture_completed',
                'protocol_completed', 'final_state_verified')) or guard.get('failure') is not None or
            guard.get('outcome') != 'simultaneous_clean_success' or
            episode.get('reason') != 'timeline_complete' or episode.get('steps') != 330 or
            abs(episode.get('task_time_s', 0)-5.5) > 1e-9 or
            pair.get('source_score_window_s') != [3.3, 4.8] or pair.get('target_ids') != TARGET_IDS or
            pair.get('integration_hz') != 240 or pair.get('success') is not True or
            pair.get('full_safe') is not True or pair.get('individual_achievements') != [True, True] or
            pair.get('wrong_union_s') != 0 or pair.get('unsafe_s') != 0 or
            any(abs(pair.get(k, 0)-1.5) > 1e-9 for k in ('observed_s', 'clean_s', 'longest_clean_s')) or
            episode.get('failure_reasons') != [] or
            metadata.get('no_mid_episode_state_injection') is not True or
            metadata.get('condition') != 'nominal' or metadata.get('training_updates') != 0 or
            metadata.get('action_names') != list(ACTIVE_NAMES) or
            metadata.get('teacher_observation_alignment') !=
                'row i: observation before action i; poses row i is after4 physics substeps'):
        raise ValueError('Only the complete safe simultaneous1.5s native teacher is eligible')


def validate_arrays(data, poses, contract):
    shapes = dict(state=(330, 557), events=(330, 64, 24), mask=(330, 64),
                  priority_events=(330, 8, 24), priority_mask=(330, 8), action=(330, 39))
    if set(data) != set(shapes):
        raise ValueError('Exact complete pre-action observation/action fields required')
    for key, shape in shapes.items():
        if data[key].shape != shape or not np.isfinite(data[key]).all():
            raise ValueError('Incomplete/nonfinite teacher field: '+key)
        if key.endswith('mask') and data[key].dtype != np.bool_:
            raise ValueError('Boolean teacher masks required')
    if (poses['q'].shape != (330, 105) or poses['body_state'].shape != (330, 106, 13) or
            not all(np.isfinite(v).all() for v in poses.values()) or
            not np.array_equal(poses['action'], data['action']) or
            not np.array_equal(poses['control_tick'], np.arange(1, 331)) or
            not np.array_equal(poses['physics_step'], 4*np.arange(1, 331)) or
            not np.allclose(poses['time_s'], np.arange(1, 331)/60., atol=1e-12, rtol=0) or
            np.abs(data['action']).max() > 1 or np.any(data['action'][:, 33:] != 0)):
        raise ValueError('Complete consecutive post-action native poses/actions must match teacher rows')
    fields, scales = contract['observation']['fields'], contract['observation']['scales']
    elapsed = fields.index('music.elapsed_s')
    if not np.allclose(data['state'][:, elapsed]*scales[elapsed], np.arange(330)/60., atol=1e-6, rtol=0):
        raise ValueError('Teacher observations must precede actions, not use post-action states')


def build_plan():
    manifest = read(SOURCE_MANIFEST)
    verify_pins(manifest['pins'])
    required = [SOURCE/'guard_report.json', SOURCE/'capture/report.json',
        SOURCE/'capture/episode_env0000.json', SOURCE/'capture/metadata.json',
        SOURCE/'capture/settings.json', SOURCE/'capture/poses_env0000.npz',
        SOURCE/'capture/teacher_observations.npz', SOURCE_MANIFEST, CHECKPOINT, Path(__file__).resolve()]
    pins = dict(manifest['pins'])
    for path in required:
        if str(path) in pins and pins[str(path)] != sha(path):
            raise ValueError('An inherited immutable pin changed')
        pins[str(path)] = sha(path)
    return dict(schema='multi_press.teacher_bootstrap_plan.v1', sealed=False,
        condition='B1', environment='E0', source_capture=str(SOURCE), source_checkpoint=str(CHECKPOINT),
        source_manifest=str(SOURCE_MANIFEST), projection=PROJECTION, budget=BUDGET,
        target_ids=TARGET_IDS, common_window_s=[3.3, 4.8], pins=pins,
        initialization='fresh actor supervised only; fresh std/critics; no PPO optimizer or RNG transfer')


def load_teacher(plan):
    if (plan.get('schema') != 'multi_press.teacher_bootstrap_plan.v1' or plan.get('sealed') is not True or
            plan.get('condition') != 'B1' or plan.get('environment') != 'E0' or
            plan.get('source_capture') != str(SOURCE) or plan.get('source_checkpoint') != str(CHECKPOINT) or
            plan.get('source_manifest') != str(SOURCE_MANIFEST) or plan.get('budget') != BUDGET or
            plan.get('projection') != PROJECTION or plan.get('target_ids') != TARGET_IDS or
            plan.get('common_window_s') != [3.3, 4.8]):
        raise ValueError('Reviewed sealed B1/E0 actor-only bootstrap plan required')
    pins = plan['pins']
    required = [SOURCE/'guard_report.json', SOURCE/'capture/report.json', SOURCE/'capture/episode_env0000.json',
        SOURCE/'capture/metadata.json', SOURCE/'capture/settings.json', SOURCE/'capture/poses_env0000.npz',
        SOURCE/'capture/teacher_observations.npz', SOURCE_MANIFEST, CHECKPOINT, Path(__file__).resolve()]
    if any(str(p) not in pins for p in required):
        raise ValueError('Every teacher evidence and bootstrap source file must be pinned')
    manifest = read(SOURCE_MANIFEST)
    if any(pins.get(k) != v for k, v in manifest['pins'].items()):
        raise ValueError('Original native source/input pins must be preserved')
    verify_pins(pins)
    capture = SOURCE/'capture'
    report, guard, episode, metadata = [read(p) for p in
        (capture/'report.json', SOURCE/'guard_report.json', capture/'episode_env0000.json', capture/'metadata.json')]
    validate_evidence(report, guard, episode, metadata)
    if (guard['source_manifest_sha256'] != sha(SOURCE_MANIFEST) or
            metadata['source_manifest_sha256'] != sha(SOURCE_MANIFEST)):
        raise ValueError('Native capture/guard manifest identity mismatch')
    from guitar_learning.training import finger_skill_runner
    payload = torch.load(CHECKPOINT, map_location='cpu', weights_only=False)
    finger_skill_runner._validate_metadata_schema(payload['metadata'])
    finger_skill_runner._validate_pins(payload['metadata'])
    source = payload['identity']['architecture']['contract']
    settings = read(capture/'settings.json')
    expected_settings = localize(payload['metadata']['settings'])
    expected_settings['num_envs'] = 1
    if (settings['experiment']['target_ids'] != TARGET_IDS or
            settings['experiment']['common_window_s'] != [3.3, 4.8] or
            settings['experiment'].get('improvement') is not None or
            settings['song_training']['control_ticks'] != 330 or settings['size'] != 'medium' or
            settings != expected_settings):
        raise ValueError('Original E0 task/architecture identity differs')
    with torch.random.fork_rng(devices=[]):
        architecture = FingerSkillPolicy(557, size='medium', contract=copy.deepcopy(source)).architecture
    if portable(architecture) != portable(payload['identity']['architecture']):
        raise ValueError('Source policy architecture differs from its complete original E0 contract')
    with np.load(capture/'teacher_observations.npz', allow_pickle=False) as file:
        data = {k: file[k].copy() for k in file.files}
    with np.load(capture/'poses_env0000.npz', allow_pickle=False) as file:
        poses = {k: file[k].copy() for k in file.files}
    validate_arrays(data, poses, source)
    return data, source, target_contract(source)


def actor_parameters(policy):
    return {name: p for name, p in policy.named_parameters() if name.startswith(ACTOR_PREFIXES)}


def new_policy(contract):
    torch.manual_seed(BUDGET['seed'])
    policy = FingerSkillPolicy(557, size='medium', contract=copy.deepcopy(contract)).cpu()
    for name, parameter in policy.named_parameters():
        parameter.requires_grad_(name.startswith(ACTOR_PREFIXES))
    return policy


def tensors(data):
    return {k: torch.from_numpy(v) for k, v in data.items()}


def prediction(policy, batch):
    return policy(**{k: batch[k] for k in ('state', 'events', 'mask', 'priority_events', 'priority_mask')})['mean'].tanh()


def fit_metrics(policy, data):
    with torch.no_grad():
        predicted = torch.cat([prediction(policy, {k: v[i:i+64] for k, v in data.items()})
                               for i in range(0, 330, 64)])
        error = predicted[:, :33]-data['action'][:, :33]
        assigned = error[:, 17:25]
        return dict(active33_mse=float(error.square().mean()), active33_rmse=float(error.square().mean().sqrt()),
            assigned8_rmse=float(assigned.square().mean().sqrt()), assigned8_max_abs=float(assigned.abs().max()),
            per_axis_rmse=error.square().mean(0).sqrt().tolist(),
            scope='in-sample330 teacher observations; native closed-loop policy success unmeasured')


def train(plan_path, out):
    plan_path, out = Path(plan_path).resolve(), Path(out).resolve()
    plan_path.relative_to(STUDY); out.relative_to(STUDY)
    if out.exists():
        raise FileExistsError('Fresh B1 bootstrap output required')
    plan_sha = sha(plan_path); plan = read(plan_path)
    torch.set_num_threads(BUDGET['threads'])
    data, source, target = load_teacher(plan)
    policy = new_policy(target)
    data = tensors(data)
    frozen = {k: v.clone() for k, v in policy.state_dict().items() if k not in actor_parameters(policy)}
    optimizer = torch.optim.Adam(list(actor_parameters(policy).values()), lr=BUDGET['actor_lr'])
    generator = torch.Generator(device='cpu').manual_seed(BUDGET['seed'])
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    history = [dict(step=0, **fit_metrics(policy, data))]
    for step in range(1, BUDGET['steps']+1):
        indices = torch.randint(330, (BUDGET['batch_size'],), generator=generator)
        batch = {k: v[indices] for k, v in data.items()}
        loss = (prediction(policy, batch)[:, :33]-batch['action'][:, :33]).square().mean()
        optimizer.zero_grad(set_to_none=True); loss.backward(); optimizer.step()
        if step % 40 == 0:
            row = dict(step=step, **fit_metrics(policy, data)); history.append(row)
            with (out/'fit_metrics.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row, allow_nan=False)+'\n')
    if any(not torch.equal(policy.state_dict()[k], v) for k, v in frozen.items()):
        raise RuntimeError('Fresh std/critic/buffer was modified by actor-only bootstrap')
    verify_pins(plan['pins'])
    if sha(plan_path) != plan_sha:
        raise ValueError('Bootstrap plan changed during training')
    artifact = dict(schema='multi_press.teacher_actor_initialization.v1', condition='B1', environment='E0',
        architecture=portable(policy.architecture), source_contract=source, contract=target,
        contract_projection=PROJECTION, actor_state={k: v.detach().cpu() for k, v in actor_parameters(policy).items()},
        lineage=dict(plan=str(plan_path), plan_sha256=plan_sha, source_sha256=plan['pins']),
        transfers=dict(actor=True, std=False, critics=False, ppo_optimizer=False, rng=False),
        success_scope='imitation fit only; native learned-policy success not inherited')
    path = out/'actor_initialization.pt'; torch.save(artifact, path)
    report = dict(schema='multi_press.teacher_bootstrap_result.v1', completed=True, cpu_only=True,
        budget=BUDGET, wall_s=time.monotonic()-started, projection=PROJECTION,
        source_contract=source, contract=target, source_sha256=plan['pins'],
        plan=str(plan_path), plan_sha256=plan_sha, artifact=str(path), artifact_sha256=sha(path),
        initial_fit=history[0], final_fit=history[-1], native_policy_success=None,
        std_critic_buffers_unchanged=True, optimizer_rng_transferred=False)
    (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    return report


def load_actor_artifact(policy, path, expected_contract, expected_sha256):
    """Only call on a fresh matching E0 policy; never a PPO checkpoint loader."""
    if sha(path) != expected_sha256:
        raise ValueError('Bootstrap artifact differs from the reviewed result SHA')
    artifact = torch.load(path, map_location='cpu', weights_only=False)
    if (artifact.get('schema') != 'multi_press.teacher_actor_initialization.v1' or
            artifact.get('condition') != 'B1' or artifact.get('environment') != 'E0' or
            artifact.get('contract_projection') != PROJECTION or
            artifact.get('contract') != portable(expected_contract) or
            portable(policy.architecture) != artifact.get('architecture') or
            target_contract(artifact['source_contract']) != artifact['contract'] or
            set(artifact['actor_state']) != set(actor_parameters(policy))):
        raise ValueError('Strict B1 actor/full contract/architecture/key identity mismatch')
    verify_pins(artifact['lineage']['source_sha256'])
    if sha(artifact['lineage']['plan']) != artifact['lineage']['plan_sha256']:
        raise ValueError('Bootstrap plan lineage changed')
    plan = read(artifact['lineage']['plan'])
    if (plan.get('schema') != 'multi_press.teacher_bootstrap_plan.v1' or
            plan.get('sealed') is not True or plan.get('condition') != 'B1' or
            plan.get('environment') != 'E0' or plan.get('budget') != BUDGET or
            plan.get('pins') != artifact['lineage']['source_sha256']):
        raise ValueError('Artifact requires its original sealed E0 bootstrap plan')
    with torch.no_grad():
        for name, parameter in actor_parameters(policy).items():
            value = artifact['actor_state'][name]
            if value.shape != parameter.shape or not torch.isfinite(value).all():
                raise ValueError('Invalid B1 actor tensor: '+name)
        for name, parameter in actor_parameters(policy).items():
            parameter.copy_(artifact['actor_state'][name])
    return artifact


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = train(args.plan, args.out)
    print(json.dumps(dict(completed=result['completed'], artifact=result['artifact'],
        final_fit=result['final_fit']), ensure_ascii=False))
