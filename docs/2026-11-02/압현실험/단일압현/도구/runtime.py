"""18개 단일 압현의 독립 실행기: 현행 E4 물리·PPO와 엄격한 새 입력 계약.

학습은 목표 손가락4축만 허용한다. 팔은 각 목표의 유한 PD 정렬 지원이다.
기존 모델을 새 조합에 전용하지 않으며 원래 소스·catalog는 수정하지 않는다.
"""
if __name__ == '__main__':
    import isaacgym  # native 확장은 Torch보다 먼저 로드한다.

import argparse
import copy
import hashlib
import json
import math
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import torch
from guitar_learning.tool.experiments import natural_press as natural

SCHEMA = 'guitar_learning.single18.natural_press.v1'
POLICY_SCHEMA = 'guitar_learning.single18.policy.v1'
MAX_UPDATES = 100


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def row_identity(row):
    value = {k:v for k,v in row.items() if k not in ('native_verified', 'native_validation')}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()


def inputs(catalog_path, provenance_path, case, *, unverified=False):
    catalog_path, provenance_path = Path(catalog_path).resolve(), Path(provenance_path).resolve()
    for path in (catalog_path, provenance_path):
        path.relative_to(ROOT)
    catalog = json.loads(catalog_path.read_text())
    provenance = json.loads(provenance_path.read_text())
    if digest(catalog_path) != provenance['catalog_sha256']:
        raise ValueError('새 단일압현 catalog SHA 불일치')
    for name, expected in provenance['active_physical_inputs'].items():
        path = Path(name) if Path(name).is_absolute() else ROOT/name
        path.resolve().relative_to(ROOT)
        if digest(path) != expected:
            raise ValueError('단일압현 물리 입력 변경: '+name)
    rows = [r for r in catalog['goals'] if case in (r.get('case'),r.get('case_id'),r.get('song'))]
    if len(rows) != 1 or not rows[0]['candidate_valid']:
        raise ValueError('유효한 새 단일압현 조합 필요')
    row = rows[0]
    if not unverified:
        evidence = row.get('native_validation', {})
        path = Path(evidence.get('path',''))
        path.resolve().relative_to(ROOT)
        if not row.get('native_verified') or not path.is_file() or digest(path) != evidence.get('sha256'):
            raise ValueError('이 조합의 실제 native 검증 근거 필요')
        checked = json.loads(path.read_text())
        if (not checked.get('native_verified') or checked.get('candidate_sha256') != row_identity(row)
                or checked.get('runtime_sha256') != digest(__file__)):
            raise ValueError('native 검증과 현재 후보·실행기 불일치')
    bundle = Path(row['bundle']).resolve()
    bundle.relative_to(ROOT)
    return catalog, provenance, row


@contextmanager
def configuration_runtime(catalog_path, provenance_path, case, *, unverified=False):
    """한 프로세스 안에서만 factory를 교체하며 예외 때에도 모두 복원한다."""
    catalog_path, provenance_path = Path(catalog_path).resolve(), Path(provenance_path).resolve()
    catalog, provenance, row = inputs(catalog_path, provenance_path, case, unverified=unverified)
    original = natural.load_configuration, natural.verify_catalog, natural.SCHEMA, natural.NaturalPolicy.schema
    # 기존 검증 catalog의 성공·pin을 상속하지 않고 현행 E4 수치 계약만 구성한다.
    template = dict(schema=SCHEMA,condition='E4',distribution='aligned',axes='goal4',
        observation_extra_fields=natural.EXTRA_FIELDS, finger_initial_std=.15,finger_std_floor=.10,
        support_initial_std=math.exp(-3),phase_arm_support=False,
        inactive_execution='reset actual hold; v9 goal4 arm12 uses fixed aligned IK; no phase relatch',
        initial_distribution=dict(v9_fraction=0.,rng='torch CPU global RNG; official checkpoint restored; episode reset only'),
        readiness=dict(wrist_axis_excess_m=.010,wrist_continuous_s=.10,tangent_m=.010,
            height_m=[.002,.020],normal_cos=.1,aligned_continuous_s=.10),
        lr=dict(floor=7.5e-6,cap=3e-5,retry_factor=.5,stable_updates=10,stable_kl_below=.005,recovery_factor=1.25),
        likelihood='saved active axes Gaussian tanh latent; phase never blocks active actions')
    def load(song, condition='E4', distribution='aligned', axes='goal4'):
        if (song,condition,distribution,axes) != (row['song'],'E4','aligned','goal4'):
            raise ValueError('단일18은 동일 목표 E4/aligned/goal4만 허용')
        inputs(catalog_path, provenance_path, case, unverified=unverified)
        config = copy.deepcopy(template)
        finger = row['finger']
        if isinstance(finger,int):
            finger = natural.FINGERS[finger-1]
        config.update(schema=SCHEMA, song=song, finger=finger,
            geometry=str(catalog_path), geometry_sha256=digest(catalog_path),
            provenance_sha256=digest(provenance_path),
            active_axes=natural.active_axes('goal4',finger),
            single18=dict(case=case, runtime_sha256=digest(__file__),
                provenance=str(provenance_path), planned_updates=MAX_UPDATES,
                validation='probe_only' if unverified else 'native_verified'))
        return config
    natural.load_configuration, natural.verify_catalog = load, lambda: inputs(catalog_path,provenance_path,case,unverified=unverified)[1]
    natural.SCHEMA, natural.NaturalPolicy.schema = SCHEMA, POLICY_SCHEMA
    try:
        yield load(row['song']), row
    finally:
        natural.load_configuration, natural.verify_catalog, natural.SCHEMA, natural.NaturalPolicy.schema = original


