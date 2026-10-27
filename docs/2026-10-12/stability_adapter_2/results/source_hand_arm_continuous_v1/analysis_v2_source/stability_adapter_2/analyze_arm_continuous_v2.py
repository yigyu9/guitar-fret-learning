"""Independently summarize saved bounded source optimization, without geometry solves."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import struct
import sys

R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2'
D=R/'docs/2026-10-12/stability_adapter_2';P=D/'results/source_hand_arm_continuous_v1'
OLD=D/'results/fixed_strap_source_hand_initial_v1'


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')
def f32(v):return struct.unpack('f',struct.pack('f',v))[0]


def main():
    assert not (P/'analysis_v2.json').exists()
    execution=read(P/'search_execution.json');data=read(P/'search.json')
    direct={Path(__file__).resolve(),P/'search.json',P/'search_execution.json',P/'search_source_manifest.json',P/'evaluations.jsonl',
        A/'SOURCE_HAND_ARM_CONTINUOUS_PLAN.md',A/'ARM_CONTINUOUS_EXECUTION.md',A/'ARM_CONTINUOUS_ANALYSIS_V2.md',P/'analysis_failure.json',P/'analysis_source_manifest.json',P/'analysis_invocation.json'}
    before=dict(execution['input_sha256_before']);before.update({str(p):sha(p) for p in direct})
    copies={}
    for p in direct:
        dest=P/'analysis_v2_source'/p.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        assert sha(dest)==before[str(p)];copies[str(p)]=dict(snapshot=str(dest),sha256=sha(dest))
    save(P/'analysis_v2_source_manifest.json',copies)
    initial=read(OLD/'native/initial_values.json');names=initial['human_joint_names'];q0=initial['initial_PD_target_rad'];t0=initial['preserved_absolute_targets_rad']
    old=read(OLD/'proposal.json');trial=read(old['rows'][0]['trial_path']);offsets=[trial['main_target_offsets_rad'].get(n,0.) for n in names]
    indices=[names.index(n) for n in data['selected_names']];other=[i for i in range(81) if i not in indices]
    limits={(r['kind'],r['name']):r for r in (json.loads(s) for s in (D/'results/fixed_strap_source_compatibility_v1/joint_ranges.jsonl').read_text().splitlines()) if r['label']=='initial_aligned'}
    rows=[];max_component_error=0.;max_total_error=0.
    for raw in data['rows']:
        q=q0.copy()
        for i,delta in zip(indices,raw['requested_delta_rad']):q[i]=f32(q0[i]+delta)
        target=[f32(x+y) for x,y in zip(q,offsets)]
        assert q==raw['raw_initial_rad'] and target==raw['raw_absolute_targets_rad']
        assert all(q[i]==q0[i] and target[i]==t0[i] for i in other)
        assert raw['actual_delta_rad']==[q[i]-q0[i] for i in indices] and max(abs(v) for v in raw['actual_delta_rad'])<=.15
        variants=[('actual_initial',q),('held',target)]
        for sign in (-1,1):
            moving=offsets.copy();moving[names.index('L_Wrist_x')]+=sign*.005
            variants.append(('held',[f32(x+y) for x,y in zip(q,moving)]))
        assert all(limits[k,n]['effective_lower_rad']<=v<=limits[k,n]['effective_upper_rad'] for k,values in variants for n,v in zip(names,values))
        hg=raw['source_human_guitar_intersections'];distances=raw['support_patch_distances']
        derived=dict(collision=1e6*sum((v['common_radius_m']*1000)**2 for v in hg),support=sum((v['distance_m']*1000)**2 for v in distances.values()),
            posture=.01*sum((v/.15)**2 for v in raw['actual_delta_rad']),plane=.1*(1-raw['palm_neck_plane_alignment_abs'])**2,hard_invalid=0.)
        def close(a,b):return abs(a-b)<=1e-10+8*sys.float_info.epsilon*max(abs(a),abs(b))
        max_component_error=max(max_component_error,max(abs(raw['objective_terms'][k]-v) for k,v in derived.items()))
        max_total_error=max(max_total_error,abs(raw['objective_value']-sum(derived.values())))
        assert all(close(raw['objective_terms'][k],v) for k,v in derived.items()) and close(raw['objective_value'],sum(derived.values()))
        rows.append(dict(order=raw['order'],seed_id=raw['seed_id'],seed_evaluation=raw['seed_evaluation'],objective_value=raw['objective_value'],objective_terms=derived,
            max_HG_common_radius_mm=max(v['common_radius_m']*1000 for v in hg),HG_pair_count=len(hg),
            palm_patch_upper_mm=distances['LH:palm']['distance_m']*1000,thumb_patch_upper_mm=distances['LH:thumb3']['distance_m']*1000,
            initial_delta_L2_rad=math.sqrt(sum(v*v for v in raw['actual_delta_rad'])),palm_up_proxy_z=raw['palm_up_proxy_z']))
    checks=dict(source10_pass=len(data['checks'])==10 and all(data['checks'].values()),
        source_exit0_inputs_preserved=execution['exit_code']==0 and execution['terminal_state']=='completed' and execution['input_sha256_before']==execution['input_sha256_after'],
        source_log_exact=sha(P/'search.log')==execution['log_sha256'],
        two400_calls_exact=len(rows)==800 and all(s['nfev']==s['stored_evaluations']==400 and s['status']==1 and not s['success'] for s in data['solves']) and [r['seed_id'] for r in rows]==[0]*400+[1]*400,
        all800_HG_remain_no_selection=all(r['HG_pair_count']>0 for r in rows) and data['selected'] is None and data['clear_count']==0,
        all800_full_secondary_screens_unmeasured=all(r['source_cross_hand_intersections'] is None and r['source_self_intersections'] is None and r['self_pair_count'] is None for r in data['rows']),
        all800_range_up_identity=all(r['within_effective_ranges'] and not r['numeric_violations'] and r['palm_up_proxy_z']>0 and r['upstream_pose_identity'] and r['other_meshes_identity'] and r['hand_relative_identity'] for r in data['rows']),
        all800_inputs_and_objectives_independently_reconstructed=True,
        jsonl_rows_exact=data['rows']==[json.loads(s) for s in (P/'evaluations.jsonl').read_text().splitlines()],
        no_native_or_candidate=data['native_initializations']==data['physics_steps']==0 and all(not (P/n).exists() for n in ['proposal.json','source_prediction.json','native','native_execution.json']))
    best={str(seed):dict(objective=min((r for r in rows if r['seed_id']==seed),key=lambda r:r['objective_value']),
        max_HG=min((r for r in rows if r['seed_id']==seed),key=lambda r:r['max_HG_common_radius_mm'])) for seed in (0,1)}
    checks['all_inputs_current_preserved']=all(sha(p)==h for p,h in before.items());assert all(checks.values()),checks
    result=dict(checks=checks,rows=rows,best_per_seed=best,min_palm_up_proxy_z=min(r['palm_up_proxy_z'] for r in rows),
        input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},native_initializations=0,physics_steps=0,actor_inference_calls=0,training_updates=0,
        five_second_stability_measured=False,max_objective_component_abs_error=max_component_error,max_objective_total_abs_error=max_total_error,scope='800 saved conditional source evaluations; budgets exhausted without a clear candidate, not a global infeasibility proof; cross/self deferred, not certified clear; LP radius is not PhysX penetration depth')
    save(P/'analysis_v2.json',result)
    save(P/'analysis_v2_execution.json',dict(command=[sys.executable,'-m','stability_adapter_2.analyze_arm_continuous_v2'],exit_code=0,terminal_state='completed',input_sha256_before=before,input_sha256_after=result['input_sha256_after']))
    print(json.dumps(dict(checks=len(checks),best=best,min_up=result['min_palm_up_proxy_z']),indent=2))


if __name__=='__main__':main()
