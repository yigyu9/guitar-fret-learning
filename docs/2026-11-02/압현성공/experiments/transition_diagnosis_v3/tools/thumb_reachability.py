"""엄지 5축만으로 넥 뒤에 도달하는지 CPU 탐색하고 유한 PD 재생을 준비한다.

CPU 후보는 표면 기하일 뿐 native 접촉 성공이 아니다. native 명령은 최초
학습 초기화 이후 실제 상태를 쓰지 않고 동일 직접 위치 제어기만 통과한다.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

BASE = Path(__file__).resolve().parents[1]
ROOT = next(p for p in BASE.parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def inputs():
    import numpy as np
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.tool.validation.press_acquisition import action_bounds
    from guitar_learning.core.geometry import frame
    from guitar_learning.gpu.contact import load_thumb_support
    catalog_path = BASE/'geometry/initial_catalog.json'
    catalog = json.loads(catalog_path.read_text())
    row = next(r for r in catalog['goals'] if r['song']=='virtual_finger_v9_middle_s3_f6')
    contract = load_gpu_prepared_reset_contract('left')
    names = contract['initial']['joint_names']
    if names != catalog['joint_names']:
        raise ValueError('105 DOF name order mismatch')
    q = np.asarray(row['q105'], dtype=float)
    fk = full_fk(SimpleNamespace(names=names, human_bodies=contract['initial']['human_body_names'], q_ref=q), row['state'])
    indices, low, high = action_bounds(contract)
    gp, gr = frame(row['state']['guitar_body_states'][0])
    from guitar_learning.core.control import ACTIVE_NAMES
    channels = list(range(12, 17))
    if not all(ACTIVE_NAMES[c].startswith('LH:thumb') for c in channels):
        raise ValueError('Explicit thumb channels required')
    return row, q, fk, gp, gr, load_thumb_support(), indices, low, high


def search(output, starts=8):
    import numpy as np
    import torch
    from scipy.optimize import minimize
    from guitar_learning.gpu.contact import thumb_support_geometry
    torch.set_num_threads(1)
    row, q0, fk, gp, gr, patch, indices, lower, upper = inputs()
    native = indices[12:17]
    lo, hi = lower[12:17], upper[12:17]
    seed = q0[native].copy()
    # 작업 프렛 중심은 학습 A 셀의 정의를 그대로 사용한다.
    center = float(row['center_G_m'][1])
    def tensor(value):
        return torch.as_tensor(value, dtype=torch.float64)
    valid = torch.as_tensor(patch['valid'], dtype=torch.bool)
    rear, plane = tensor(patch['rear_vertices']), tensor(patch['plane'])
    def measure(x):
        q = q0.copy(); q[native] = x
        p, r = fk(q)['LH:thumb3']
        points = gr.inv().apply(p+r.apply(patch['points_local'])-gp)
        normals = gr.inv().apply(r.apply(patch['normals_local']))
        with torch.no_grad():
            v = thumb_support_geometry(tensor(points[None]), tensor(normals[None]), valid,
                tensor([center]), rear, plane)
        return {k: value[0].tolist() for k,value in v.items()}
    def objective(x):
        v = measure(x)
        # 동일 선택점의 간격·영역·방향을 평가한다. CPU에서는 접촉 하중을 주지 않는다.
        return -v['quality'] + .005*((v['signed_gap']-.0002)/.003)**2 + 1e-6*float(np.square(x-seed).sum())
    rng = np.random.RandomState(7)
    candidates = []
    for i in range(starts):
        start = np.clip(seed, lo+1e-7, hi-1e-7) if i==0 else rng.uniform(lo, hi)
        fit = minimize(objective, start, bounds=list(zip(lo, hi)), method='Powell',
                       options={'maxiter':100, 'maxfev':3500, 'xtol':1e-5, 'ftol':1e-8})
        value = measure(fit.x)
        print('thumb CPU', i, 'quality', value['quality'], 'gap', value['signed_gap'], flush=True)
        candidates.append(dict(x=fit.x.tolist(), measurement=value, objective=float(fit.fun),
                               optimizer_success=bool(fit.success), nfev=int(fit.nfev)))
    best = min(candidates, key=lambda v:v['objective'])
    q = q0.copy(); q[native] = best['x']
    v = best['measurement']
    feasible = bool(v['valid'] and -.001 <= v['signed_gap'] <= .003 and
                    v['region_excess'] <= .001 and v['normal_cos'] >= .1)
    result = dict(schema='guitar_learning.thumb_reachability.v1', policy_training=False,
        native_verified=False, cpu_candidate_valid=feasible,
        initial_catalog=str(BASE/'geometry/initial_catalog.json'),
        initial_catalog_sha256=sha(BASE/'geometry/initial_catalog.json'),
        scope='thumb5 only; all other q105 and guitar pose unchanged; unmodified action bounds',
        q105=q.tolist(), initial_q105=q0.tolist(), initial_hold_target105=row['hold_target105'],
        active_channels=list(range(12,17)), native_indices=native.tolist(),
        action_lower=lower.tolist(), action_upper=upper.tolist(),
        center_Gy_m=center, initial_measurement=measure(seed), best=best, starts=candidates,
        limitation='Source FK finite support patch geometry only; no force/contact pair/collision freedom certification',
        source_sha256={str(Path(__file__)):sha(__file__),str(BASE/'geometry/initial_catalog.json'):sha(BASE/'geometry/initial_catalog.json')})
    write(output, result)
    print('written', output, 'cpu_candidate_valid', feasible, flush=True)


def native(candidate, out, device):
    import copy
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.natural_press import NaturalScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
    from guitar_learning.gpu.environment import FAILURE_REASONS
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    data=json.loads(Path(candidate).read_text())
    if not data['cpu_candidate_valid']:
        raise ValueError('CPU geometry candidate did not pass; do not call it reachable')
    if any(sha(path)!=value for path,value in data['source_sha256'].items()):
        raise ValueError('Candidate source changed; regenerate CPU candidate')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    catalog=Path(data['initial_catalog']);row=json.loads(catalog.read_text())['goals'][0]
    config=dict(geometry=str(catalog),geometry_sha256=sha(catalog),song=row['song'],
        distribution='aligned',initial_distribution=dict(v9_fraction=0.))
    scene=None;rows=[];failure=None;report=None
    try:
        scene=NaturalScene(1,'left',device=device,out=out,natural_press=config)
        controller=BatchedController(scene,finger_action_mode='position')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(controller.contract)
        env=FingerSkillEnvironment(metadata,bundle=ROOT/'data/song_bundles/virtual_middle_s3_f6_f7_AB_v2',
            song=dict(pre_roll_s=3.,tail_s=.5,left_fraction=.4,window_s=.1),
            skill=dict(schema='guitar_learning.finger_skill.v3',phase='J',exploration='independent',
                hold_ticks=1,scope='scheduled',planned_transitions=4,full_song_after=1),hand='left',device=device)
        sample=scene.snapshot();ids=torch.arange(1,device=device)
        controller.reset(ids,sample);controller.target[:]=scene.initial_hold
        env.set_evaluation(True,full_song=True);env.reset(ids,sample)
        initial=scene.initial_hold[:,controller.active].clone()
        goal=torch.tensor(data['q105'],device=device,dtype=initial.dtype)[controller.active]
        channels=torch.tensor(data['active_channels'],device=device)
        rates=controller.rate[torch.tensor(data['native_indices'],device=device)]
        delta=(goal[channels]-initial[0,channels]).abs()
        ramp_s=max(2.,float((1.875*delta/rates.clamp_min(1e-9)).max())+.1)
        total_s=.5+ramp_s+2.;reset_count=scene.reset_calls
        last=scene.efforts.clone()
        for tick in range(round(total_s*60)):
            t=(tick+1)/60.;u=max(0.,min(1.,(t-.5)/ramp_s));blend=u*u*u*(10+u*(-15+6*u))
            desired=initial.clone();desired[:,channels]=initial[:,channels]+blend*(goal[channels]-initial[:,channels])
            action=trajectory_actions(desired,controller.reference[controller.active],controller.action_low,controller.action_high)
            target=controller.targets(action,sample)
            for sub in range(4):
                efforts=controller.efforts(sample);checks=controller.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):
                    raise RuntimeError('Native finite/support certificate failed')
                undefined=~checks['chest_normal_defined'];efforts=torch.where(undefined[:,None],last,efforts);last.copy_(efforts)
                sample=scene.step(target,efforts)
                env.clock[:]=tick*4+sub+1
                env.tick_failure=torch.zeros(1,len(FAILURE_REASONS),dtype=torch.bool,device=device)
                env.tick_cost=torch.zeros(1,device=device)
                env._snapshot(sample);env._safety()
                m=env.thumb_support
                rows.append(dict(time_s=(tick*4+sub+1)/240.,
                    **{k:v[0].cpu().tolist() for k,v in m.items()},
                    actual_thumb_rad=scene.q[0,torch.tensor(data['native_indices'],device=device)].cpu().tolist()))
                if bool(env.tick_failure.any()) or bool(undefined.any()):
                    failure=dict(time_s=rows[-1]['time_s'],reason='physical or undefined support');break
            if failure:break
        hold=[r for r in rows if r['time_s']>.5+ramp_s]
        report=dict(schema=data['schema'],cpu_candidate=str(candidate),native_verified=False,
            ramp_s=ramp_s,hold_observed_s=len(hold)/240.,failure=failure,
            no_intermediate_reset=scene.reset_calls==reset_count,
            contact_candidate_s=sum(bool(r['contact_candidate']) for r in hold)/240.,
            near_geometry_s=sum(bool(r['near_geometry']) for r in hold)/240.,
            max_normal_load_N=max((r['normal_load'] for r in rows),default=0.),
            minimum_signed_gap_m=min((r['signed_gap'] for r in rows),default=0.),
            limitation='Thumb3 source geometry and native resultant load proxy, not exact contact-pair/pressure certification')
        report['native_verified']=bool(not failure and report['contact_candidate_s']>=.1 and report['no_intermediate_reset'])
    finally:
        if scene is not None:scene.close()
        write(out/'trace240.json',rows)
        if report is not None:write(out/'report.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='mode',required=True)
    cpu=sub.add_parser('search');cpu.add_argument('--out',type=Path,default=BASE/'geometry/thumb_candidate.json');cpu.add_argument('--starts',type=int,default=8)
    gpu=sub.add_parser('native');gpu.add_argument('--candidate',type=Path,default=BASE/'geometry/thumb_candidate.json');gpu.add_argument('--out',type=Path,required=True);gpu.add_argument('--device',default='cuda:0')
    args=parser.parse_args()
    if args.mode=='native':
        import isaacgym  # 반드시 torch보다 먼저 초기화한다.
        native(args.candidate,args.out,args.device)
    else:search(args.out,args.starts)
