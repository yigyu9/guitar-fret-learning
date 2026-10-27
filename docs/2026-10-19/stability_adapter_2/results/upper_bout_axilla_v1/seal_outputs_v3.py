"""Audit exact input preservation, appended navigation prefixes and media copies."""
from pathlib import Path
import json,hashlib,re,ast
P=Path(__file__).resolve().parent
R=P.parents[4]
A=R/'stability_adapter_2'
OLD=R/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
PREV=R/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
D=R/'docs/2026-10-19/stability_adapter_2'
LEFT=D/'results/left_lean_axilla_v1'
BODY=D/'results/body_side_lean_axilla_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 with p.open('x')as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def main():
 assert A.exists() and (P/'review_final_v1.md').exists()
 updates=read(P/'navigation_update_v1.json');history=read(PREV/'navigation_update_v1.json')+read(LEFT/'navigation_update_v1.json')+read(BODY/'navigation_update_v1.json');prefixes={}
 for r in history+updates:prefixes[(r['path'],r['before_sha256'])]=r
 for r in updates:
  before=Path(r['before_snapshot']).read_bytes();after=Path(r['path']).read_bytes();assert sha(r['before_snapshot'])==r['before_sha256'] and sha(r['path'])==r['after_sha256'] and after.startswith(before)
  assert after.decode().splitlines()[r['append_heading_line']-1].startswith('##')
 preserved=[];seen=set()
 def verify(path,expected):
  key=(path,expected)
  if key in seen:return
  seen.add(key)
  if sha(path)==expected:preserved.append({'path':path,'expected_sha256':expected,'resolution':'current exact'});return
  row=prefixes.get((path,expected))
  assert row and row['before_sha256']==expected and sha(row['before_snapshot'])==expected,(path,'unexpected modification')
  preserved.append({'path':path,'expected_sha256':expected,'resolution':'exact original prefix snapshot of authorized append','snapshot':row['before_snapshot']})
 for f in sorted(P.glob('search_v*/inputs_before.json'))+sorted(P.glob('search_v*/inputs_before_v*.json')):
  for p,h in read(f).items():verify(p,h)
 for f in sorted(P.glob('native_v*/*/attempt.json')):
  for p,h in read(f)['input_sha256'].items():verify(p,h)
 for f in sorted(P.glob('analysis_v*/inputs_before.json')):
  for p,h in read(f).items():verify(p,h)
 for f in sorted(P.glob('baseline_source_probe_v*.json')):
  for p,h in read(f)['input_sha256'].items():verify(p,h)
 for f in sorted(P.glob('contact_region_v*.json')):
  for p,h in read(f)['input_sha256'].items():verify(p,h)
 for f in sorted(P.glob('result_summary_v*.json')):
  for p,h in read(f)['inputs_sha256'].items():verify(p,h)
 for f in sorted((P/'artifacts_v1').glob('provenance*.json')):
  data=read(f)
  for p,row in data.get('inputs_before',{}).items():verify(p,row['sha256'])
  for field in ('outputs','producer','inputs_after'):
   for path,row in data.get(field,{}).items():verify(path,row['sha256'])
  outputs=data.get('outputs_sha256_bytes',[])
  if isinstance(outputs,dict):
   for path,row in outputs.items():verify(path,row['sha256'])
  else:
   for row in outputs:verify(row['path'],row['sha256'])
 for row in read(D/'video/upper_bout_axilla_v1/manifest_v1.json')['videos']:
  verify(row['source'],row['source_sha256']);verify(row['destination'],row['copy_sha256']);assert row['ffprobe']['nb_read_frames']=='151'and row['ffprobe']['avg_frame_rate']=='30/1'
 for p,h in read(OLD/'source_final_v1.json').items():verify(p,h)
 for f in [OLD/'artifact_inventory_v1.json',D/'archive_inventory_v1.json',PREV/'artifact_inventory_v1.json',LEFT/'artifact_inventory_v1.json',BODY/'artifact_inventory_v1.json']:
  for row in read(f)['files']:verify(row['path'],row['sha256'])
 assert len(list(P.glob('native_v*/*/report.json')))==3 and len(list(P.glob('native_v*/*/failure.json')))==0
 for f in P.glob('analysis_v*/verification.json'):assert read(f)['passed']
 links=0
 docs=[P/'README.md',P/'CHANGED_FILES_v1.md']+list((P/'artifacts_v1').glob('*.md'))+list((D/'video/upper_bout_axilla_v1').glob('*.md'))
 for f in docs:
  text=f.read_text()
  for target in re.findall(r'\]\((/[^)]+)\)',text):
   target=re.sub(r':\d+$','',target);assert Path(target).exists(),(str(f),target);links+=1
 for f in A.glob('*upper_bout_axilla_v*.py'):ast.parse(f.read_text())
 ast.parse(Path(__file__).read_text())
 save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,'scope':'all current phase input maps, old phase source+7255-file inventory, previous 86-file archive and natural-right-arm1392/opposite-direction1982/body-side1337 inventories checked; changed navigation originals preserved as exact snapshots'})
 files=sorted(f for f in P.rglob('*')if f.is_file())+sorted(f for f in (D/'video/upper_bout_axilla_v1').rglob('*')if f.is_file())
 save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size}for f in files]})
 save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'links_checked':links,'native_complete_5s':3,'native_aborted':0,'training_runs':0,'initial_posture':'player-right4/6deg; guitarp/q fixed; source shoulder-side35percent closer to upper rounded bout','guitar_stability':'see result_summary_v2.json andcontact_region_v2.json; contact frequency is not support force; no final stability certification','authorized_navigation_appends':3,'review_path':str(P/'review_final_v1.md'),'review_sha256':sha(P/'review_final_v1.md')})
 print('passed',len(preserved),'preserved input versions;',len(files),'inventory files;',links,'links')
if __name__=='__main__':main()
