"""Read-only completed-run storage census; writes only its new audit JSON."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import gzip,hashlib,json,statistics
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[5]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1'
OUT=Path(__file__).with_suffix('.json')

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def equivalent(a,b):
 if isinstance(a,torch.Tensor):return isinstance(b,torch.Tensor) and torch.equal(a,b)
 if isinstance(a,np.ndarray):return isinstance(b,np.ndarray) and np.array_equal(a,b)
 if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)):return type(a)==type(b) and len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
 return a==b

def category(p):
 if p.suffix=='.pt':return 'rollout_tensor' if p.name.startswith('rollout') else 'PPO_checkpoint'
 if p.name=='transitions.jsonl.gz':return 'training_compact_trace'
 if p.name=='transitions.json.gz':return 'evaluation_full_trace'
 if p.name.startswith('transition_') and p.suffix=='.gz':return 'training_sampled_raw_trace'
 if p.name in ('resources.jsonl','events.jsonl','status.json'):return 'monitoring'
 if p.suffix=='.log':return 'stdout_stderr'
 if any(s in p.name for s in ('inputs','settings','contract','initial_values','initialization','reset_')):return 'provenance_contract_reset'
 return 'report_or_diagnostic'

def encoded(value):return len(json.dumps(value,ensure_ascii=True).encode())

def dictionaries(value,prefix=''):
 if not isinstance(value,dict):return
 for key,child in value.items():
  path=prefix+'.'+key if prefix else key
  if isinstance(child,dict):
   yield path,child
   yield from dictionaries(child,path)

def gzip_measure(path,parse_rows=False):
 raw_bytes=lines=0;sizes=[];infos=[]
 with gzip.open(path,'rb') as f:
  for line in f:
   raw_bytes+=len(line);lines+=1
   if parse_rows and line.strip():
    sizes.append(len(line));infos.extend(json.loads(line)['infos'])
 result=dict(path=str(path),compressed_bytes=path.stat().st_size,decompressed_bytes=raw_bytes,physical_text_lines=lines,compression_ratio=raw_bytes/path.stat().st_size)
 if parse_rows:
  result.update(transition_rows=len(sizes),worker_info_rows=len(infos),mean_row_bytes=statistics.mean(sizes) if sizes else 0,min_row_bytes=min(sizes) if sizes else 0,max_row_bytes=max(sizes) if sizes else 0)
  totals=Counter();dicts=defaultdict(list)
  for info in infos:
   totals.update({key:encoded(value) for key,value in info.items()})
   for name,value in dictionaries(info):
    data=json.dumps(value,sort_keys=True,ensure_ascii=True)
    if len(data)>=100:dicts[name].append(data)
  result['serialized_info_value_bytes_by_top_key']=dict(totals.most_common())
  result['constant_dictionary_components']=[dict(path=name,repetitions=len(values),serialized_value_bytes_per_row=len(values[0]),serialized_value_bytes_sum=sum(map(len,values)),unique_values=1) for name,values in sorted(dicts.items()) if len(values)==len(infos)>1 and len(set(values))==1]
  # Each component below is disjoint. Byte sums omit parent key/delimiter and
  # describe uncompressed JSON values; gzip savings cannot be attributed additively.
  selections=('musical_quality.strike.preparation','specialist.skill.config','timing.config')
  result['selected_disjoint_constant_metadata_bytes']=sum(sum(map(len,dicts[name])) for name in selections if name in dicts and len(set(dicts[name]))==1)
  duplicates=[]
  if infos:
   paired=[(info.get('specialist',{}).get('timing'),info.get('timing')) for info in infos]
   if all(a is not None and a==b for a,b in paired):duplicates.append(dict(paths=['specialist.timing','timing'],rows=len(paired),duplicated_value_bytes_sum=sum(encoded(a) for a,b in paired),scope='exact semantic duplicate within each row; value byte estimate, not compressed savings'))
  result['within_row_duplicate_summaries']=duplicates
 return result

folders={};all_groups=Counter();training_total=0;eval_total=0
for name in ('left_native_train_v2','right_native_train_v1','left_native_train_v1','left_native_eval_v1','right_native_eval_v1'):
 folder=PHASE/name
 records=[];groups=Counter()
 for path in sorted(folder.rglob('*')):
  if path.is_file():
   size=path.stat().st_size;kind=category(path);groups[kind]+=size
   records.append(dict(path=str(path),relative_path=str(path.relative_to(folder)),bytes=size,kind=kind))
 log=PHASE/(name+'.log')
 if log.is_file():
  groups['stdout_stderr']+=log.stat().st_size
  records.append(dict(path=str(log),relative_path='../'+log.name,bytes=log.stat().st_size,kind='stdout_stderr'))
 result=dict(path=str(folder),files=records,file_count=len(records),total_bytes=sum(groups.values()),bytes_by_kind=dict(groups),largest_files=sorted(records,key=lambda r:r['bytes'],reverse=True)[:10])
 if '_eval_' in name:
  result['tier']='deterministic evaluation full240Hz native/evidence trace, separate from routine training telemetry'
  eval_total+=result['total_bytes']
  result['trace']=gzip_measure(folder/'transitions.json.gz')
 else:
  result['tier']='failed startup evidence' if name=='left_native_train_v1' else 'routine training telemetry + first raw sample + full PPO recovery checkpoints'
  training_total+=result['total_bytes']
  result['trace']=gzip_measure(folder/'transitions.jsonl.gz',parse_rows=True)
  r=json.loads((folder/'report.json').read_text())
  result['runtime_evidence']={k:r.get(k) for k in ('completed','stopped','transitions','timers','wall_s','collection_transitions_per_s','recovery_checkpoint','recovery_eligible','partial_collection')}
  if name=='left_native_train_v1':result['failure']=r['failure']
  else:
   initial=torch.load(folder/'initial.pt',map_location='cpu',weights_only=False)
   checkpoint=torch.load(folder/'checkpoint_000000.pt',map_location='cpu',weights_only=False)
   final=torch.load(folder/'final.pt',map_location='cpu',weights_only=False)
   same={key:equivalent(checkpoint[key],final[key]) for key in checkpoint}
   result['checkpoint_comparison']=dict(checkpoint_path=str(folder/'checkpoint_000000.pt'),final_path=str(folder/'final.pt'),checkpoint_bytes=(folder/'checkpoint_000000.pt').stat().st_size,final_bytes=(folder/'final.pt').stat().st_size,byte_identical=sha(folder/'checkpoint_000000.pt')==sha(folder/'final.pt'),top_level_payload_equal=same,differing_payload_keys=[key for key,value in same.items() if not value],initial_updates=initial['updates'],checkpoint_updates=checkpoint['updates'],final_updates=final['updates'],checkpoint_metadata=checkpoint['metadata'],final_metadata=final['metadata'],scope='Semantic model/optimizer/RNG equality distinct from torch archive bytes and run metadata')
   rollout=torch.load(folder/'rollout_first.pt',map_location='cpu',weights_only=False)
   result['rollout_payload']={key:dict(shape=list(value.shape),dtype=str(value.dtype),tensor_bytes=value.numel()*value.element_size()) for key,value in rollout.items()}
   del initial,checkpoint,final,rollout
 all_groups.update(groups);folders[name]=result
source_refs=[('guitar_learning/train_parallel.py',132,'gzip compact transition stream opened once'),('guitar_learning/train_parallel.py',140,'step_s wraps pool.step; JSON dump/write occurs afterward'),('guitar_learning/train_parallel.py',169,'collection_s wraps whole collector, including logging and worker IPC'),('guitar_learning/train_parallel.py',173,'first rollout tensor only'),('guitar_learning/train_parallel.py',185,'periodic/last update checkpoint'),('guitar_learning/train_parallel.py',190,'final checkpoint saved again'),('guitar_learning/parallel.py',137,'first native raw transition by default; all raw only if raw_samples'),('guitar_learning/train_timing.py',40,'top-level timing copy in addition to nested specialist timing'),('guitar_learning/train_musical_quality.py',27,'append full musical_quality summary'),('guitar_learning/evaluate_timing.py',64,'full native four-substep/evidence evaluation rows retained in memory'),('guitar_learning/evaluate_timing.py',73,'evaluation rows serialized at end'),('guitar_learning/monitoring.py',55,'failure checkpoint only after trainer exists and recovery eligibility'),('guitar_learning/ppo.py',203,'full model/optimizers/RNG checkpoint'),('guitar_learning/ppo.py',218,'strict identity load and RNG/optimizer restoration'),('guitar_learning/recording.py',30,'exclusive result write; compression is opt-in')]
report=dict(schema='guitar_learning.logging_storage_audit.v1',created_utc=datetime.now(timezone.utc).isoformat(),read_only=True,folders=folders,totals=dict(training_and_failed_bytes=training_total,evaluation_bytes=eval_total,all_bytes=training_total+eval_total,bytes_by_kind=dict(all_groups)),source_evidence=[dict(path=str(ROOT/path),line=line,sha256=sha(ROOT/path),purpose=purpose) for path,line,purpose in source_refs],measurement_scope=['Sizes are actual regular-file logical byte sizes from stat, not allocated disk blocks. External per-run stdout/stderr files are included explicitly.','gzip decompressed bytes are measured by reading completed archives; no native simulation/training or original artifact write occurs.','JSON component sizes are uncompressed serialized value estimates and may overlap in constant_dictionary_components. Only selected_disjoint_constant_metadata_bytes is a deliberately nonoverlapping subset; gzip savings are not inferred from these sums.','Payload equality compares tensors/arrays/nested values exactly; different .pt container bytes or metadata do not imply different learned weights.','No dedicated serialization/write/flush/IPC timer is present. These storage measurements do not establish logging I/O as a runtime bottleneck. collection_s includes logging; step_s is pool-step wall time, containing native work/IPC and optional first raw write. Their difference includes inference/collector overhead, not just logging.','Evaluation full native traces and failed-startup diagnostics serve different retention purposes from high-volume routine training telemetry. Existing sealed files are preserved.'])
report['storage_interpretation']=dict(checkpoint_fraction_of_training_and_failure=all_groups['PPO_checkpoint']/training_total,semantically_duplicate_final_checkpoint_bytes=sum(r.get('checkpoint_comparison',{}).get('checkpoint_bytes',0) for r in folders.values()),compact_trace_compressed_bytes=sum(r['trace']['compressed_bytes'] for name,r in folders.items() if '_train_' in name),evaluation_full_trace_compressed_bytes=all_groups['evaluation_full_trace'],decisions=['Preserve all existing sealed evidence; this audit deletes or modifies none of it.','For future producers, one canonical final full-state checkpoint plus an external alias/metadata record can avoid saving the same model/optimizers/RNG twice at the final update. Strict resume still needs full identity, optimizer and RNG state.','For future compact logs, move immutable preparation/config strings to run metadata and reference schema IDs; avoid serializing identical specialist.timing and timing copies. These are uncompressed-size opportunities, not proven I/O bottlenecks.','Keep failed startup report/log/worker audit/source pins: they distinguish a configuration/import failure before trainer creation from a physically failed or resumable policy run. An empty43-byte gzip is zero transitions, not evidence of missing successful rollout data.','Treat evaluation full240Hz native/evidence traces as a separate evidence tier; do not expect routine training compact logs to replace or reconstruct them.','If runtime optimization becomes necessary, add separate JSON encoding/gzip write/flush/checkpoint-save/raw-sample and IPC/native timers before choosing a logging change.'])
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(totals=report['totals'],runs={name:dict(files=r['file_count'],bytes=r['total_bytes'],trace={k:v for k,v in r['trace'].items() if k in ('compressed_bytes','decompressed_bytes','transition_rows','mean_row_bytes')},checkpoint_differing_keys=r.get('checkpoint_comparison',{}).get('differing_payload_keys')) for name,r in folders.items()}),indent=2))
