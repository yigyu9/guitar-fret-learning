"""Measure source-plane alignment at saved native poses; no simulation."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT=Path('/home/ajou/yigyu/3')
PREVIOUS=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1'
OUT=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1'
FACET=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/facet_distal_search/search.json'
GEOMETRY=ROOT/'docs/2026-10-12/visualizations/grip_proposal/geometry.json'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xyz(value):
    return np.array([value[k] for k in ('x','y','z')],dtype=float)


def transform(body,local,normal=False):
    pose=body['pose'];q=np.array([pose['r'][k] for k in ('x','y','z','w')])
    q=q/np.linalg.norm(q);v=np.asarray(local);r=q[:3]
    result=v+2*np.cross(r,np.cross(r,v)+q[3]*v)
    return result/np.linalg.norm(result) if normal else xyz(pose['p'])+result


def main():
    OUT.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__).resolve(),FACET,GEOMETRY]
    facet=read(FACET);polygon=np.array(read(GEOMETRY)['regions_G_m']['palm'])
    normal=np.cross(polygon[1]-polygon[0],polygon[2]-polygon[0]);normal/=np.linalg.norm(normal)
    if normal[0]<0:normal=-normal
    rows={};summary=[]
    for mode in ('off','bias','tracking'):
        folder=PREVIOUS/'short'/mode;paths.extend([folder/'states.json',folder/'report.json'])
        report=read(folder/'report.json');states=read(folder/'states.json')
        if report['physics_steps']!=24 or len(states)!=25 or not all(report['checks'].values()):
            raise AssertionError('saved trial coverage/contracts')
        palm_index=report['human_body_names'].index('LH:palm');values=[]
        for step,state in enumerate(states):
            palm=state['human_body_states'][palm_index];guitar=state['guitar_body_states'][0]
            npalm=transform(palm,facet['palmar_facet_normal_local'],normal=True)
            nguitar=transform(guitar,normal,normal=True)
            delta=transform(palm,facet['palmar_facet_point_local_m'])-transform(guitar,polygon.mean(0))
            dot=float(np.clip(-npalm@nguitar,-1,1));gap=float(delta@nguitar)
            values.append({'physics_step':step,'time_s':step/240,
                'facing_normal_angle_deg':float(np.degrees(np.arccos(dot))),
                'facing_dot':dot,'signed_source_normal_gap_mm':gap*1000,
                'source_tangent_distance_to_patch_center_mm':float(np.linalg.norm(delta-gap*nguitar)*1000)})
        rows[mode]=values
        summary.append({'mode':mode,'initial':values[0],'end':values[-1],
            'max_facing_normal_angle_deg':max(v['facing_normal_angle_deg'] for v in values),
            'minimum_facing_dot':min(v['facing_dot'] for v in values)})
    checks={'finite_measurements':all(np.isfinite([v[k] for k in v if k!='physics_step']).all() for values in rows.values() for v in values),
        'same_initial_metrics':rows['off'][0]==rows['bias'][0]==rows['tracking'][0],
        'facing_hemisphere_preserved':all(s['minimum_facing_dot']>0 for s in summary)}
    output={'checks':checks,'summary':summary,'rows':rows,'input_sha256':{str(p):sha(p) for p in paths},
        'native_initializations':0,'physics_steps':0,
        'scope':'source-facet normals and selected point transformed by saved native poses; not cooked surfaces or force measurements'}
    (OUT/'measurements.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    if not all(checks.values()):raise AssertionError(checks)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
