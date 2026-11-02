"""B 초기 snapshot32환경을 자유 기타 GPU에서2초 유지하며 실제 검증값을 저장한다."""
import argparse
import copy
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).parent))
import initial_mix as mix


def run(candidate,out,device='cuda:0'):
    import torch
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.gpu.control import BatchedController,apply,conjugate
    from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
    from guitar_learning.gpu.environment import FAILURE_REASONS
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    r=mix.runtime();b=mix.verify_candidate(candidate);settings=r.build_settings(num_envs=32)
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True);started=time.monotonic()
    catalog=json.loads((mix.BASE/'geometry/initial_catalog.json').read_text())
    a=next(row for row in catalog['goals'] if row['song']==r.INITIAL_SONG)
    a.update(state=b['state'],q105=b['q105'],hold_target105=b['hold_target105'],native_verified=False)
    catalog_path=out/'B_reset_catalog.json';mix.write(catalog_path,catalog)
    config=copy.deepcopy(settings['natural_press']);config.update(geometry=str(catalog_path.resolve()),geometry_sha256=r.natural.digest(catalog_path))
    scene=None;failure=None;cleanup_error=None;readback=[];frames=[];finite=True
    physical=torch.zeros(32,dtype=torch.bool,device=device);wrist=physical.clone()
    initial_height=None;first_dof=None;observed_ticks=0
    pins={str(Path(candidate).resolve()):r.natural.digest(candidate),str(Path(__file__).resolve()):r.natural.digest(__file__),
        str(Path(mix.__file__).resolve()):r.natural.digest(mix.__file__),str(catalog_path.resolve()):r.natural.digest(catalog_path)}
    pins.update({str(mix.ROOT/name):value for name,value in b['active_physical_inputs'].items()})
    mix.write(out/'inputs_before.json',pins)
    try:
        scene=r.TransitionScene(32,'left',device=device,out=out,natural_press=config)
        controller=BatchedController(scene,finger_action_mode='position')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(controller.contract)
        metadata['reset_body_source'].update(verified=False,native_verified=False,scope='independent B reset preflight; CPU data is not native evidence')
        env=FingerSkillEnvironment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],hand='left',device=device)
        env.set_evaluation(True,full_song=True)
        ids=torch.arange(32,device=device);sample=scene.snapshot();controller.reset(ids,sample)
        controller.target[:]=scene.initial_hold;env.reset(ids,sample)
        action=r.natural.normalized_action(scene.initial_hold[:,controller.active],controller.reference[controller.active],controller.action_low,controller.action_high)
        fk=full_fk(SimpleNamespace(names=scene.names,human_bodies=scene.human_bodies,q_ref=np.asarray(b['q105'])),b['state'])
        expected_q=torch.tensor(b['q105'],device=device,dtype=scene.q.dtype)
        last_valid=scene.efforts.clone();reset_count=scene.reset_calls
        for tick in range(120):
            env.begin_control(action);target=controller.targets(action,sample)
            for sub in range(4):
                efforts=controller.efforts(sample);checks=controller.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):
                    finite=bool(checks['finite'].all());raise RuntimeError('native support finite/witness certificate failed')
                invalid=~checks['chest_normal_defined'];env.invalidate_control(invalid)
                efforts=torch.where(env.control_invalid[:,None],last_valid,efforts);last_valid.copy_(efforts)
                sample=scene.step(target,efforts);env.substep(sample)
                finite=finite and all(bool(torch.isfinite(sample[key]).all()) for key in ('q','qd','body_state','target'))
                physical|=env.tick_failure.any(-1);wrist|=env.wrist_failure|env.wrist_severe_failure
                if tick==0 and sub==0:
                    # 합성 reset_body_snapshot이 해제된 최초 native 물리 frame만 사용한다.
                    if bool(sample['reset_body_snapshot'].any()):raise RuntimeError('native readback 대신 CPU reset snapshot 감지')
                    first_dof=(sample['q']-expected_q).abs().amax(-1).cpu().tolist()
                    native_body=sample['body_state'].cpu().numpy();native_q=sample['q'].cpu().numpy()
                    for row in range(32):
                        predicted=fk(native_q[row])
                        for name in scene.human_bodies:
                            actual=native_body[row,scene.body_names.index('human/'+name)];position,rotation=predicted[name]
                            readback.append(dict(env_id=row,body=name,position_error_m=float(np.linalg.norm(position-actual[:3])),
                                rotation_error_rad=float((rotation.inv()*Rotation.from_quat(actual[3:7])).magnitude())))
                    bodies=env.body[:,env.pad_indices];world=bodies[:,:,None,:3]+apply(bodies[:,:,None,3:7],env.pad_local[None])
                    points=apply(conjugate(env.guitar_q[:,None,None]),world-env.guitar_body[:,None,None,:3])
                    height=(points[:,1]*env.press_plane[:3]).sum(-1)+env.press_plane[3]
                    initial_height=height[:,env.pad_valid[1]].amin(-1).cpu().tolist()
                    mix.write(out/'first_native_readback.json',dict(time_s=1/240.,dof_error_rad=first_dof,minimum_pad_height_m=initial_height,bodies=readback))
                if not finite:raise FloatingPointError('non-finite native state')
            env.end_control();observed_ticks=tick+1
            if tick%15==0:frames.append(dict(time_s=(tick+1)/60.,physical=physical.cpu().tolist(),wrist=wrist.cpu().tolist(),pad_height_m=env.surface_height[:,1].cpu().tolist()))
        if scene.reset_calls!=reset_count:raise RuntimeError('유지 도중 reset 감지')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error))
    finally:
        if scene is not None:
            try:scene.close()
            except BaseException as error:cleanup_error=str(error)
    unchanged=all(r.natural.digest(path)==value for path,value in pins.items())
    report=dict(schema='guitar_learning.transition_initial_mix_native.v1',candidate_sha256=r.natural.digest(candidate),
        initial_catalog_sha256=b['initial_catalog_sha256'],active_physical_inputs=b['active_physical_inputs'],
        completed=failure is None and cleanup_error is None and observed_ticks==120 and unchanged,
        finite=finite,episodes=32 if observed_ticks==120 else 0,hold_duration_s=observed_ticks/60.,
        physical_failures=int(physical.sum()),wrist_failures=int(wrist.sum()),
        max_readback_position_error_m=max((x['position_error_m'] for x in readback),default=None),
        max_readback_rotation_error_rad=max((x['rotation_error_rad'] for x in readback),default=None),
        max_readback_dof_error_rad=max(first_dof) if first_dof else None,
        minimum_initial_pad_height_m=min(initial_height) if initial_height else None,
        readback_scope='first real native frame after1/240s; body versus candidate-calibrated FK at actual q; DOF versus requested B reset q; dynamic drift included',
        duration_s=time.monotonic()-started,inputs_unchanged=unchanged,failure=failure,cleanup_error=cleanup_error)
    mix.write(out/'observed_trace.json',frames);mix.write(out/'report.json',report)
    try:mix.verify_native(candidate,out/'report.json');report['accepted']=True
    except (ValueError,TypeError) as error:report['accepted']=False;report['acceptance_error']=str(error)
    mix.write(out/'report.json',report)
    if not report['completed']:raise RuntimeError('B native preflight 미완료: '+str(failure))
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--device',default='cuda:0');args=parser.parse_args()
    sys.path.insert(0,str(mix.ROOT))
    import isaacgym
    run(args.candidate.resolve(),args.out.resolve(),args.device)

if __name__=='__main__':main()
