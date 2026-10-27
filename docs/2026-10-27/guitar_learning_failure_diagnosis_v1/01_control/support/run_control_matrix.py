"""Native GPU named-joint target/response matrix; no training or state injection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path('/home/ajou/yigyu/3')
B = {'index':(25.,-14.,35.,12.), 'middle':(28.,-3.,38.,14.),
     'ring':(31.,3.,41.,16.), 'pinky':(34.,10.,44.,18.)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('incremental','position'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.geometry import conjugate,multiply,rotvec
    from guitar_learning.core.control import LEFT_HAND_NAMES,ACTIVE_NAMES
    paths=[]
    for folder,dirs,files in os.walk(ROOT/'guitar_learning'):
        dirs[:]=[d for d in dirs if d not in ('archive','__pycache__')]
        paths.extend(Path(folder)/name for name in files if name.endswith('.py'))
    paths.append(Path(__file__).resolve())
    pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (out/'inputs_before.json').write_text(json.dumps(pins,indent=2))
    cases=[dict(row=i,protocol=protocol,joint=name,sign=sign)
           for i,(protocol,name,sign) in enumerate((p,n,s) for p in ('target_path','output_bias') for n in LEFT_HAND_NAMES for s in (-1,1))]
    (out/'settings.json').write_text(json.dumps(dict(mode=args.mode,cases=cases,
        control_hz=60,physics_hz=240,duration_s=12.,
        target_path='0..1 hold reference;1..2 ramp +sign*.15rad;2..4 hold;4..5 ramp -sign*.15rad;5..6 hold;6..7 raw action0;7..10 ramp B;10..12 B hold',
        output_bias='0..1 zero;1..6 sign*.05;6..8 opposite*.05;8..9 zero;9..10 ramp B;10..12 B hold',
        guitar='production free guitar; no diagnostic asset override',
        force_scope='body net force magnitude; cannot identify contact partner or prove unloaded',
        effort_scope='submitted external effort command only; POSITION-driven LH21 command is zero by design, native drive torque/effort saturation not measured',
        body_capture_scope='trace60 body_state stores env0 only; joint/action and trace240 selected DOF/hand net force cover all84rows',
        after_failure='Data censored from first hard safety failure; remaining actions zero (incremental holds target; position returns reference); no state reset',
        state_writes='prepared initial reset only; all subsequent motion through existing action controller'),indent=2))
    scene=None;frames=[];fast=[];report=None;failure=None;start=time.monotonic()
    torch.set_num_threads(1);torch.manual_seed(7)
    try:
        scene=GpuScene(len(cases),'left',out=out/'scene')
        ctrl=BatchedController(scene,finger_action_mode=args.mode)
        sample=scene.snapshot();ctrl.reset(range(len(cases)),sample)
        joints=[scene.names.index(n) for n in LEFT_HAND_NAMES]
        actions=[ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES]
        n=len(cases);device=scene.device;rows=torch.arange(n,device=device)
        # Case order is protocol,joint,sign, so each pair targets the same named DOF.
        selected=torch.tensor([scene.names.index(c['joint']) for c in cases],device=device)
        channels=torch.tensor([ACTIVE_NAMES.index(c['joint']) for c in cases],device=device)
        signs=torch.tensor([c['sign'] for c in cases],device=device)
        path_mask=torch.tensor([c['protocol']=='target_path' for c in cases],device=device)
        reference=ctrl.reference[ctrl.active];initial=ctrl.target[:,ctrl.active].clone()
        bgoal=initial.clone()
        for finger,angles in B.items():
            for suffix,deg in zip(('1_x','1_z','2','3'),angles):
                bgoal[:,ACTIVE_NAMES.index('LH:'+finger+suffix)]=deg*np.pi/180
        assert bool(((bgoal>=ctrl.action_low-1e-6)&(bgoal<=ctrl.action_high+1e-6)).all())
        sign_delta=torch.zeros_like(initial);sign_delta[rows,channels]=signs*.15
        plus=torch.maximum(torch.minimum(initial+sign_delta,ctrl.action_high),ctrl.action_low)
        minus=torch.maximum(torch.minimum(initial-sign_delta,ctrl.action_high),ctrl.action_low)
        b_start=None;bias_start=None
        guitar_i=len(scene.human_bodies);initial_guitar=sample['body_state'][:,guitar_i,:7].clone()
        bodies=[i for i,name in enumerate(scene.body_names) if name.startswith('human/LH:')]
        alive=torch.ones(n,dtype=torch.bool,device=device);reasons=[None]*n
        codec_error=0.;target_speed=0.;last_target=ctrl.target.clone()
        def capture(tick,action,stage):
            t=tick/60
            bias_stage=('initial_hold' if t<=1 else 'bias_forward' if t<=6 else 'bias_reverse' if t<=8 else 'raw_zero' if t<=9 else 'B_ramp' if t<=10 else 'B_hold')
            labels=np.array([stage if c['protocol']=='target_path' else bias_stage for c in cases])
            frames.append(dict(tick=tick,stage=labels,q=sample['q'][:,joints].cpu().numpy().copy(),
                qd=sample['qd'][:,joints].cpu().numpy().copy(),target=ctrl.target[:,joints].cpu().numpy().copy(),
                action=action[:,actions].cpu().numpy().copy(),alive=alive.cpu().numpy().copy(),
                body_state=sample['body_state'][0].cpu().numpy().copy()))
        capture(0,torch.zeros(n,39,device=device),'initial')
        for tick in range(720):
            t=(tick+1)/60
            action=torch.zeros(n,39,device=device)
            desired=initial.clone()
            if t<=1:stage='initial_hold'
            elif t<=2:desired=initial+(plus-initial)*(t-1);stage='positive_ramp'
            elif t<=4:desired=plus;stage='positive_hold'
            elif t<=5:desired=plus+(minus-plus)*(t-4);stage='reverse_ramp'
            elif t<=6:desired=minus;stage='reverse_hold'
            elif t<=7:stage='raw_zero'
            elif t<=10:
                if b_start is None:b_start=ctrl.target[:,ctrl.active].clone()
                desired=b_start+(bgoal-b_start)*((t-7)/3);stage='B_ramp'
            else:desired=bgoal;stage='B_hold'
            if args.mode=='incremental':
                action[:,actions]=((desired-ctrl.target[:,ctrl.active])*(60/4))[:,actions].clamp(-1,1)
            else:
                delta=desired-reference;span=torch.where(delta>=0,ctrl.action_high-reference,reference-ctrl.action_low)
                action[:,actions]=(delta/span.clamp_min(1e-9))[:,actions].clamp(-1,1)
            if 6<t<=7:action[path_mask]=0
            if t<=9:
                action[~path_mask]=0
                if 1<t<=6:action[rows[~path_mask],channels[~path_mask]]=signs[~path_mask]*.05
                elif 6<t<=8:action[rows[~path_mask],channels[~path_mask]]=-signs[~path_mask]*.05
            else:
                if bias_start is None:bias_start=ctrl.target[:,ctrl.active].clone()
                desired_bias=bias_start+(bgoal-bias_start)*min(t-9,1.)
                if args.mode=='incremental':
                    values=((desired_bias-ctrl.target[:,ctrl.active])*15)[:,actions].clamp(-1,1)
                else:
                    delta=desired_bias-reference;span=torch.where(delta>=0,ctrl.action_high-reference,reference-ctrl.action_low)
                    values=(delta/span.clamp_min(1e-9))[:,actions].clamp(-1,1)
                for j,a in enumerate(actions):action[~path_mask,a]=values[~path_mask,j]
            action=torch.where(alive[:,None],action,torch.zeros_like(action))
            before=ctrl.target[:,joints].clone()
            target=ctrl.targets(action,sample)
            if args.mode=='incremental':
                expected=torch.maximum(torch.minimum(before+action[:,actions]*(4/60),scene.upper[joints]),scene.lower[joints])
                codec_error=max(codec_error,float((target[:,joints]-expected).abs().max()))
            target_speed=max(target_speed,float((target[:,joints]-last_target[:,joints]).abs().max())*60)
            last_target=target.clone()
            for sub in range(4):
                effort=ctrl.efforts(sample);checks=ctrl.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):raise RuntimeError('Invalid finite support control')
                sample=scene.step(target,effort)
                if not all(bool(torch.isfinite(sample[k]).all()) for k in ('q','qd','body_state','contact_force')):raise FloatingPointError('Nonfinite native response')
                guitar=sample['body_state'][:,guitar_i,:7]
                gd=torch.linalg.vector_norm(guitar[:,:3]-initial_guitar[:,:3],dim=-1)
                ga=torch.linalg.vector_norm(rotvec(multiply(conjugate(initial_guitar[:,3:]),guitar[:,3:])),dim=-1)
                flags=torch.stack((gd>.08,ga>.35,sample['qd'].abs().amax(-1)>50,~checks['chest_normal_defined']),-1)
                just=alive&flags.any(-1)
                for row in just.nonzero().flatten().cpu().tolist():reasons[row]=dict(time_s=(tick*4+sub+1)/240,flags=flags[row].cpu().tolist())
                alive&=~just
                fast.append(dict(time_s=(tick*4+sub+1)/240,actual_selected=sample['q'][rows,selected].cpu().numpy().copy(),
                    target_selected=target[rows,selected].cpu().numpy().copy(),
                    qd_selected=sample['qd'][rows,selected].cpu().numpy().copy(),
                    hand_net_force_max=torch.linalg.vector_norm(sample['contact_force'][:,bodies],dim=-1).amax(-1).cpu().numpy().copy(),
                    effort_selected=effort[rows,selected].cpu().numpy().copy(),
                    guitar_translation=gd.cpu().numpy().copy(),guitar_rotation=ga.cpu().numpy().copy(),alive=alive.cpu().numpy().copy()))
            capture(tick+1,action,stage)
            if (tick+1)%120==0:print('mode',args.mode,'tick',tick+1,'alive',int(alive.sum()),flush=True)
        report=dict(completed=True,mode=args.mode,controls=720,rows=n,failed=sum(x is not None for x in reasons),
            failure_reasons=reasons,max_incremental_codec_error_rad=codec_error if args.mode=='incremental' else None,
            maximum_target_speed_rad_s=target_speed,joint_names=list(LEFT_HAND_NAMES),native_lower=scene.lower[joints].cpu().tolist(),
            native_upper=scene.upper[joints].cpu().tolist(),B_target_rad=bgoal[0,actions].cpu().tolist(),
            native_effort_caps=ctrl.caps[joints].cpu().tolist(),native_stiffness=ctrl.kp[joints].cpu().tolist(),
            native_damping=ctrl.kd[joints].cpu().tolist(),position_driven=[scene.names.index(n) in scene.initial['position_indices'] if hasattr(scene,'initial') else scene.names.index(n) in scene.contract['initial']['position_indices'] for n in LEFT_HAND_NAMES],
            force_scope='body net force only; no partner-specific contact force or unloaded certification',
            effort_scope='submitted external effort command, not native motor torque; zero on native POSITION axes by design',
            body_capture_scope='row0 only; cannot infer other cases body poses or collision from this array',
            body_names=scene.body_names,wall_s=time.monotonic()-start)
        assert codec_error<2e-6 and target_speed<4.0001
    except BaseException as error:
        failure=repr(error);raise
    finally:
        if frames:np.savez_compressed(out/'trace60.npz',**{k:np.stack([r[k] for r in frames]) for k in frames[0]})
        if fast:np.savez_compressed(out/'trace240.npz',**{k:np.stack([r[k] for r in fast]) for k in fast[0]})
        if scene is not None:scene.close()
        changed=[p for p,v in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=v]
        if report is None:report=dict(completed=False,failure=failure)
        report.update(changed_inputs=changed,scene=scene.diagnostics if scene else None,failure=failure)
        report['completed']=bool(report['completed'] and failure is None and not changed and scene is not None and scene.closed)
        (out/'report.json').write_text(json.dumps(report,indent=2))
        if changed:raise RuntimeError('Source changed during diagnostic')
    print(json.dumps(dict(completed=report['completed'],failed=report['failed'],wall_s=report['wall_s'])),flush=True)
if __name__=='__main__':main()
