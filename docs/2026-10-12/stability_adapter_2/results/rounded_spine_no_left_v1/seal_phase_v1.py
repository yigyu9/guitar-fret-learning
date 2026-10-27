"""Audit preservation and seal the completed rounded-spine comparison."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1';V=R/'docs/2026-10-12/video/rounded_spine_no_left_v1';OLD=P.parent/'upper_arm_static_support_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def exact(mapping):return all(Path(p).is_file() and sha(p)==h for p,h in mapping.items())
def main():
    checks={};verified=read(P/'verification_v1.json');checks['native_33_checks_and_analysis_inputs_exact']=verified['passed'] and exact(verified['input_sha256'])
    pins=read(P/'source_before_native_v2.json');checks['consumed_sources_unchanged']=exact(pins)
    checks['both_source_search_inputs_unchanged']=all(exact(read(P/f'search_v{v}/selected.json')['input_sha256']) for v in (1,2))
    correction=read(P/'right_hand_contact_audit_v1.json');checks['right_hand_companion_inputs_exact']=correction['passed'] and exact(correction['input_sha256'])
    records=[read(P/name) for name in ('main_append_v1.json','main_append_v2.json','main_completion_append_v1.json','main_correction_append_v1.json')];main_paths={e['path']:e for e in records[0]};old_inventory=read(OLD/'artifact_inventory_v2.json')['files'];preserved=[]
    for e in old_inventory:
        if e['path'] in main_paths:
            snap=Path(main_paths[e['path']]['snapshot']);preserved.append(sha(snap)==e['sha256'] and Path(e['path']).read_bytes().startswith(snap.read_bytes()))
        else:preserved.append(sha(e['path'])==e['sha256'])
    checks['previous_2590_files_exact_or_main_prefix_append']=all(preserved)
    chain=[]
    for i in range(4):
        entries=[part[i] for part in records]
        chain.extend(sha(e['snapshot'])==e['before_sha256'] for e in entries)
        chain.extend(Path(entries[j+1]['snapshot']).read_bytes().startswith(Path(entries[j]['snapshot']).read_bytes()) and entries[j]['after_sha256']==entries[j+1]['before_sha256'] for j in (0,1,2))
        chain.append(Path(entries[-1]['path']).read_bytes().startswith(Path(entries[-1]['snapshot']).read_bytes()) and sha(entries[-1]['path'])==entries[-1]['after_sha256'])
    checks['four_main_append_chains_preserved']=all(chain)
    image_count=0
    for entry in read(P/'native_v2/batch_report.json')['records']:
        out=Path(entry['output']);cap=read(out/'media/capture.json');images={}
        for frame in cap['frames']:images.update(frame['image_sha256']);images.update(frame['raw_image_sha256'])
        image_count+=len(images);checks[entry['label']+'_604_images_exact']=len(images)==604 and exact(images)
        checks[entry['label']+'_native_inputs_exact']=exact(read(out/'attempt.json')['input_sha256'])
        checks[entry['label']+'_300_contact_queries']=len(read(out/'contacts.json'))==300
    archive=read(V/'manifest.json')['files'];archive_ok=len(archive)==8
    for e in archive:
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,avg_frame_rate,duration','-of','json',e['destination']],text=True))['streams'][0]
        archive_ok&=sha(e['source'])==e['sha256_source']==e['sha256_destination']==sha(e['destination']) and probe['nb_read_frames']=='151' and probe['avg_frame_rate']=='30/1' and abs(float(probe['duration'])-151/30)<.002
    checks['eight_archived_videos_full_and_exact']=archive_ok
    provenance=read(P/'artifacts_v1/provenance_v1.json');checks['artifact_inputs_and_outputs_exact']=exact(provenance['input_sha256_before']) and exact(provenance['input_sha256_after']) and all(sha(e['path'])==e['sha256'] for e in provenance['outputs'])
    review=P/'review_final_v2.md';checks['independent_final_review_exists']=review.is_file() and review.stat().st_size>0
    docs=[P/'README.md',P/'README_V2.md',P/'CHANGED_FILES_V1.md',P/'CHANGED_FILES_V2.md',P/'artifacts_v1/README.md',V/'README.md',V.parent/'README_ABSOLUTE_V12.md']
    checks['new_links_exist']=all(Path(re.sub(r':\d+$','',t)).exists() for p in docs for t in re.findall(r'\]\((/[^)]+)\)',p.read_text()))
    assert all(checks.values()),checks
    source_dir=P/'source_final_v1';source_dir.mkdir(exist_ok=False);sources=[Path(p) for p in pins]+[Path(e['path']) for e in records[-1]]+[P/'analyze_native_v1.py',P/'audit_right_hand_contacts_v1.py',Path(__file__),P/'README.md',P/'README_V2.md',P/'CHANGED_FILES_V1.md',P/'CHANGED_FILES_V2.md',P/'review_preflight_v1.md',P/'review_preflight_v2.md',P/'review_final_v1.md',review,P/'artifacts_v1/make_rounded_spine_figures_v1.py'];manifest=[]
    for source in sources:
        target=source_dir/source.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());manifest.append({'source':str(source),'snapshot':str(target),'sha256':sha(source)})
    (source_dir/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    files=[p for p in P.rglob('*') if p.is_file()]+[p for p in V.rglob('*') if p.is_file()]+[V.parent/'README_ABSOLUTE_V12.md']+[Path(p) for p in pins]+[Path(e['path']) for e in records[-1]]
    inventory=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(files))];inventory_path=P/'artifact_inventory_v1.json';inventory_path.write_text(json.dumps({'files':inventory},ensure_ascii=False,indent=2))
    result={'passed':True,'checks':checks,'previous_files_preserved':len(old_inventory),'native_images_verified':image_count,'videos_verified':len(archive),'sources_snapshotted':len(manifest),'files_sealed':len(inventory),'artifact_inventory_sha256':sha(inventory_path),'source_manifest_sha256':sha(source_dir/'manifest.json'),'review_sha256':sha(review),'scope':'four completed five-second constant-q_ref PD trials; left-away conditions have zero left-arm contacts at300queries but guitar retention failed; original strapON, no runtime release/music/policy/training'}
    (P/'final_verification_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
