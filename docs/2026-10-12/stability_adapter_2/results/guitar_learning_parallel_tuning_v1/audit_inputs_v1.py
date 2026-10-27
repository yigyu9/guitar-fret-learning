"""Root audit of existing native records; creates no physics or training."""
from pathlib import Path
import json,hashlib,gzip,xml.etree.ElementTree as ET
base=Path(__file__).resolve().parent;root=base.parents[4]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
errors=[];variants={};cases=[];reset_count=0;raw_count=0;raw_samples=0;static_reference=None;static_mismatch=[];mesh_paths=set();report_inputs={}
fields=('joint_names','human_body_names','guitar_body_names','loaded_assets','collision_policy','actual_shape_properties','zero_range_indices','position_indices','effort_indices','native_PD_properties','control_K105','control_D105','human_root_fixed','guitar_root_fixed','guitar_gravity_disabled','human_properties','guitar_properties')
for path in sorted(base.glob('*/report.json')):
 d=read(path)
 if 'collection_transitions_per_s' not in d:continue
 pins=read(path.parent/'inputs_before.json');report_inputs[str(path.resolve())]=sha(path);report_inputs[str((path.parent/'inputs_before.json').resolve())]=sha(path.parent/'inputs_before.json')
 for filename,h in pins.items():variants.setdefault(filename,set()).add(h)
 keys=('changed_inputs','missing_import_pins','original_source_parity_errors','missing_worker_audits','guard_violations','worker_failures','physical_flags_errors')
 if not d['completed'] or d['failure'] is not None or any(d[k] for k in keys):errors.append('invalid run '+str(path))
 if set(d['actual_imported_sources'])-set(pins):errors.append('import census gap '+str(path))
 episode_rows=[e for u in d['updates'] for e in u['completed_episodes']]
 logged=0;done=0
 with gzip.open(path.parent/'transitions.jsonl.gz','rt') as stream:
  for line in stream:
   row=json.loads(line);logged+=len(row['infos']);done+=sum(bool(t or u) for t,u in zip(row['terminated'],row['truncated']))
 if logged!=d['transitions'] or done!=len(episode_rows):errors.append('transition/end count mismatch '+str(path))
 initials=list(path.parent.glob('worker_*/audit_episode_*/initial_values.json'));reset_count+=len(initials)
 local_mesh=set()
 for f in initials:
  data=read(f);native=data['native']['native'];static={k:data[k] for k in fields}
  if native['physics_step']!=480 or len(native['human_dof_states'])!=105 or len(data['zero_range_indices'])!=8:errors.append('prepared schema '+str(f))
  if static_reference is None:static_reference=static
  elif static!=static_reference:static_mismatch.append(str(f))
  for asset in data['loaded_assets']:
   xml=Path(asset['path']).resolve();local_mesh.add(str(xml));tree=ET.parse(xml);compiler=tree.find('compiler');md=compiler.get('meshdir','') if compiler is not None else ''
   local_mesh.update(str((xml.parent/md/e.attrib['file']).resolve()) for e in tree.findall('./asset/mesh'))
 for f in local_mesh:
  if f not in pins or sha(f)!=pins.get(f):errors.append('actual declared mesh closure '+str(path)+' '+f)
 mesh_paths.update(local_mesh)
 raw_paths=list(path.parent.glob('worker_*/audit_episode_*/transition_*.json.gz'));raw_count+=len(raw_paths)
 for f in raw_paths:
  with gzip.open(f,'rt') as stream:data=json.load(stream)
  n=len(data['info']['physics_measurements']);raw_samples+=n
  if n!=4:errors.append('raw first tick samples '+str(f))
 cases.append(dict(run=path.parent.name,transitions=d['transitions'],logged_transitions=logged,completed_episodes=len(episode_rows),failure_episodes=sum(e['reason']=='terminal_failure' for e in episode_rows),resets=len(initials),worker_final_audits=len(d['worker_audits'])))
