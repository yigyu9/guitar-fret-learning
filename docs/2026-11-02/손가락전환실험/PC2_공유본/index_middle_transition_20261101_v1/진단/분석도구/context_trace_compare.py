if not __debug__:raise RuntimeError('Scientific checks require optimization disabled')
from pathlib import Path
import json,gzip,hashlib,itertools
D=Path(__file__).resolve().parents[2];paths=[D/'진단'/n for n in ('final128_seed17_mean','context_repeat_seed17_mean_128')];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();reports=[json.loads((p/'report.json').read_text()) for p in paths];assert reports[0]['settings']==reports[1]['settings'];assert reports[0]['checkpoint_sha256']==reports[1]['checkpoint_sha256']
first={};arm={};different=0;count=0
with gzip.open(paths[0]/'finger_control_trace.jsonl.gz','rt') as fa,gzip.open(paths[1]/'finger_control_trace.jsonl.gz','rt') as fb:
 for aa,bb in itertools.zip_longest(fa,fb):
  assert aa is not None and bb is not None,'trace length differs';a,b=json.loads(aa),json.loads(bb);count+=1;assert a['episode_time_s']==b['episode_time_s']
  for key in ('requested_target_rad','applied_target_rad','actual_rad'):
   delta=max(abs(x-y) for x,y in zip(a[key],b[key]))
   if key not in first and delta>1e-6:first[key]={'t':a['episode_time_s'],'max_delta':delta}
  x=a['natural_preparation']['transition'];y=b['natural_preparation']['transition'];different+=x['all_env_candidate']!=y['all_env_candidate']
  for key in ('arm_requested_rad','arm_applied_rad','arm_actual_rad'):
   delta=max(abs(p-q) for p,q in zip(x[key],y[key]))
   if key not in arm and delta>1e-6:arm[key]={'t':a['episode_time_s'],'max_delta':delta}
result={'settings_equal':True,'checkpoint_sha256':reports[0]['checkpoint_sha256'],'threshold_rad':1e-6,'compared_240Hz_rows':count,'first_env0_differences_above1e_6rad':first,'first_env0_arm_differences_above1e_6rad':arm,'all_env_candidate_different_rows':different,'input_trace_sha256':{str(p/'finger_control_trace.jsonl.gz'):sha(p/'finger_control_trace.jsonl.gz') for p in paths},'input_report_sha256':{str(p/'report.json'):sha(p/'report.json') for p in paths},'analysis_source_sha256':sha(Path(__file__)),'scope':'first threshold exceedance only. Smaller earlier command differences and untracked controller efforts are not excluded. Physical/control feedback sensitivity observed; exact initiating cause not established.'};(D/'진단/context_trace_comparison.json').write_text(json.dumps(result,indent=2));print(result)