def build_settings(config, row, *, num_envs=64, seed=7):
    from guitar_learning.training.launch import settings_document
    from guitar_learning.song.task import make_task
    settings = settings_document(song='virtual_finger_v9_middle_s3_f6', size='large', num_envs=num_envs,
        horizon=32, updates=MAX_UPDATES, seed=seed, checkpoint_every=10, device='cuda:0', physics='gpu')
    task = make_task(Path(row['bundle']), pre_roll_s=settings['song']['pre_roll_s'], tail_s=settings['song']['tail_s'])
    if (len(task.targets) != 1 or task.targets[0].fret != row['fret']
            or task.targets[0].string != row['string'] or task.targets[0].finger != row['finger_id']):
        raise ValueError('새 bundle 단일 목표와 catalog 불일치')
    settings['song_training'].update(song_id=row['song'], bundle=str(Path(row['bundle']).resolve()),
        target_count=1, control_ticks=task.provenance['song']['control_ticks'], episode_duration_s=task.duration_s)
    settings['phrase_events'] = task.provenance['song']['source_event_count']
    settings['natural_press'] = config
    settings['ppo']['retry_lr_factor'] = .5
    settings['simple_start']['initial_pose'] = SCHEMA+':aligned:goal4'
    return settings


@contextmanager
def experiment_runtime(config):
    from guitar_learning.training import finger_skill_runner as runner
    with natural.natural_runtime(config):
        old_pins = runner._pins
        def pins(settings, out, extra=()):
            record = settings['natural_press']['single18']
            paths = [Path(__file__).resolve(),Path(config['geometry']),Path(record['provenance'])]
            catalog = json.loads(Path(config['geometry']).read_text())
            row = next(r for r in catalog['goals'] if r['song']==config['song'])
            if row.get('native_validation'):
                paths.append(Path(row['native_validation']['path']))
            return old_pins(settings, out, list(extra)+paths)
        runner._pins = pins
        try:
            yield
        finally:
            runner._pins = old_pins


