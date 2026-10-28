"""CPU strict load, observer fixture, output protection and one-job preparation."""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

from common import HERE, ROOT, OLD, CHECKPOINT, CLOCKS, LIMIT, reused, sha, write, protocol, reject_existing, owned
import run_probe
sys.path.insert(0, str(ROOT))


def main():
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner, runtime
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    assert not torch.cuda.is_available()
    torch.set_num_threads(1)
    payload = torch.load(CHECKPOINT, map_location='cpu', weights_only=False)
    runner._validate_pins(payload['metadata'])
    assert payload['updates'] == 0
    settings = payload['metadata']['settings']
    meta, _ = fixture(4)
    env = runtime.ShortEnvironment(meta, bundle=settings['song_training']['bundle'], song=settings['song'],
        skill=settings['finger_skill'], device='cpu')
    contract_path = OLD/'runs/index_reference/training_contract.json'
    native_contract = json.loads(contract_path.read_text())
    assert native_contract == payload['identity']['architecture']['contract']
    # Fixture native backend/controller differs; verify current environment math sections.
    for key in ('observation', 'task', 'reward', 'termination'):
        if key in env.contract:
            assert env.contract[key] == native_contract[key], key
    policy = runtime.ShortPolicy(contract=native_contract, size=settings['size'])
    trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
    assert trainer._identity() == payload['identity']
    assert all(torch.isfinite(v).all() for v in payload['model'].values())
    policy.load_state_dict(payload['model'], strict=True)
    assert trainer.updates == 0 and all(torch.equal(v, policy.state_dict()[k]) for k, v in payload['model'].items())
    job = run_probe.jobs()[0]; original = reused().jobs()[1]
    restored = copy.deepcopy(job); restored['out'] = original['out']
    index = restored['args'].index(str(HERE/'child.py'))
    restored['args'][index:index+1] = ['-m', reused().MODULE]
    restored['args'] = [v.replace(job['out'], original['out']) for v in restored['args']]
    assert restored == original and len(run_probe.jobs()) == 1

    # Execute the actual nested observer class against a CPU-only original-pool fixture.
    class Base:
        def __init__(self, settings, output):
            self.scene = SimpleNamespace(device='cpu')
            self.environment = SimpleNamespace(clock=torch.full((4,), 476), tick_failure=torch.zeros(4, 3, dtype=torch.bool),
                failure=torch.zeros(4, 3, dtype=torch.bool), wrist_failure=torch.zeros(4, dtype=torch.bool),
                wrist_severe_failure=torch.zeros(4, dtype=torch.bool))
            self.native = dict(q=torch.zeros(4, 105), qd=torch.zeros(4, 105), target=torch.zeros(4, 105),
                body_state=torch.zeros(4, 106, 13), jacobian=torch.zeros(4, 65, 6, 105),
                physics_step=self.environment.clock, reset_body_snapshot=torch.zeros(4, dtype=torch.bool))
            self.scene.snapshot = lambda: self.native
            self.calls = 0
        def step(self, action):
            self.calls += 1; self.last_action = action
            self.environment.clock += 4
            return (None, None, None, None, None, [])
    tree = ast.parse((HERE/'child.py').read_text())
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    cls = next(n for n in main_node.body if isinstance(n, ast.ClassDef) and n.name == 'ObservedPool')
    rows, instances = [], []
    scope = dict(original_pool=Base, torch=torch, CLOCKS=CLOCKS, rows=rows, instances=instances)
    exec(compile(ast.Module(body=[cls], type_ignores=[]), '<actual observer class>', 'exec'), scope)
    pool = scope['ObservedPool'](dict(num_envs=4, song=dict(short_learning=dict(finger=1))), None)
    action = torch.arange(156).reshape(4, 39).float(); before_action = action.clone()
    for clock in CLOCKS:
        pool.environment.clock.fill_(clock)
        pool.step(action)
    assert pool.calls == 4 and pool.last_action is action and torch.equal(action, before_action)
    assert pool.four_substeps and len(rows) == 4 and all(r['jacobian'].shape == (4, 65, 6, 105) for r in rows)
    assert np.array_equal(np.stack([r['clock'] for r in rows]), np.array(CLOCKS)[:, None]*np.ones((4, 4)))
    pool.native['q'].fill_(99); pool.native['jacobian'].fill_(99)
    assert all((r['q'] == 0).all() and (r['jacobian'] == 0).all() for r in rows)
    pool.environment.clock.fill_(777); pool.step(action)
    pool.environment.clock.fill_(476); pool.step(action)  # Duplicate clock rejected without altering original call.
    assert len(rows) == 4 and pool.calls == 6
    expected_bytes = sum(v.nbytes for row in rows for v in row.values())+106*3*4
    assert expected_bytes < LIMIT

    with tempfile.TemporaryDirectory(prefix='coordinate_output_') as temp:
        out = Path(temp)/'existing'; out.mkdir(); sentinel = out/'untouched'; sentinel.write_bytes(b'preserve')
        stat = out.stat(); identity = (stat.st_dev, stat.st_ino)
        assert owned(out, identity) and not owned(out, (identity[0], identity[1]+1))
        # Child must fail before either native extension or original evaluator can import.
        args = job['args'][job['args'].index(str(HERE/'child.py')):]
        args[args.index('--out')+1] = str(out)
        check_env = __import__('os').environ.copy(); check_env['PYTHONPATH'] = str(ROOT)
        result = subprocess.run([sys.executable, '-v', *args], env=check_env, capture_output=True, text=True)
        assert result.returncode != 0 and 'FileExistsError' in result.stderr
        assert "import 'isaacgym" not in result.stderr and "import 'guitar_learning.tool.experiments.short_finger_learning.runner" not in result.stderr
        assert sentinel.read_bytes() == b'preserve' and list(out.iterdir()) == [sentinel]
        assert (out.stat().st_dev, out.stat().st_ino) == identity
        dangling = Path(temp)/'dangling'; dangling.symlink_to(Path(temp)/'missing')
        args[args.index('--out')+1] = str(dangling)
        rejected = subprocess.run([sys.executable, '-v', *args], env=check_env, capture_output=True, text=True)
        assert rejected.returncode != 0 and 'FileExistsError' in rejected.stderr
        assert "import 'isaacgym" not in rejected.stderr and dangling.is_symlink() and not dangling.exists()
    for path in HERE.glob('*.py'):
        ast.parse(path.read_text(), feature_version=(3, 8))
    assert not torch.cuda.is_initialized()
    verification = dict(CPU_only=True, GPU_executed=False, strict_checkpoint_pins=len(payload['metadata']['input_pins']),
        initial_updates=trainer.updates, exact_model_tensors=len(policy.state_dict()), complete_identity_config_equal=True, strict_model_load=True,
        native_complete_trainer_load='required unchanged runner at GPU runtime; CPU cannot restore saved CUDA RNG topology',
        original_job_exact_except_child_and_out=True, jobs=1, actual_observer_class_fixture=True,
        unchanged_action_object_and_values=True, exactly_one_original_call_per_step=True,
        captured_clones_independent=True, only_four_predeclared_clocks=True,
        expected_uncompressed_capture_bytes=expected_bytes, byte_limit=LIMIT,
        existing_output_unchanged_and_no_native_or_runner_import=True, dangling_output_symlink_rejected=True, dev_inode_ownership=True,
        python38_syntax=True, CUDA_initialized=False)
    write(HERE/'cpu_verification.json', verification)
    write(HERE/'dry_run.json', dict(jobs=run_probe.jobs(), GPU_executed=False))
    # Existing checkpoint source identity stays strict. New observer files are explicit extra inputs.
    pins = dict(payload['metadata']['input_pins'])
    evidence = json.loads((HERE/'cpu_evidence.json').read_text())['input_pins']
    pins.update(evidence)
    pins[str(contract_path)] = sha(contract_path)
    for name in ('common.py', 'child.py', 'run_probe.py', 'prepare.py', 'cpu_audit.py', 'PLAN.md', 'README.md',
                 'cpu_evidence.json', 'cpu_verification.json', 'dry_run.json'):
        pins[str(HERE/name)] = sha(HERE/name)
    write(HERE/'preparation_seal.json', dict(independent_review='pending', protocol=protocol(), input_pins=pins))
    print(json.dumps(verification, ensure_ascii=False))


if __name__ == '__main__':
    main()
