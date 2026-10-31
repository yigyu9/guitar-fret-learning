"""CPU read-only reconstruction of existing native samples; no runtime/physics import."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'index_release_close_lead_v2/runs'
REPO=OUT.parents[4]
MODES=['candidate','noisy_candidate']
FILES=[BASE/m/n for m in MODES for n in ['trace_env0_episode0.npz','trace_metadata.json','surface_static.npz','release_clearance4.npz','evaluation.json']]
FILES += [REPO/'guitar_learning/gpu'/n for n in ['contact.py','environment.py','finger_skill_environment.py','scene.py']]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def stats(v):
 v=np.asarray(v);return {'n':int(v.size),'min':float(v.min()),'mean':float(v.mean()),'max':float(v.max())} if v.size else {'n':0}
def corr(a,b):
 return float(np.corrcoef(a,b)[0,1]) if np.std(a)>1e-10 and np.std(b)>1e-10 else None
before={str(p):sha(p) for p in FILES}
result={'scope':'existing env0 native60Hz samples and env0..3 source surface128, no new physics','contact_thresholds':{'lateral_mm_max':3,'signed_height_mm_range':[-1,3],'facing_cos_min':.1,'fret_cell_inset_mm':2,'body_force_norm_N_min':.01},'mapping':[{'compact_column':i,'source_index':s,'physical_string':st,'fret':fr,'finger':1,'distal_body':'human/LH:index3'} for i,(s,st,fr) in enumerate([(4,3,4),(7,2,5),(8,2,5)])],'runs':{}}
result['force_export_scope']={'tensor':'Isaac Gym acquire_net_contact_force_tensor -> refresh_net_contact_force_tensor -> body resultant logical mapping','physics_Hz':240,'substeps':1,'collection':'CC_LAST_SUBSTEP','saved_Hz':60,'saved_scope':'four240Hz steps per control, only post-control endpoint saved; not60Hz-averaged or all240Hz history','reset_scope':'scene.snapshot masks reset rows force to zero; audited surface rows valid_snapshot and not post_failure, audible endpoints after actual physics','limitation':'Zero exported body resultant gives unloaded flag; pairwise contacts, vector cancellation, partner identity and acoustic production cannot be isolated.'}
traces={};sample_records={}
for mode in MODES:
 d=BASE/mode;meta=json.loads((d/'trace_metadata.json').read_text());names=meta['body_names'];jn=meta['joint_names'];a=np.load(d/'trace_env0_episode0.npz');traces[mode]=a;static=np.load(d/'surface_static.npz');plane=static['plane'];body=a['body_state'];dist=body[:,names.index('human/LH:index3')];g=body[:,names.index('guitar/guitar')];rg=Rotation.from_quat(g[:,3:7]);rd=Rotation.from_quat(dist[:,3:7]);local=static['local_points'];norm=static['local_normals']
 pts=np.stack([rg[i].inv().apply(rd[i].apply(local)+dist[i,:3]-g[i,:3]) for i in range(len(g))]);ns=np.stack([rg[i].inv().apply(rd[i].apply(norm)) for i in range(len(g))]);unit=plane[:3]/np.linalg.norm(plane[:3]);height=pts@unit+plane[3]/np.linalg.norm(plane[:3]);cos=-(ns@unit);force=np.linalg.norm(a['net_body_force_n'][:,names.index('human/LH:index3')],axis=1);loaded=force>=.01
 def loc(name):return rg.inv().apply(body[:,names.index('guitar/'+name),:3]-g[:,:3])
 r={'plane':plane.tolist(),'per_note':[],'all354_candidate_predicate_exact':True};sample_records[mode]=[]
 ids=[jn.index(j) for j in ['LH:index1_x','LH:index1_z','LH:index2','LH:index3']]
 for i,(string,fret,lo,hi) in enumerate([(3,4,3,3.1703),(2,5,3.952,4.7299),(2,5,5.3568,5.7051)]):
  start=loc('G:string'+str(string));end=loc('G:string'+str(string)+'_end');start-=((start@unit+plane[3]/np.linalg.norm(plane[:3]))[:,None]*unit);end-=((end@unit+plane[3]/np.linalg.norm(plane[:3]))[:,None]*unit);line=end-start;f1=loc('G:fret'+str(fret-1));f2=loc('G:fret'+str(fret));lower=np.minimum(f1[:,1],f2[:,1])+.002;upper=np.maximum(f1[:,1],f2[:,1])-.002;proj=((pts-start[:,None])*line[:,None]).sum(-1)/(line*line).sum(-1)[:,None];lat=np.linalg.norm(pts-height[:,:,None]*unit-start[:,None]-proj[:,:,None]*line[:,None],axis=-1)
  inc=(pts[:,:,1]>=lower[:,None])&(pts[:,:,1]<=upper[:,None]);hg=(height>=-.001)&(height<=.003);lg=lat<=.003;pos=inc&hg&lg;facing=pos&(cos>=.1);pred=facing.any(1)&loaded&~a['wrong'][:,i];assert np.array_equal(pred,a['candidate'][:,i])
  aud=(a['time_s']>=lo)&(a['time_s']<=hi);bad=aud&~pred
  nr={'source_index':[4,7,8][i],'audible_endpoints':int(aud.sum()),'candidate_misses':int(bad.sum()),'misses_unloaded':int((bad&~loaded).sum()),'misses_no_position_geometry':int((bad&~pos.any(1)).sum()),'misses_no_facing_geometry':int((bad&~facing.any(1)).sum()),'misses_wrong':int((bad&a['wrong'][:,i]).sum()),'miss_time_s':a['time_s'][bad].tolist(),'groups':{}}
  # Restrict a minimum gap to samples that meet lateral/cell/facing but omit height.
  eligible=inc&lg&(cos>=.1);eligible_min=np.where(eligible,height,np.inf).min(1)*1000
  assert np.isfinite(eligible_min[aud]).all()
  for group,k in [('loaded',aud&loaded),('unloaded',aud&~loaded)]:
   nr['groups'][group]={'force_norm_N':stats(force[k]),'nearest_signed_gap_mm':stats(a['surface_height_m'][k,i]*1000),'minimum_any_pad_gap_mm':stats(height[k].min(1)*1000),'minimum_lateral_cell_facing_gap_mm':stats(eligible_min[k]),'nearest_distance_mm':stats(a['surface_distance_m'][k,i]*1000),'actual_minus_target_deg_each_axis':[stats(x) for x in np.rad2deg(a['q'][k][:,ids]-a['target'][k][:,ids]).T],'eligible_facing_cos':stats(cos[k][facing[k]])}
  records=[]
  for q in np.flatnonzero(aud):records.append({'time_s':float(a['time_s'][q]),'force_norm_N':float(force[q]),'loaded':bool(loaded[q]),'candidate':bool(pred[q]),'position_geometry':bool(pos.any(1)[q]),'facing_geometry':bool(facing.any(1)[q]),'nearest_signed_gap_mm':float(a['surface_height_m'][q,i]*1000),'minimum_lateral_cell_facing_gap_mm':float(eligible_min[q]),'actual_q_deg':np.rad2deg(a['q'][q,ids]).tolist(),'target_q_deg':np.rad2deg(a['target'][q,ids]).tolist(),'decoded_goal_deg':np.rad2deg(a['decoded_goal_rad'][q]).tolist()})
  nr['records']=records;r['per_note'].append(nr);sample_records[mode].extend(records)
 s=np.load(d/'release_clearance4.npz');k=(s['clock']/240>=3)&(s['clock']/240<=3.1703);bad=k&~s['candidate'];r['surface4_A_audible']={'rows':int(k.sum()),'misses':int(bad.sum()),'unloaded_misses':int((bad&~s['body_loaded']).sum()),'no_position_geometry_misses':int((bad&~s['aggregate_position_geometry']).sum()),'no_facing_geometry_misses':int((bad&~s['aggregate_facing_geometry']).sum()),'misses_by_env':[int((bad&(s['env_id']==e)).sum()) for e in range(4)],'force_norm_N':stats(np.linalg.norm(s['body_force_n'][k],axis=1))}
 result['runs'][mode]=r
# Correlations use paired same-time noisy-minus-deterministic records. They do not isolate a joint.
det=sample_records['candidate'];noi=sample_records['noisy_candidate'];assert [r['time_s'] for r in det]==[r['time_s'] for r in noi]
x=np.array([n['actual_q_deg'][0]-d['actual_q_deg'][0] for d,n in zip(det,noi)]);goal=np.array([n['decoded_goal_deg'][0]-d['decoded_goal_deg'][0] for d,n in zip(det,noi)]);gap=np.array([n['nearest_signed_gap_mm']-d['nearest_signed_gap_mm'] for d,n in zip(det,noi)]);min_gap=np.array([n['minimum_lateral_cell_facing_gap_mm']-d['minimum_lateral_cell_facing_gap_mm'] for d,n in zip(det,noi)]);force=np.array([n['force_norm_N'] for n in noi]);load=np.array([n['loaded'] for n in noi])
result['paired_env0_audible_correlation']={'n':len(x),'actual_index1_x_delta_deg_by_load':{'loaded':stats(x[load]),'unloaded':stats(x[~load])},'goal_index1_x_delta_deg_by_load':{'loaded':stats(goal[load]),'unloaded':stats(goal[~load])},'corr_actual_x_delta_nearest_gap_delta':corr(x,gap),'corr_actual_x_delta_eligible_min_gap_delta':corr(x,min_gap),'corr_actual_x_delta_force_norm':corr(x,force),'corr_goal_x_delta_actual_x_delta':corr(goal,x),'qualification':'All four goals perturbed simultaneously with dynamics; these correlations do not identify partial derivative/sign of independent index1_x action or causal force response.'}
dump('analysis.json',result)
after={str(p):sha(p) for p in FILES};checks={'input_sha_unchanged':before==after,'predicate_exact_all354_both_modes':all(r['all354_candidate_predicate_exact'] for r in result['runs'].values()),'noisy_all_env0_misses_unloaded':all(n['candidate_misses']==n['misses_unloaded'] for n in result['runs']['noisy_candidate']['per_note']),'noisy_all_env0_misses_geometry_facing_pass':all(n['misses_no_position_geometry']==n['misses_no_facing_geometry']==0 for n in result['runs']['noisy_candidate']['per_note']),'surface4_A_allmisses_unloaded':result['runs']['noisy_candidate']['surface4_A_audible']['misses']==result['runs']['noisy_candidate']['surface4_A_audible']['unloaded_misses']}
dump('verification.json',{'all_checks_passed':all(checks.values()),'checks':checks,'input_sha256_before':before,'input_sha256_after':after,'new_GPU_runs':0,'new_training_steps':0,'new_NN':0});assert all(checks.values())
print(json.dumps(result['paired_env0_audible_correlation'],indent=2))
for mode,r in result['runs'].items():
 for n in r['per_note']:print(mode,n['source_index'],{g:{k:s for k,s in v.items() if k in ['force_norm_N','nearest_signed_gap_mm','minimum_lateral_cell_facing_gap_mm']} for g,v in n['groups'].items()})
