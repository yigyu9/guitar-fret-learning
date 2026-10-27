"""Run the frozen contact measurement over existing free-guitar recordings."""
import gzip,hashlib,json
from pathlib import Path
from dataclasses import asdict
from stability_adapter_2.initial_pose_video60_v1.replay_v6 import rows
from stability_adapter_2.free_guitar_learning_v1.fretting_v1 import FretTarget,FretContract,measure_sample,FrettingTracker
root=Path('/home/ajou/yigyu/3');phase=root/'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1';out=Path(__file__).parent
base=root/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1'
cases=[('free_strike',base/'native_free_strike_v14',4080,9600,4080,5280),('regrasp',base/'native_regrasp_v14',9600,11760,10560,11760)]
files=[Path(__file__)]+[root/'stability_adapter_2/free_guitar_learning_v1'/n for n in ['fretting_v1.py','geometry_v1.py']]+[root/'stability_adapter_2/initial_pose_video60_v1/replay_v6.py']
for _,run,*_ in cases:files.extend(run/n for n in ['initial_values.json','states240.json','contacts240.json','raw4_storage_manifest.json'])
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
pins={str(p):sha(p) for p in files};(out/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
target=FretTarget(1,5,'index');contract=FretContract(.05)
summary={'target':asdict(target),'contract':asdict(contract),'selection':'Existing prepared index2 contact diagnostic; target chosen from current grip, not independently specified song accuracy','scope':'Replay of native post-fetch samples. Candidate is not string pressure, calibrated fingertip or sound. No new physics.','cases':{}}
for label,run,first,last,nstart,nend in cases:
 initial=json.loads((run/'initial_values.json').read_text());tracker=FrettingTracker(contract,nstart,nend)
 total=valid=0;windows={name:dict(samples=0,candidate_samples=0) for name in ('prepared17_22','free25_40','regrasp44_49')};loss=[];reacquire=[];before=None;valid_bodies={};maxgap=0.
 with gzip.open(out/(label+'.jsonl.gz'),'wt') as stream:
  for state_row,contact_row in zip(rows(run/'states240.json'),rows(run/'contacts240.json')):
   step=state_row['physics_step'];assert step==contact_row['physics_step']
   if step<first:continue
   if step>last:break
   measurement=measure_sample(state_row['state'],initial['human_body_names'],initial['guitar_body_names'],contact_row,target,contract)
   progress=tracker.update(step,measurement);candidate=measurement['fretting_contact_candidate'];total+=1;valid+=candidate
   for lo,hi,name in [(4080,5280,'prepared17_22'),(6000,9600,'free25_40'),(10560,11760,'regrasp44_49')]:
    if lo<=step<=hi and (label=='free_strike' or name=='regrasp44_49'):
     windows[name]['samples']+=1;windows[name]['candidate_samples']+=candidate
   for evidence in measurement['contact_evidence']:
    if evidence['valid']:
     key=evidence['human_body'];valid_bodies[key]=valid_bodies.get(key,0)+1;maxgap=max(maxgap,evidence['body_pair_witness_gap_m'])
   if progress['measured_contact_release']:loss.append(step/240.)
   if before is False and candidate:reacquire.append(step/240.)
   before=candidate
   stream.write(json.dumps(dict(measurement=measurement,progress=progress),allow_nan=False)+'\n')
 assert total==last-first+1
 summary['cases'][label]=dict(source=str(run.resolve()),samples=total,candidate_samples=valid,windows=windows,
  measured_contact_loss_times_s=loss,measured_recontact_times_s=reacquire,valid_evidence_bodies=valid_bodies,
  max_valid_witness_gap_m=maxgap,final_progress=progress)
 print(label,total,'samples',valid,'candidates',flush=True)
summary['inputs_unchanged']=all(sha(Path(p))==h for p,h in pins.items());assert summary['inputs_unchanged'];summary['new_physics_steps']=0
(out/'result.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
