"""Verify actual bank, four-worker warm start and repeated native resets."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with p.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
bank=read(P/'bank_build_v1/bank.json');search=read(P/'bank_build_v1/search.json');smoke=read(P/'smoke_v1/report.json');probe=read(P/'reset_probe_v1/report.json')
basecfg=bank['configs'][bank['entries'][0]['config_path']];base=read(Path(basecfg['initial_candidate']));q0=np.array(base['joint_angles_rad']);names=base['joint_names'];fixed=np.array([i for i,n in enumerate(names) if not n.startswith(('L_','R_'))])
rows=[]
for i,e in enumerate(bank['entries']):
    cfg=bank['configs'][e['config_path']];c=read(Path(cfg['initial_candidate']));q=np.array(c['joint_angles_rad'])
    rows.append({'bank_index':i,'proposal_trial':e['trial'],'translation_W_mm':(np.array(e['delta_position_W_m'])*1000).tolist(),'world_rotvec_component_deg':e['world_rotvec_deg'],'SO3_jitter_magnitude_deg':float(np.linalg.norm(e['world_rotvec_deg'])),'max_arm_q_change_deg':float(np.rad2deg(abs(q-q0)).max()),'fixed_body_head_finger_q_exact':bool(np.array_equal(q[fixed],q0[fixed])),'max_native_palm_position_error_mm':max(m['position_error_m'] for m in e['native_palm_error'].values())*1000,'max_native_palm_rotation_error_deg':max(m['orientation_error_deg'] for m in e['native_palm_error'].values()),'source_clear':e['source_clear'],'native_palm_up_proxy_z':e['native_palm_up_proxy_z']})
metrics=smoke['metrics'][0]['metrics'];checks={'bank_zero_plus_four':len(rows)==5 and bank['entries'][0]['trial']==0,'all_bank_source_native_clear':all(e['validated_native'] and e['source_clear'] for e in bank['entries']),'fixed_q_unchanged':all(r['fixed_body_head_finger_q_exact'] for r in rows),'four_actual_workers':len(smoke['initial_native'])==4,'actual_CUDA_update_256':smoke['updates']==1 and smoke['transitions']==256 and metrics['optimizer_steps']>0,'KL_and_RMS':metrics['final_analytic_kl']<=.02 and not metrics['RMS_updated'],'sample_diversity':len(set(r['index'] for r in smoke['reset_records']))>1,'six_native_reset_exact':probe['completed'] and probe['ABI_constant'] and probe['all_initial_native_exact'] and probe['resets']==3 and probe['workers']==2,'bank_inputs_pinned':all(sha(p)==h for p,h in bank['input_sha256'].items()),'new_sources_pinned':all(sha(p)==h for p,h in read(P/'source_before_native_v1.json').items()),'probe_source_pinned':all(sha(p)==h for p,h in read(P/'source_addition_probe_v1.json').items()),'zero_forbidden_after_training':all(not s['forbidden_calls'] for s in smoke['final_native'])}
inputs={str(p):sha(p) for p in [Path(__file__),P/'bank_build_v1/bank.json',P/'bank_build_v1/search.json',P/'smoke_v1/report.json',P/'reset_probe_v1/report.json',P/'source_before_native_v1.json',P/'source_addition_probe_v1.json']}
save(P/'analysis_v1.json',{'passed':all(checks.values()),'checks':checks,'rows':rows,'proposals':len(search['rows']),'rejection_absolute_rotation_envelope':sum(r.get('rejection')=='absolute_rotation_envelope' for r in search['rows']),'smoke_collection':smoke['metrics'][0]['collection'],'smoke_metrics':metrics,'reset_indices':probe['indices'],'input_sha256':inputs,'scope':'initial placement and real optimizer/collector correctness; no music or stabilization success claim; discrete filtered bank, not full independent continuous uniform noise'})
assert all(checks.values()),checks
print({'passed':True,'checks':len(checks),'rows':len(rows)})
