"""현행 약지 fresh PPO. 원 runner 루프와 엄격 load를 scoped binding으로 재사용한다."""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
PRE = DIAG/'02_contact_reward/current_ring_precheck_v1'
module = importlib.util.spec_from_file_location('reviewed_ring_precheck_helpers', PRE/'experiment.py')
pre = importlib.util.module_from_spec(module)
module.loader.exec_module(pre)  # stdlib뿐이며 과거 probe import 체인은 실행하지 않는다.
SCHEMA = 'diagnostic.current_ring_learning.v1'
UPDATES = (0,50,100,150,200,250,300)
COUNT = 128


def historical_paths(pins):
    # 진행문서 한 개만 동일SHA snapshot으로 재배치한다. 실행 소스·자료는 원경로 그대로 검증한다.
    original = str(ROOT/'docs/plans/guitar_learning_failure_diagnosis_20261027.md')
    snapshot = DIAG/'progress_review/document_snapshots/before_20261029_resume/guitar_learning_failure_diagnosis_20261027.md'
    mapped = dict(pins)
    if original in mapped:
        expected = mapped.pop(original)
        if expected != '705495b4a1a076bdb73881ea75d750d4a7a537d14c0c1d62531d8069a080d79f':
            raise ValueError('Historical document version differs')
        mapped[str(snapshot)] = expected
    pre.verify_pins(mapped)
    return {Path(p) for p in mapped}


def base_gate():
    review = pre.read(PRE/'actual_review.json')
    if review.get('verdict') != 'PASS' or review.get('findings') != []:
        raise ValueError('Current physical precheck independent PASS required')
    paths = historical_paths(review['reviewed_sha256'])
    seal=pre.read(PRE/'preparation_seal.json'); prepared_review=pre.read(PRE/'review.json')
    if seal['independent_review']!='passed_no_findings' or prepared_review['verdict']!='PASS' or prepared_review['findings'] or prepared_review['reviewed_sha256']!=seal['input_pins']:
        raise ValueError('Original precheck exact-map independent review required')
    paths.update(historical_paths(seal['input_pins']))
    coverage=pre.read(pre.COVERAGE/'review.json')
    if coverage['verdict']!='PASS' or coverage['findings']: raise ValueError('Coverage review required')
    paths.update(historical_paths(coverage['reviewed_sha256']))
    pre.verify_pins(seal['review_documents_sha256']); pre.provenance_gate()
    return paths | {PRE/'actual_review.json', PRE/'REVIEW_ACTUAL.md'}


def train_args(out):
    return argparse.Namespace(command='train',teacher=str(PRE/'inputs/teacher.json'),mode='incremental',
        initial_std=pre.STD,song='05_BN2-131-B_solo',size='large',seed=7,num_envs=COUNT,
        horizon=32,updates=300,save_every=50,out=str(out))


def configuration():
    from guitar_learning.tool.experiments.short_finger_learning import runner
    value = runner.make_settings(train_args(HERE/'runs/train'))
    if value['song']['short_learning'] != pre.settings()['song']['short_learning']:
        raise ValueError('Teacher/source/range/std contract differs from current precheck')
    return value


