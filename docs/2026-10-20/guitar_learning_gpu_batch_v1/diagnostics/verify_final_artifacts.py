"""Read-only cross checks; write a fresh verification report once."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2]
load = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks = {}
old = load(ROOT/'guitar_learning/archive/20261020_before_gpu_batch_v1/manifest.json')
checks['archive_intact'] = all(sha(row['archived']) == row['sha256'] for row in old['files'])
changed_old = {str(Path(row['path']).relative_to(ROOT)) for row in old['files'] if sha(row['path']) != row['sha256']}
checks['only_expected_old_files_changed'] = changed_old == {
    'guitar_learning/training/start.py', 'guitar_learning/tests/test_simple_start.py',
    'guitar_learning/README.md', 'guitar_learning/AGENTS.md'}
manifest = load(BASE/'source_manifest.json')
checks['active_sources_match'] = all(sha(p) == value for p, value in manifest['active_python'].items())
checks['snapshots_match'] = all(sha(row['path']) == sha(row['saved']) == row['sha256'] for row in manifest['snapshots'])
for path in manifest['active_python']:
    ast.parse(Path(path).read_bytes(), filename=path)
checks['active_syntax'] = True
runs = {}
for name, (transitions, optimizer_updates, dimension) in {
        'n1024_large_v4': (65536, 2, 512), 'n1024_resume_v1': (32768, 3, 512),
        'n128_default_v1': (8192, 2, 512), 'right_n2_v1': (16, 1, 500)}.items():
    report = load(BASE/name/'report.json')
    contract = load(BASE/name/'training_contract.json')
    pins = load(BASE/name/'inputs_before.json')
    scene = report['gpu_scene']
    journal = report['journal']
    episodes = [json.loads(line)['episode'] for line in (BASE/name/'episodes.jsonl').read_text().splitlines()]
    console = (BASE/(name+'_console.log')).read_text()
    run_checks = dict(completed=report['completed'] is True,
        counts=report['transitions'] == transitions and report['optimizer_updates'] == optimizer_updates,
        journal=all(journal[key] == transitions for key in ('sampled','logged','durable','committed')) and journal['discarded'] == 0,
        sources=not report['changed_inputs'] and not report['missing_import_pins'] and all(sha(p) == value for p, value in pins.items()),
        lifecycle=report['lifecycle_verified'] and scene['closed'] and not report['cleanup_errors'],
        actual_cuda=scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['simulator_count'] == 1 and
            all(device == 'cuda:0' for device in scene['tensor_devices'].values()),
        observation=contract['observation']['dimension'] == dimension,
        new_contact=contract['task']['contact_measurement']['schema'] == 'guitar_learning.gpu_loaded_geometry.v1',
        episodes=len(episodes) == report['completed_episodes'],
        no_physics_capacity_or_cuda_error=not re.search('miss interactions|CUDA error|device-side assert|out of memory',console,re.I))
    runs[name] = dict(checks=run_checks, physical_failure_episodes=sum(e['reason'] == 'terminal_failure' for e in episodes),
        timeline_complete_episodes=sum(e['reason'] == 'timeline_complete' for e in episodes))
    checks[name] = all(run_checks.values())
zero = load(BASE/'zero_action_song_v1/report.json')
checks['native_whole_song'] = (zero['completed'] and zero['timeline_complete_episodes'] == 2 and
    zero['physical_failure_episodes'] == 0 and zero['controls'] == 1969 and zero['target_count'] == 67 and
    all(zero['checks'].values()) and not zero['clock_errors'] and not zero['curriculum_clock_errors'])
checks['selective_reset'] = load(BASE/'selective_reset_v1/report.json')['passed']
checks['strict_resume'] = load(BASE/'resume_verification.json')['passed']
checks['reject_cpu_checkpoint'] = load(BASE/'cpu_checkpoint_rejection.json')['passed']
cpu = load(BASE/'cpu_regression/assessment.json')
checks['gpu_cpu_unit_tests_pass'] = cpu['final_gpu_all_passed'] and not cpu['module_test_sources_changed_since_their_latest_run']
checks['legacy_failure_reported_honestly'] = (not cpu['all_tests_passed'] and cpu['passing_test_methods'] == 784 and
    cpu['effective_unique_test_methods'] == 785 and len(cpu['standalone_fatal_cases']) == 1 and
    all(row['unchanged'] for row in cpu['teacher_proof_sources']))
# Check the new/updated local documentation links after all artifacts exist.
missing_links = []
for path in (ROOT/'guitar_learning/README.md',ROOT/'docs/2026-10-26/learning_flow/README.md',BASE/'README.md'):
    for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        target = target.split('#')[0]
        resolved = Path(target) if target.startswith('/') else path.parent/target
        if resolved.name == 'verification.json':
            continue
        if not resolved.exists():
            missing_links.append(dict(document=str(path), target=target))
checks['local_links'] = not missing_links
result = dict(schema='guitar_learning.gpu_final_verification.v1', passed=all(checks.values()), checks=checks,
    runs=runs, active_python_files=len(manifest['active_python']), missing_links=missing_links,
    cpu_all_tests_passed=False, known_cpu_failure=cpu['standalone_fatal_cases'],
    scope='GPU implementation/runtime/serialization verified;1024 long-run physical stability and learned music not certified')
with Path(sys.argv[1]).open('x') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result, indent=2))
raise SystemExit(not result['passed'])
