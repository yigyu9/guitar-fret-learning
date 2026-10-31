"""실제 rl38 CPU 검사. native/NN/모델load 없이 현재 환경과 evaluator를 검사한다."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('current_ring_precheck', HERE/'experiment.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


def rejected(call, kind=Exception):
    try:
        call()
    except kind:
        return
    raise AssertionError('Invalid fixture accepted')


def environment(config):
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    metadata, snapshot = fixture(4)
    metadata['action_contract']['action_codec'] = dict(mode='incremental')
    env = ShortEnvironment(metadata, bundle=config['song_training']['bundle'],
        song=config['song'], skill=config['finger_skill'], device='cpu')
    obs = env.reset(range(4), snapshot)
    return env, snapshot, obs, metadata


def native_fixture(source, helpers):
    import numpy as np
    from guitar_learning.gpu.scene import left_hand_collision_properties
    private, document = helpers.private_contract(source)
    dtype = np.dtype([(key, np.bool_ if key == 'hasLimits' else np.int32 if key == 'driveMode' else np.float32)
        for key in source['initial']['native_PD_properties']])
    baseline = helpers.expected_properties(source, dtype)
    actual = baseline.copy(); actual['effort'][document['native_indices']] = e.CAP
    shapes, collision = left_hand_collision_properties(source['initial']['actual_shape_properties']['human'])
    names = list(shapes)
    flat = []; spans = []
    for name in names:
        records = shapes[name]; spans.append(SimpleNamespace(start=len(flat), count=len(records)))
        flat.extend(SimpleNamespace(filter=r['filter'], friction=r['friction'], contact_offset=r['contact_offset_m']) for r in records)
    gym = SimpleNamespace(get_actor_dof_properties=lambda env, actor: actual.copy(),
        get_actor_rigid_body_names=lambda env, actor: names,
        get_actor_rigid_body_shape_indices=lambda env, actor: spans,
        get_actor_rigid_shape_properties=lambda env, actor: copy.deepcopy(flat))
    scene = SimpleNamespace(pd_properties=actual.copy(), contract=private, physics_steps=0,
        hand_collision=collision, _hand_collision_readback_count=4, num_envs=4,
        envs=list(range(4)), actors=[(0,1,2)]*4, gym=gym)
    return scene, document, actual, flat


def evaluator_fixture(config, control, out):
    import torch
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.tool.experiments.short_finger_learning import runner
    env, snapshot, obs, metadata = environment(config)
    reference = snapshot['target'][0, [metadata['joint_names'].index(n) for n in ACTIVE_NAMES]]
    # native가 아닌 정지 CPU snapshot. 첫 환경의 실제 종료코드는 첫 tick에 실패시킨다.
    class Pool:
        def __init__(self):
            self.num_envs = 4; self.environment = env; self.observation = obs
            self.teacher_reference = reference
            self.incremental_mask = torch.zeros(39, dtype=torch.bool)
            self.incremental_mask[:33] = True
            props = metadata['action_contract']
            self.controller = SimpleNamespace(action_low=torch.tensor(props['action_lower_rad']),
                action_high=torch.tensor(props['action_upper_rad']), target=snapshot['target'].clone(),
                active=torch.tensor([metadata['joint_names'].index(n) for n in ACTIVE_NAMES]))
            self.scene = SimpleNamespace(q=snapshot['q'], target=snapshot['target'],
                body_state=snapshot['body_state'], metadata=metadata, names=metadata['joint_names'],
                snapshot=lambda: snapshot)
            self.steps = 0; self.resets = []; self.finished = []

        def step(self, action):
            self.steps += 1
            self.last_policy_action = action.clone(); self.last_executed_action = action.clone()
            self.last_wrist_feedback = {key: torch.zeros(4, size) for key, size in (
                ('pose_error_world',6),('requested_delta_rad',12),('requested_arm_rad',12),
                ('candidate_arm_rad',12),('position_goal_G_m',3),('quaternion_goal_G_xyzw',4))}
            self.last_wrist_feedback['active'] = torch.zeros(4, dtype=torch.bool)
            row = {k: v.clone() for k,v in snapshot.items()}
            row['body_state'][0, env.guitar_index, 0] += .1
            env.begin_control(action)
            for _ in range(4):
                env.substep(row)
            result = env.end_control()
            self.observation = result[0]; self.finished.extend(copy.deepcopy(result[-1]))
            return result

        def reset(self, ids):
            self.resets.append(ids.tolist())
            self.observation = env.reset(ids, snapshot)
            return self.observation, []
    pool = Pool()
    runner._evaluate(pool, e.Actions(control), config['song']['short_learning'],
        SimpleNamespace(control=control, reference=str(e.INPUTS/'reference.json'), episodes=4), out)
    value = e.read(out/'evaluation.json'); e.validate_evaluation(value, control)
    assert len(value['episodes']) == 4 and pool.resets[0] == [0]
    assert value['episodes'][0]['env_id'] == 0 and value['episodes'][0]['reason'] == 'terminal_failure'
    assert value['summary']['any_failure_fraction'] == .25
    assert sorted(r['env_id'] for r in value['episodes']) == [0,1,2,3]
    assert len(pool.finished) > 4  # 조기 실패 환경의 반복 결과를 분모에 더하지 않는다.
    for mutation in ('drop', 'duplicate', 'quota', 'summary'):
        bad = copy.deepcopy(value)
        if mutation == 'drop': bad['episodes'].pop()
        elif mutation == 'duplicate': bad['episodes'][-1]['env_id'] = 0
        elif mutation == 'quota': bad['assigned_quotas'] = [0,1,1,1]
        else: bad['summary']['episodes'] = 3
        rejected(lambda: e.validate_evaluation(bad, control), ValueError)
    return dict(control=control, first_attempts=4, failures_in_denominator=1,
                later_repeated_completions_excluded=len(pool.finished)-4, ticks=pool.steps)


def constructor_failure_fixture(config):
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    helpers=e.effort_helpers(); original=prepared_reset_v1.load_prepared_reset_contract
    errors=[]
    class Scene:
        def close(self):
            raise RuntimeError('secondary scene close error')
    def create(self, config, out):
        prepared_reset_v1.load_prepared_reset_contract()
        return Scene()
    def initialize(self, config, out):
        try:
            self._create_scene(config,out)
        except BaseException:
            self.close()
            raise
    cls=e.pool_class(helpers,errors)
    with patch.object(ShortPool,'__init__',initialize), patch.object(ShortPool,'_create_scene',create), \
            patch.object(ShortPool,'close',side_effect=RuntimeError('secondary pool close error')), \
            patch.object(e,'native_readback',side_effect=ValueError('primary readback error')):
        try:
            cls(config,Path('/unused_cpu_fixture'))
        except ValueError as error:
            assert str(error)=='primary readback error'
        else: raise AssertionError('Constructor primary exception lost')
    assert prepared_reset_v1.load_prepared_reset_contract is original
    assert [r['message'] for r in errors]==['secondary scene close error','secondary pool close error']


def primary_failure_fixture(config):
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.runtime import prepared_reset_v1
    original = prepared_reset_v1.load_prepared_reset_contract
    class Pool:
        def __init__(self, config, out):
            import torch
            import numpy as np
            self.observation = dict(state=torch.zeros(4,557))
            caps=torch.zeros(105)
            props=np.zeros(105,dtype=[('effort',np.float32)])
            self.scene=SimpleNamespace(effort_caps=caps,pd_properties=props)
            self.controller=SimpleNamespace(caps=caps)
            self.contract = dict(native_backend={}); self.effort_readback = dict(cap_Nm=.25)
            self.spec = config['song']['short_learning']; self.first_attempts = [dict(env_id=0)]
        def close(self):
            raise RuntimeError('secondary close error')
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder)
        source = HERE/'experiment.py'; pins = {str(source): e.sha(source)}
        real_read = e.read
        def local_read(path):
            if Path(path) == e.INPUTS/'settings.json': return config
            return real_read(path)
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), patch.object(e, 'settings', return_value=config), \
                patch.object(e, 'pool_class', return_value=Pool), patch.object(runner, '_pins', return_value=pins), \
                patch.object(e, 'read', side_effect=local_read), \
                patch.object(runner, '_evaluate', side_effect=ValueError('primary evaluation error')):
            try:
                e.execute('zero', out, dict(input_pins=pins))
            except ValueError as error:
                assert str(error) == 'primary evaluation error'
            else: raise AssertionError('Primary exception lost')
        report = real_read(out/'report.json')
        assert report['failure']['message'] == 'primary evaluation error'
        assert report['close_failure']['message'] == 'secondary close error' and not report['completed']
        assert real_read(out/'first_attempts.json')['episodes'] == [dict(env_id=0)]
        assert prepared_reset_v1.load_prepared_reset_contract is original


def run():
    assert sys.version_info[:2] == (3,8) and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert 'numpy' not in sys.modules and 'torch' not in sys.modules and 'isaacgym' not in sys.modules
    coverage = e.coverage_gate(); e.provenance_gate()
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runner, runtime
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_teacher
    torch.set_num_threads(1)
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    # 이 경로에서 NN 생성/CP읽기는 즉시 실패한다. 환경 tensor 측정은 허용한다.
    forbidden = AssertionError('NN construction/checkpoint load forbidden')
    with patch.object(torch.nn.Module, '__init__', side_effect=forbidden), patch.object(torch, 'load', side_effect=forbidden):
        config = e.settings(); env, snapshot, obs, metadata = environment(config)
        assert tuple(obs['state'].shape) == (4,557) and torch.isfinite(obs['state']).all()
        assert env.selected_index == 54 and env.focus_mask.sum(-1).tolist() == [1]*4
        assert env.contract['task']['finger_skill']['phase'] == 'J'
        assert config['song']['short_learning']['learned_action_indices'] == e.SELECTED
        assert [metadata['joint_names'].index(n) for n in config['song']['short_learning']['learned_action_names']] == [64,65,66,67]
        torch.testing.assert_close(env.onset[54]-env.score_offset, torch.full((4,),3.,dtype=torch.float64))
        env.clock[:] = torch.tensor([4,8,12,16]); env.wrist_elapsed[:] = .7; env.failure_paid[:] = True
        old = env.observation()['state'][1:].clone()
        env.reset([0], snapshot)
        assert env.clock.tolist() == [0,8,12,16] and env.failure_paid.tolist() == [False,True,True,True]
        torch.testing.assert_close(env.observation()['state'][1:], old)
        assert env.wrist_elapsed[0] == 0 and torch.all(env.wrist_elapsed[1:] == .7)
        state = obs['state']; global_before = torch.get_rng_state().clone()
        a=e.Actions('random'); b=e.Actions('random'); generator=torch.Generator().manual_seed(7)
        for _ in range(2):
            action=a.act(state, deterministic=False)['action']; expected=torch.zeros(4,39)
            expected[:,e.SELECTED]=(torch.randn((4,4),generator=generator)*e.STD).tanh()
            assert torch.equal(action,expected) and torch.equal(action,b.act(state)['action'])
            assert torch.count_nonzero(action[:,list(range(25))+list(range(29,39))]) == 0
        assert torch.equal(global_before,torch.get_rng_state())
        assert torch.count_nonzero(e.Actions('zero').act(state)['action']) == 0
        rejected(lambda: a.act(torch.zeros(4,561)), ValueError)
        original_teacher=e.read(e.INPUTS/'provenance.json')['original_teacher']['path']
        rejected(lambda: read_teacher(original_teacher), ValueError)
        helpers=e.effort_helpers(); original=prepared_reset_v1.load_prepared_reset_contract
        source=original(); saved=copy.deepcopy(source); calls=[]
        try:
            with helpers.effort_loader(calls):
                private=prepared_reset_v1.load_prepared_reset_contract()
                assert private['initial']['native_PD_properties']['effort'] != source['initial']['native_PD_properties']['effort']
                raise RuntimeError('constructor failure')
        except RuntimeError as error: assert str(error)=='constructor failure'
        assert original is prepared_reset_v1.load_prepared_reset_contract and len(calls)==1
        np.testing.assert_equal(source,saved); np.testing.assert_equal(original(),saved)
        scene,document,actual,flat=native_fixture(source,helpers)
        readback=e.native_readback(scene,source,document,helpers)
        assert len(readback['direct_readback_environments'])==4
        assert len(readback['actual_native_PD105'])==10 and document['unchanged_other_axes']==89
        for field in actual.dtype.names:
            bad=actual.copy();bad[field][0]=not bool(bad[field][0]) if field=='hasLimits' else bad[field][0]+1
            with patch.object(scene.gym,'get_actor_dof_properties',return_value=bad):
                rejected(lambda:e.native_readback(scene,source,document,helpers),ValueError)
        bad_shapes=copy.deepcopy(flat);bad_shapes[0].filter^=1
        with patch.object(scene.gym,'get_actor_rigid_shape_properties',return_value=bad_shapes):
            rejected(lambda:e.native_readback(scene,source,document,helpers),ValueError)
        rows=[]
        with tempfile.TemporaryDirectory() as folder:
            for control in e.CONTROLS:
                out=Path(folder)/control;out.mkdir();rows.append(evaluator_fixture(config,control,out))
            old_path=Path(folder)/'existing';old_path.mkdir();(old_path/'sentinel').write_text('same')
            rejected(lambda:e.launch('zero',old_path,Path(folder)/'missing'),FileExistsError)
            link=Path(folder)/'link';link.symlink_to(Path(folder)/'missing')
            rejected(lambda:e.reject_existing(link/'child'),ValueError)
            assert (old_path/'sentinel').read_text()=='same'
            pin=Path(folder)/'pin';pin.write_text('before'); pins={str(pin):e.sha(pin)};pin.write_text('after')
            rejected(lambda:e.verify_pins(pins),ValueError)
        constructor_failure_fixture(config)
        primary_failure_fixture(config)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(schema=e.SCHEMA,completed=True,python=sys.version,CUDA_VISIBLE_DEVICES='',
        GPU=0,native=0,NN_construction=0,NN_forward=0,checkpoint_load=0,PPO_updates=0,
        coverage_reviewed_inputs=103,current_observation=557,source_row=16,source_index=54,
        selected_action_indices=e.SELECTED,selected_native_indices=[64,65,66,67],
        original_content_except_explicit_paths_deep_equal=True,current_strict_readers=True,
        original_stale_evidence_rejected=True,private_effort16_only_other89_unchanged=True,
        constructor_loader_error_restored=True,constructor_primary_error_preserved=True,direct_native_readback_synthetic_all4_PD105_fields10=True,
        all10_PD_mutations_and_collision_filter_rejected=True,partial_reset_preserves_other_rows=True,
        noNN_random_sequence_exact_and_global_RNG_unchanged=True,evaluator_CPU_tensor_cases=rows,
        primary_error_preserved_despite_close_error=True,partial_first_attempts_preserved=True,
        existing_symlink_and_changed_input_rejected=True,
        source_sha256={str(HERE/n):e.sha(HERE/n) for n in ('experiment.py','cpu_check.py')},
        limitation='CPU synthetic stationary snapshots validate contracts/loop/denominator only; no native physics or success claim')


if __name__=='__main__':
    result=run();e.write(HERE/'cpu_verification.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