def verify128(scene, source, declaration):
    """4환경 검증기는 그대로 둔다. 모든128 actor를 직접 읽는 별도 검증이다."""
    import numpy as np
    from guitar_learning.gpu.scene import left_hand_collision_properties
    baseline = pre.expected_properties(source,scene.pd_properties.dtype)
    expected = baseline.copy(); expected['effort'][declaration['native_indices']] = .25
    if len(expected.dtype.names) != 10 or scene.names != source['initial']['joint_names']:
        raise ValueError('Native named105/all10 fields required')
    if not (scene.num_envs == len(scene.envs) == len(scene.actors) == scene._hand_collision_readback_count == COUNT and scene.physics_steps == 0):
        raise ValueError('Constructor-only128 environments required')
    reverted = copy.deepcopy(scene.contract)
    reverted['initial']['native_PD_properties']['effort'] = source['initial']['native_PD_properties']['effort']
    np.testing.assert_equal(reverted,source)
    changed = {k:np.flatnonzero(expected[k]!=baseline[k]).tolist() for k in expected.dtype.names}
    if changed['effort'] != declaration['native_indices'] or any(v for k,v in changed.items() if k!='effort'):
        raise ValueError('Only16 effort fields may change')
    shapes, collision = left_hand_collision_properties(source['initial']['actual_shape_properties']['human'])
    if scene.hand_collision != collision or collision['enabled_distinct_finger_pairs'] != 90 or not np.array_equal(scene.pd_properties,expected):
        raise ValueError('Original native PD/collision contract differs')
    rows = []
    for identity,(env,actors) in enumerate(zip(scene.envs,scene.actors)):
        human = actors[0]; actual = scene.gym.get_actor_dof_properties(env,human)
        if actual.dtype != expected.dtype or actual.shape != (105,) or not np.array_equal(actual,expected):
            raise ValueError('Native direct PD105 mismatch at env '+str(identity))
        names = scene.gym.get_actor_rigid_body_names(env,human)
        spans = scene.gym.get_actor_rigid_body_shape_indices(env,human)
        native = scene.gym.get_actor_rigid_shape_properties(env,human); filters = [None]*len(native)
        if len(names)!=len(spans) or set(names)!=set(shapes):
            raise ValueError('Native body/shape mapping differs')
        for name,span in zip(names,spans):
            if span.count != len(shapes[name]): raise ValueError('Native shape count differs')
            for offset,record in enumerate(shapes[name]):
                index = span.start+offset; prop = native[index]
                if (prop.filter != record['filter'] or not np.isclose(prop.friction,record['friction'],rtol=0,atol=1e-7) or
                        not np.isclose(prop.contact_offset,record['contact_offset_m'],rtol=0,atol=1e-9)):
                    raise ValueError('Native direct collision readback differs')
                filters[index] = int(prop.filter)
        if any(v is None for v in filters): raise ValueError('Native shape coverage incomplete')
        rows.append(dict(env_id=identity,native_PD105={k:actual[k].tolist() for k in actual.dtype.names},human_shape_filters=filters))
    return dict(**declaration,environment_count=COUNT,direct_readback_environments=rows,hand_collision=collision,
        actual_native_PD105={k:expected[k].tolist() for k in expected.dtype.names},
        original_profile_native_PD105={k:baseline[k].tolist() for k in baseline.dtype.names},
        changed_native_field_indices=changed,expected_readback_exact=True,
        property_scope='All128 native actors directly reread:105DOF/all10fields/human collision shapes; before physics step0')


def private_act(bound_act, device):
    """별도 seed7 정책 스트림. 원 bound act 전체 selected4 표본을 쓰며 global RNG를 복원한다."""
    import torch
    device = torch.device(device)
    generator = torch.Generator(device=device).manual_seed(7)
    state = generator.get_state()
    devices = [device.index if device.index is not None else torch.cuda.current_device()] if device.type=='cuda' else []
    def act(*args,**kwargs):
        nonlocal state
        with torch.random.fork_rng(devices=devices):
            if device.type=='cuda': torch.cuda.set_rng_state(state,device)
            else: torch.set_rng_state(state)
            try:
                kwargs['deterministic'] = False
                return bound_act(*args,**kwargs)
            finally:
                state = torch.cuda.get_rng_state(device) if device.type=='cuda' else torch.get_rng_state()
    return act


