"""현재557 약지 scripted 첫시도12개. prepare/gate는 native를 import하지 않는다."""
import argparse
import ast
import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
COVERAGE = HERE.parent/'current_contract_coverage_v1'
EFFORT = DIAG/'05_verified_fixes/finger_effort_limit_v1/probe.py'
INPUTS = HERE/'inputs'
SCHEMA = 'diagnostic.current_ring_precheck.v1'
STD = .1711710544767014
SELECTED = [25, 26, 27, 28]
CONTROLS = ('reference', 'zero', 'random')
CAP = .25


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def verify_pins(pins):
    changed = [p for p, h in pins.items() if not Path(p).is_file() or sha(p) != h]
    if not pins or changed:
        raise ValueError('Input SHA mismatch: '+str(changed[:8]))


def coverage_gate():
    review = read(COVERAGE/'review.json')
    if review.get('verdict') != 'PASS' or review.get('findings') != []:
        raise ValueError('Coverage independent PASS required')
    pins = review['reviewed_sha256']
    if len(pins) != 103 or str(EFFORT) not in pins:
        raise ValueError('Coverage evidence map incomplete')
    verify_pins(pins)
    return {Path(p) for p in pins} | {COVERAGE/n for n in ('README.md', 'manifest.json', 'review.json', 'REVIEW.md')}


def provenance_gate():
    p = read(INPUTS/'provenance.json')
    for key in ('original_teacher', 'original_reference', 'derived_teacher', 'derived_reference'):
        verify_pins({p[key]['path']: p[key]['sha256']})
    old = read(p['original_teacher']['path']); expected = copy.deepcopy(old)
    if len(p['source_evidence_relocations']) != 3:
        raise ValueError('Exactly three provenance relocations required')
    for row in p['source_evidence_relocations']:
        old_sha = expected['source_evidence'].pop(row['original_path'])
        if old_sha != row['original_sha256'] or old_sha != row['cas_sha256']:
            raise ValueError('Historical evidence SHA changed')
        cas = ROOT/'guitar_learning/assets/historical_inputs/objects'/(old_sha+'.data')
        if str(cas) != row['cas_path']:
            raise ValueError('Only SHA addressed historical object allowed')
        verify_pins({str(cas): old_sha})
        expected['source_evidence'][str(cas)] = old_sha
    if expected != read(INPUTS/'teacher.json'):
        raise ValueError('Teacher content changed beyond three evidence paths')
    ref = read(p['original_reference']['path'])
    if ref['source_evidence'] != {p['original_teacher']['path']: p['original_teacher']['sha256']}:
        raise ValueError('Original reference evidence changed')
    ref['source_evidence'] = {str(INPUTS/'teacher.json'): sha(INPUTS/'teacher.json')}
    if ref != read(INPUTS/'reference.json'):
        raise ValueError('Reference content changed beyond teacher crossreference')
    verify_pins(p['current_execution_source_sha256'])
    return {Path(p[k]['path']) for k in ('original_teacher', 'original_reference')} | {
        Path(row['cas_path']) for row in p['source_evidence_relocations']}


def effort_helpers():
    # 필요한 세 함수만 재사용한다. 과거 probe의 최상위 import 체인은 실행하지 않는다.
    pins = read(COVERAGE/'review.json')['reviewed_sha256']
    verify_pins({str(EFFORT): pins[str(EFFORT)]})
    names = {'private_contract', 'effort_loader', 'verify_native'}
    tree = ast.parse(EFFORT.read_text(), filename=str(EFFORT))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in nodes} != names:
        raise ValueError('Effort helper functions missing')
    namespace = dict(copy=copy, contextmanager=contextmanager,
                     SCHEMA='diagnostic.finger16_native_effort_limit.v1', CAP=CAP, expected_properties=expected_properties)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(EFFORT), 'exec'), namespace)
    return SimpleNamespace(expected_properties=expected_properties, **{name: namespace[name] for name in names})


def expected_properties(source, dtype):
    # 현재 scene의 LH profile을 적용한다. 제거된 과거 core.finger_control은 import하지 않는다.
    import numpy as np
    from guitar_learning.core.control import default_profile
    native = source['initial']['native_PD_properties']
    if set(dtype.names) != set(native):
        raise ValueError('Native PD field set mismatch')
    result = np.empty(105, dtype=dtype)
    for field in dtype.names:
        result[field] = native[field]
    profile = default_profile()
    for i, name in enumerate(source['initial']['joint_names']):
        if name.startswith('LH:'):
            prefix = 'thumb' if name.startswith('LH:thumb') else 'finger'
            result['stiffness'][i] = profile[prefix+'_stiffness']
            result['damping'][i] = profile[prefix+'_damping']
    return result


