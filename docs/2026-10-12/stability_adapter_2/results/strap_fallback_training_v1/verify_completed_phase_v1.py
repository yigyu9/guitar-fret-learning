"""Audit only completed smoke/probe/artifacts; ongoing runs are excluded."""
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
checks = {}
inputs = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    inputs[str(path)] = sha(path)
    return json.loads(path.read_text())


def verify_hashes(name, expected):
    changed = [path for path, value in expected.items() if sha(path) != value]
    checks[name] = {'count': len(expected), 'changed': changed, 'passed': not changed}


source = read(P/'source_before_native_v1/sha256.json')
verify_hashes('executed_source_preserved', source)
snapshot = P/'source_final_v1'
snapshot.mkdir(exist_ok=False)
for path in source:
    shutil.copyfile(path, snapshot/Path(path).name)
prefix = read(P/'main_prefix_v1.json')
checks['main_prefix_preserved'] = {
    path: Path(path).read_bytes().startswith(Path(value['snapshot']).read_bytes())
    and sha(value['snapshot']) == value['sha256'] for path, value in prefix.items()}
physical_steps = scenes = transitions = updates = 0
evaluation_summary = []
for mode in ('off', 'on'):
    base = P/f'smoke_{mode}_v1'
    report = read(base/'report.json')
    verify_hashes(f'{mode}_closure', read(base/'attempt.json')['input_sha256'])
    rows = [json.loads(line) for line in (base/'training.jsonl').read_text().splitlines()]
    inputs[str(base/'training.jsonl')] = sha(base/'training.jsonl')
    checks[f'{mode}_optimizer'] = len(rows) == 12 and all(
        row['ppo']['optimizer_steps'] > 0 for row in rows)
    checks[f'{mode}_report'] = report['completed'] and report['inputs_unchanged']
    updates += report['updates']; transitions += report['transitions']
    physical_steps += sum(x['physics_steps'] for x in rows[-1]['completed_episodes'])
    physical_steps += report['native_report']['physics_steps']
    scenes += len(rows[-1]['completed_episodes']) + 1
    for record in report['evaluations']:
        evaluation = read(Path(record['output'])/'report.json')
        native = evaluation['native_report']
        checks[f'{mode}_{record["label"]}'] = evaluation['completed'] and not record['returncode']
        verify_hashes(f'{mode}_{record["label"]}_videos', {
            value['path']: value['sha256'] for value in native['videos'].values()})
        physical_steps += native['physics_steps']; scenes += 1
        evaluation_summary.append({'mode': mode, 'label': record['label'],
            'full_horizon': native['full_horizon_completed'],
            'actual_seconds': native['physics_seconds'],
            'stop_reason': native['stop_reason'],
            'music_success': native['joint_success_events']})
probe = read(P/'reset_probe_v2/report.json')
verify_hashes('reset_probe_closure', read(P/'reset_probe_v2/attempt.json')['input_sha256'])
checks['actual_reset'] = probe['probe_completed'] and probe['physical_reset_observed'] \
    and probe['optimization_updates_added'] == 0 and probe['batch_transitions'] == 300
physical_steps += sum(x['physics_steps'] for x in probe['episode_reports'])
scenes += len(probe['episode_reports'])
for version in ('v1', 'v2'):
    hashes = read(P/f'artifacts_initial_{version}/input_hashes.json')
    verify_hashes(f'artifacts_{version}_inputs', hashes['before'])
comparison = read(P/'initial_comparison_v1.json')
verify_hashes('comparison_inputs', comparison['input_sha256'])
checks['initial_policy_state_equal'] = comparison['same_initial_native_state_exact'] \
    and comparison['same_model_RMS']['initial_model_and_RMS_all_keys_exact']
links = {}
for name in ('README.md', 'CHANGED_FILES.md'):
    path = P/name; inputs[str(path)] = sha(path)
    for target in re.findall(r'\]\((/[^)]+)\)', path.read_text()):
        match = re.fullmatch(r'(.*):(\d+)', target)
        file = Path(match[1] if match else target)
        links[target] = file.exists() and (not match or len(file.read_text().splitlines()) >= int(match[2]))
checks['document_links'] = links
verify_hashes('audit_inputs_still_unchanged', inputs)
passed = all(value['passed'] if isinstance(value, dict) and 'passed' in value
             else all(value.values()) if isinstance(value, dict) else value
             for value in checks.values())
result = {'utc': datetime.now(timezone.utc).isoformat(), 'completed_scope_passed': passed,
    'scope': 'completed smokes, reset probe v2, initial comparison and artifacts; ongoing long runs excluded',
    'checks': checks, 'evaluation_summary': evaluation_summary,
    'training_updates': updates, 'training_transitions': transitions,
    'diagnostic_transitions_no_optimization': probe['batch_transitions'],
    'actual_physics_steps_in_scope': physical_steps, 'actual_scene_initializations_in_scope': scenes,
    'failed_probe_v1_additional_physics_steps': 0,
    'production_reward_certified': False, 'training_goal_achieved': False,
    'input_sha256': inputs, 'producer_sha256': sha(__file__)}
(P/'final_verification_v1.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: result[key] for key in ('completed_scope_passed',
    'training_updates', 'training_transitions', 'actual_physics_steps_in_scope',
    'actual_scene_initializations_in_scope')}))
if not passed:
    raise SystemExit('Completed-scope audit failed; inspect preserved verification output.')