@contextmanager
def binding(paths,state,sampling='mean'):
    import numpy as np
    import torch
    from guitar_learning.runtime import prepared_reset_v1
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    old = (runner.ShortPool,runtime.ShortPool,runner._pins,runner.ShortPolicy,runner.SCHEMA)
    loader = prepared_reset_v1.load_prepared_reset_contract
    helpers = pre.effort_helpers()
    def pins(config,out,extra=()):
        return old[2](config,out,[*extra,*paths])
    class EffortPool(old[1]):
        def __init__(self,config,out):
            if config != pre.read(HERE/'inputs/settings.json'): raise ValueError('Own prepared settings required')
            state['pool'] = self
            super().__init__(config,out)
            if not np.array_equal(self.scene.effort_caps.cpu().numpy(),self.scene.pd_properties['effort']) or not torch.equal(self.controller.caps,self.scene.effort_caps):
                raise ValueError('Native/controller effort cap mismatch')
            self.contract['native_backend']['diagnostic_native_effort'] = copy.deepcopy(self.effort_readback)
            pre.write(Path(out)/'native_effort_readback.json',self.effort_readback)
        def _create_scene(self,config,out):
            calls = []; scene = None
            try:
                with helpers.effort_loader(calls): scene = super()._create_scene(config,out)
                state['scene'] = scene
                if prepared_reset_v1.load_prepared_reset_contract is not loader or len(calls)!=1:
                    raise RuntimeError('Constructor loader not restored')
                self.effort_readback = verify128(scene,*calls[0]); return scene
            except BaseException:
                if scene is not None:
                    try: scene.close()
                    except BaseException as error: state['cleanup_errors'].append(pre.error_info(error))
                raise
        def close(self):
            try: super().close()
            except BaseException as error: state['cleanup_errors'].append(pre.error_info(error))
    def policy(*args,**kwargs):
        value = old[3](*args,**kwargs)
        state['NN_constructions'] += 1
        if sampling=='stochastic': value.act = private_act(value.act,'cuda:0')
        return value
    runner.ShortPool = runtime.ShortPool = EffortPool
    runner._pins = pins; runner.ShortPolicy = policy; runner.SCHEMA = SCHEMA
    try: yield runner
    finally:
        runner.ShortPool,runtime.ShortPool,runner._pins,runner.ShortPolicy,runner.SCHEMA = old
        state['aliases_restored'] = (runner.ShortPool,runtime.ShortPool,runner._pins,runner.ShortPolicy,runner.SCHEMA)==old
        state['loader_restored'] = prepared_reset_v1.load_prepared_reset_contract is loader


class NoNN:
    def act(self,state,*unused,**kwargs):
        if tuple(state.shape)!=(COUNT,557): raise ValueError('Current128×557 required')
        return dict(action=state.new_zeros((COUNT,39)))


def complete_evaluation(value):
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    rows=value['episodes']
    if value['assigned_quotas']!=[1]*COUNT or len(rows)!=COUNT or sorted(r['env_id'] for r in rows)!=list(range(COUNT)) or value['summary']!=summary(rows):
        raise ValueError('All128 first attempts including failures required')
    if any(r['target_id']!='event-000053/string-3/note-54' or r['selected_target_count']!=1 for r in rows):
        raise ValueError('Own source54 ring target required')


def preflight(runner,control,out):
    import numpy as np
    import random
    import torch
    config = configuration(); out.mkdir(parents=True,exist_ok=False)
    pre.write(out/'settings.json',config); pre.write(out/'inputs_before.json',runner._pins(config,out))
    random.seed(7); np.random.seed(7); torch.manual_seed(7); torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool=runner.ShortPool(config,out); pre.write(out/'training_contract.json',pool.contract)
    runner._evaluate(pool,NoNN(),pool.spec,argparse.Namespace(control=control,reference=str(PRE/'inputs/reference.json'),episodes=COUNT),out)
    value=pre.read(out/'evaluation.json'); complete_evaluation(value)
    if value['condition']!=control or value['policy_performance'] is not False: raise ValueError('Scripted control required')


