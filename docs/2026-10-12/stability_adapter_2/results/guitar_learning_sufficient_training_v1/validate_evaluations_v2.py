"""Finalize named evaluations, binding every case to the planned checkpoint."""
import hashlib
import json
import sys
from pathlib import Path

from guitar_learning.transition_refinement_runtime_v2.evidence import validate_report

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1')
ARTIFACTS = {
    'trace_sha256': 'trace.jsonl.gz', 'demonstration_sha256': 'demonstration.npz',
    'contract_sha256': 'contract.json', 'settings_sha256': 'settings.json',
    'inputs_before_sha256': 'inputs_before.json', 'context_sha256': 'context.json',
    'initial_sha256': 'initial.json', 'initial_state_sha256': 'initial_state.json',
    'case_spec_sha256': 'case_spec.json', 'evaluation_seed_sha256': 'evaluation_seed.json',
}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_inputs(path):
    pins = read(path)
    assert all(sha(name) == expected for name, expected in pins.items())
    return len(pins)


def check_native(folder, mode, protocol, indices, checkpoint, checkpoint_sha, updates):
    runtime = folder.parent/(folder.name+'_runtime_json_audit.json')
    validate_report(runtime, folder, 'evaluate')
    result = read(folder/'result.json')
    assert result['completed'] and result['source_unchanged'] and result['physical_flags_ok']
    assert not any(result[key] for key in ('forbidden_calls', 'missing_import_pins', 'failure', 'cleanup_error'))
    assert result['process_mode'] == protocol['process_mode'] and result['evaluation_mode'] == mode
    assert result['mode'] == 'evaluate' and len(result['case_manifests']) == len(indices)
    assert sha(folder/'reset_comparisons.json') == result['reset_comparisons_sha256']
    checked_inputs = check_inputs(folder/'inputs_before.json')
    rows = []
    for local_index, protocol_index in enumerate(indices):
        case = folder/('case_%03d' % local_index)
        assert result['case_manifests'][str(case)] == sha(case/'result.json')
        capture = read(case/'result.json')
        assert capture['completed'] and capture['teacher_intervention'] is False and capture['perturbation'] is None
        assert capture['source_unchanged'] and capture['physical_flags_ok']
        assert Path(capture['source_checkpoint']).resolve() == checkpoint
        assert capture['initialization_checkpoint_sha256'] == checkpoint_sha
        assert all(capture[key] == sha(case/file) for key, file in ARTIFACTS.items())
        initialization = read(case/'initialization.json')
        assert initialization == dict(mode='strict_PPO', optimizer_updates=updates)
        seed = read(case/'evaluation_seed.json')
        assert seed['seed_applied_after_checkpoint_load'] and seed['checkpoint_sha256'] == checkpoint_sha
        assert seed['case_index'] == local_index and seed['protocol_case_index'] == protocol_index
        assert seed['evaluation_mode'] == mode and seed['process_mode'] == protocol['process_mode']
        assert seed['seed'] == protocol['cases'][protocol_index]['seed']
        spec = read(case/'case_spec.json')
        assert spec['seed'] == seed['seed'] and spec['protocol_case_index'] == protocol_index
        assert spec['perturbation'] is None and spec['process_mode'] == protocol['process_mode']
        target = next(iter(capture['episode']['transition']['per_target'].values()))
        rows.append(dict(seed=seed['seed'], successful=capture['success'],
                         checked_inputs=checked_inputs, checked_artifacts=len(ARTIFACTS),
                         initial_state_sha256=capture['initial_state_sha256'],
                         initialization_sha256=sha(case/'initialization.json'),
                         hold_fraction=target['clean_hold_fraction'],
                         release_fraction=target['qualified_target_contact_absent_fraction']))
    return rows


assert sys.argv[1:]
for name in sys.argv[1:]:
    assert name in ('baseline_fresh6_v1', 'final_fresh6_v1', 'final_deterministic_v1', 'final_stochastic_v1')
    folder = BASE/name
    if name == 'baseline_fresh6_v1':
        checkpoint = BASE.parent/'guitar_learning_contact_recovery_v1/reference_provenance_migration_v1/checkpoint_evaluation_only.pt'
        checkpoint_sha = '8bedd8d9affc16406b3fb82667429615b8f13ec5e894d1dc576e940549edfd67'
        updates = 32
    else:
        metadata = read(BASE/'training_long_v1/final_checkpoint.json')
        checkpoint = BASE/'training_long_v1/final.pt'
        assert Path(metadata['path']).resolve() == checkpoint and metadata['updates'] == 160
        checkpoint_sha, updates = metadata['sha256'], metadata['updates']
    assert sha(checkpoint) == checkpoint_sha
    fresh = 'fresh6' in name
    mode = 'deterministic' if name == 'final_deterministic_v1' else 'stochastic'
    protocol = read(BASE/('evaluate_stochastic_fresh6_v1.json' if fresh else 'evaluate_'+mode+'_20_v1.json'))
    if fresh:
        batch = read(folder/'result.json')
        assert batch['schema'] == 'guitar_learning.contact_recovery.batch.v1'
        assert batch['completed'] and batch['source_unchanged'] and not batch['failure']
        assert batch['process_mode'] == 'fresh_process' and batch['mode'] == 'evaluate'
        assert len(batch['children']) == len(protocol['cases']) == 6
        parent_inputs = check_inputs(folder/'inputs_before.json')
        observations = [json.loads(line) for line in (BASE/'fresh_process_pid_observations_v1.jsonl').read_text().splitlines()]
        rows = []
        for index, child in enumerate(batch['children']):
            native = folder/('process_%03d' % index)
            assert child['case_index'] == index and child['returncode'] == 0
            assert child['result'] == str(native/'result.json') and sha(child['result']) == child['result_sha256']
            assert sha(child['runtime_audit']) == child['runtime_audit_sha256']
            row = check_native(native, mode, protocol, [index], checkpoint, checkpoint_sha, updates)[0]
            lifecycle = read(native/'environment/persistent_lifecycle.json')
            assert lifecycle['closed'] and lifecycle['episode_index'] == 0 and lifecycle['forbidden_calls_total'] == 0
            assert lifecycle['native_calls']['create_sim'] == lifecycle['native_calls']['destroy_sim'] == 1
            assert lifecycle['native_calls']['create_env'] == 1
            pids = [item for item in observations if item['out'] == str(native) and item['protocol_case_index'] == index]
            assert len(pids) == 1
            row.update(pid=pids[0]['pid'], start_ticks=pids[0]['start_ticks'])
            rows.append(row)
        assert len({(row['pid'], row['start_ticks']) for row in rows}) == 6
    else:
        assert len(protocol['cases']) == 20
        rows = check_native(folder, mode, protocol, list(range(20)), checkpoint, checkpoint_sha, updates)
        parent_inputs = rows[0]['checked_inputs']
    summary = dict(passed=True, run=name, expected_checkpoint=str(checkpoint),
                   expected_checkpoint_sha256=checkpoint_sha, optimizer_updates=updates,
                   parent_checked_inputs=parent_inputs, successful_cases=sum(row['successful'] for row in rows),
                   cases=rows, validator_sha256=sha(BASE/'validate_evaluations_v2.py'),
                   scope='Planned checkpoint and complete artifact verification; no hidden-cache equality or statistical independence claim.')
    (BASE/(name+'_validation_v2.json')).write_text(json.dumps(summary, indent=2)+'\n')
    print(dict(passed=True, run=name, successes=summary['successful_cases'], cases=len(rows)))
