from pathlib import Path
import json,hashlib,datetime,sys
L=Path(__file__).resolve().parents[1];D=L.parent;R=next(p for p in L.parents if (p/'scripts/tab2body.py').exists())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(8*1024*1024),b''):h.update(c)
 return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
seal=json.loads((D/'보존/study_seal.json').read_text());art=json.loads((D/'보존/artifact_manifest.json').read_text());changed=[]
for base,files in [(R,seal['files']),(D,{p:v['sha256'] for p,v in art['files'].items()})]:
 for p,h in files.items():
  f=base/p
  if not f.is_file() or sha(f)!=h:changed.append(str(f))
assert not changed,changed
paths=[D/'진단/final128_seed17_mean',D/'진단/context_repeat_seed17_mean_128',D/'진단/base_seed17_u200_mean']+sorted((L/'runs').glob('*repeat[123]'))
records=[];ref=None
for p in paths:
 rep=json.loads((p/'report.json').read_text());settings=rep['settings'];pins=json.loads((p/'inputs_before.json').read_text());stable={k:v for k,v in pins.items() if not k.endswith('/settings.json')};ss={k:v for k,v in settings.items() if k!='num_envs'}
 if ref is None:ref=(settings,pins,ss,stable)
 # RNG restored from same checkpoint; actual runtime snapshot and all origins were not logged.
 records.append(dict(name=p.name,checkpoint_sha256=rep['checkpoint_sha256'],settings_digest=digest(settings),same_settings_as_old128=settings==ref[0],same_settings_except_num_envs=ss==ref[2],same_non_settings_input_pins=stable==ref[3],inputs_digest=digest(stable),num_envs=settings['num_envs'],seed=settings['seed'],action=json.loads((p/'action_mode.json').read_text()),scene=json.loads((p/'gpu_scene_initial.json').read_text()),report_sha256=sha(p/'report.json')))
out=dict(checked_at=datetime.datetime.now().astimezone().isoformat(),original_sealed_files=len(seal['files']),original_artifact_files=len(art['files']),changed=changed,study_seal_sha256=sha(D/'보존/study_seal.json'),artifact_manifest_sha256=sha(D/'보존/artifact_manifest.json'),records=records,source_git_head=(D/'보존/source_git_head.txt').read_text().strip(),environment_origin_limit='actual origin arrays not saved; scene.py:create_env uses ceil(sqrt(N)) columns; state coordinate contract environment-local; do not infer numeric-origin invariance from this alone')
(L/'identity_integrity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('original seal/artifacts unchanged',out['original_sealed_files'],out['original_artifact_files']);print([(r['name'],r['same_settings_except_num_envs'],r['same_non_settings_input_pins']) for r in records])
