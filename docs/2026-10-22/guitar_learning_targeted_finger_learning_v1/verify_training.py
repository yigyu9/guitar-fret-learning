"""CPU audit of actual small GPU runs; no native imports or GPU execution."""
from pathlib import Path
import copy
import argparse
import hashlib
import json
import random
from types import SimpleNamespace

import numpy as np
import torch

from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
from guitar_learning.training.ppo import PPOTrainer, PPOConfig
from guitar_learning.training.training_log_io import iter_transitions
from guitar_learning.training.json_io import dumps


PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
RUNS = Path('/dev/shm/guitar_learning_targeted_finger_v8_20261022')


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype==b.dtype and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype==b.dtype and np.array_equal(a, b)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def finite(value):
    if isinstance(value, torch.Tensor):
        assert torch.isfinite(value).all()
        return 1
    if isinstance(value, dict):
        return sum(finite(v) for v in value.values())
    if isinstance(value, (tuple, list)):
        return sum(finite(v) for v in value)
    return 0


def load(path):
    return torch.load(path, map_location='cpu', weights_only=False)


def main():
    global RUNS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,default=RUNS,help='Extracted GPU run root')
    RUNS=parser.parse_args().runs
    torch.set_num_threads(1)
    result = dict(scope='Short GPU integration and strict restore; not song performance or learned naturalness', runs={})
    for name, transitions, updates in [('gpu_smoke8', 262144, 8), ('gpu_resume1', 32768, 9)]:
        run = RUNS/name
        report = json.loads((run/'report.json').read_text())
        assert report['completed'] and report['lifecycle_verified']
        assert report['failure'] is None and not report['cleanup_errors']
        assert not report['changed_inputs'] and not report['missing_import_pins']
        assert report['settings']['song_training']['observation_dimension']==544
        assert report['transitions'] == transitions and report['optimizer_updates'] == updates
        journal = report['journal']
        assert all(journal[k] == transitions for k in ('sampled', 'logged', 'durable', 'committed'))
        assert journal['closed'] and not journal['failed'] and not journal['discarded']
        audit={}
        rows=list(iter_transitions(run/'transitions.jsonl.gz',diagnostics=audit))
        assert audit['complete'] and audit['error'] is None
        assert audit['completed_members']==transitions//32768
        assert audit['valid_compressed_prefix_bytes']==(run/'transitions.jsonl.gz').stat().st_size
        assert len(rows)*1024 == transitions
        for index,row in enumerate(rows):
            assert row['update_index']==index//32 and row['tick_in_update']==index%32
            for key in ('reward','cost','terminated','truncated'):
                assert len(row[key])==1024
            assert np.isfinite(row['reward']).all() and np.isfinite(row['cost']).all()
        failures=sum(sum(r['terminated']) for r in rows)
        episodes=[json.loads(line) for line in (run/'episodes.jsonl').read_text().splitlines()]
        assert len(episodes)==report['completed_episodes']==failures
        from_rows=[dict(update_index=r['update_index'],episode=e) for r in rows for e in r['episodes']]
        assert same(episodes,from_rows)
        assert all(e['episode']['reason']=='terminal_failure' for e in episodes)
        assert len(list(run.glob('update_*.json')))==transitions//32768
        assert not any(any(r['truncated']) for r in rows)
        means = []
        for path in sorted(run.glob('update_*.json')):
            row = json.loads(path.read_text())
            chunk=rows[row['update_index']*32:(row['update_index']+1)*32]
            for key in ('reward','cost'):
                assert abs(np.asarray([r[key] for r in chunk]).mean()-row['mean_'+key])<1e-6
            advantages=row['diagnostics']['advantages']
            assert advantages['normalization']=='separate'
            for key in ('reward_normalized','cost_normalized','combined_normalized'):
                stats=advantages[key]
                assert stats['count']==32768 and stats['nonfinite_count']==0
                assert abs(stats['mean'])<1e-5 and abs(stats['std']-1)<1e-5
            components = row['reward_component_means']
            for key in ('song_finger_coordination', 'song_finger_standby'):
                assert 0 < components[key] <= .05/60+1e-8
            assert abs(sum(components.values())-row['mean_reward']) < 1e-7
            means.append({k:components[k] for k in ('song_finger_coordination', 'song_finger_standby')})
        pins=json.loads((run/'inputs_before.json').read_text())
        for pin_name,sha in pins.items():
            pinned=Path(pin_name)
            old_root=Path('/dev/shm/guitar_learning_targeted_finger_v8_20261022')
            if old_root in pinned.parents:
                pinned=RUNS/pinned.relative_to(old_root)
            assert hashlib.sha256(pinned.read_bytes()).hexdigest()==sha
        checkpoint = load(run/'final.pt')
        counts = {key:finite(checkpoint[key]) for key in ('model','actor_optimizer','value_optimizer')}
        assert checkpoint['updates'] == updates
        assert checkpoint['model']['left_curriculum_state'].shape == (3331,)
        assert checkpoint['identity']['architecture']['state_dim']==544
        assert len(checkpoint['identity']['architecture']['priority_slots'])==8
        assert checkpoint['identity']['architecture']['contract']['reward']['schema'].endswith('.v8')
        assert checkpoint['identity']['config']['advantage_normalization']=='separate'
        assert checkpoint['identity']['config']['gae_lambda']==.98
        assert checkpoint['identity']['architecture']['finger_actor']['schema']=='guitar_learning.targeted_finger_actor.v1'
        assert all('finger_heads.'+f+'.0.weight' in checkpoint['model'] for f in ('index','middle','ring','pinky'))
        result['runs'][name] = dict(gzip_audit=audit,input_sha_count=len(pins),wall_s=report['wall_s'],transitions=transitions, optimizer_updates=updates, rows=len(rows),
            finite_tensor_counts=counts, new_reward_component_means=means, physical_failures=failures,
            physical_failure_reasons={reason:sum(reason in e['episode']['failure_reasons'] for e in episodes) for reason in set(r for e in episodes for r in e['episode']['failure_reasons'])},
            checkpoint_sha256=hashlib.sha256((run/'final.pt').read_bytes()).hexdigest())
    assert set(result['runs'])=={'gpu_smoke8','gpu_resume1'}
    saved = load(RUNS/'gpu_smoke8/final.pt')
    initial=load(RUNS/'gpu_smoke8/initial.pt')
    for finger in ('index','middle','ring','pinky'):
        assert not same(initial['model']['finger_heads.'+finger+'.2.weight'],saved['model']['finger_heads.'+finger+'.2.weight'])
    result['all_four_finger_output_weights_updated']=True
    restored = load(RUNS/'gpu_resume1/initial.pt')
    keys = ('identity','model','actor_optimizer','value_optimizer','cost_weight','updates',
            'torch_rng','numpy_rng','python_rng','cuda_rng')
    assert all(same(saved[k],restored[k]) for k in keys)
    final = load(RUNS/'gpu_resume1/final.pt')
    assert not same(final['model'], restored['model'])
    for k in ('actor_optimizer','value_optimizer'):
        assert not same(final[k],restored[k])
    result['exact_restore'] = list(keys)
    old_path = ROOT/'docs/2026-10-22/guitar_learning_finger_inputs_v1/gpu_smoke8/final.pt'
    old = load(old_path)
    contract = saved['identity']['architecture']['contract']
    settings = json.loads((RUNS/'gpu_smoke8/settings.json').read_text())
    policy = SpecialistPolicy(544,size='large',contract=contract,role='left',frozen_partner=False)
    CurriculumCoordinator(policy, SimpleNamespace(environment=SimpleNamespace(finger_counts=[25,18,12,12])))
    trainer = PPOTrainer(policy,PPOConfig(**settings['ppo']))
    # Match old PPO configuration so the reward/architecture contract is the rejection cause.
    trainer.config = PPOConfig(**old['identity']['config'])
    assert old['identity']['architecture']['contract']['reward']['schema'].endswith('.v6')
    snapshots = copy.deepcopy((policy.state_dict(),trainer.actor_optimizer.state_dict(),
        trainer.value_optimizer.state_dict(),torch.get_rng_state(),np.random.get_state(),random.getstate()))
    try:
        trainer.load(old_path)
    except ValueError as error:
        rejection = str(error)
        assert rejection == 'own schema/architecture/input/control/config mismatch'
    else:
        raise AssertionError('old rewardv6 checkpoint accepted')
    after = (policy.state_dict(),trainer.actor_optimizer.state_dict(),trainer.value_optimizer.state_dict(),
        torch.get_rng_state(),np.random.get_state(),random.getstate())
    assert same(snapshots,after)
    result['old_v6_rejected_without_mutation'] = dict(path=str(old_path),reason=rejection,
        sha256=hashlib.sha256(old_path.read_bytes()).hexdigest())
    source = json.loads((PHASE/'tested_source_manifest.json').read_text())['source']
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in source.items())
    result['active_source_unchanged_since_freeze'] = len(source)
    (PHASE/'training_verification.json').write_text(dumps(result,indent=2,allow_nan=False)+'\n')
    print('PASS: GPU8 updates N1024 + exact restore + GPU1 update, strict v6 rejection, separate signals and per-finger architecture, source unchanged')


if __name__ == '__main__':
    main()