def settings():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    args = SimpleNamespace(teacher=str(INPUTS/'teacher.json'), mode='incremental', initial_std=STD,
        song='05_BN2-131-B_solo', size='large', seed=7, num_envs=4, horizon=32, updates=1, save_every=50)
    value = runner.make_settings(args)
    spec = value['song']['short_learning']
    if (spec['finger'] != 3 or spec['teacher']['source_row'] != 16 or
            spec['teacher']['source_target_id'] != 'event-000053/string-3/note-54' or
            spec['view']['source_index'] != 54 or spec['learned_action_indices'] != SELECTED or
            spec['learned_action_names'] != ['LH:ring1_x', 'LH:ring1_z', 'LH:ring2', 'LH:ring3'] or
            value['finger_skill']['schema'] != 'guitar_learning.finger_skill.v3' or
            value['finger_skill']['phase'] != 'J' or spec['view']['local_onset_s'] != 3.):
        raise ValueError('Current Jv3 ring/source54 contract required')
    read_reference(INPUTS/'reference.json', spec)  # 원 strict evidence/target 검사를 그대로 쓴다.
    return value


class Actions:
    """NN 없는 선택4축 행동. random은 run별 별도 seed7 Normal 후 tanh다."""
    def __init__(self, control):
        if control not in CONTROLS:
            raise ValueError('Predeclared control required')
        self.control = control
        self.generator = None
        self.calls = 0

    def act(self, state, *unused, deterministic=True):
        import torch
        if tuple(state.shape) != (4, 557):
            raise ValueError('Current four-environment557 observation required')
        action = state.new_zeros((4, 39))
        if self.control == 'random':
            if self.generator is None:
                self.generator = torch.Generator(device=state.device).manual_seed(7)
            action[:, SELECTED] = (torch.randn((4, 4), device=state.device,
                dtype=state.dtype, generator=self.generator)*STD).tanh()
        self.calls += 1
        return dict(action=action)


def native_readback(scene, source, document, helpers):
    import numpy as np
    from guitar_learning.gpu.scene import left_hand_collision_properties
    result = helpers.verify_native(scene, source, document)
    if len(scene.pd_properties.dtype.names) != 10:
        raise ValueError('Full native PD ten fields required')
    expected = helpers.expected_properties(source, scene.pd_properties.dtype)
    expected['effort'][document['native_indices']] = CAP
    human_shapes, collision = left_hand_collision_properties(source['initial']['actual_shape_properties']['human'])
    if collision != scene.hand_collision:
        raise ValueError('Current collision contract mismatch')
    rows = []
    for env_id, (env, actors) in enumerate(zip(scene.envs, scene.actors)):
        human = actors[0]
        actual = scene.gym.get_actor_dof_properties(env, human)
        if actual.shape != (105,) or actual.dtype != expected.dtype or not np.array_equal(actual, expected):
            raise ValueError('Direct native PD105 readback mismatch')
        names = scene.gym.get_actor_rigid_body_names(env, human)
        spans = scene.gym.get_actor_rigid_body_shape_indices(env, human)
        shapes = scene.gym.get_actor_rigid_shape_properties(env, human)
        filters = [None]*len(shapes)
        if len(names) != len(spans) or set(names) != set(human_shapes):
            raise ValueError('Human body/shape mapping mismatch')
        for name, span in zip(names, spans):
            records = human_shapes[name]
            if span.count != len(records):
                raise ValueError('Native human shape count mismatch')
            for offset, record in enumerate(records):
                index = span.start+offset; prop = shapes[index]
                if (prop.filter != record['filter'] or
                        not np.isclose(prop.friction, record['friction'], rtol=0, atol=1e-7) or
                        not np.isclose(prop.contact_offset, record['contact_offset_m'], rtol=0, atol=1e-9)):
                    raise ValueError('Direct native collision readback mismatch')
                filters[index] = int(prop.filter)
        if any(v is None for v in filters):
            raise ValueError('Native shape coverage incomplete')
        rows.append(dict(env_id=env_id, native_PD105={key: actual[key].tolist() for key in actual.dtype.names},
                         human_shape_filters=filters))
    if len(rows) != 4 or scene.physics_steps != 0:
        raise ValueError('Four constructor-only direct readbacks required')
    result.update(direct_readback_environments=rows, hand_collision=collision,
                  property_scope='All105 × all10 fields directly reread from native actors in all4 environments before first step')
    return result