def preflight_gate():
    paths=set(); results={}
    for control in ('reference','zero'):
        out=HERE/'runs'/('preflight_'+control)
        report=pre.read(out/'diagnostic_report.json'); after=pre.read(out/'diagnostic_inputs_after.json')
        if not report['completed'] or not after['verified'] or report['NN_constructions']!=0 or report['phase']!='preflight':
            raise ValueError('Successful noNN128 preflight required')
        pre.verify_pins(after['input_pins']); pre.verify_pins(report['result_sha256'])
        value=pre.read(out/'evaluation.json')
        # stdlib gate: 여기서는 numeric 모듈을 import하지 않고 분모/수용값을 직접 계산한다.
        rows=value['episodes']
        if value['condition']!=control or value['policy_performance'] is not False or value['assigned_quotas']!=[1]*COUNT or len(rows)!=COUNT or sorted(r['env_id'] for r in rows)!=list(range(COUNT)):
            raise ValueError('Preflight denominator/control mismatch')
        results[control] = dict(achieved=sum(r['achieved'] for r in rows)/COUNT,clean=sum(r['clean_fraction'] for r in rows)/COUNT,
            wrong=sum(r['audible_wrong_fraction'] for r in rows)/COUNT,failure=sum(r['termination']['physical_failure'] or r['termination']['wrist_failure'] for r in rows)/COUNT)
        paths.update(p for p in out.iterdir() if p.is_file())
    r=results['reference']
    if not (r['achieved']>=.8 and r['clean']>=.7 and r['wrong']<=.1 and r['failure']<=.05 and results['zero']['achieved']<r['achieved']):
        raise ValueError('128 reference/zero acceptance gate failed')
    return paths


def gate(phase,require_review=True):
    paths=base_gate(); seal=pre.read(HERE/'preparation_seal.json')
    if seal.get('schema')!=SCHEMA: raise ValueError('Own preparation schema required')
    pre.verify_pins(seal['input_pins'])
    if require_review:
        review=pre.read(HERE/'review.json'); documents=seal.get('review_documents_sha256',{})
        if (seal.get('independent_review')!='passed_no_findings' or review.get('verdict')!='PASS' or review.get('findings')!=[] or
                review.get('reviewed_sha256')!=seal['input_pins'] or set(documents)!={str(HERE/'review.json'),str(HERE/'REVIEW.md')}):
            raise ValueError('Independent exact-map review and separate review-document pins required')
        pre.verify_pins(documents); paths.update(map(Path,documents))
    if phase!='preflight': paths.update(preflight_gate())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])}


def output(phase,control,update,sampling):
    name='preflight_'+control if phase=='preflight' else 'train' if phase=='train' else 'evaluation_%06d'%update+('_stochastic' if sampling=='stochastic' else '')
    return HERE/'runs'/name


def checkpoint(update):
    return HERE/'runs/train'/('initial.pt' if update==0 else 'final.pt' if update==300 else 'evaluation_%06d.pt'%update)


def launch(phase,control=None,update=0,sampling='mean'):
    if (phase not in ('preflight','train','evaluate') or update not in UPDATES or sampling not in ('mean','stochastic') or
            (phase=='preflight')!=(control in ('reference','zero')) or (phase!='preflight' and control is not None) or
            (phase!='evaluate' and (update!=0 or sampling!='mean')) or (sampling=='stochastic' and update!=300)):
        raise ValueError('Predeclared schedule only')
    out=output(phase,control,update,sampling); pre.reject_existing(out)
    seal,paths=gate(phase)
    if phase=='evaluate':
        train=pre.read(HERE/'runs/train/diagnostic_report.json')
        if not train['completed'] or train['phase']!='train': raise ValueError('Completed own training required')
        pre.verify_pins(train['result_sha256']); paths.add(checkpoint(update))
    state=dict(pool=None,scene=None,cleanup_errors=[],NN_constructions=0,aliases_restored=False,loader_restored=False)
    completed=False; failure=None; started=time.monotonic()
    try:
        import isaacgym  # gate는 NumPy/Torch보다 먼저 끝난다.
        with binding(paths,state,sampling) as runner:
            try:
                if phase=='preflight': preflight(runner,control,out)
                else:
                    args=train_args(out) if phase=='train' else argparse.Namespace(command='evaluate',checkpoint=str(checkpoint(update)),control='policy',reference=None,episodes=COUNT,out=str(out))
                    runner.run(args)
                    if phase=='evaluate': complete_evaluation(pre.read(out/'evaluation.json'))
                completed=True
            finally:
                if state['pool'] is not None: state['pool'].close()
    except BaseException as error:
        failure=pre.error_info(error); raise
    finally:
        try:
            from guitar_learning.training.training_log_io import project_source_paths
            out.mkdir(parents=True,exist_ok=True)
            pins=pre.read(out/'inputs_before.json') if (out/'inputs_before.json').is_file() else seal['input_pins']
            changed=[p for p,h in pins.items() if not Path(p).is_file() or pre.sha(p)!=h]
            missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins))
            audit=state['scene'].diagnostics if state['scene'] is not None else {}
            valid=(audit.get('closed') is True and audit.get('environment_count')==COUNT and audit.get('diagnostic_guitar_mode')=='fixed' and
                audit.get('physx_use_gpu') is True and audit.get('use_gpu_pipeline') is True and audit.get('hand_collision',{}).get('enabled_distinct_finger_pairs')==90 and audit.get('hand_collision_native_readback_environments')==COUNT)
            ok=completed and valid and state['aliases_restored'] and state['loader_restored'] and not changed and not missing and not state['cleanup_errors']
            result_pins={str(p):pre.sha(p) for p in out.iterdir() if p.is_file() and not p.name.startswith('diagnostic_')}
            pre.write(out/'diagnostic_inputs_after.json',dict(verified=not changed and not missing,input_pins=pins,changed_paths=changed,unpinned_project_sources=missing))
            pre.write(out/'diagnostic_report.json',dict(schema=SCHEMA,completed=ok,failure=failure,scene_valid=valid,closed=audit.get('closed') is True,
                cleanup_errors=state['cleanup_errors'],aliases_restored=state['aliases_restored'],loader_restored=state['loader_restored'],
                changed_inputs=changed,unpinned_project_sources=missing,phase=phase,control=control,update=update,sampling=sampling,
                policy_noise_seed=7 if sampling=='stochastic' else None,NN_constructions=state['NN_constructions'],fit_steps=0,critic_warmup_steps=0,
                result_sha256=result_pins,wall_s=time.monotonic()-started,
                authority='This diagnostic report is authoritative; cleanup failure rejects a parent report marked completed.'))
            if failure is None and not ok: raise RuntimeError('Diagnostic native/source/cleanup verification failed')
        except BaseException:
            if failure is None: raise


