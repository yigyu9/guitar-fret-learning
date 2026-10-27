"""Preserve prior evidence and verify actual complete/partial native media and navigation."""
from pathlib import Path
import ast
import hashlib
import json
import re

P=Path(__file__).resolve().parent
R=P.parents[4];A=R/'stability_adapter_2';D=R/'docs/2026-10-19/stability_adapter_2'
B=P.parent/'waist_straighten_v1';V=D/'video/right_arm_wrap_upright_v1'

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)

def main():
    review=P/'review_final_v1.md'
    assert review.exists() and 'Critical: 0' in review.read_text()
    updates=read(P/'navigation_update_v1.json');assert len(updates)==3
    snapshots={}
    previous=read(B/'source_final_v1.json')['preserved']
    for row in previous:
        if row.get('snapshot'):snapshots[row['path'],row['expected_sha256']]=row['snapshot']
    for row in updates:
        before=Path(row['before_snapshot']).read_bytes();current=Path(row['path']).read_bytes()
        assert sha(row['before_snapshot'])==row['before_sha256'] and sha(row['path'])==row['after_sha256']
        assert current.startswith(before)
        assert current.decode().splitlines()[row['append_heading_line']-1].startswith('## ')
        snapshots[row['path'],row['before_sha256']]=row['before_snapshot']
    preserved=[];seen=set()
    def verify(path,expected):
        key=str(path),expected
        if key in seen:return
        seen.add(key)
        if sha(path)==expected:preserved.append({'path':str(path),'expected_sha256':expected,'resolution':'current exact'});return
        snapshot=snapshots.get(key);assert snapshot,(path,'unexpected modification')
        assert sha(snapshot)==expected and Path(path).read_bytes().startswith(Path(snapshot).read_bytes())
        preserved.append({'path':str(path),'expected_sha256':expected,'resolution':'exact prefix snapshot of authorized append','snapshot':snapshot})
    assert read(B/'final_verification_v1.json')['passed']
    for row in previous:verify(row['path'],row['expected_sha256'])
    for row in read(B/'artifact_inventory_v1.json')['files']:verify(row['path'],row['sha256'])
    for name in ('source_final_v1.json','artifact_inventory_v1.json','final_verification_v1.json'):verify(B/name,sha(B/name))
    source_rows=[]
    for folder in sorted(P.glob('search_v*')):
        result=read(folder/'search.json');source_rows+=result['rows']
        for name in ('inputs_before.json','discovery_before.json','guitar_xml_discovery_before.json'):
            for path,h in read(folder/name).items():verify(path,h)
        for path,h in result['input_sha256'].items():verify(path,h)
    assert len(source_rows)==21 and sum(r['accepted_for_native'] for r in source_rows)==4
    cases=sorted(P.glob('native_*/report.json'));assert len(cases)==7
    physics=controls=frames=completed=0
    for file in cases:
        folder=file.parent;report=read(file);attempt=read(folder/'attempt.json')
        for path,h in attempt['input_sha256'].items():verify(path,h)
        assert report['inputs_unchanged'] and not report['forbidden_calls']
        assert not report['strap_enabled'] and not report['checkpoints_connected'] and report['training_updates']==0
        physics+=report['physics_steps'];controls+=report['control_steps'];completed+=int(report['completed'])
        if not report['completed']:assert report['failure']['message']=='guitar safety displacement'
        capture=read(folder/'media/capture.json');assert capture['actual_strap_enabled'] is False
        assert capture['frames'][0]['physics_step']==0 and capture['frames'][-1]['physics_step']==report['physics_steps']
        for row in capture['frames']:
            assert row['render_preserves_states']
            for path,h in row['image_sha256'].items():verify(path,h);frames+=1
    assert (physics,controls,completed)==(3512,878,2)
    for name in ('timelines_final_v1.json','posture_final_v1.json','waist_final_v1.json'):
        for path,h in read(P/name)['input_sha256'].items():verify(path,h)
    timeline=read(P/'timelines_final_v1.json');assert timeline['passed']
    comparison=timeline['comparisons']['native_wrap55_elbow_wave']
    assert comparison['initial_full_state_and_first2p5s_trace_exact']
    assert abs(comparison['max_same_time_body_centre_difference_mm']-.4581259148095153)<1e-9
    assert abs(comparison['max_same_time_rotation_difference_deg']-.20099363415099772)<1e-9
    for label in ('native_wrap55_static','native_wrap55_elbow_wave'):
        row=timeline['cases'][label];assert row['completed_5s'] and row['physics_steps']==1200
        assert row['per_body_virtual_request_parameters']=={'R_Thorax':{'cap_N':10.,'depth_m':.004},'R_Shoulder':{'cap_N':20.,'depth_m':.008}}
        for field in ('chest_guitar_contacts','trunk_guitar_contacts','right_forearm_body_contacts','right_distal_guitar_contacts','head_guitar_contacts'):
            assert row['contacts'][field]['presence_steps']==0
        assert row['contacts']['right_upper_arm_body_contacts']['presence_steps']==1196
        assert row['contacts']['upper_full_raw_presence_steps']==181 and row['contacts']['upper_full_last120_presence_steps']==120
        waist=read(P/'waist_final_v1.json')['cases'][label]
        assert waist['waist_presence_steps']==waist['waist_positive_steps']==1198
        assert waist['waist_last120_presence_steps']==waist['waist_last120_positive_steps']==120
    for row in timeline['cases'].values():
        if not row['completed_5s']:assert row['body_centre_2_to_5s_mm'] is None and row['upper_last_half_second_presence_steps'] is None
    provenance=read(P/'artifacts_v1/provenance_v1.json')
    for row in provenance['native_source_inputs']+provenance['producers']:
        assert row['unchanged'] and row['sha256_before']==row['sha256_after'];verify(row['path'],row['sha256_before'])
    verify(provenance['manifest_path'],provenance['manifest_sha256'])
    manifest=read(V/'manifest_v1.json');assert len(manifest['video_copies'])==16
    for row in manifest['video_copies']:
        assert row['byte_exact'] and row['source_sha256']==row['copy_sha256']
        verify(row['source'],row['source_sha256']);verify(row['path'],row['copy_sha256'])
        assert Path(row['path']).stat().st_size==row['bytes']
        info=row['ffprobe'];assert (info['width'],info['height'],info['avg_frame_rate'])==(1280,720,'30/1')
        folder=B/'native_add8_static' if row['run']=='baseline_add8_static' else P/row['run']
        report=read(folder/'report.json');capture=read(folder/'media/capture.json')
        assert row['completed_5s']==report['completed'] and row['physics_steps']==report['physics_steps']
        assert int(info['nb_read_frames'])==len(capture['frames']) and abs(float(info['duration'])-len(capture['frames'])/30)<1e-6
    for row in manifest['derived_images']:verify(row['path'],row['sha256'])
    assert manifest['camera_comparison']['whole_body']['view_matrix_exact'] and manifest['camera_comparison']['whole_body']['projection_matrix_exact']
    docs=[P/'README.md',P/'CHANGED_FILES_v1.md',A/'RIGHT_ARM_WRAP_UPRIGHT_COMPLETION_V1.md',P/'artifacts_v1/README.md',P/'artifacts_v1/README_V2.md',V/'INDEX.md']
    links=0
    future={P/'source_final_v1.json',P/'final_verification_v1.json'}
    for file in docs:
        for target in re.findall(r'\]\((/[^)]+)\)',file.read_text()):
            path=Path(re.sub(r':\d+$','',target));line=re.search(r':(\d+)$',target)
            if path in future:links+=1;continue
            assert path.exists(),(file,path)
            if line:assert 1<=int(line[1])<=len(path.read_text().splitlines())
            links+=1
    for file in list(A.glob('*right_arm_wrap*.py'))+[P/'artifacts_v1/build_artifacts_v1.py',Path(__file__)]:ast.parse(file.read_text())
    save(P/'source_final_v1.json',{'preserved':preserved,'append_prefixes':updates,
         'scope':'prior waist-straighten preservation chain; current source/native/analysis/capture/artifacts and append-only navigation; prior historical source before-pin limits retained',
         'artifact_before_pin_limitations':'original artifact builder did not explicitly before-pin baseline two MP4s or font; baseline MP4 preservation is independently closed by the prior sealed inventory and native video hashes; font before rendering is not retroactively certified'})
    files=sorted(f for f in P.rglob('*') if f.is_file())+sorted(f for f in V.rglob('*') if f.is_file())
    save(P/'artifact_inventory_v1.json',{'files':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files]})
    save(P/'final_verification_v1.json',{'passed':True,'preserved_input_versions':len(preserved),'inventory_files':len(files),'links_checked':links,
        'raw_native_png_verified':frames,'source_proposals':21,'source_accepted':4,'source_rejected':17,
        'native_attempts':7,'native_execution_completed':2,'native_execution_partial':5,'native_total_physics_steps':physics,'native_total_control_ticks':controls,
        'video_copies':16,'derived_images':len(manifest['derived_images']),'training_updates':0,'authorized_navigation_appends':3,
        'review_path':str(review),'review_sha256':sha(review),
        'scope':'upright right upper-arm endcap visual candidate with one completed static and one elbow cycle; initial settling and left-hand support remain; no learning-default replacement, passive no-left-hand stability, music or repeatability certification'})
    print('passed',len(preserved),'input versions;',len(files),'files;',links,'links;',frames,'raw PNG')

if __name__=='__main__':main()