def pool_class(helpers, creation_close_errors):
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    from guitar_learning.tool.experiments.short_finger_learning.runner import compact_episode

    class EffortPool(ShortPool):
        def __init__(self, config, out):
            self.first_attempts = []
            self.first_ids = set()
            self.velocity_trace = []
            self.constructing = True
            try:
                super().__init__(config, out)
            finally:
                self.constructing = False

        def close(self):
            try:
                super().close()
            except BaseException as error:
                if not self.constructing:
                    raise
                creation_close_errors.append(error_info(error))

        def _create_scene(self, config, out):
            original = prepared_reset_v1.load_prepared_reset_contract
            calls = []; scene = None
            try:
                with helpers.effort_loader(calls):
                    scene = super()._create_scene(config, out)
                if prepared_reset_v1.load_prepared_reset_contract is not original or len(calls) != 1:
                    raise RuntimeError('Constructor loader scope violated')
                self.effort_readback = native_readback(scene, *calls[0], helpers)
                return scene
            except BaseException:
                if scene is not None:
                    try:
                        scene.close()
                    except BaseException as error:
                        creation_close_errors.append(error_info(error))
                raise

        def step(self, actions):
            result = super().step(actions)
            if 0 not in self.first_ids:
                self.velocity_trace.append(self.scene.qd[0, self.controller.active[SELECTED]].cpu().numpy().copy())
            for row in result[-1]:
                index = row['env_id']
                if index not in self.first_ids:
                    self.first_attempts.append(compact_episode(row, self.spec))
                    self.first_ids.add(index)
            return result
    return EffortPool


def validate_evaluation(value, control):
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    rows = value['episodes']
    if (value.get('assigned_quotas') != [1]*4 or len(rows) != 4 or
            sorted(r['env_id'] for r in rows) != list(range(4)) or
            value.get('condition') != control or value.get('policy_performance') is not False or
            any(r['target_id'] != 'event-000053/string-3/note-54' or r['selected_target_count'] != 1 for r in rows) or
            value['summary'] != summary(rows)):
        raise ValueError('Four first attempts, including all failures, required')


def error_info(error):
    return dict(type=type(error).__name__, message=str(error))


def reject_existing(path):
    path = Path(path).absolute()
    if path.exists() or path.is_symlink():
        raise FileExistsError(str(path))
    if any(p.is_symlink() for p in path.parents):
        raise ValueError('Symlink output parent refused')


def gate(seal_path, require_review=True):
    # GPU 실행에서는 이 함수가 NumPy/Torch/Isaac import보다 먼저 끝나야 한다.
    seal = read(seal_path)
    if seal.get('schema') != SCHEMA:
        raise ValueError('Own preparation schema required')
    verify_pins(seal['input_pins'])
    coverage_gate(); provenance_gate()
    if require_review:
        review_path = HERE/'review.json'; review = read(review_path)
        if (seal.get('independent_review') != 'passed_no_findings' or review.get('verdict') != 'PASS' or
                review.get('findings') != [] or review.get('reviewed_sha256') != seal['input_pins']):
            raise ValueError('Independent exact-map review required')
    return seal


def prepare():
    coverage = coverage_gate(); provenance = provenance_gate()
    config = settings()
    write(INPUTS/'settings.json', config)
    from guitar_learning.tool.experiments.short_finger_learning import runner
    paths = coverage | provenance | {HERE/'PLAN.md', Path(__file__), HERE/'cpu_check.py', HERE/'cpu_verification.json'}
    paths.update(INPUTS.glob('*.json'))
    teacher = config['song']['short_learning']['teacher']
    paths.update(map(Path, teacher['source_evidence']))
    pins = runner._pins(config, INPUTS, paths)
    write(HERE/'preparation_seal.json', dict(schema=SCHEMA, independent_review='pending', input_pins=pins,
        controls=list(CONTROLS), assigned_quotas=[1]*4, GPU_executed=False,
        scope='CPU preparation only; noNN scripted controls; prior561 success not inherited'))
    print(json.dumps(dict(pins=len(pins), independent_review='pending', GPU=0)))


