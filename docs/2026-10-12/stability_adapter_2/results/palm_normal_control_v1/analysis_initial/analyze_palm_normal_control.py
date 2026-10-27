"""Verify saved normal-control trials and report geometric/contact observations."""
import json
from pathlib import Path
from scipy.spatial.transform import Rotation
from .palm_side_feedback import PHASE as PREVIOUS,context,np
from .palm_normal_task import prepare,error_from_state
from .build_fixed_lower_asset import read,sha,pose
from .analyze_palm_side_feedback import finite

PHASE=PREVIOUS.parent/'palm_normal_control_v1'


def main():
    ctx=prepare(context());checks={};summaries=[];inputs=[Path(__file__).resolve()]
    folders={'full_0p15':PHASE/'short/full','normal_0p15':PHASE/'short/normal',
        'normal_0p3':PHASE/'cap_0p3/short','normal_0p5':PHASE/'cap_0p5/short'}
    counts={'native_initializations':0,'physics_steps':0};archive={}
    for p in PHASE.rglob('*.py'):archive.setdefault(sha(p),[]).append(str(p))
    resolution=[]
    def trial(folder):
        report=read(folder/'report.json');raw={n:read(folder/(n+'.json')) for n in ('states','trace','tasks','normal_tasks','controls','contacts')}
        steps=report['physics_steps'];inputs.extend(folder/(n+'.json') for n in ('report',*raw))
        if not all(report['checks'].values()) or report['failure'] is not None:raise AssertionError('trial contracts')
        if not (all(len(raw[n])==steps+1 for n in ('states','trace','tasks','normal_tasks')) and
            all(len(raw[n])==steps for n in ('controls','contacts')) and finite(raw) and
            all(r['physics_step']==i+1 for n in ('controls','contacts') for i,r in enumerate(raw[n])) and
            all(abs(r['time_s']-i/240)<1e-9 for i,r in enumerate(raw['trace'])) and
            all(r['updated_before_step']==(i%4==0) for i,r in enumerate(raw['controls'])) and
            all(np.asarray(raw[n]).shape==(steps+1,6) for n in ('tasks','normal_tasks')) and
            all(s['physics_step']==i and error_from_state(s,ctx).tolist()==raw['normal_tasks'][i] for i,s in enumerate(raw['states']))):raise AssertionError('raw coverage/finite')
        for path,h in report['source_sha256'].items():
            if sha(Path(path))!=h:
                if not archive.get(h):raise AssertionError('unresolved production source: '+path)
                resolution.append({'report':str(folder/'report.json'),'input':path,'sha256':h,'archived_paths':archive[h]})
        counts['native_initializations']+=report['native_initializations'];counts['physics_steps']+=steps
        return report,raw
    baseline=read(folders['full_0p15']/'states.json')
    for label,folder in folders.items():
        report,raw=trial(folder)
        if report['physics_steps']!=24:raise AssertionError('short comparison must cover24steps')
        normal=np.array(raw['normal_tasks']);metrics=[]
        for state in raw['states']:
            pp,pq=pose(state['human_body_states'][ctx['palm_index']]);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
            delta=pp+Rotation.from_quat(pq).apply(ctx['local_point'])-(gp+gr.apply(ctx['goal_point_G']-ctx['normal_G']*.00005))
            ng=gr.apply(ctx['normal_G']);gap=float(delta@ng)
            metrics.append({'signed_source_normal_gap_mm':gap*1000,'source_tangent_distance_to_center_mm':float(np.linalg.norm(delta-gap*ng)*1000)})
        pairs=[(r['physics_step'],v) for r in raw['contacts'] for v in r['contacts']]
        palms=[(step,v) for step,v in pairs if {v['body0_name'],v['body1_name']}=={'human/LH:palm','guitar/guitar'}]
        updates=[r for r in raw['controls'] if r['updated_before_step']]
        summaries.append({'label':label,'max_point_error_mm':float(np.linalg.norm(normal[:,:3],axis=1).max()*1000),
            'max_facing_normal_angle_deg':float(np.linalg.norm(normal[:,3:],axis=1).max()/.08*180/np.pi),
            'end_geometry':metrics[-1],'max_guitar_position_error_mm':report['max_position_error_m']*1000,
            'max_guitar_rotation_error_deg':report['max_rotation_error_deg'],
            'guitar_all_body_states_exact_to_full':len(raw['states'])==len(baseline) and all(s['guitar_body_states']==b['guitar_body_states'] for s,b in zip(raw['states'],baseline)),
            'palm_contact_steps':sorted({step for step,v in palms}),'palm_contact_rows':len(palms),
            'positive_raw_palm_lambda_rows':sum(v['lambda']>0 for step,v in palms),
            'positive_raw_human_self_lambda_rows':sum(v['lambda']>0 and v['body0_name'].startswith('human/') and v['body1_name'].startswith('human/') for step,v in pairs),
            'max_torso_actual_drift_deg':float(np.abs([r['torso_drift_deg'] for r in raw['trace']]).max()),
            'minimum_source_palm_up_proxy_z':report['minimum_source_palm_up_proxy_z'],
            'blocked_counts_at_updates':[sum(r['integral_blocked']) for r in updates]})
        checks[label+'_contracts_coverage_finite']=True
    first=[]
    for label,folder in [('0p15',PHASE/'first_step'),('0p3',PHASE/'cap_0p3/first_step'),('0p5',PHASE/'cap_0p5/first_step')]:
        report,raw=trial(folder);a=np.array(report['actual_normal_first_error_m_scaled_rad']);b=np.array(report['predicted_normal_first_error_m_scaled_rad'])
        first.append({'cap':label,'actual_point_mm':float(np.linalg.norm(a[:3])*1000),'predicted_point_mm':float(np.linalg.norm(b[:3])*1000),
            'actual_normal_angle_deg':float(np.linalg.norm(a[3:])/.08*180/np.pi),'predicted_normal_angle_deg':float(np.linalg.norm(b[3:])/.08*180/np.pi)})
    report,camera=trial(PHASE/'native_cap_0p3');checks['camera_saved_raw_exact']=all(camera[n]==read(PHASE/'cap_0p3/short'/(n+'.json')) for n in camera)
    checks['camera_images_sha']=all(sha(Path(p))==v['sha256'] for p,v in report['images'].items())
    checks['all_first_step_contracts_coverage_finite']=True
    for prior,count in [('palm_side_feedback_v1',135),('palm_plane_alignment_v1',22)]:
        path=PREVIOUS.parent/prior/'artifact_inventory.json';inventory=read(path);inputs.append(path)
        checks[prior+'_preserved']=len(inventory)==count and all(sha(Path(p))==v['sha256'] for p,v in inventory.items())
    checks['counts_8_init_123_steps']=counts=={'native_initializations':8,'physics_steps':123}
    output={'checks':checks,'summary':summaries,'first_step':first,'counts':counts,
        'archived_producer_resolution':resolution,'input_sha256':{str(p):sha(p) for p in inputs},
        'scope':'source geometry/contact observations; no sustained support or guitar improvement; verification 0 native/0 physics'}
    (PHASE/'analysis.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    if not all(checks.values()):raise AssertionError(checks)
    print(json.dumps({'checks':checks,'summary':summaries,'counts':counts},indent=2))


if __name__=='__main__':main()
