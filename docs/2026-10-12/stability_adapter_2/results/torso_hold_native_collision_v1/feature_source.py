"""Locate SDK guitar-side contact features near requested finite neck patches; source proximity only."""
import ast,hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'torso_hold_native_collision_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def vector(v):return np.array([v[k] for k in 'xyz'])
def pose(v):return vector(v['pose']['p']),Rotation.from_quat([v['pose']['r'][k] for k in 'xyzw'])
def main():
    out=PHASE/'native_feature_analysis.json';assert not out.exists()
    inputs={str(Path(__file__).resolve()):sha(__file__)}
    def sealed(p):inputs[str(p)]=sha(p);return read(p)
    analysis=sealed(PHASE/'analysis.json');assert all(analysis['checks'].values());inputs.update(analysis['input_sha256'])
    proposal=sealed(PHASE/'proposal.json');old=ROOT/'stability_adapter_2/analyze_three_face_native_features_v2.py';inputs[str(old)]=sha(old)
    # Preserve the previously reviewed finite-patch geometry computation exactly.
    tree=ast.parse(old.read_text());fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='patch_metrics');scope={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(old),'exec'),scope);metrics=scope['patch_metrics']
    shapes=sealed(BASE/'three_face_support_loss_v1/native/saved_finger_targets/shape_properties.json');guitar_names=[r['body'] for r in shapes['actors']['guitar']['body_ranges']]
    regions={k:np.array(v) for k,v in proposal['regions_G_m'].items()};regions['front'][:,2]=proposal['front_outer_source_z_G_m'];outward=dict(front=[0,0,1],thumb=[0,0,-1],palm=[1,0,0]);summary=[];rows=[]
    for label in ('palm_wide_near17',):
        folder=PHASE/'native';init=sealed(folder/'initial_values.json');h_names=init['human_body_names'];group={}
        for n in ('states','contacts'):inputs[str(folder/f'{n}.jsonl')]=sha(folder/f'{n}.jsonl')
        states=[json.loads(v) for v in (folder/'states.jsonl').read_text().splitlines()];contacts=[json.loads(v) for v in (folder/'contacts.jsonl').read_text().splitlines()]
        assert len(states)==1201 and len(contacts)==1200 and init['physics_parameters'].get('substeps',1)==1
        cached=[[pose(b) for b in state['guitar_body_states']] for state in states]
        human_cached=[[pose(b) for b in state['human_body_states']] for state in states]
        for rec in contacts:
            step=rec['physics_step']
            for index,c in enumerate(rec['contacts']):
                ns=[c['body0_name'],c['body1_name']]
                if not any(n.startswith('guitar/') for n in ns) or not any(n.startswith('human/LH:') for n in ns):continue
                j=next(i for i,n in enumerate(ns) if n.startswith('guitar/'));gbody=ns[j].split('/',1)[1];hbody=ns[1-j].split('/',1)[1];gi=guitar_names.index(gbody)
                assert c['body'+str(j)]==len(h_names)+gi and c['body'+str(1-j)]==h_names.index(hbody)
                local=vector(c['localPos'+str(j)]);at=[]
                for t in (step-1,step):
                    p,r=cached[t][gi];gp,gr=cached[t][0];at.append(gr.inv().apply(p+r.apply(local)-gp))
                normal=cached[step][0][1].inv().apply(vector(c['normal'])*(1 if j==0 else -1))
                hp,hr=human_cached[step][h_names.index(hbody)];human_feature=hp+hr.apply(vector(c['localPos'+str(1-j)]));gp,gr=cached[step][0];pair_residual_mm=float(np.linalg.norm(human_feature-(gp+gr.apply(at[1])))*1000)
                face='palm' if hbody=='LH:palm' else 'thumb' if hbody.startswith('LH:thumb') else 'front'
                values=metrics(at[1],normal,regions[face],outward[face]);near=values['projection_inside'] and abs(values['signed_plane_distance_mm'])<=2 and pair_residual_mm<=.001
                item=dict(label=label,physics_step=step,contact_row=index,human_body=hbody,guitar_body=gbody,raw_lambda=c['lambda'],requested_face=face,point_G_m=at[1].tolist(),pre_post_feature_shift_mm=float(np.linalg.norm(at[1]-at[0])*1000),requested_patch_metrics=values,pair_reconstruction_residual_mm=pair_residual_mm,post_pose_feature_within2mm=near);rows.append(item)
                g=group.setdefault(hbody,dict(requested_face=face,rows=0,positive_rows=0,positive_requested_patch_rows=0,near_positive_steps=set(),positive_finite_patch_distances_mm=[],max_pre_post_feature_shift_mm=0.))
                g['rows']+=1;g['max_pre_post_feature_shift_mm']=max(g['max_pre_post_feature_shift_mm'],item['pre_post_feature_shift_mm'])
                if c['lambda']>0:
                    g['positive_rows']+=1;g['positive_finite_patch_distances_mm'].append(values['finite_patch_distance_mm'])
                    if near:g['positive_requested_patch_rows']+=1;g['near_positive_steps'].add(step)
        for g in group.values():
            distances=g.pop('positive_finite_patch_distances_mm');steps=sorted(g.pop('near_positive_steps'));g.update(positive_finite_patch_distance_range_mm=[min(distances),max(distances)] if distances else None,near_positive_step_count=len(steps),last_near_positive_step=max(steps,default=None),near_positive_steps=steps)
        summary.append(dict(label=label,by_body=group))
    assert all(sha(p)==h for p,h in inputs.items())
    out.write_text(json.dumps(dict(input_sha256=inputs,checks=dict(native_body_mapping_sequence_and_single_substep=True,prior_reviewed_patch_metrics_exact_AST=True,inputs_unchanged=True),summary=summary,rows=rows,normal_convention='SDK guitar-side normal direction and opposite shown separately; no normal gate',threshold_mm=2,scope='SDK guitar-side local feature transformed using post-step body poses; twin-point pair residual<=1um required for near classification; finite source-patch proximity, not actual face identity/force N/cooked penetration/persistent support; pre-post motion reported; offline no native initialization'),indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(samples=len(rows),summary=summary),indent=2))
if __name__=='__main__':main()
