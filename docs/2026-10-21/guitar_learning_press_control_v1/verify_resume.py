"""CPU audit of actual GPU100->101 resume and old-control identity rejection.

CUDA RNG payload bytes are compared, never installed in a GPU generator here.
The real GPU runner's strict load/initial snapshot/closed report is the new-load
runtime evidence; CPU tensor binding below is explicitly not PPOTrainer.load.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.gpu_left_curriculum import CurriculumState, STATE_SIZE
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.training import json_io


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same_tree(a, b):
    if isinstance(a, torch.Tensor):
        return (isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and
                torch.equal(a.detach().cpu().reshape(-1).view(torch.uint8), b.detach().cpu().reshape(-1).view(torch.uint8)))
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same_tree(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(same_tree(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return type(a) is type(b) and struct.pack('d', a) == struct.pack('d', b)
    return type(a) is type(b) and a == b


def finite_tree(value):
    if isinstance(value, torch.Tensor):
        require(bool(torch.isfinite(value).all()), 'Nonfinite checkpoint tensor')
    elif isinstance(value, np.ndarray):
        require(bool(np.isfinite(value).all()), 'Nonfinite checkpoint array')
    elif isinstance(value, float):
        require(math.isfinite(value), 'Nonfinite checkpoint scalar')
    elif isinstance(value, dict):
        for item in value.values(): finite_tree(item)
    elif isinstance(value, (tuple, list)):
        for item in value: finite_tree(item)


def verify_input_pins(pins):
    require(isinstance(pins, dict) and bool(pins), 'Nonempty training input pins required')
    for path, expected in pins.items():
        source = Path(path)
        require(source.is_file() and hashlib.sha256(source.read_bytes()).hexdigest() == expected,
                'Training source/asset/song input changed or missing: '+path)
    return len(pins)


def unchanged_right(a, b):
    keys = [k for k in a['model'] if k.startswith(('actor_encoders.right.', 'actor_heads.right.'))]
    require(bool(keys) and all(same_tree(a['model'][k], b['model'][k]) for k in keys), 'Inactive right actor changed')
    require(same_tree(a['model']['log_std'][33:], b['model']['log_std'][33:]), 'Inactive right log_std changed')
    require(same_tree(a['model']['partner_initialized'], b['model']['partner_initialized']), 'Partner state changed')
    for first, second in ((a['actor_optimizer'], b['actor_optimizer']),):
        # SpecialistPolicy.actor_parameters puts shared log_std last.
        ia, ib = first['param_groups'][0]['params'][-1], second['param_groups'][0]['params'][-1]
        sa, sb = first['state'].get(ia, {}), second['state'].get(ib, {})
        for key in ('exp_avg', 'exp_avg_sq', 'max_exp_avg_sq'):
            if key in sa or key in sb:
                va, vb = sa.get(key, torch.zeros(39)), sb.get(key, torch.zeros(39))
                require(va.shape == vb.shape == (39,) and same_tree(va[33:], vb[33:]), 'Inactive right Adam moments changed')
    return len(keys)


def check_resume_payloads(selected, initial, final):
    require(same_tree({k:v for k,v in selected.items() if k != 'metadata'},
                      {k:v for k,v in initial.items() if k != 'metadata'}), 'Selected100 -> resumed initial differs outside metadata')
    require(selected['updates'] == initial['updates'] == 100 and final['updates'] == 101, 'Expected actual100->101 update counts')
    for payload in (selected, initial, final): finite_tree(payload)
    require(isinstance(selected['cuda_rng'], list) and bool(selected['cuda_rng']) and
            all(isinstance(v, torch.Tensor) and v.dtype == torch.uint8 and v.ndim == 1 and v.numel() > 0
                for v in selected['cuda_rng']), 'Actual serialized CUDA RNG states required')
    require(same_tree(initial['identity'], final['identity']), 'Resumed checkpoint identity changed')
    left_keys = [k for k in initial['model'] if k.startswith(('actor_encoders.left.', 'actor_heads.left.'))]
    value_keys = [k for k in initial['model'] if k.startswith(('value_encoder.', 'reward_critic.', 'cost_critic.'))]
    left_changed = sum(not same_tree(initial['model'][k], final['model'][k]) for k in left_keys)
    value_changed = sum(not same_tree(initial['model'][k], final['model'][k]) for k in value_keys)
    require(left_changed > 0 and value_changed > 0, 'Actual left actor/value model update required')
    for key in ('actor_optimizer', 'value_optimizer'):
        require(not same_tree(initial[key], final[key]), 'Actual optimizer update required: '+key)
    return dict(exact_nonmetadata_100_to_initial=True, finite=True, left_changed_tensors=left_changed,
                value_changed_tensors=value_changed, inactive_right_unchanged_tensors=unchanged_right(initial, final))


def reject_old_without_mutation(trainer, old_checkpoint):
    before = copy.deepcopy(dict(model=trainer.policy.state_dict(), actor=trainer.actor_optimizer.state_dict(),
        value=trainer.value_optimizer.state_dict(), cost_weight=trainer.cost_weight, updates=trainer.updates,
        torch_rng=torch.get_rng_state(), numpy_rng=np.random.get_state(), python_rng=random.getstate()))
    # Identity mismatch must happen before CUDA topology/state hooks.
    with patch.object(torch.cuda, 'is_available', side_effect=AssertionError('CUDA queried during old identity rejection')), \
         patch.object(torch.cuda, 'set_rng_state_all', side_effect=AssertionError('CUDA RNG touched')):
        try:
            trainer.load(old_checkpoint)
        except ValueError as error:
            require(str(error) == 'own schema/architecture/input/control/config mismatch', 'Old checkpoint failed for another reason: '+str(error))
        else:
            raise ValueError('Old action/control checkpoint was unexpectedly accepted')
    after = dict(model=trainer.policy.state_dict(), actor=trainer.actor_optimizer.state_dict(),
        value=trainer.value_optimizer.state_dict(), cost_weight=trainer.cost_weight, updates=trainer.updates,
        torch_rng=torch.get_rng_state(), numpy_rng=np.random.get_state(), python_rng=random.getstate())
    require(same_tree(before, after), 'Old rejection mutated model/optimizers/counters or host RNG')
    return dict(rejected=True, reason='PPO identity equality guard; not a source SHA predicate',
                host_state_and_rng_unchanged=True, cuda_hooks_not_called=True)


def verify(run, resumed, old_checkpoint):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Run CPU verifier with CUDA_VISIBLE_DEVICES empty')
    torch.set_num_threads(1)
    pins = {}
    def read(path, checkpoint=False):
        pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return torch.load(path, map_location='cpu', weights_only=False) if checkpoint else json.loads(path.read_text())
    settings, contract, report = [read(run/name) for name in ('settings.json','training_contract.json','report.json')]
    rs, rc, rr = [read(resumed/name) for name in ('settings.json','training_contract.json','report.json')]
    require(contract == rc, 'Resume training contract changed')
    require((settings['size'],settings['num_envs'],settings['horizon'],settings['specialist']['role']) == ('large',1024,32,'left'), 'Expected large1024/H32 left smoke')
    require(settings['updates'] == 100 and rs['updates'] == 1, 'Expected100-update smoke and1-update resume')
    for key in ('size','num_envs','horizon','seed','specialist','ppo','song','song_training','initial_std','physics_backend'):
        require(settings[key] == rs[key], 'Resume changed setting: '+key)
    codec = contract['action']['target_contract']['action_codec']
    require(codec['schema'] == 'guitar_learning.gpu_left_incremental_fingers.v1' and
            contract['diagnostics']['left_finger_motion']['schema'] == 'guitar_learning.gpu_left_finger_motion.v1', 'New codec/diagnostic contract required')
    require(contract['observation']['dimension'] == 512, 'Expected512 state contract')
    for current, configuration, count, updates in ((report,settings,100,100),(rr,rs,1,101)):
        scene = current['gpu_scene']
        require(current['settings'] == configuration and current['completed'] is True and current['lifecycle_verified'] is True and
                current['optimizer_updates'] == updates and current['transitions'] == count*32768 and
                len(current['updates']) == count and not current['failure'] and not current['cleanup_errors'] and
                not current['changed_inputs'] and not current['missing_import_pins'], 'Actual completed run/closed lifecycle evidence required')
        require(scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and
                scene['simulator_count'] == 1 and scene['environment_count'] == 1024 and scene['physics_steps'] == count*128,
                'Actual GPU1024 physics/close evidence required')
        require(all(row['update_index'] == i and row['optimizer_updates'] == updates-count+i+1 and
                    row['transitions'] == 32768 for i,row in enumerate(current['updates'])), 'Nonconsecutive actual optimizer updates')
    require(rr['updates'][0]['update_index'] == 0 and rr['updates'][0]['optimizer_updates'] == 101, 'Actual resumed optimizer101 row required')
    selected = read(run/'final.pt', True)
    initial = read(resumed/'initial.pt', True)
    final = read(resumed/'final.pt', True)
    original = read(run/'initial.pt', True)
    old = read(old_checkpoint, True)
    require(original['updates'] == 0, 'Fresh smoke initial must be optimizer0')
    run_inputs = read(run/'inputs_before.json')
    resumed_inputs = read(resumed/'inputs_before.json')
    pin_counts = dict(smoke=verify_input_pins(run_inputs), resumed=verify_input_pins(resumed_inputs))
    require(resumed_inputs.get(str((run/'final.pt').resolve())) == pins[str(run/'final.pt')], 'Actual resume input must pin smoke final')
    checks = check_resume_payloads(selected, initial, final)
    checks['inactive_right_unchanged_from_fresh_initial'] = unchanged_right(original, final)
    policy = SpecialistPolicy(512, size='large', contract=contract, role='left').cpu()
    counts = [sum(t['finger'] == f for t in contract['task']['provenance']['song']['schedule']) for f in range(1,5)]
    state = CurriculumState(counts)
    require(final['model']['left_curriculum_state'].shape == (STATE_SIZE,) and
            final['model']['left_curriculum_state'].dtype == torch.float64, 'Expected3331 float64 curriculum checkpoint buffer')
    state.load_state(final['model']['left_curriculum_state'].numpy())
    policy.register_buffer('left_curriculum_state', torch.as_tensor(state.state_vector(), dtype=torch.float64))
    trainer = PPOTrainer(policy, PPOConfig(**settings['ppo']))
    require(same_tree(selected['identity'], trainer._identity()), 'Saved new identity does not match actual new policy/config')
    # Bind actual nonempty CPU tensors to make the old-load no-mutation check substantive.
    policy.load_state_dict(final['model'], strict=True)
    trainer.actor_optimizer.load_state_dict(final['actor_optimizer'])
    trainer.value_optimizer.load_state_dict(final['value_optimizer'])
    trainer.cost_weight, trainer.updates = final['cost_weight'], final['updates']
    old_contract = old['identity']['architecture']['contract']
    require(all(old['identity']['architecture'][key] == selected['identity']['architecture'][key]
                for key in ('schema', 'state_dim', 'event_dim', 'size', 'role')), 'Old baseline must share model dimensions/role')
    require(old_contract['action']['target_contract'].get('action_codec') == codec and
            old_contract['reward']['schema'] == 'guitar_learning.gpu_tensor_song_reward.v3' and
            contract['reward']['schema'] == 'guitar_learning.gpu_tensor_song_reward.v4' and
            old_contract['observation']['surface_geometry']['schema'] == 'guitar_learning.left_surface_events.v1' and
            contract['observation']['surface_geometry']['schema'] == 'guitar_learning.left_surface_events.v2',
            'Previous incremental checkpoint must differ in press target/reward, not action dimensions')
    rejection = reject_old_without_mutation(trainer, old_checkpoint)
    rejection.update(new_reward_schema=contract['reward']['schema'], old_reward_schema=old_contract['reward']['schema'], new_control_schema=contract['action']['target_contract']['schema'],
        old_control_schema=old_contract['action']['target_contract']['schema'],
        new_action_codec_schema=codec['schema'],
        old_action_codec_schema=old_contract['action']['target_contract'].get('action_codec', {}).get('schema'),
        new_finger_diagnostics_schema=contract['diagnostics']['left_finger_motion']['schema'],
        old_finger_diagnostics_schema=old_contract.get('diagnostics', {}).get('left_finger_motion', {}).get('schema'),
        same_model_dimensions_and_role=True)
    require(all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == value for path,value in pins.items()), 'Verification inputs changed')
    return dict(schema='guitar_learning.press_control_resume_verification.v1', completed=True,
        run=str(run), resumed=str(resumed), old_checkpoint=str(old_checkpoint), checks=checks,
        old_checkpoint_rejection=rejection, curriculum_values=STATE_SIZE,
        training_input_pins_verified=pin_counts,
        actual_new_strict_resume=dict(scope='Real GPU runner strict load followed by exact initial100, optimizer101 and closed nativeGPU report; not an unmodified GPU-checkpoint CPU PPOTrainer.load pass',
            source_optimizer_updates=100, final_optimizer_updates=101, real_gpu_lifecycle_verified=True),
        cpu_new_binding='Strict model.load_state_dict plus both optimizer state_dict loads; CUDA RNG was not installed and PPOTrainer.load on new GPU payload was not claimed',
        cuda_rng_scope='CUDA payload bytes are exact in selected100->initial100 whole-tree comparison; no CUDA generator queried or changed by this CPU tool',
        limitations=['Resume restores PPO/RNG/curriculum and restarts prepared physical episodes; no interrupted physics trajectory restored.',
            'Identity/finite/update preservation is not pressure, acoustic, musical or generalization success.'], inputs_sha256=pins)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=PHASE/'smoke100')
    parser.add_argument('--resumed', type=Path, default=PHASE/'smoke_resume1')
    parser.add_argument('--old-checkpoint', type=Path, default=PHASE.parent/'guitar_learning_incremental_fingers_v1/smoke100/final.pt')
    parser.add_argument('--out', type=Path, default=PHASE/'resume_verification.json')
    args = parser.parse_args()
    result = verify(args.run.resolve(), args.resumed.resolve(), args.old_checkpoint.resolve())
    with args.out.open('x') as stream: json_io.dump(result, stream, indent=2, allow_nan=False)
    print(json_io.dumps(dict(completed=True, output=str(args.out))))


if __name__ == '__main__':
    main()
