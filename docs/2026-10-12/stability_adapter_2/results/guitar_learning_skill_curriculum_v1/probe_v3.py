"""Bounded real-physics candidates; proxy IK never substitutes for native success."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[name]='1'
import isaacgym
import argparse, gzip, json, sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scipy.optimize import least_squares
from guitar_learning.skill_environment import build_skill_environment, skill_pick_guide
from guitar_learning.control import ACTIVE_NAMES
from guitar_learning.geometry_v1 import frame, fret_target
from guitar_learning.recording import write,digest,project_source_paths
from stability_adapter_2.lower_body_release_v1.controller_horizontal_v4 import full_fk

ROOT=Path('/home/ajou/yigyu/3')
BASE=ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1'
CONFIG=BASE/'inputs_spine_margin035_v1/baseline_v1.json'
BUNDLE=ROOT/'data/song_bundles/05_BN2-131-B_solo'


def inverse(control, desired):
    c=control.contract; ref=c.q_ref[c.active_indices]
    delta=desired-ref
    scale=np.where(delta>=0,c.action_upper-ref,ref-c.action_lower)
    return np.clip(np.divide(delta,scale,out=np.zeros(39),where=scale>0),-1,1)


def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=('right_replay','right_servo','left_servo'),required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    role=a.case.split('_')[0]
    env=build_skill_environment(CONFIG,a.out/'environment',role=role,skill='cross' if role=='right' else 'hold',bundle=BUNDLE)
    paths={str(Path(__file__).resolve()),str(CONFIG)}|project_source_paths(list(sys.modules.items()))
    source=BASE/'native_free_strike_v14/targets60.json'
    oldref=ROOT/'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/prepared.json'
    if a.case=='right_replay':paths|={str(source),str(oldref)}
    anchor_source=a.out.parent/'left_servo_v1/trace.json.gz'
    if role=='left':paths.add(str(anchor_source))
    before={x:digest(x) for x in sorted(paths)};write(a.out/'inputs.json',before)
    rows=[]
    try:
        obs,reset=env.reset();write(a.out/'reset.json',reset)
        c=env.control;scene=c.session.scene
        ai=np.array([scene.names.index(n) for n in ACTIVE_NAMES]); selection=np.arange(33,39) if role=='right' else np.r_[np.arange(12),np.arange(25,29)]
        idx=ai[selection]
        if a.case=='right_replay':
            old=json.loads(gzip.decompress(source.read_bytes()))['rows'];old=[r for r in old if 27<=r['physics_step_before']/240<31]
            oldidx=[old[0]['joint_names'].index(n) for n in ACTIVE_NAMES]
            oldreference=np.array(json.loads(oldref.read_text())['metadata']['prepared_target105_rad'])[oldidx]
        local=np.zeros(3)
        if role=='left':
            old_sample=json.loads(gzip.decompress(anchor_source.read_bytes()))[-1]['samples240'][-1]
            anchors=[]
            for r in old_sample['native_contacts']['contacts']:
                names=[r['body0_name'],r['body1_name']]
                if 'human/LH:ring3' in names and 'guitar/G:fret7' in names and r['lambda']>0:
                    v=r['localPos'+str(names.index('human/LH:ring3'))];anchors.append([v[k] for k in 'xyz'])
            local=np.mean(anchors,axis=0)
            write(a.out/'pad_anchor.json',dict(body='LH:ring3',local_m=local,source=str(anchor_source),scope='past raw native feature average used only as candidate IK marker; fresh native success required'))
        initial=env.last_sample
        gp,gr=frame(initial['native']['guitar_body_states'][0]);initial_pick=np.array(initial['geometry']['pick_G_m'])
        guide=skill_pick_guide(env.task,initial,0.,'cross'); goal_end=np.array(guide['goal_G_m']);front=skill_pick_guide(env.task,initial,0.,'ready')['goal_G_m']
        for tick in range(240):
            now=tick/60.;desired=c.reference105[ai].copy();diagnostic={}
            if a.case=='right_replay':
                r=old[min(tick,len(old)-1)];delta=np.array(r['final105_rad'])[oldidx]-oldreference
                desired[33:]=c.reference105[ai][33:]+delta[33:]
                diagnostic={'old_time_s':r['physics_step_before']/240,'unclipped_delta6':delta[33:].tolist(),'outside_box_axes':int(np.count_nonzero(abs(delta[33:])>.25))}
            else:
                native=env.last_sample['native'];q=np.array([r['pos'] for r in native['human_dof_states']]);gp,gr=frame(native['guitar_body_states'][0])
                # Live FK anchored at measured q: exact at expansion point, no state writes.
                fk=full_fk(SimpleNamespace(names=scene.names,human_bodies=scene.human_bodies,q_ref=q),native)
                if role=='right':
                    live_front=np.array(skill_pick_guide(env.task,env.last_sample,now,'ready')['goal_G_m']);live_end=np.array(skill_pick_guide(env.task,env.last_sample,now,'cross')['goal_G_m'])
                    if now<1.5:goal_G=initial_pick+(live_front-initial_pick)*min(1.,now/1.)
                    elif now<2.5:goal_G=live_front+(live_end-live_front)*min(1.,(now-1.5)/.6)
                    else:goal_G=live_end
                    body='RH:pick'
                else:
                    goal_G=fret_target(env.last_sample['geometry'],2,7)+np.array([0.,0.,-.004])
                    goal_G[1]=env.last_sample['geometry']['fret_markers_G_m'][7,1]+.001
                    body='LH:ring3'
                goal=gp+gr.apply(goal_G)
                # Incremental command-space feedback; finite, clipped authority. It is only a candidate generator.
                def residual(v):
                    trial=q.copy();trial[idx]+=v;position=fk(trial)[body][0]
                    position=position+fk(trial)[body][1].apply(local)
                    return np.r_[1000*(position-goal),2*v]
                current=scene.target[ai].astype(float)
                lo=np.maximum(-.025,c.contract.action_lower[selection]-current[selection]);hi=np.minimum(.025,c.contract.action_upper[selection]-current[selection])
                lo=np.minimum(lo,-1e-10);hi=np.maximum(hi,1e-10)
                fit=least_squares(residual,np.zeros(len(idx)),bounds=(lo,hi),max_nfev=15)
                current=scene.target[ai].astype(float);desired[selection]=current[selection]+fit.x*.7
                diagnostic={'goal_G_m':goal_G.tolist(),'live_error_m':float(np.linalg.norm(fk(q)[body][0]+fk(q)[body][1].apply(local)-goal)),'increment_rad':fit.x.tolist(),'nfev':fit.nfev}
            action=inverse(c,desired);action[33:]=0 if role=='left' else action[33:]
            if role=='right':action[:33]=0
            obs,reward,done,truncated,info=env.step(action)
            rows.append(dict(tick=tick,action=action,reward=reward,cost=info['cost'],failure=info['failure_reasons'],specialist=info['specialist'],music=info['music'],diagnostic=diagnostic,
                requested_upper81=info['native_control']['requested_upper81_rad'],final_upper81=info['native_control']['codec_target_upper81_rad'],samples240=info['native_control']['physics_samples240'],measurements=info['physics_measurements']))
            if done or truncated:break
        write(a.out/'trace.json.gz',rows,compressed=True)
        write(a.out/'result.json',dict(case=a.case,ticks=len(rows),last=info['specialist'],episode=info.get('episode'),physical_failures=list({x for r in rows for x in r['failure']}),
            minimum_marker_m=min(np.linalg.norm(list(r['measurements'][-1]['music']['geometry'].values())[0]['delta']) for r in rows),source_unchanged=all(digest(x)==sha for x,sha in before.items()),scope='native bounded candidate; actual success only from original measured contact/cross and safe whole-horizon ledger'))
    finally:env.close()

if __name__=='__main__':main()
