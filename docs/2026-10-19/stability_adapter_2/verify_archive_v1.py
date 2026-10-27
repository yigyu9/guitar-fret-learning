"""Verify copied archive, corrected video index and recorded root navigation append."""
from pathlib import Path
import hashlib,json,re,subprocess
N=Path(__file__).resolve().parent;R=N.parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):
 with(N/name).open('x')as f:json.dump(data,f,indent=2,ensure_ascii=False)
p1=read(N/'provenance_v1.json');p2=read(N/'provenance_v2.json');nav=read(N/'root_navigation_append_v1.json')
def historical(path):return Path(nav['snapshot'])if path==nav['path']else Path(path)
assert sha(nav['snapshot'])==nav['before_sha256']and sha(nav['path'])==nav['after_sha256'];assert Path(nav['path']).read_bytes().startswith(Path(nav['snapshot']).read_bytes())
for row in p1['output_files_sha256_bytes']:assert sha(historical(row['path']))==row['sha256']
for row in p2['v1_preservation']['records']:assert row['sha256_before']==row['sha256_after']==sha(historical(row['path']))
assert p1['copy_stage']['pin_inputs_before']==p1['copy_stage']['pin_inputs_after']and p2['direct_inputs_before']==p2['direct_inputs_after']
for pins in [p1['copy_stage']['pin_inputs_before'],p2['direct_inputs_before']]:
 for p,row in pins.items():assert sha(p)==row['sha256'],p
for row in p1['additional_direct_input_pins']:assert sha(row['path'])==row['sha256_before_finalization']==row['sha256_after_finalization']
for row in p2['new_outputs_sha256_bytes']:assert sha(row['path'])==row['sha256']
records=p1['copy_stage']['copy_records'];assert len(records)==61 and len({r['destination']for r in records})==61
for row in records:assert sha(row['source'])==row['sha256_before']==row['sha256_after']==sha(row['destination'])==row['copy_sha256']
focus=p2['focus_reference_copy'];assert sha(focus['source'])==focus['source_sha256_before']==focus['source_sha256_after']==sha(focus['destination']);assert sha(focus['source_readme'])==sha(focus['readme_copy'])==focus['source_readme_sha256']
by_source={r['source']:r for r in records};original={r['source']:r for v in (1,2,3)for r in read(R/'docs/2026-10-12/video/om_no_strap_upper_arm_v1'/('manifest_v%d.json'%v))['videos']};videos=read(N/'video/manifest_v2.json')['videos'];assert len(videos)==len({r['source']for r in videos})==len({r['destination']for r in videos})==22
streams=[]
for row in videos:
 expected=original[row['source']];assert row['destination']==by_source[row['source']]['destination']and row['view']==expected['view']and row['label']==expected['label'];assert sha(row['source'])==sha(row['destination'])==row['copy_sha256']==expected['source_sha256']
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate,duration','-of','json',row['destination']]))['streams'][0];assert info['nb_read_frames']=='151'and info['r_frame_rate']=='30/1';streams.append({'path':row['destination'],**info})
active=[N.parent/'README.md',N/'README.md',N/'guitar/README_v2.md',N/'posture/README_v2.md',N/'video/README_v2.md',N/'video/INDEX_v2.md',N/'data/README.md'];links=0
for p in active:
 for target in re.findall(r'\]\((/[^)\n]+)\)',p.read_text()):
  target=target.split('#',1)[0];match=re.search(r':(\d+)$',target);dest=Path(re.sub(r':\d+$','',target));assert dest.exists(),(p,target)
  if match:assert int(match.group(1))<=len(dest.read_text().splitlines())
  links+=1
prior=R/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1';pv=read(prior/'final_verification_v1.json');assert sha(prior/'artifact_inventory_v1.json')==pv['inventory_sha256'];assert all(sha(p)==h for p,h in read(prior/'source_final_v1.json').items())
review=N/'review_v1.md';assert review.exists()
files=sorted({p for p in N.rglob('*')if p.is_file()}|{N.parent/'README.md',R/'stability_adapter_2/OCT19_GUITAR_POSTURE_ARCHIVE_PLAN_V1.md'})
save('archive_inventory_v1.json',{'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in files]})
save('archive_verification_v1.json',{'passed':True,'copied_sources':63,'completed_videos':22,'candidate_videos':4,'diagnostic_videos':18,'video_source_destination_identity_checked':True,'video_streams':streams,'active_document_links_checked':links,'original_experiment_source_hashes_preserved':True,'original_inventory_sha256':pv['inventory_sha256'],'historical_root_index_preserved_with_append_record':True,'review_sha256':sha(review),'archive_inventory_sha256':sha(N/'archive_inventory_v1.json'),'new_physics_runs':0,'new_training_runs':0,'scope':'documentation/archive verification only; v1 erroneous metadata retained as history, v2 active'})
for row in read(N/'archive_inventory_v1.json')['files']:assert sha(row['path'])==row['sha256']
print(json.dumps({'passed':True,'videos':22,'copies':63,'links':links,'files':len(files)},ensure_ascii=False))