def probe_snapshot(pool, row, tick):
    """첫·마지막 native 끝점만 전체 관절·몸체·패드·오압현 출처를 저장한다."""
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.gpu.control import apply, conjugate
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    scene, env = pool.scene, pool.environment
    snapshot = scene.snapshot()
    q = snapshot['q'][0].detach().cpu().numpy()
    contract = load_gpu_prepared_reset_contract('left')
    q_ref = np.asarray([r['pos'] for r in contract['state']['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=scene.names,human_bodies=scene.human_bodies,q_ref=q_ref),contract['state'])
    predicted = fk(q)
    native = snapshot['body_state'][0].detach().cpu().numpy()
    pelvis_index = scene.human_bodies.index('Pelvis')
    native_pelvis = native[pelvis_index]
    cpu_pelvis_p, cpu_pelvis_r = predicted['Pelvis']
    alignment = Rotation.from_quat(native_pelvis[3:7])*cpu_pelvis_r.inv()
    body_comparison=[]
    for index,name in enumerate(scene.human_bodies):
        cpu_p,cpu_r=predicted[name]
        aligned_p=native_pelvis[:3]+alignment.apply(cpu_p-cpu_pelvis_p)
        aligned_r=alignment*cpu_r
        native_r=Rotation.from_quat(native[index,3:7])
        body_comparison.append(dict(name=name,cpu_actual_q_position_W_m=cpu_p.tolist(),
            cpu_actual_q_rotation_xyzw=cpu_r.as_quat().tolist(),
            world_position_error_m=float(np.linalg.norm(cpu_p-native[index,:3])),
            world_rotation_error_rad=float((cpu_r.inv()*native_r).magnitude()),
            pelvis_aligned_position_error_m=float(np.linalg.norm(aligned_p-native[index,:3])),
            pelvis_aligned_rotation_error_rad=float((aligned_r.inv()*native_r).magnitude())))
    bodies=env.body[:,env.pad_indices]
    world=bodies[:,:,None,:3]+apply(bodies[:,:,None,3:7],env.pad_local[None])
    points=apply(conjugate(env.guitar_q[:,None,None]),world-env.guitar_body[:,None,None,:3])
    normals=apply(conjugate(env.guitar_q[:,None,None]),apply(bodies[:,:,None,3:7],env.pad_normals[None]))
    goal_finger=int(env.finger[0])-1
    selected_global=int(env.surface_sample[0,0])
    selected_finger,selected=divmod(selected_global,points.shape[2])
    if selected_finger != goal_finger or not 0 <= selected_finger < points.shape[1]:
        raise ValueError('접근 표본 global index와 담당 손가락 불일치')
    initial_q=np.asarray(row['q105'])
    target=snapshot['target'][0].detach().cpu().numpy()
    return dict(control_tick=tick,physics_step=int(snapshot['physics_step'][0]),
        joint_names=scene.names,q105=q.tolist(),qd105=snapshot['qd'][0].cpu().tolist(),target105=target.tolist(),
        hold_target105=row['hold_target105'],initial_q105=row['q105'],
        q_minus_initial105=(q-initial_q).tolist(),target_minus_initial105=(target-initial_q).tolist(),
        logical_body_names=scene.body_names,logical_body_states13=native.tolist(),
        raw_native_body_states13=scene._bodies[0].detach().cpu().tolist(),
        contact_force=snapshot['contact_force'][0].detach().cpu().tolist(),
        cpu_vs_native_body=body_comparison,
        pad=dict(finger_order=list(natural.FINGERS),points_G_m=points[0].detach().cpu().tolist(),
            normals_G=normals[0].detach().cpu().tolist(),valid=env.pad_valid.cpu().tolist(),
            selected_finger_zero_based=goal_finger,selected_sample=selected,selected_global_sample=selected_global,
            selected_point_G_m=points[0,goal_finger,selected].detach().cpu().tolist(),
            selected_normal_G=normals[0,goal_finger,selected].detach().cpu().tolist(),
            surface_delta=env.surface_delta[0].detach().cpu().tolist(),
            surface_height=env.surface_height[0].detach().cpu().tolist(),
            surface_alignment=env.surface_alignment[0].detach().cpu().tolist(),
            press_plane_G=env.press_plane.cpu().tolist(),goals_G_m=env.goals[0].cpu().tolist()),
        wrong_source_body_names=[scene.body_names[int(i)] for i in env.finger_indices],
        wrong_source_flags=env.wrong_source_flags[0].cpu().tolist(),
        wrong_source_fret_min=env.wrong_source_fret_min[0].cpu().tolist(),
        wrong_source_fret_max=env.wrong_source_fret_max[0].cpu().tolist())


def probe(config, row, catalog_path, provenance_path, out):
    """후보당180 native 제어 tick: 3초 무압현·유지 안전·말미 패드 정렬을 검사한다."""
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.training.rollout import GpuPool
    out.mkdir(parents=True,exist_ok=False)
    settings = build_settings(config,row,num_envs=4)
    pool = None
    passed, failure = False, None
    samples=[]
    endpoint_diagnostics=[]
    pins={}
    try:
        with experiment_runtime(config):
            write(out/'settings.json',settings)
            pins=runner._pins(settings,out)
            write(out/'inputs_before.json',pins)
            pool=natural.NaturalPool(settings,out)
            for tick in range(180):
                result=pool.step(pool.execution_hold_action.clone())
                _,_,_,terminated,truncated,_=result
                samples.append(dict(tick=tick+1,candidate=pool.environment.candidate.cpu().tolist(),
                    wrong=pool.environment.wrong.cpu().tolist(),terminated=terminated.cpu().tolist(),
                    truncated=truncated.cpu().tolist(),finite=bool(torch.isfinite(pool.scene.snapshot()['q']).all()),
                    surface_delta=pool.environment.surface_delta[:,0].cpu().tolist(),
                    surface_height=pool.environment.surface_height[:,0].cpu().tolist(),
                    surface_alignment=pool.environment.surface_alignment[:,0].cpu().tolist()))
                if tick == 0 or tick == 179 or bool(terminated.any() or truncated.any()):
                    endpoint_diagnostics.append(probe_snapshot(pool,row,tick+1))
                if bool(terminated.any() or truncated.any()):
                    break
            passed=(len(samples)==180 and all(r['finite'] and not any(r['terminated']) and not any(r['truncated']) for r in samples)
                and not any(any(any(v) for v in r['candidate']) or any(any(v) for v in r['wrong']) for r in samples)
                and all(.005 <= h <= .015 for h in samples[-1]['surface_height'])
                and all((d[0]**2+d[1]**2)**.5 <= .005 for d in samples[-1]['surface_delta'])
                and all(f >= .1 for f in samples[-1]['surface_alignment']))
    except Exception as error:
        failure=dict(type=type(error).__name__,message=str(error))
    finally:
        if pool is not None:
            pool.close()
    write(out/'native_endpoint_diagnostics.json',dict(schema=SCHEMA+'.native_diagnostics',
        case=config['single18']['case'],scope='env0 native first/last endpoints, no state override',
        cpu_candidate_geometry=row.get('geometry'),cpu_candidate_pad_points_G_m=row.get('pad_points_G_m'),
        cpu_candidate_normal_cos=row.get('normal_cos'),endpoints=endpoint_diagnostics))
    changed=[str(path) for path,expected in pins.items() if not Path(path).is_file() or digest(path)!=expected]
    passed=passed and not changed and failure is None
    report=dict(schema=SCHEMA+'.probe',completed=failure is None,native_verified=passed,
        case=config['single18']['case'], candidate_sha256=row_identity(row),runtime_sha256=digest(__file__),
        physics_hz=240,control_hz=60,hold_ticks=180,initial_no_press_ticks=180,
        final_required=dict(height_m=[.005,.015],tangent_max_m=.005,facing_min=.1),
        scope='target-specific aligned finite PD hold; not learned pressing success',
        samples=samples,failure=failure,changed_inputs=changed)
    write(out/'report.json',report)
    if passed:
        destination=out/'verified';destination.mkdir()
        catalog=json.loads(Path(catalog_path).read_text())
        actual=next(r for r in catalog['goals'] if r['song']==row['song'])
        actual['native_verified']=True
        actual['native_validation']=dict(path=str((out/'report.json').resolve()),sha256=digest(out/'report.json'))
        write(destination/'catalog.json',catalog)
        provenance=json.loads(Path(provenance_path).read_text())
        provenance['catalog_sha256']=digest(destination/'catalog.json')
        provenance['native_validation']=actual['native_validation']
        write(destination/'provenance.json',provenance)
    return report


def summarize(out, duration, expected_count):
    """고정 메타데이터를 복원하고 실패도 포함한 최초 에피소드 분모를 검사한다."""
    from guitar_learning.training.training_log_io import _restore_episode
    report=json.loads((out/'report.json').read_text())
    required=('completed','lifecycle_verified','failed_episodes_in_denominator','first_episode_per_env_per_batch')
    if not all(report.get(key) is True for key in required) or report['episodes']!=expected_count:
        raise ValueError('평가 완결성·최초episode·고정분모 검사 실패')
    metadata=json.loads((out/'episode_metadata.json').read_text())
    records=[json.loads(line) for line in (out/'episodes.jsonl').read_text().splitlines()]
    rows=[_restore_episode(record['episode'],metadata) for record in records]
    if len(rows)!=expected_count or {row['env_id'] for row in rows}!=set(range(expected_count)):
        raise ValueError('평가 에피소드 수 또는 고유 환경 분모 불일치')
    def values(row):return row['left_note_ledger']['values']
    def eligible(row):return row['valid'] and not row['termination']['physical_failure'] and not row['termination']['wrist_failure']
    if any(len(values(row)['left'])!=1 for row in rows):
        raise ValueError('단일 목표 원장 필요')
    metrics=dict(episodes=len(rows),achievement=sum(bool(values(row)['left'][0]) and eligible(row) for row in rows),
        contact=sum(bool(values(row)['contact_done'][0]) for row in rows),
        clean_fraction=sum(values(row)['clean'][0]/duration for row in rows)/len(rows),
        entire_hold=sum(values(row)['clean'][0]>=duration-1e-8 and eligible(row) for row in rows),
        hold90=sum(values(row)['clean'][0]>=duration*.9-1e-8 and eligible(row) for row in rows),
        physical=sum(bool(row['termination']['physical_failure']) for row in rows),
        wrist=sum(bool(row['termination']['wrist_failure']) for row in rows),
        wrong_s=sum(values(row)['wrong'][0] for row in rows)/len(rows),
        first_episodes_only=True,scope='native geometric loaded-pad task achievement; not acoustic measurement')
    write(out/'metrics.json',metrics)
    return metrics


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('train','evaluate','render','probe'))
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--provenance',type=Path,required=True)
    parser.add_argument('--case',required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--resume',type=Path)
    parser.add_argument('--updates',type=int,default=25)
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--num-envs',type=int)
    parser.add_argument('--episodes',type=int,choices=(16,32),default=16)
    args=parser.parse_args(argv)
    if args.out.exists():raise FileExistsError(args.out)
    if not 1<=args.updates<=100:parser.error('updates는1..100 추가 블록 길이')
    if args.operation=='train' and args.checkpoint:parser.error('학습은 --resume만 허용')
    if args.operation!='train' and args.resume:parser.error('평가·영상은 --checkpoint만 허용')
    if args.operation in ('evaluate','render') and not args.checkpoint:parser.error('--checkpoint 필요')
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.portability import localize
    with configuration_runtime(args.catalog,args.provenance,args.case,unverified=args.operation=='probe') as (config,row):
        source=args.resume if args.operation=='train' else args.checkpoint
        source_sha=digest(source) if source else None
        if source:
            payload=torch.load(source,map_location='cpu',weights_only=False)
            runner._validate_pins(payload['metadata'])
            settings=localize(payload['metadata']['settings'])
            if settings.get('natural_press')!=config or payload['identity']['architecture']['schema']!=POLICY_SCHEMA:
                raise ValueError('동일 새18 목표·코드·입력·정책 계약만 재개/평가 가능')
            if args.operation=='train' and (settings['seed']!=args.seed or args.num_envs is not None and settings['num_envs']!=args.num_envs):
                raise ValueError('재개시 seed와 환경수 유지 필요')
            if args.operation=='train' and payload['updates']+args.updates>MAX_UPDATES:
                raise ValueError('최초100회 계획 초과 학습 금지')
        else:
            settings=build_settings(config,row,num_envs=args.num_envs or 64,seed=args.seed)
        if args.operation=='probe':
            report=probe(config,row,args.catalog,args.provenance,args.out.resolve())
        else:
            with experiment_runtime(config):
                if args.operation=='train':
                    settings['updates']=args.updates
                    runner.run(settings,SimpleNamespace(out=args.out.resolve(),resume=source))
                    report=json.loads((args.out/'report.json').read_text())
                elif args.operation=='evaluate':
                    report,_=runner.evaluate_checkpoint(source,args.out,num_envs=args.episodes,scope='full_song',max_episodes=args.episodes)
                    from guitar_learning.song.task import make_task
                    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
                    target=task.targets[0]
                    duration=target.end_s-target.onset_s
                    summarize(args.out,duration,args.episodes)
                else:
                    from guitar_learning.tool.demonstration.render_finger_skill import render
                    report=render(source,args.out,num_envs=args.num_envs or 4,scope='full_song')
        if source and digest(source)!=source_sha:raise ValueError('실행 중 원본 모델 변경')
        if not report.get('completed') or report.get('failure') or args.operation=='probe' and not report.get('native_verified'):
            raise RuntimeError('실행 미완료/초기 상태 미확보; report.json 확인')


if __name__=='__main__':main()
