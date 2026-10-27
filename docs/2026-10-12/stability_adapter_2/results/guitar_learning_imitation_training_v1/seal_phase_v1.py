"""Seal this finite training attempt after final evaluation/review; no native calls.

Writes new files only. A failed final policy remains a failed policy: audit
completion is separate from learned-skill success. Run only after root approval.
"""
from pathlib import Path
import hashlib
import json
import shutil
import gzip

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_imitation_training_v1'
PREVIOUS = PHASE.parent/'guitar_learning_skill_curriculum_v1'
# Captured while preparing this audit, after the preceding independent seal check.
PREVIOUS_SEALS = {
    'final_verification_v1.json': 'f73ec0b656704ab1b69a4aca34b06fcb7a875439ce23c4c0bffce503e75faa63',
    'source_final_v1.json': 'd2a4f3e22d03f02b42fbc2d1aaf2f73579b3a25956ff1400f63851435b16eff3',
    'artifact_inventory_v1.json': '0cc38f79d9d934e0d664cd3060d43991145e1ee23835546debe144e6df3e4111',
}
ARCHIVE_SEALS = {
    '20261018_before_imitation': '7c5465f197e05b1c6a94460e489809b5a66d30edc11e320cc8dbcc0f6ea5fac6',
    '20261018_before_imitation_contract_v2': 'f59d1ef145be582edab5ae4e26d468c80fa7b66e53ec06397911a499d3787768',
}


def path(name):
    value = Path(name)
    return (value if value.is_absolute() else ROOT/value).resolve()


