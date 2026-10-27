"""Read finalized fresh-process evidence inside the preserved execution view."""
import hashlib
import json
import sys
from pathlib import Path

from guitar_learning.transition_refinement_runtime_v2.evidence import validate_report

BASE = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_inputs(path):
    pins = read(path)
    assert all(sha(name) == expected for name, expected in pins.items())
    return len(pins)


name = sys.argv[1]
assert name in ('baseline_fresh6_v1', 'final_fresh6_v1')
folder = BASE/name
batch = read(folder/'result.json')
assert batch['completed'] and batch['source_unchanged'] and not batch['failure']
assert batch['schema'] == 'guitar_learning.contact_recovery.batch.v1'
assert batch['process_mode'] == 'fresh_process' and batch['mode'] == 'evaluate'
protocol = read(BASE/'evaluate_stochastic_fresh6_v1.json')
assert len(batch['children']) == len(protocol['cases']) == 6
parent_inputs = check_inputs(folder/'inputs_before.json')
observations = [json.loads(line) for line in (BASE/'fresh_process_pid_observations_v1.jsonl').read_text().splitlines()]
records = []
for index, entry in enumerate(batch['children']):
    child = folder/('process_%03d' % index)
    assert entry['case_index'] == index and entry['returncode'] == 0
    assert entry['result'] == str(child/'result.json')
    assert sha(entry['result']) == entry['result_sha256']
    assert sha(entry['runtime_audit']) == entry['runtime_audit_sha256']
    validate_report(Path(entry['runtime_audit']), child, 'evaluate')
    result = read(child/'result.json')
    assert result['completed'] and result['source_unchanged'] and result['physical_flags_ok']
    assert not any(result[key] for key in ('forbidden_calls', 'missing_import_pins', 'failure', 'cleanup_error'))
    assert result['process_mode'] == 'fresh_process' and result['evaluation_mode'] == 'stochastic'
    assert len(result['case_manifests']) == 1
    assert result['case_manifests'][str(child/'case_000')] == sha(child/'case_000/result.json')
    inputs = check_inputs(child/'inputs_before.json')
    case = child/'case_000'
    capture = read(case/'result.json')
    assert capture['completed'] and capture['teacher_intervention'] is False
    assert capture['perturbation'] is None and capture['source_unchanged'] and capture['physical_flags_ok']
    assert capture['initialization_checkpoint_sha256'] == sha(capture['source_checkpoint'])
    seed = read(case/'evaluation_seed.json')
    assert seed['seed_applied_after_checkpoint_load'] and seed['case_index'] == 0
    assert seed['protocol_case_index'] == index and seed['seed'] == protocol['cases'][index]['seed']
    assert seed['evaluation_mode'] == 'stochastic' and seed['process_mode'] == 'fresh_process'
    assert seed['checkpoint_sha256'] == capture['initialization_checkpoint_sha256']
    artifacts = {
        'trace_sha256': 'trace.jsonl.gz', 'demonstration_sha256': 'demonstration.npz',
        'contract_sha256': 'contract.json', 'settings_sha256': 'settings.json',
        'inputs_before_sha256': 'inputs_before.json', 'context_sha256': 'context.json',
        'initial_sha256': 'initial.json', 'initial_state_sha256': 'initial_state.json',
        'case_spec_sha256': 'case_spec.json', 'evaluation_seed_sha256': 'evaluation_seed.json',
    }
    assert all(capture[key] == sha(case/file) for key, file in artifacts.items())
    lifecycle = read(child/'environment/persistent_lifecycle.json')
    assert lifecycle['closed'] and lifecycle['episode_index'] == 0
    assert lifecycle['native_calls']['create_sim'] == lifecycle['native_calls']['destroy_sim'] == 1
    assert lifecycle['native_calls']['create_env'] == 1 and lifecycle['forbidden_calls_total'] == 0
    pids = [item for item in observations if item['out'] == str(child) and item['protocol_case_index'] == index]
    assert len(pids) == 1
    target = next(iter(capture['episode']['transition']['per_target'].values()))
    records.append(dict(seed=seed['seed'], pid=pids[0]['pid'], start_ticks=pids[0]['start_ticks'],
                        successful=capture['success'], checked_inputs=inputs,
                        initial_state_sha256=capture['initial_state_sha256'],
                        hold_fraction=target['clean_hold_fraction'],
                        release_fraction=target['qualified_target_contact_absent_fraction']))
assert len({(row['pid'], row['start_ticks']) for row in records}) == 6
summary = dict(passed=True, run=name, parent_checked_inputs=parent_inputs,
               successful_cases=sum(row['successful'] for row in records), cases=records,
               scope='Separate native processes with local case index zero; no hidden-cache equality claim.',
               validator_sha256=sha(BASE/'validate_fresh6_v1.py'))
(BASE/(name+'_validation.json')).write_text(json.dumps(summary, indent=2)+'\n')
print(dict(passed=True, run=name, successes=summary['successful_cases'], cases=len(records)))
