"""Finalize the bounded implementation/experiment phase, not research success."""
from pathlib import Path
import json
from guitar_learning.recording import digest,write
P=Path(__file__).resolve().parent
ROOT=Path('/home/ajou/yigyu/3')


def checks():
 inputs={};conflicts=[]
 manifests=sorted(P.glob('*/inputs.json'))+sorted(P.glob('*/inputs_before.json'))
 for f in manifests:
  data=json.loads(f.read_text())
  for name,sha in data.items():
   path=str(Path(name).resolve())
   if not isinstance(sha,str) or len(sha)!=64:raise ValueError('unexpected manifest '+str(f))
   if path in inputs and inputs[path]!=sha:conflicts.append(path)
   inputs[path]=sha
 changed=[p for p,s in inputs.items() if digest(p)!=s]
 if changed or conflicts:raise RuntimeError(dict(changed=changed,conflicts=conflicts))
 runs={}
 for role in ('left','right'):
  for cost in ('1p0','0p1'):
   name=role+'_cost'+cost+'_run_v2';p=P/name;r=json.loads((p/'report.json').read_text());a=json.loads((p/'persistent_audit.json').read_text())
   if not r['completed'] or len(r['updates'])!=12 or r['transitions']!=5760 or not a['completed']:raise RuntimeError('run incomplete '+name)
   if any(r[k] for k in ('changed_inputs','missing_import_pins','guard_violations','worker_failures','physical_flags_errors')):raise RuntimeError('run audit '+name)
   ev=json.loads((P/(role+'_cost'+cost+'_eval_v1')/'result.json').read_text())
   if not ev['completed'] or not ev['source_unchanged'] or len(ev['episodes'])!=2:raise RuntimeError('evaluation incomplete '+name)
   runs[name]=dict(updates=12,transitions=5760,episodes=len(json.loads((p/'skill_report.json').read_text())['episodes']),
      deterministic_successes=sum(e['specialist']['stage_success'] for e in ev['episodes']),persistent_audit=True)
 lifecycle=[]
 for f in sorted(P.rglob('persistent_lifecycle.json')):
  r=json.loads(f.read_text());counts=r['native_calls']
  if not r['closed'] or counts['create_sim']!=1 or counts['destroy_sim']!=1 or counts['create_env']!=1 or r['forbidden_calls_total']:raise RuntimeError('native lifecycle '+str(f))
  lifecycle.append(dict(path=str(f),sha256=digest(f),resets=r['episode_index']+1))
 for role in ('left','right'):
  d=json.loads((P/(role+'_demonstration_v1')/'result.json').read_text())
  if not d['success'] or d['observation_dimension']!=505 or d['ticks']!=240 or not d['source_unchanged']:raise RuntimeError('demonstration '+role)
 original=json.loads((ROOT/'guitar_learning/archive/20261018_before_skill_curriculum/manifest.json').read_text())['files'];original_py=0
 for f in original:
  if digest(f['archive'])!=f['sha256']:raise RuntimeError('archive changed '+f['archive'])
  if f['original'].endswith('.py'):
   original_py+=1
   if digest(f['original'])!=f['sha256']:raise RuntimeError('old code changed '+f['original'])
 for f in json.loads((ROOT/'guitar_learning/archive/20261018_before_skill_history_v2/manifest.json').read_text())['files']:
  if digest(f['archive'])!=f['sha256'] or digest(f['path'])!=f['sha256']:raise RuntimeError('v1 dependency changed')
 log=(P/'cpu_tests_v2.log').read_text()
 if 'Ran 189 tests' not in log or not log.rstrip().endswith('OK'):raise RuntimeError('CPU result missing')
 reviews={str(P/n):digest(P/n) for n in ('review_implementation_v2.md','review_experiments_v1.md','review_results_v1.md')}
 for n in ('learning_comparison_v1.json','evaluation_comparison_v1.json','setup_comparison_v1.json','trajectory_analysis_v1.json','advantage_diagnostic_v1.json','plot_inputs_v2.json'):
  doc=json.loads((P/n).read_text())
  if not doc['inputs_unchanged']:raise RuntimeError('producer input check '+n)
  for f,s in doc['inputs'].items():
   if digest(f)!=s:raise RuntimeError('producer input changed '+f)
 return dict(inputs=inputs,runs=runs,lifecycles=lifecycle,original_python_files_unchanged=original_py,reviews=reviews)


def main():
 result=checks()
 source_paths={p.resolve() for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}|{p.resolve() for p in P.glob('*.py')}
 source_paths|={ROOT/'guitar_learning/README.md',ROOT/'guitar_learning/SKILL_CURRICULUM.md',ROOT/'docs/plans/guitar_learning_skill_curriculum_20261018.md',ROOT/'stability_adapter_2/PLAN.md',ROOT/'stability_adapter_2/README.md',ROOT/'docs/2026-10-12/stability_adapter_2/README.md',ROOT/'docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md',P/'README.md'}
 source={str(p):digest(p) for p in sorted(source_paths)}
 write(P/'source_final_v1.json',dict(files=source,scope='current implementation/tests, all local producers and directly edited documentation; consumed input union is separate'))
 excluded={'artifact_inventory_v1.json','final_verification_v1.json'}
 artifacts={str(p):digest(p) for p in sorted(P.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts}
 write(P/'artifact_inventory_v1.json',dict(files=artifacts,scope='closed phase artifacts except this inventory and final verification to avoid circular hashes'))
 write(P/'final_verification_v1.json',dict(completed=True,research_goal_complete=False,runs=result['runs'],
  consumed_input_manifest_count=len(list(P.glob('*/inputs.json')))+len(list(P.glob('*/inputs_before.json'))),consumed_input_count=len(result['inputs']),consumed_inputs_unchanged=True,
  consumed_inputs=result['inputs'],original_python_files_unchanged=result['original_python_files_unchanged'],
  lifecycle_count=len(result['lifecycles']),native_scene_lifecycles=result['lifecycles'],cpu_tests=189,reviews=result['reviews'],
  source_manifest=dict(path=str(P/'source_final_v1.json'),sha256=digest(P/'source_final_v1.json'),count=len(source)),
  artifact_inventory=dict(path=str(P/'artifact_inventory_v1.json'),sha256=digest(P/'artifact_inventory_v1.json'),count=len(artifacts)),
  scope='completed stage implementation and bounded experiment comparison; all deterministic learned policy preparation tests failed; teacher contact/cross success is distinct; LH load independence and musical/acoustic completion unverified'))
 print(json.dumps(dict(completed=True,consumed_inputs=len(result['inputs']),artifacts=len(artifacts),sources=len(source),native_lifecycles=len(result['lifecycles']))))

if __name__=='__main__':main()
