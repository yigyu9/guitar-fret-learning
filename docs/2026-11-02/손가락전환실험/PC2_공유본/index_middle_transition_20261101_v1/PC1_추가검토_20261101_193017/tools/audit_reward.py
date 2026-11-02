"""공유 실행 코드를 import하지 않는 CPU 원시 보상 독립 검산."""
from pathlib import Path
import json,gzip,math,collections,struct,hashlib
OUT=Path(__file__).resolve().parents[1]; ROOT=OUT.parent
f32=lambda x:struct.unpack('f',struct.pack('f',x))[0]
results={}
for path in sorted((ROOT/'로그분석/runs').glob('*repeat[123]')):
    episodes={}
    for line in (path/'episodes.jsonl').open():
        e=json.loads(line)['episode']; episodes.setdefault(e['env_id'],e)
    es=[episodes[i] for i in sorted(episodes)]; n=len(es)
    ids=[e['finger_control_diagnostics']['episode_id'] for e in es]
    sums=[collections.defaultdict(float) for _ in es]; counts=[0]*n; disc=[0.]*n; ret_err=counter_err=0.; phases=collections.defaultdict(lambda:collections.defaultdict(float)); seq=[]
    with gzip.open(path.with_name(path.name+'_reward60.jsonl.gz'),'rt') as f:
        for line in f:
            row=json.loads(line)
            for i in range(n):
                if row['episode_ids'][i]!=ids[i]: continue
                terms={k:v[i] for k,v in row['reward_terms'].items()}
                ret_err=max(ret_err,abs(sum(terms.values())-row['returned_reward'][i]))
                counter_err=max(counter_err,max(abs(v-row['counter_delta'][k][i]) for k,v in terms.items()))
                disc[i]+=.99**counts[i]*terms['song_left_approach']; counts[i]+=1
                if i==0:seq.append(terms['song_left_approach'])
                t=row['end_s'][i]-1/120
                phase='prepare' if t<3 else 'A' if t<4.5 else 'gap' if t<5.25 else 'B' if t<6.75 else 'tail'
                for k,v in terms.items():sums[i][k]+=v; phases[phase][k]+=v/n
    mismatch=max(abs(sums[i][k]-e['reward_components'][k]) for i,e in enumerate(es) for k in sums[i])
    assert min(counts)==max(counts)==435
    assert ret_err<1e-5 and mismatch<1e-4
    results[path.name]={'N':n,'counts':[min(counts),max(counts)],'component_return_max_abs':ret_err,'counter_delta_max_abs':counter_err,'episode_sum_max_abs':mismatch,'discounted_approach_range':[min(disc),max(disc)],'phase_mean_terms':dict(phases)}
    if path.name=='s17_u200_mean_N128_repeat1':
        phi=[]; valid=viol=0
        with gzip.open(path/'finger_control_trace.jsonl.gz','rt') as f:
            for line in f:
                x=json.loads(line)
                if x['env_id']!=0 or x['episode_id']!=ids[0]:continue
                nat=x['natural_preparation']; t=x['episode_time_s']
                for finger in nat['fingers']:
                    if finger.get('preparation_valid'):
                        valid+=1;viol+=finger.get('standby_weight')!=0 or finger.get('standby_rate_per_s')!=0
                if abs(t*60-round(t*60))<1e-6:phi.append(nat['approach_potential_endpoint'])
        assert len(phi)==len(seq)==435
        initial=.99*phi[0]-seq[0];phi[-1]=0.
        results[path.name]['endpoint_check']={'inferred_initial_phi':initial,'later_transition_max_abs':max(abs(seq[j]-(.99*phi[j]-phi[j-1])) for j in range(1,435)),'telescoping_residual':abs(disc[0]+initial),'valid_finger_endpoint_count':valid,'standby_nonzero_on_valid':viol,'scope':'env0 only, initial Phi inferred, first episode; final Phi0 from static code contract'}
cl=f32(.999999); latent=f32(math.atanh(cl)); derivative=1-math.tanh(latent)**2
results['saturation_independent']={'float32_clamp':cl,'float32_atanh':latent,'dq_degrees_per_latent_span1deg':derivative,'linear_sd_deg_std005':derivative*.05,'float32_Ulp_at_10deg_in_rad_to_deg':(f32(f32(math.radians(10))+2**-26)-f32(math.radians(10)))*180/math.pi,'scope':'continuous Jacobian local approximation, not measured float32 distribution'}
saturation_rows={}
for seed in (7,17):
    for update in (100,200,300):
        for mode in ('mean','sampled'):
            name=f'base_seed{seed}_u{update}_{mode}'; req=[]; app=[]; act=[]; action=[]
            with gzip.open(ROOT/'진단'/name/'finger_control_trace.jsonl.gz','rt') as f:
                for line in f:
                    x=json.loads(line)
                    if x['env_id']!=0 or not 5.25<=x['score_time_s']<6.75:continue
                    tr=x['natural_preparation']['transition'];j=tr['arm_joint_names'].index('L_Thorax_y')
                    req.append(math.degrees(tr['arm_requested_rad'][j]));app.append(math.degrees(tr['arm_applied_rad'][j]));act.append(math.degrees(tr['arm_actual_rad'][j]));action.append(tr['arm_action'][j])
            saturation_rows[name]={'frames':len(req),'requested_range_deg':[min(req),max(req)],'applied_range_deg':[min(app),max(app)],'actual_mean_deg':sum(act)/len(act),'saturation_fraction':sum(abs(a)>=.98 for a in action)/len(action)}
catalog=json.loads((ROOT/'진단/geometry/initial_catalog.json').read_text());j=catalog['joint_names'].index('L_Thorax_y');k=catalog['action_indices'].index(j)
reference_trace=json.loads((ROOT/'진단/native_reference_v2/reference_trace60.json').read_text());teacher=[math.degrees(x['requested_q105'][j]) for x in reference_trace if 5.25<=x['time_s']<6.75]
results['raw_saturation']={'rows':saturation_rows,'reference_deg':math.degrees(catalog['reference105'][j]),'hold_deg':math.degrees(catalog['goals'][0]['hold_target105'][j]),'upper_deg':math.degrees(catalog['action_upper'][k]),'teacher_B_requested_range_deg':[min(teacher),max(teacher)]}
results['audit_scope']={'no_import_of_shared_code':True,'no_model_load':True,'no_gpu':True,'identity_full_revalidation':'not performed: reading copy is not original executable project; original strict-loader evidence remains provenance, not bypassed'}
(OUT/'code_reward_audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps({k:({a:v[a] for a in ('component_return_max_abs','episode_sum_max_abs','discounted_approach_range') if a in v}) for k,v in results.items()},ensure_ascii=False,indent=2))
