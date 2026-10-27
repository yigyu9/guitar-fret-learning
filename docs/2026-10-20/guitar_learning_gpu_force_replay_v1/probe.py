"""Separate GPU physics response from fresh feedback by replaying identical forces."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--envs',type=int,default=1)
    p.add_argument('--tape',type=Path)
    p.add_argument('--steps',type=int,default=128)
    args=p.parse_args()
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.geometry import conjugate,multiply,rotvec
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths
    args.out.mkdir(parents=True,exist_ok=False)
    paths=set(p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts)
    paths.update(prepared_input_paths());paths.add(Path(__file__).resolve())
    if args.tape:paths.add(args.tape.resolve())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    pins={str(p):sha(p) for p in paths};write(args.out/'inputs_before.json',pins)
    torch.set_num_threads(1)
    tape=np.load(str(args.tape)) if args.tape else None
    scene=GpuScene(args.envs,'left',out=args.out/'scene')
    controller=None if tape is not None else BatchedController(scene)
    count=args.steps if tape is None else len(tape['efforts'])
    ids=[0] if args.envs==1 else [0,1,33,64,512,1023]
    selected=torch.tensor(ids,device=scene.device)
    snapshot=scene.snapshot();initial=snapshot['body_state'].clone();g=len(scene.human_bodies)
    feet=torch.tensor([scene.human_bodies.index(s+'_Ankle') for s in ('L','R')],device=scene.device)
    body=[initial[selected].cpu().numpy()];q=[snapshot['q'][selected].cpu().numpy()];qd=[snapshot['qd'][selected].cpu().numpy()]
    targets=[];efforts=[];rows=[];first_failure=torch.full((args.envs,),-1,device=scene.device,dtype=torch.long)
    started=time.monotonic();failure=None
    try:
        with torch.no_grad():
            for step in range(count):
                if tape is None:
                    if step%4==0:target=controller.targets(torch.zeros(1,39,device=scene.device),snapshot)
                    effort=controller.efforts(snapshot)
                    if not bool(controller.diagnostics['valid'].all()):raise RuntimeError('Uncertified reference control')
                else:
                    target=torch.as_tensor(tape['targets'][step],device=scene.device).expand(args.envs,-1)
                    effort=torch.as_tensor(tape['efforts'][step],device=scene.device).expand(args.envs,-1)
                targets.append(target[0].cpu().numpy().copy());efforts.append(effort[0].cpu().numpy().copy())
                snapshot=scene.step(target,effort)
                b=snapshot['body_state'];finite=torch.isfinite(b).flatten(1).all(-1)&torch.isfinite(snapshot['qd']).all(-1)
                if not bool(finite.all()):raise FloatingPointError('Nonfinite native physics response')
                delta=torch.linalg.vector_norm(b[:,g,:3]-initial[:,g,:3],dim=-1)
                angle=torch.linalg.vector_norm(rotvec(multiply(conjugate(initial[:,g,3:7]),b[:,g,3:7])),dim=-1)
                foot=torch.linalg.vector_norm(b[:,feet,:3]-initial[:,feet,:3],dim=-1).amax(-1)
                speed=snapshot['qd'].abs().amax(-1)
                bad=(delta>.08)|(angle>.35)|(foot>.04)|(speed>50)
                first_failure=torch.where((first_failure<0)&bad,step+1,first_failure)
                body.append(b[selected].cpu().numpy());q.append(snapshot['q'][selected].cpu().numpy());qd.append(snapshot['qd'][selected].cpu().numpy())
                rows.append(dict(step=step+1,ever_failed=int((first_failure>=0).sum()),current_failed=int(bad.sum()),
                    max_displacement_m=float(delta.max()),max_rotation_rad=float(angle.max()),max_speed_rad_s=float(speed.max()),
                    envs=ids,displacement_m=delta[selected].tolist(),rotation_rad=angle[selected].tolist(),foot_delta_m=foot[selected].tolist(),speed_rad_s=speed[selected].tolist()))
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        scene.close()
        np.savez_compressed(args.out/'tape.npz',targets=np.stack(targets),efforts=np.stack(efforts),body=np.stack(body),q=np.stack(q),qd=np.stack(qd))
        changed=[p for p,h in pins.items() if sha(p)!=h]
        write(args.out/'report.json',dict(completed=failure is None,failure=failure,num_envs=args.envs,env_ids=ids,steps=len(rows),
            feedback=controller is not None,replay=str(args.tape) if args.tape else None,scope='Identical-force open-loop diagnostic; pose/speed safety only, no support contact certification',
            first_failure_physics_steps=first_failure.cpu().tolist(),rows=rows,changed_inputs=changed,elapsed_s=time.monotonic()-started,scene=scene.diagnostics))
        print('completed',args.out,'steps',len(rows),'failed',int((first_failure>=0).sum()),flush=True)

if __name__=='__main__':main()
