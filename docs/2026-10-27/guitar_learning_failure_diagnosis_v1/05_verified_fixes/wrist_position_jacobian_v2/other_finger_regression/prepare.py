"""CPU-only readers, exact settings, initial model and fixed original-CLI plan checks."""
import json
from pathlib import Path
import sys
import tempfile

import run_regression as run


def main():
    sys.path.insert(0, str(run.ROOT))
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.__main__ import parser
    from guitar_learning.tool.experiments.short_finger_learning import runner, runtime
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    from guitar_learning.tool.experiments.short_finger_learning.wrist import WRIST_CONTROL
    baseline = run.reused().original()
    assert not torch.cuda.is_available() and WRIST_CONTROL['schema'].endswith('.v2')
    run.reject_existing(run.HERE/'runs')
    plan = run.jobs()
    assert len(plan) == 12 and len({j['out'] for j in plan}) == 12
    assert [j['name'] for j in plan] == [f+'_'+c for f in run.FINGERS for c in ('initial', 'reference', 'zero', 'random')]
    inputs = run.HERE/'cpu_inputs'; inputs.mkdir()
    settings_by_finger, references, hashes = {}, {}, {}
    evidence = set()
    for finger in run.FINGERS:
        group = [j for j in plan if j['finger'] == finger]
        args = parser().parse_args(group[0]['args'][group[0]['args'].index(baseline.MODULE)+1:])
        settings = runner.make_settings(args)
        spec = settings['song']['short_learning']
        assert settings['num_envs'] == 4 and settings['updates'] == 1 and settings['horizon'] == 32
        assert settings['seed'] == 7 and settings['size'] == 'large' and settings['checkpoint_every'] == 50
        assert spec['wrist_control'] == WRIST_CONTROL and spec['teacher']['ramp_s'] == 2 and spec['view']['local_onset_s'] == 3
        ref_job = group[1]
        reference_path = Path(ref_job['args'][ref_job['args'].index('--reference')+1])
        reference = read_reference(reference_path, spec)
        assert len(reference['selected_targets_rad']) == 4
        references[finger] = dict(path=str(reference_path), sha256=baseline.sha(reference_path),
            target_id=spec['teacher']['source_target_id'], finger=spec['finger'])
        for job in group[1:]:
            evaluated = parser().parse_args(job['args'][job['args'].index(baseline.MODULE)+1:])
            assert evaluated.episodes == 4 and Path(evaluated.checkpoint) == inputs.parent/'runs'/(finger+'_initial')/'initial.pt'
            assert evaluated.control == job['control']
        metadata, snapshot = fixture(4)
        env = runtime.ShortEnvironment(metadata, bundle=settings['song_training']['bundle'],
            song=settings['song'], skill=settings['finger_skill'], device='cpu')
        observation = env.reset(range(4), snapshot)
        torch.manual_seed(7)
        policy = runtime.ShortPolicy(contract=env.contract, size='large')
        assert len(policy.state_dict()) == 73 and observation['state'].shape == (4, 561)
        hashes[finger] = run.model_hash(policy.state_dict())
        baseline.write(inputs/(finger+'_settings.json'), settings)
        settings_by_finger[finger] = settings
        evidence.update(map(Path, spec['teacher']['source_evidence']))
        evidence.update(map(Path, reference['source_evidence']))
        evidence.update((Path(spec['teacher']['input_path']), reference_path))
    assert len(set(hashes.values())) == 1
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'output'
        path.mkdir()
        try: run.reject_existing(path)
        except FileExistsError: pass
        else: raise AssertionError('Existing output accepted')
        link = Path(temp)/'dangling'; link.symlink_to(Path(temp)/'missing')
        try: run.reject_existing(link)
        except FileExistsError: pass
        else: raise AssertionError('Dangling output symlink accepted')
    baseline.write(run.HERE/'dry_run.json', dict(jobs=plan, GPU_executed=False, old_checkpoints_used=False))
    baseline.write(run.HERE/'cpu_verification.json', dict(CPU_only=True, GPU_executed=False,
        current_wrist_control=WRIST_CONTROL, references=references, settings_exact_files=[str(inputs/(f+'_settings.json')) for f in run.FINGERS],
        CPU_initial73_model_sha256=hashes, state_dim=561, selected_action_count=4,
        output_existing_and_dangling_symlink_rejected=True, original_CLI_jobs=12,
        original_source_tests='38 CPU tests and independent source review passed upstream; not rerun here',
        CUDA_initialized=torch.cuda.is_initialized(), scope='preparation only; no native outcome or learned performance'))
    assert not torch.cuda.is_initialized()
    evidence.update(run.HERE/p for p in ('run_regression.py','prepare.py','PLAN.md','dry_run.json','cpu_verification.json'))
    evidence.update((Path(run.reused().__file__), Path(baseline.__file__)))
    evidence.update(inputs/(f+'_settings.json') for f in run.FINGERS)
    # _pins includes its output settings path; use the already-created middle settings under its original name.
    baseline.write(inputs/'settings.json', settings_by_finger['middle'])
    pins = runner._pins(settings_by_finger['middle'], inputs, evidence)
    active = {p:h for p,h in pins.items() if str(p).startswith(str(run.ROOT/'guitar_learning')+'/') and p.endswith('.py')}
    assert all(baseline.sha(p) == h for p,h in pins.items())
    baseline.write(run.HERE/'preparation_seal.json', dict(independent_review='pending', input_pins=pins,
        active_source_pins=active, wrist_control=WRIST_CONTROL, CPU_initial_model_sha256=hashes['middle'],
        planned_jobs=12, controls=['reference','zero','random'], episodes_per_condition=4,
        scope='CPU preparation only; wait for root index analysis and GPU handoff'))
    print(json.dumps(dict(CPU_only=True, jobs=12, input_pins=len(pins), CPU_initial73_equal=True, GPU_executed=False)))


if __name__ == '__main__':
    main()