def prepare():
    paths=base_gate()
    config=configuration(); inputs=HERE/'inputs'; inputs.mkdir(exist_ok=True)
    pre.write(inputs/'settings.json',config)
    original=str(ROOT/'docs/plans/guitar_learning_failure_diagnosis_20261027.md')
    snapshot=DIAG/'progress_review/document_snapshots/before_20261029_resume/guitar_learning_failure_diagnosis_20261027.md'
    pre.write(inputs/'prior_review_scope.json',dict(original_document_path=original,
        original_review_sha256='705495b4a1a076bdb73881ea75d750d4a7a537d14c0c1d62531d8069a080d79f',
        snapshot_path=str(snapshot),snapshot_sha256=pre.sha(snapshot),
        scope='Only the mutable overall progress document is relocated to its SHA-identical historical snapshot. Current progress document is not an execution input. All original execution source/data pins remain strict. Original reviews/seals unchanged.'))
    from guitar_learning.tool.experiments.short_finger_learning import runner
    paths.update((Path(__file__),HERE/'cpu_check.py',HERE/'cpu_verification.json',HERE/'PLAN.md',HERE/'supervise.py',inputs/'settings.json',inputs/'prior_review_scope.json'))
    pins=runner._pins(config,inputs,paths)
    pre.write(HERE/'preparation_seal.json',dict(schema=SCHEMA,independent_review='pending',input_pins=pins,
        review_documents_sha256={},updates=list(UPDATES),last_stochastic_policy_noise_seed=7,GPU_executed=False))
    print('CPU prepared inputs:',len(pins))


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('command',choices=('prepare','gate','execute'))
    parser.add_argument('--phase',choices=('preflight','train','evaluate'),default='preflight')
    parser.add_argument('--control',choices=('reference','zero')); parser.add_argument('--update',type=int,choices=UPDATES,default=0)
    parser.add_argument('--sampling',choices=('mean','stochastic'),default='mean'); args=parser.parse_args()
    if args.command=='prepare': prepare()
    elif args.command=='gate': gate(args.phase); print('PASS')
    else: launch(args.phase,args.control,args.update,args.sampling)


if __name__=='__main__':
    sys.path.insert(0,str(ROOT)); main()