runner=str(root/'guitar_learning/train_parallel.py');old=root/'guitar_learning/archive/20261018_before_cuda_collection_timing/train_parallel.py';allowed={sha(old),sha(runner)}
changed=[]
for path,hashes in variants.items():
 if path==runner:
  if hashes!=allowed:errors.append('unexpected runner version')
 elif hashes!={sha(path)}:changed.append(path)
if changed:errors.extend('changed input '+p for p in changed)
if static_mismatch:errors.append('static native properties changed across resets')
archive_count=0;snapshot_count=0;archive_errors=[]
for manifest in [root/'guitar_learning/archive/20261018_before_parallel_tuning/archive_manifest.json',root/'guitar_learning/archive/20261018_before_cuda_collection_timing/archive_manifest.json',base/'source_run_v1_manifest.json',base/'source_run_v2_manifest.json',base/'main_docs_before_manifest.json']:
 data=read(manifest);rows=data['files'] if isinstance(data,dict) else data
 for row in rows:
  f=row.get('archived_path',row.get('preserved'));h=row['sha256']
  if sha(f)!=h:archive_errors.append(f)
  snapshot_count+=1
 if 'archive' in manifest.parts:archive_count+=len(rows)
if archive_errors:errors.append('archive/snapshot mismatch')
runtime_errors=[]
for row in read(base/'source_run_v2_manifest.json'):
 if row['path'].endswith('.py') and sha(row['path'])!=row['sha256']:runtime_errors.append(row['path'])
if runtime_errors:errors.append('post-pilot runtime source changed')
summary=read(base/'run_summary.json')
if any(sha(p)!=h for p,h in summary['sha256'].items()):errors.append('summary inputs changed')
ck=read(base/'pilot_checkpoint_analysis.json')
if ck['changed_inputs'] or any(sha(p)!=h for p,h in ck['input_sha256'].items()):errors.append('checkpoint analysis inputs changed')
if any(not r['all_finite'] for r in ck['rows']):errors.append('nonfinite model')
checks=read(base/'long_config_validation.json')
if not checks['settings_valid'] or not checks['strict_selected_checkpoint_load']:errors.append('long config validation failed')
if 'Ran 104 tests' not in (base/'cpu_tests_v2.txt').read_text() or not (base/'cpu_tests_v2.txt').read_text().rstrip().endswith('OK'):errors.append('CPU tests not passed')
result=dict(passed=not errors,errors=errors,cases=cases,native_runs=len(cases),transitions=sum(c['transitions'] for c in cases),learning_physics_samples=4*sum(c['transitions'] for c in cases),prepared_resets=reset_count,prepared_physics_steps=480*reset_count,total_physics_seconds=(4*sum(c['transitions'] for c in cases)+480*reset_count)/240,completed_episodes=sum(c['completed_episodes'] for c in cases),failure_episodes=sum(c['failure_episodes'] for c in cases),saved_full_raw_ticks=raw_count,saved_full_raw_physics_samples=raw_samples,all_reset_native_static_properties_equal=not static_mismatch,static_mismatch=static_mismatch,declared_mesh_and_xml_count=len(mesh_paths),declared_mesh_and_xml_paths=sorted(mesh_paths),project_input_paths=len(variants),versioned_inputs={p:sorted(v) for p,v in variants.items() if len(v)>1},versioned_input_scope='runner version1 exact archive and active version2 only; version2 adds CUDA collect-end synchronization',archive_files_checked=archive_count,preserved_files_checked=snapshot_count,archive_errors=archive_errors,runtime_errors=runtime_errors,input_versions={p:sorted(v) for p,v in variants.items()},report_sha256=report_inputs,scope='Existing records only, project Python imports and declared XML assets; no new native run, no full solver binary closure or longrun/music success certification')
(base/'input_audit.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('cases','input_versions','report_sha256','declared_mesh_and_xml_paths')},indent=2))
if errors:raise SystemExit(1)