def digest(filename):
    result = hashlib.sha256()
    with path(filename).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def read(filename):
    return json.loads(path(filename).read_text())


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write(filename, document):
    with path(filename).open('x') as stream:
        json.dump(document, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write('\n')


def checks():
    archives, document_copies, substitutions = {}, {}, {}
    manifests = sorted((ROOT/'guitar_learning/archive').glob('20261018_before_imitation*/manifest.json'))
    require(set(ARCHIVE_SEALS) <= {f.parent.name for f in manifests}, 'Required archive manifest missing')
    for filename in manifests:
        if filename.parent.name in ARCHIVE_SEALS:
            require(digest(filename) == ARCHIVE_SEALS[filename.parent.name], 'Original archive manifest changed')
        entries = read(filename)['files']
        for item in entries:
            original, archived, expected = path(item['original']), path(item['archive']), item['sha256']
            require(digest(archived) == expected, 'Archived bytes changed: '+str(archived))
            if original.suffix == '.md':
                document_copies[(str(original), expected)] = archived
            else:
                require(digest(original) == expected, 'Existing implementation/input changed: '+str(original))
        archives[str(filename)] = dict(sha256=digest(filename), files=len(entries))
    main_documents = PHASE/'main_documents_before/manifest.json'
    for name, item in read(main_documents).items():
        original, archived = path(name), path(item['archive'])
        require(original.suffix == '.md' and digest(archived) == item['sha256'],
                'Main-document archive mismatch: '+name)
        document_copies[(str(original), item['sha256'])] = archived
    archives[str(main_documents)] = dict(sha256=digest(main_documents), files=len(read(main_documents)))

    def preserved(filename, expected):
        filename = path(filename)
        actual = digest(filename) if filename.is_file() else None
        if actual == expected:
            return
        archived = document_copies.get((str(filename), expected))
        require(filename.suffix == '.md' and archived is not None,
                'Consumed/source bytes changed without an exact document archive: '+str(filename))
        require(digest(archived) == expected, 'Document archive mismatch: '+str(archived))
        substitutions[(str(filename), expected)] = dict(original=str(filename),
            expected_sha256=expected, archive=str(archived), live_sha256=actual)

    input_manifests = sorted(PHASE.glob('*/inputs_before.json')) + sorted(PHASE.glob('*/inputs.json'))
    inputs = {}
    for filename in input_manifests:
        for name, expected in read(filename).items():
            name = str(path(name))
            require(isinstance(expected, str) and len(expected) == 64, 'Invalid input digest')
            require(name not in inputs or inputs[name] == expected, 'Conflicting consumed input versions: '+name)
            inputs[name] = expected
    require(inputs, 'No consumed input manifests')
    for name, expected in inputs.items():
        preserved(name, expected)
    consumed_substitutions = [v for (name, _), v in substitutions.items() if name in inputs]

    for name, expected in PREVIOUS_SEALS.items():
        require(digest(PREVIOUS/name) == expected, 'Previous seal changed: '+name)
    previous = read(PREVIOUS/'final_verification_v1.json')
    require(previous['completed'], 'Previous phase was not sealed')
    for key, name in (('source_manifest', 'source_final_v1.json'),
                      ('artifact_inventory', 'artifact_inventory_v1.json')):
        require(path(previous[key]['path']) == PREVIOUS/name and
                previous[key]['sha256'] == PREVIOUS_SEALS[name], 'Previous manifest reference mismatch')
    previous_sources = read(PREVIOUS/'source_final_v1.json')['files']
    previous_artifacts = read(PREVIOUS/'artifact_inventory_v1.json')['files']
    for name, expected in previous_artifacts.items():
        require(digest(name) == expected, 'Previous result artifact changed: '+name)
    for mapping in (previous_sources, previous['consumed_inputs']):
        for name, expected in mapping.items():
            preserved(name, expected)

    analyses = {}
    for filename in sorted(PHASE.glob('*.json')):
        document = read(filename)
        if isinstance(document, dict) and 'inputs' in document and 'inputs_unchanged' in document:
            require(document['inputs_unchanged'] is True, 'Analysis input check failed: '+str(filename))
            for name, expected in document['inputs'].items():
                preserved(name, expected)
            analyses[str(filename)] = dict(sha256=digest(filename), inputs=len(document['inputs']))

    log = (PHASE/'cpu_tests_v2.log').read_text()
    require('Ran 207 tests' in log and log.rstrip().endswith('OK'), 'CPU207 pass log missing')
    reviews = {str(PHASE/name): digest(PHASE/name) for name in
               ('review_implementation_v2.md', 'review_results_v1.md')}
    admission = read(PHASE/'ppo_admission_v1.json')
    require(admission['admitted'] is True and admission['cpu_tests'] == 207, 'PPO admission missing')
    runs, rejected_initializations = {}, {}
    import torch  # CPU checkpoint inspection only; no simulator or policy construction.
    for role in ('left', 'right'):
        rejected = PHASE/(role+'_bc_eval_v1')
        failed_lifecycle = read(rejected/'environment/persistent_lifecycle.json')
        require((rejected/'reset_00.json').is_file() and not (rejected/'result.json').exists() and
                failed_lifecycle['closed'] and failed_lifecycle['episode_index'] == 0 and
                failed_lifecycle['episode_local_physics_steps'] == 480 and
                failed_lifecycle['controller_target_history_length'] == 120,
                'Original pre-policy BC initialization failure was not preserved: '+role)
        rejected_initializations[role] = dict(status='v1_contract_loader_rejection_preserved',
            policy_control_steps=0, preparation_physics_steps=480, result_absent=True,
            reset_sha256=digest(rejected/'reset_00.json'),
            lifecycle_sha256=digest(rejected/'environment/persistent_lifecycle.json'))
        initialization = PHASE/(role+'_bc_v1/actor_initialization.pt')
        bc = read(PHASE/(role+'_bc_v1/report.json'))
        capture = read(PHASE/(role+'_capture_v1/result.json'))
        require(capture['success'] and capture['source_unchanged'] and capture['ticks'] == 240 and
                capture['observation_dimension'] == 505, 'Native profile capture failed: '+role)
        require(bc['completed'] and bc['source_unchanged'] and bc['ppo_updates'] == 0 and
                path(bc['checkpoint']['path']) == initialization and
                bc['checkpoint']['sha256'] == digest(initialization), 'BC checkpoint/report mismatch: '+role)
        bc_payload = torch.load(initialization, map_location='cpu', weights_only=False)
        require(bc_payload['schema'] == 'guitar_learning.imitation.v1' and
                bc_payload['role'] == role and 'identity' not in bc_payload and
                'updates' not in bc_payload, 'BC is not an own single-hand initialization')
        bc_eval = read(PHASE/(role+'_bc_eval_v2/result.json'))
        require(bc_eval['completed'] and bc_eval['source_unchanged'] and bc_eval['kind'] == 'BC' and
                capture['role'] == bc['role'] == bc_eval['role'] == role and
                path(bc_eval['checkpoint']) == initialization and len(bc_eval['episodes']) == 2 and
                all(e['specialist']['stage_success'] and e['reason'] == 'timeline_complete'
                    for e in bc_eval['episodes']), 'BC native2/2 admission failed: '+role)
        admitted = admission['native'][role]
        require(admitted['native_successes'] == admitted['episodes'] == 2 and admitted['input_unchanged'] and
                path(admitted['checkpoint']) == initialization, 'Admission evidence mismatch: '+role)
        folder = PHASE/(role+'_ppo_v1')
        report, settings = read(folder/'report.json'), read(folder/'settings.json')
        updates = len(report['updates'])
        require(report['completed'] and read(folder/'persistent_audit.json')['completed'], 'PPO incomplete: '+role)
        require(report['settings'] == settings and settings['specialist']['role'] == role and
                settings['skill'] == ('hold' if role == 'left' else 'cross'), 'PPO profile/settings mismatch')
        require(not any(report[k] for k in ('changed_inputs', 'missing_import_pins', 'guard_violations',
                    'worker_failures', 'physical_flags_errors', 'cleanup_errors')), 'PPO audit failed: '+role)
        require(settings['num_envs'] == 2 and settings['horizon'] == 240 and settings['updates'] == 24 and
                settings['ppo']['cost_weight'] == 1 and settings['ppo']['actor_lr'] == 1e-5 and
                settings['initial_std'] == .02 and settings['max_wall_seconds'] == 1800 and
                0 < updates <= 24 and report['transitions'] == updates*480, 'PPO budget/config mismatch: '+role)
        require((report['stopped'] == 'updates_complete' and updates == 24) or
                report['stopped'] == 'wall_budget', 'Unexpected PPO stop: '+role)
        logged = 0
        with gzip.open(folder/'transitions.jsonl.gz', 'rt') as stream:
            for line in stream:
                row = json.loads(line)
                require(len(row['infos']) == len(row['reward']) == settings['num_envs'], 'Partial PPO log row')
                logged += len(row['infos'])
        require(logged == report['transitions'], 'Logged/committed PPO transition mismatch: '+role)
        transfer = read(folder/'actor_initialization.json')
        require(transfer['mode'] == 'BC_actor_only_new_critics_and_optimizers' and
                path(transfer['path']) == initialization and transfer['sha256'] == digest(initialization),
                'PPO actor admission mismatch: '+role)
        initial = torch.load(folder/'initial.pt', map_location='cpu', weights_only=False)
        final = torch.load(folder/'final.pt', map_location='cpu', weights_only=False)
        require(initial['updates'] == 0 and final['updates'] == updates and
                initial['identity'] == final['identity'] and not initial['actor_optimizer']['state'] and
                not initial['value_optimizer']['state'], 'PPO counter/optimizer identity mismatch: '+role)
        for key, value in bc_payload['model'].items():
            if key.startswith(('actor_encoders.'+role+'.', 'actor_heads.'+role+'.')):
                require(torch.equal(value, initial['model'][key]), 'Initial PPO actor differs from BC: '+key)
        selected = slice(0, 33) if role == 'left' else slice(33, 39)
        require(torch.equal(bc_payload['model']['log_std'][selected], initial['model']['log_std'][selected]),
                'Initial PPO exploration differs from BC: '+role)
        evaluation_folder = PHASE/(role+'_ppo_eval_v1')
        evaluation = read(evaluation_folder/'result.json')
        require(evaluation['completed'] and evaluation['source_unchanged'] and evaluation['kind'] == 'PPO' and
                evaluation['role'] == role and len(evaluation['episodes']) == 2 and
                path(evaluation['checkpoint']) == folder/'final.pt',
                'Final policy evaluation missing/mismatched: '+role)
        pins = {str(path(k)): v for k, v in read(evaluation_folder/'inputs_before.json').items()}
        require(pins.get(str(folder/'final.pt')) == digest(folder/'final.pt'), 'Final checkpoint SHA mismatch: '+role)
        runs[role] = dict(updates=updates, transitions=report['transitions'], stopped=report['stopped'],
            bc_fit_converged=bc['fit']['converged'], bc_native_successes=2,
            final_native_successes=sum(e['specialist']['stage_success'] for e in evaluation['episodes']),
            final_physical_failures=sum(e['reason'] == 'terminal_failure' for e in evaluation['episodes']),
            final_episodes=2, checkpoint_sha256=digest(folder/'final.pt'))

    lifecycles = []
    for filename in sorted(PHASE.rglob('persistent_lifecycle.json')):
        document = read(filename)
        calls = document['native_calls']
        require(document['closed'] and calls['create_sim'] == calls['destroy_sim'] == calls['create_env'] == 1 and
                not document['forbidden_calls_total'], 'Native session not safely closed: '+str(filename))
        lifecycles.append(dict(path=str(filename), sha256=digest(filename), resets=document['episode_index']+1))
    require(lifecycles, 'No native lifecycle evidence')
    return dict(runs=runs, rejected_bc_initializations=rejected_initializations,
        archives=archives, analyses=analyses, consumed_inputs=inputs,
        consumed_input_manifest_count=len(input_manifests), consumed_input_count=len(inputs),
        consumed_inputs_unchanged=not consumed_substitutions,
        consumed_input_preservation_passed=True, consumed_document_substitutions=consumed_substitutions,
        preserved_document_versions=list(substitutions.values()), native_scene_lifecycles=lifecycles,
        lifecycle_count=len(lifecycles), cpu_tests=207, reviews=reviews,
        previous_seals={str(PREVIOUS/k): v for k, v in PREVIOUS_SEALS.items()},
        previous_artifact_count=len(previous_artifacts), previous_source_count=len(previous_sources))


def main():
    outputs = [PHASE/n for n in ('source_final_v1', 'source_final_v1.json',
                                  'artifact_inventory_v1.json', 'final_verification_v1.json')]
    require(not any(p.exists() for p in outputs), 'Seal output already exists; preserve it instead of overwriting')
    result = checks()  # No output is created unless every admission/completion check passes.
    sources = {p.resolve() for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    sources |= {p.resolve() for p in PHASE.glob('*.py')} | {p.resolve() for p in PHASE.glob('*.md')}
    sources |= {p.resolve() for p in (ROOT/'guitar_learning').glob('*.md')}
    sources |= {ROOT/n for n in ('guitar_learning/README.md', 'guitar_learning/SKILL_CURRICULUM.md',
        'docs/plans/guitar_learning_imitation_training_20261018.md', 'stability_adapter_2/PLAN.md',
        'stability_adapter_2/README.md', 'docs/2026-10-12/stability_adapter_2/README.md',
        'docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md')}
    copies, source_hashes = {}, {}
    outputs[0].mkdir()
    for source in sorted(sources):
        expected = digest(source)
        destination = outputs[0]/source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        require(digest(destination) == digest(source) == expected, 'Source changed during snapshot: '+str(source))
        source_hashes[str(source)] = expected
        copies[str(source)] = str(destination)
    write(outputs[1], dict(files=source_hashes, copies=copies,
        scope='Current implementation/tests, local producers, final documentation and reviews; exact byte snapshots'))
    excluded = {outputs[2], outputs[3]}
    artifacts = {str(p): digest(p) for p in sorted(PHASE.rglob('*'))
                 if p.is_file() and p not in excluded and '__pycache__' not in p.parts}
    write(outputs[2], dict(files=artifacts,
        scope='Closed phase artifacts including source snapshots; excludes this inventory and final verification to avoid hash cycles'))
    require(checks() == result, 'Audit inputs/results changed while sealing')
    for name, expected in {**source_hashes, **artifacts}.items():
        require(digest(name) == expected, 'Source/artifact changed while sealing: '+name)
    write(outputs[3], dict(completed=True, research_goal_complete=False, **result,
        source_manifest=dict(path=str(outputs[1]), sha256=digest(outputs[1]), count=len(source_hashes)),
        artifact_inventory=dict(path=str(outputs[2]), sha256=digest(outputs[2]), count=len(artifacts)),
        scope='Finite BC/PPO training and preservation audit; final skill success is reported separately; no music/audio/generalization certification'))
    print(json.dumps(dict(completed=True, consumed_inputs=len(result['consumed_inputs']),
        sources=len(source_hashes), artifacts=len(artifacts), runs=result['runs'])))


if __name__ == '__main__':
    main()
