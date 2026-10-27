"""Summarize saved arm proposals; no simulator or geometry solver execution."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

R=Path(__file__).resolve().parents[1]
A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2'
P=D/'results/source_hand_arm_position_v1'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def main():
    assert not (P/'analysis.json').exists()
    execution=read(P/'search_execution.json');data=read(P/'search.json')
    direct={Path(__file__).resolve(),P/'search.json',P/'search_execution.json',P/'search_source_manifest.json',
            A/'SOURCE_HAND_ARM_POSITION_PLAN.md',A/'ARM_POSITION_EXECUTION.md'}
    before=dict(execution['input_sha256_before'])
    before.update({str(p):sha(p) for p in direct})
    manifest={}
    for p in direct:
        dest=P/'analysis_source'/p.relative_to(R)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        assert sha(dest)==before[str(p)]
        manifest[str(p)]=dict(snapshot=str(dest),sha256=sha(dest))
    save(P/'analysis_source_manifest.json',manifest)
    rows=[]
    for row in data['rows']:
        hg=row['source_human_guitar_intersections']
        radii=None if hg is None else [x['common_radius_m']*1000 for x in hg]
        rows.append(dict(order=row['order'],seed_wrist_y_rad=row['seed_wrist_y_rad'],joint=row['joint'],requested_delta_rad=row['requested_delta_rad'],
            initial_delta_L2_rad=row['initial_delta_L2_rad'],source_evaluated=row['source_evaluated'],source_clear=row['source_clear'],
            numeric_violations=row['numeric_violations'],HG_pair_count=None if hg is None else len(hg),
            max_HG_common_radius_mm=None if hg is None else max(radii,default=0.),
            thumb2_G_common_radius_mm=None if hg is None else max([x['common_radius_m']*1000 for x in hg if x['a']=='LH:thumb2' and x['b']=='guitar'],default=0.),
            palm_G_common_radius_mm=None if hg is None else max([x['common_radius_m']*1000 for x in hg if x['a']=='LH:palm' and x['b']=='guitar'],default=0.),
            palm_up_proxy_z=row.get('palm_up_proxy_z'),palm_neck_plane_alignment_abs=row.get('palm_neck_plane_alignment_abs')))
    evaluated=[r for r in rows if r['source_evaluated']]
    checks=dict(search9_pass=len(data['checks'])==9 and all(data['checks'].values()),
        source_exit0_72_inputs_preserved=execution['exit_code']==0 and execution['terminal_state']=='completed' and len(execution['input_sha256_before'])==72 and execution['input_sha256_before']==execution['input_sha256_after'],
        source_log_exact=sha(P/'search.log')==execution['log_sha256'],
        seventy_four_proposals=len(rows)==74,
        sixty_eight_evaluated_six_explicit_exclusions=len(evaluated)==68 and sum(not r['source_evaluated'] for r in rows)==6 and all(r['numeric_violations'] and r['max_HG_common_radius_mm'] is None for r in rows if not r['source_evaluated']),
        all68_HG_intersections_no_selected=all(r['HG_pair_count']>0 and not r['source_clear'] for r in evaluated) and data['selected'] is None,
        all68_cross_self1188_clear=all(not r['source_cross_hand_intersections'] and not r['source_self_intersections'] and r['self_pair_count']==1188 for r in data['rows'] if r['source_evaluated']),
        all68_up_and_identity=all(r['palm_up_proxy_z']>0 and r['upper_arm_identity'] and r['other_meshes_identity'] and r['hand_relative_identity'] for r in data['rows'] if r['source_evaluated']),
        all74_other_q_held_exact=all(r['other_q_and_held_exact'] for r in data['rows']),
        no_proposal_native_or_dynamics=data['native_initializations']==data['physics_steps']==0 and all(not (P/n).exists() for n in ['proposal.json','source_prediction.json','native','native_execution.json']))
    best={str(seed):min((r for r in evaluated if r['seed_wrist_y_rad']==seed),key=lambda r:(r['max_HG_common_radius_mm'],r['HG_pair_count'],r['order'])) for seed in (0.,-.1)}
    checks['inputs_current_and_preserved']=all(sha(p)==h for p,h in before.items())
    assert all(checks.values()),checks
    result=dict(checks=checks,rows=rows,best_max_HG_radius_per_seed=best,min_palm_up_proxy_z=min(r['palm_up_proxy_z'] for r in evaluated),
        zero_thumb2_overlap_orders=[r['order'] for r in evaluated if r['thumb2_G_common_radius_mm']==0.],
        input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},
        native_initializations=0,physics_steps=0,actor_inference_calls=0,training_updates=0,five_second_stability_measured=False,
        scope='Saved source geometry only; common inscribed LP radius is not PhysX penetration depth; no reported thumb pair does not imply physical contact or zero surface distance')
    save(P/'analysis.json',result)
    save(P/'analysis_execution.json',dict(command=[sys.executable,'-m','stability_adapter_2.analyze_arm_position'],exit_code=0,terminal_state='completed',input_sha256_before=before,input_sha256_after=result['input_sha256_after']))
    print(json.dumps(dict(checks=len(checks),best=best,zero_thumb2_overlap_orders=result['zero_thumb2_overlap_orders']),indent=2))


if __name__=='__main__':main()