def execute(control, out, seal):
    # Isaac은 Torch보다 먼저 import한다. stdlib gate는 launch에서 이미 완료했다.
    import isaacgym
    import numpy as np
    import random
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.training.training_log_io import project_source_paths
    from guitar_learning.tool.experiments.short_finger_learning import runner
    config = settings()
    if config != read(INPUTS/'settings.json'):
        raise ValueError('Prepared settings changed')
    write(out/'settings.json', config)
    pins = runner._pins(config, out, [HERE/'preparation_seal.json', HERE/'review.json', HERE/'REVIEW.md', *map(Path, seal['input_pins'])])
    write(out/'inputs_before.json', pins)
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    helpers = effort_helpers(); creation_errors = []
    original = prepared_reset_v1.load_prepared_reset_contract
    pool = None; completed = False; failure = None; close_error = None
    started = time.monotonic(); calls = 0; resources = {}
    try:
        pool = pool_class(helpers, creation_errors)(config, out)
        if tuple(pool.observation['state'].shape) != (4, 557):
            raise ValueError('Native observation must be557')
        if not np.array_equal(pool.scene.effort_caps.cpu().numpy(), pool.scene.pd_properties['effort']) or not torch.equal(pool.controller.caps, pool.scene.effort_caps):
            raise ValueError('Actual native/controller effort cap mismatch')
        pool.contract['native_backend']['diagnostic_native_effort'] = pool.effort_readback
        write(out/'native_effort_readback.json', pool.effort_readback)
        write(out/'training_contract.json', pool.contract)
        provider = Actions(control)
        write(out/'action_provider.json', dict(schema=SCHEMA, control=control, NN=False,
            selected=SELECTED, random_std=STD, generator_seed=7, random_shape=[4,4], checkpoint_loads=0))
        args = SimpleNamespace(control=control, reference=str(INPUTS/'reference.json'), episodes=4)
        runner._evaluate(pool, provider, pool.spec, args, out)
        value = read(out/'evaluation.json'); validate_evaluation(value, control)
        if value['episodes'] != pool.first_attempts:
            raise ValueError('Observer first-attempt ledger differs from original evaluator')
        np.savez_compressed(out/'selected_native_velocity_env0.npz', qd=np.asarray(pool.velocity_trace))
        calls = provider.calls
        resources = dict(control_ticks=calls, physics_steps=pool.scene.physics_steps)
        if pool.scene.physics_steps != calls*4 or calls > pool.spec['view']['duration_ticks'] or list(out.glob('*.pt')):
            raise ValueError('Single-tick noNN resource contract violated')
        completed = True
    except BaseException as error:
        failure = error_info(error)
        raise
    finally:
        # 정리 실패/보고 실패는 먼저 발생한 실행 예외를 가리지 않는다.
        if pool is not None:
            try:
                write(out/'first_attempts.json', dict(assigned_quotas=[1]*4, completed=completed, episodes=pool.first_attempts))
            except BaseException as error:
                close_error = error_info(error)
            try:
                pool.close()
            except BaseException as error:
                close_error = close_error or error_info(error)
        if creation_errors:
            close_error = close_error or creation_errors[0]
        try:
            changed = [p for p, h in pins.items() if not Path(p).is_file() or sha(p) != h]
            missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
            restored = prepared_reset_v1.load_prepared_reset_contract is original
            final = read(out/'gpu_scene_final.json') if (out/'gpu_scene_final.json').is_file() else {}
            scene_valid = (final.get('closed') is True and final.get('environment_count') == 4 and
                final.get('diagnostic_guitar_mode') == 'fixed' and final.get('hand_collision', {}).get('enabled_distinct_finger_pairs') == 90 and
                final.get('hand_collision_native_readback_environments') == 4 and final.get('physics_steps') == resources.get('physics_steps') and
                final.get('physx_use_gpu') is True and final.get('use_gpu_pipeline') is True)
            verified = not changed and not missing
            write(out/'inputs_after.json', dict(verified=verified, changed_paths=changed, unpinned_project_sources=missing, input_pins=pins))
            ok = completed and verified and restored and scene_valid and close_error is None
            write(out/'report.json', dict(schema=SCHEMA, completed=ok, closed=final.get('closed') is True,
                failure=failure, close_failure=close_error, loader_restored=restored, scene_valid=scene_valid,
                resources=resources, changed_inputs=changed, unpinned_project_sources=missing,
                actual_NN_constructions=0, NN_forward=0, checkpoint_loads=0, fit_steps=0, PPO_updates=0,
                assigned_quotas=[1]*4, control=control, wall_s=time.monotonic()-started))
            if failure is None and not ok:
                raise RuntimeError('Source/scene/cleanup verification failed; outputs preserved')
        except BaseException:
            if failure is None:
                raise


def launch(control, out, seal_path):
    reject_existing(out)
    seal = gate(seal_path)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'invocation.json', dict(argv=sys.argv, schema=SCHEMA, control=control))
    try:
        execute(control, out, seal)
    except BaseException as error:
        if not (out/'report.json').exists():
            try:
                write(out/'report.json', dict(schema=SCHEMA, completed=False, closed=False, failure=error_info(error)))
            except BaseException:
                pass  # 보고 실패도 원래 실행 예외를 대체하지 않는다.
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'gate', 'execute'))
    parser.add_argument('--control', choices=CONTROLS)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.command == 'gate':
        gate(HERE/'preparation_seal.json'); print('PASS')
    else:
        if args.control is None:
            raise ValueError('Predeclared control required')
        launch(args.control, HERE/'runs'/args.control, HERE/'preparation_seal.json')


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    main()
