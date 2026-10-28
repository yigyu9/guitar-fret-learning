"""New finite schedules only; original prefix scene, collector and music math."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PREFIX = HERE.parent/'index_prefix_4_7_8_v1'
ZERO = HERE.parent/'low_effort_index_learning_v1'


def module(name, path):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return sys.modules[name]


prefix = module('release_original_prefix', PREFIX/'probe.py')
timing = module('release_fixed_schedule', HERE/'schedule.py')
grid, cap = prefix.grid, prefix.cap


def reviewed(path):
    review = grid.read(path); assert review['verdict'] == 'PASS' and not review['findings']
    verification = path.parent/'verification.json'
    assert str(verification) in review['reviewed_sha256']
    paths = {path}
    for values in (review['reviewed_sha256'], *[grid.read(verification)[k] for k in ('input_sha256', 'verified_input_sha256')]):
        assert values and all(Path(p).is_file() and grid.sha(p) == h for p, h in values.items()); paths.update(map(Path, values))
    return paths


def evidence():
    return prefix.evidence() | reviewed(PREFIX/'analysis/results_v1/review.json') | reviewed(ZERO/'precheck_analysis/results_v1/review.json')


def settings(): return grid.read(HERE/'cpu_inputs/index_settings.json')


def gate(require_review=True):
    paths = evidence(); seal = grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p) == h for p, h in seal['input_pins'].items())
    if require_review:
        review = grid.read(HERE/'review.json')
        assert seal['independent_review'] == 'passed_no_findings' and review['verdict'] == 'PASS' and not review['findings']
        assert seal['input_pins'][str(HERE/'review.json')] == grid.sha(HERE/'review.json')
    return seal, paths | {HERE/'preparation_seal.json'}


@contextmanager
def execution_scope(state):
    import torch
    extra = prefix.support()  # Load the frozen module before scoping its producer HERE.
    old = (prefix.HERE, prefix.settings, extra.PrefixPool, extra.transition_fraction, extra.trajectory_actions)
    config = settings(); short = config['song']['short_learning']; action_ids = short['learned_action_indices']
    observer = timing.Observer(short['view']); state['observer'] = observer
    state['requests'] = []; hooks = []

    class ReleasePool(old[2]):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs); state['pool'] = self
            env = self.environment; original = env.substep; hooks.append((env, original))
            distal = self.scene.metadata['body_names'].index('human/LH:index3')
            def observe(snapshot):
                value = original(snapshot)
                failed = (env.invalid | env.control_invalid | env.tick_failure.any(-1) | env.wrist_failure | env.wrist_severe_failure |
                          ~torch.isfinite(snapshot['q']).all(-1) | ~torch.isfinite(snapshot['qd']).all(-1))
                observer.observe(env.clock.detach().cpu().tolist(), env.candidate[:, [4,7,8]].detach().cpu().tolist(),
                    env.surface_body_loaded[:, [4,7,8]].detach().cpu().tolist(), env.wrong[:, [4,7,8]].detach().cpu().tolist(),
                    torch.linalg.vector_norm(snapshot['contact_force'][:, distal], dim=-1).detach().cpu().tolist(), failed.detach().cpu().tolist())
                return value
            env.substep = observe

        def step(self, action):
            native = self.controller.active[action_ids]; old_target = self.controller.target[:, native].clone()
            result = super().step(action)
            target = self.controller.target[:, native]
            assert torch.equal(target, self.scene.target[:, native]) and bool(torch.isfinite(target).all())
            low = torch.maximum(self.controller.lower[native], self.controller.action_low[action_ids])
            high = torch.minimum(self.controller.upper[native], self.controller.action_high[action_ids])
            assert bool(((target >= low-2e-6) & (target <= high+2e-6)).all())
            assert bool(((target-old_target).abs() <= self.controller.rate[native]/60+2e-6).all())
            request = state['requests'][-1]
            request['actual_native_target_rad'] = target.detach().cpu().numpy().copy()
            request['actual_selected_q_rad'] = self.scene.q[:, native].detach().cpu().numpy().copy()
            request['failure_after_control'] = (self.environment.invalid | self.environment.wrist_failure | self.environment.wrist_severe_failure).detach().cpu().numpy().copy()
            observer.finish(result[5]); return result

    def trajectory(desired, current, *args, **kwargs):
        pool = state['pool']; endpoint = pool.environment._local_time()+1/60
        goal = desired.clone(); weight = timing.negative_weight(endpoint, short['view']).to(goal)
        declared = short['release_transfer']
        goal[:, action_ids] += weight[:, None]*(goal.new_tensor(declared['negative_selected_rad'])-goal.new_tensor(declared['reference_selected_rad']))
        state['requests'].append(dict(submit_clock=pool.environment.clock.detach().cpu().numpy().copy(),
            endpoint_clock=(pool.environment.clock+4).detach().cpu().numpy().copy(), first_attempt=list(observer.active),
            phase=[timing.phase(float(t), short['view']) for t in endpoint.detach().cpu().tolist()],
            selected_goal_rad=goal[:, action_ids].detach().cpu().numpy().copy(), old_target_rad=current[:, action_ids].detach().cpu().numpy().copy()))
        assert len(state['requests']) <= 354
        return old[4](goal, current, *args, **kwargs)

    prefix.HERE = HERE; prefix.settings = settings; extra.PrefixPool = ReleasePool
    extra.transition_fraction = timing.wrist_weight; extra.trajectory_actions = trajectory
    try:
        with prefix.execution_scope(state): yield
    finally:
        for env, original in hooks: env.substep = original
        state['observer_hooks_restored'] = all(env.substep is original for env, original in hooks)
        prefix.HERE, prefix.settings, extra.PrefixPool, extra.transition_fraction, extra.trajectory_actions = old
        state['schedule_aliases_restored'] = all(a is b for a,b in zip((prefix.HERE,prefix.settings,extra.PrefixPool,extra.transition_fraction,extra.trajectory_actions),old))


def postcheck(out):
    import numpy as np
    import torch
    config = settings(); short = config['song']['short_learning']; view = short['view']; declared = short['release_transfer']
    evaluation = grid.read(out/'evaluation.json'); rows = evaluation['episodes']
    assert grid.complete(rows,4) and evaluation['assigned_quotas'] == [1]*4 and evaluation['policy_performance'] is False
    by_note = {}
    for col, target in enumerate(view['source_targets']):
        one = []
        for row in rows:
            assert row['selected_target_count'] == len(row['notes']) == 3 and len(row['reward_components']) == 9 and row['steps'] <= 354
            note = row['notes'][col]; assert note['target_id'] == target['target_id'] and note['source_index'] == [4,7,8][col]
            one.append(dict(note,env_id=row['env_id'],termination=row['termination']))
        by_note[target['target_id']] = cap.repro.acceptance(one)
    with np.load(out/'trace_env0_episode0.npz') as saved: trace = dict(saved)
    with np.load(out/'schedule_requests.npz') as saved: requests = dict(saved)
    time = torch.tensor(trace['time_s']); hold = trace['time_s'] >= 2.
    ids = [grid.read(out/'trace_metadata.json')['joint_names'].index(n) for n in short['learned_action_names']]
    target = trace['target'][:,ids]; native = grid.read(out/'native_effort_readback.json')['actual_native_PD105']
    assert np.isfinite(target).all() and ((target >= np.array(native['lower'])[ids]-2e-6) & (target <= np.array(native['upper'])[ids]+2e-6)).all()
    assert np.all(np.diff(np.rint(trace['time_s']*240)) == 4)
    np.testing.assert_allclose(trace['source_time_s'],trace['time_s']+view['score_offset_s'],rtol=0,atol=1e-8)
    expected = np.array(declared['reference_selected_rad'])+timing.negative_weight(time,view).numpy()[:,None]*(np.array(declared['negative_selected_rad'])-declared['reference_selected_rad'])
    np.testing.assert_allclose(target[hold],expected[hold],rtol=0,atol=2e-6)
    position = np.array(short['teacher']['wrist_position_G_m'])+timing.wrist_weight(time,view).numpy()[:,None]*np.array(short['prefix']['delta_G_m'])
    np.testing.assert_allclose(trace['wrist_position_goal_G_m'][hold],position[hold],rtol=0,atol=2e-6)
    np.testing.assert_allclose(abs(trace['wrist_quaternion_goal_G_xyzw'][hold]@np.array(short['teacher']['wrist_quaternion_G_xyzw'])),1.,rtol=0,atol=2e-6)
    first = requests['first_attempt'][:,0]
    assert np.array_equal(requests['actual_native_target_rad'][first,0],target)
    np.testing.assert_allclose(requests['endpoint_clock'][first,0]/240,trace['time_s'],rtol=0,atol=1e-8)
    step = abs(requests['actual_native_target_rad']-requests['old_target_rad']); assert np.isfinite(step).all() and step.max() <= 4/60+2e-6
    return dict(per_note_original_acceptance=by_note,prefix_passed=all(a['passed'] for a in by_note.values()),
        all3_achieved_attempts=sum(r['achieved'] for r in rows),attempts=4,env0_endpoints=len(target),
        selected_max_control_delta_rad=float(step.max()),request_controls=len(first),finite_schedule_and_rate_bounds_verified=True,
        postramp_endpoints=int(hold.sum()),postramp_schedule_match=True if hold.any() else None,
        scope='original each-note acceptance AND; observed N is not guaranteed A release/B negative; no new release success gate')


def launch():
    out = HERE/'runs/index'; cap.reject_existing(out); seal, paths = gate()
    out.mkdir(parents=True,exist_ok=False); identity = (out.stat().st_dev,out.stat().st_ino)
    state = dict(task_verified=False,aliases_restored=False,cleanup_errors=[]); failure = None; completed = False
    try:
        import isaacgym
        with execution_scope(state): prefix.base.execute('index','reference',out,identity,seal,paths)
        import numpy as np
        assert state['requests'] and all('actual_native_target_rad' in r for r in state['requests'])
        np.savez_compressed(out/'schedule_requests.npz',**{key:np.asarray([r[key] for r in state['requests']]) for key in state['requests'][0]})
        grid.write(out/'release_transfer_acceptance.json',postcheck(out)); completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error))
        if not (out/'report.json').exists(): grid.write(out/'report.json',dict(completed=False,closed=False,failure=failure))
        raise
    finally:
        cap.owned(out,identity)
        if 'observer' in state: grid.write(out/'native_gate_events.json',state['observer'].document())
        flags = {k:state.get(k,False) for k in ('task_verified','aliases_restored','schedule_aliases_restored','observer_hooks_restored')}
        ok = all(flags.values()) and not state['cleanup_errors']
        grid.write(out/'release_transfer_scope_report.json',dict(completed=completed and ok,failure=failure,cleanup_errors=state['cleanup_errors'],**flags))
        if failure is None and not ok: raise RuntimeError('Release scope failed; outputs preserved')


def prepare():
    assert not any(n in sys.modules for n in ('numpy','torch','isaacgym'))
    paths = evidence(); cap.reject_existing(HERE/'cpu_inputs'); cap.reject_existing(HERE/'preparation_seal.json')
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    config = prefix.settings(); short = config['song']['short_learning']; zero = ZERO/'runs/precheck_zero'
    names = grid.read(zero/'trace_metadata.json')['joint_names']; ids = [names.index(n) for n in short['learned_action_names']]
    with np.load(zero/'trace_env0_episode0.npz') as saved: target = saved['target'][:,ids].copy()
    assert np.array_equal(target,np.broadcast_to(target[0],target.shape))
    reference = grid.read(prefix.base.INPUTS['index'][1]); positive = [reference['selected_targets_rad'][n] for n in short['learned_action_names']]
    short['release_transfer'] = dict(schema='diagnostic.index_prefix_release_transfer.v1',negative_selected_rad=target[0].tolist(),reference_selected_rad=positive,
        phase_boundaries_local_s=list(timing.boundaries(short['view'])),durations_s=[.10,.4417,.12],negative_source=str(zero/'trace_env0_episode0.npz'),
        source_evidence={str(p):grid.sha(p) for p in (zero/'settings.json',zero/'evaluation.json',zero/'trace_env0_episode0.npz',ZERO/'precheck_analysis/results_v1/review.json',PREFIX/'analysis/results_v1/review.json')},
        scope='A env0 distal-unloaded/candidate-negative from reset only; proximal load remains; not proven transfer release/B negative',
        requested_cartesian_speed_mm_s=66.84051870048756,original_requested_cartesian_speed_mm_s=44.6175844189442)
    short['prefix']['transition'] = 'A hold through release request; move AtoB during .4417s; B hold while reference closes; original endpoint clock semantics'
    short['result_scope'] = 'conditional noNN3note release-transfer hypothesis; original music gates; intermediate failure retained; no full-skin separation/pressure/freeguitar claim'
    inputs = HERE/'cpu_inputs'; inputs.mkdir()
    for name in ('index_settings.json','settings.json'): grid.write(inputs/name,config)
    for name in ('source_task.json','effort_declaration.json'): grid.write(inputs/name,grid.read(PREFIX/'cpu_inputs'/name))
    metadata,_ = fixture(4); metadata['action_contract'] = grid.read(prefix.base.FRESH/'runs/index/training_contract.json')['action']['target_contract']
    env = prefix.support().PrefixEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    grid.write(inputs/'expected_environment.json',env.contract)
    tests = module('release_transfer_cpu_checks',HERE/'cpu_checks.py'); checks = tests.check(sys.modules[__name__],config,metadata)
    grid.write(HERE/'cpu_verification.json',checks)
    grid.write(inputs/'commands.json',[dict(finger='index',control='reference',episodes=4,argv=[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute'])])
    paths.update(inputs.glob('*.json')); paths.update((Path(__file__).resolve(),HERE/'schedule.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'cpu_verification.json'))
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(config,inputs,paths),scope='CPU prepared only; root-only noNN4 release transfer'))
    result = subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True)
    grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout)); seal = grid.read(HERE/'preparation_seal.json')
    seal['input_pins'][str(HERE/'fresh_process_gate.json')] = grid.sha(HERE/'fresh_process_gate.json')
    (HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),native_trials=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); group = parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','execute','gate-check','dry-plan'): group.add_argument('--'+name,action='store_true')
    args = parser.parse_args(); sys.path.insert(0,str(grid.ROOT))
    if args.prepare: prepare()
    elif args.execute: launch()
    elif args.dry_plan: print(json.dumps([dict(finger='index',control='reference',episodes=4,selected_indices=[4,7,8],ticks=354,out=str(HERE/'runs/index'))]))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym')); seal,_ = gate(require_review=False)
        if seal['independent_review'] == 'pending':
            try: launch()
            except (FileNotFoundError,AssertionError): pass
            else: raise AssertionError('Unreviewed native admitted')
        else: gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym')) and not (HERE/'runs').exists()
        print(json.dumps(dict(stdlib_gate=True,Torch_imported=False,NumPy_imported=False,IsaacGym_imported=False)))
