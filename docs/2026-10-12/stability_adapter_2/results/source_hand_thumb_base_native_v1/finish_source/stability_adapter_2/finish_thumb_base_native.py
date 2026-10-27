"""Summarize four saved initial rejections and collect explicitly partial clips."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

R = Path(__file__).resolve().parents[1]
A = R/'stability_adapter_2'
D = R/'docs/2026-10-12/stability_adapter_2'
P = D/'results/source_hand_thumb_base_native_v1'
OLD = D/'results/fixed_strap_source_hand_initial_v1'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def lines(p): return [json.loads(s) for s in Path(p).read_text().splitlines()]
def save(p,d): Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def main():
    assert not (P/'analysis.json').exists() and not (P/'finish_execution.json').exists()
    old_index, new_index = D/'VIDEO_INDEX_v12.md', D/'VIDEO_INDEX_v13.md'
    update_path = D/'video_collection_update_v12.json'
    assert not new_index.exists() and not update_path.exists()
    proposal, batch = read(P/'proposal.json'), read(P/'native_batch.json')
    assert len(batch['attempts']) == 4 and batch['selected'] is None and batch['physical_steps'] == 0
    baseline = read(OLD/'native/initial_values.json')
    paths = {Path(__file__).resolve(), A/'SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md',
             A/'run_thumb_base_native_phase.py', A/'run_thumb_base_candidate.py',
             P/'proposal.json',P/'native_batch.json',P/'preparation_execution.json',old_index,
             OLD/'native/initial_values.json',OLD/'native/initial_grip_audit.json'}
    old_videos = sorted((D/'videos').glob('*.mp4'))
    assert len(old_videos) == 144
    paths.update(old_videos)
    for item in proposal['candidates']:
        label = item['label']; native = P/'native'/label
        paths.update([Path(item['trial_path']),Path(item['proposal_path']),P/(label+'_execution.json'),P/(label+'.log')])
        paths.update(native/n for n in ['initial_values.json','initial_grip_audit.json','report.json','capture.json','videos.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl'])
        capture, videos = read(native/'capture.json'),read(native/'videos.json')
        paths.update(Path(p) for frame in capture['frames'] for key in ['image_sha256','raw_image_sha256'] for p in frame[key])
        paths.update(Path(v['path']) for v in videos.values())
    before = {str(p):sha(p) for p in sorted(paths,key=str)}
    manifest = {}
    for p in sorted(paths,key=str):
        if p.suffix in ('.py','.md','.json'):
            dest = P/'finish_source'/p.relative_to(R)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
            assert sha(dest) == before[str(p)]
            manifest[str(p)] = dict(snapshot=str(dest),sha256=before[str(p)])
    save(P/'finish_source_manifest.json',manifest)
    checks = dict(preparation23_pass=len(proposal['checks']) == 23 and all(proposal['checks'].values()),
                  four_initializations_zero_steps_no_selection=batch['physical_initializations'] == 4 and batch['physical_steps'] == 0 and batch['selected'] is None)
    rows = []
    copies = []
    for item in proposal['candidates']:
        label = item['label']; native = P/'native'/label
        initial, audit, report = read(native/'initial_values.json'), read(native/'initial_grip_audit.json'), read(native/'report.json')
        execution = read(P/(label+'_execution.json'))
        candidate = read(item['proposal_path'])['rows'][0]
        names = initial['human_joint_names']; axis = names.index(item['name'])
        q = [initial['actual_initial_angles_rad'][n] for n in names]
        other = [i for i in range(len(names)) if i != axis]
        failed = [n for n,v in audit['checks'].items() if not v]
        checks[label+'_expected_zero_step_geometry_rejection'] = execution['exit_code'] == 1 and execution['terminal_state'] == 'initial_geometry_rejected_zero_steps' and report['completed'] is False and report['physics_steps'] == 0 and report['native_initializations'] == 1 and report['frame_count'] == 1
        checks[label+'_only_HG_fails15'] = len(audit['checks']) == 15 and failed == ['source_human_guitar_clear']
        checks[label+'_only_thumb2_overlap_self1188_cross_clear'] = len(audit['source_intersections']) == 1 and audit['source_intersections'][0]['human'] == 'LH:thumb2' and audit['source_intersections'][0]['guitar'] == 'guitar' and audit['complete_source_self_screen']['pair_count'] == 1188 and not audit['complete_source_self_screen']['intersections'] and not audit['cross_hand_intersections']
        checks[label+'_actual_q_declared_and_other80_exact'] = q == candidate['expected_initial_angles_rad'] == initial['initial_PD_target_rad'] and all(q[i] == baseline['initial_PD_target_rad'][i] and candidate['expected_absolute_targets_rad'][i] == baseline['preserved_absolute_targets_rad'][i] for i in other)
        checks[label+'_G_PD_LA_physics_exact'] = initial['native_initial_state']['guitar_body_states'] == baseline['native_initial_state']['guitar_body_states'] and initial['PD_properties'] == baseline['PD_properties'] and initial['physics_parameters'] == baseline['physics_parameters'] and initial['absolute_strap_rest_length_m'] == baseline['absolute_strap_rest_length_m'] == 1.1018469719600776
        checks[label+'_one_state_no_controls_contacts'] = len(lines(native/'states.jsonl')) == len(lines(native/'trace.jsonl')) == 1 and not lines(native/'controls.jsonl') and not lines(native/'contacts.jsonl')
        capture, videos = read(native/'capture.json'),read(native/'videos.json')
        checks[label+'_raw_overlay_readonly_SHA'] = len(capture['frames']) == 1 and capture['frames'][0]['physics_step'] == 0 and capture['frames'][0]['render_preserves_states'] and sum(len(capture['frames'][0][key]) for key in ['image_sha256','raw_image_sha256']) == 4 and all(sha(p) == h for key in ['image_sha256','raw_image_sha256'] for p,h in capture['frames'][0][key].items())
        checks[label+'_two_one_frame_partial_videos'] = set(videos) == {'hands','whole_body'} and all(v['ffmpeg_exit_code'] == v['ffprobe_exit_code'] == 0 and v['stream']['nb_read_frames'] == '1' and v['stream']['avg_frame_rate'] == '30/1' and abs(float(v['stream']['duration'])-1/30)<1e-6 and sha(v['path']) == v['sha256'] for v in videos.values())
        rows.append(dict(item,failed_initial_checks=failed,source_intersections=audit['source_intersections'],palm_up_proxy_z=audit['palm_up_proxy_z'],physics_steps=0,native_initializations=1))
        for view,v in videos.items():
            dest = D/'videos'/('source_hand_thumb_base_native_v1__'+label+'__ZERO_STEP_PARTIAL__'+view+'.mp4')
            assert not dest.exists()
            copies.append(dict(source=v['path'],copy=str(dest),sha256=v['sha256'],physics_steps=0,frames=1))
    checks['inputs_preserved'] = all(sha(p) == h for p,h in before.items())
    assert all(checks.values()),checks
    save(P/'analysis.json',dict(checks=checks,rows=rows,baseline_source_intersections=read(OLD/'native/initial_grip_audit.json')['source_intersections'],physical_initializations=4,physical_steps=0,five_second_stability_measured=False,actor_inference_calls=0,training_updates=0,scope='Four actual native t0 poses screened by source geometry; all failed before integration; LP radius is not PhysX penetration depth; no five-second stability measurement'))
    for v in copies:
        shutil.copy2(v['source'],v['copy'])
        assert sha(v['copy']) == v['sha256']
        v['size'] = Path(v['copy']).stat().st_size
    text = '# 영상 모음 갱신 v13 — 152개\n\n엄지 기저부4조건의 새8파일은 초기 형상 검사로 거절된 **0step·1frame·약0.033초 partial**이다. 5초 경과 영상이 아니다. 기존144영상과목록은보존했다.\n\n'
    text += '\n\n'.join('!['+Path(v['copy']).name+']('+v['copy']+')' for v in copies)+'\n\n'
    new_index.write_text(text+old_index.read_text())
    assert all(sha(p) == h for p,h in before.items()) and len(list((D/'videos').glob('*.mp4'))) == 152
    save(update_path,dict(previous_index_sha256=before[str(old_index)],new_index_sha256=sha(new_index),previous_video_sha256={str(p):before[str(p)] for p in old_videos},copies=copies,total_count=152,producer_sha256=sha(Path(__file__))))
    (P/'finish.log').write_text(json.dumps(dict(checks=checks,physical_initializations=4,physical_steps=0,total_collection_count=152),indent=2)+'\n')
    save(P/'finish_execution.json',dict(command=[sys.executable,'-m','stability_adapter_2.finish_thumb_base_native'],exit_code=0,terminal_state='completed',input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/'finish.log'),scope='Saved data and byte-identical video collection only; no simulator import or new physics'))
    print(json.dumps(dict(checks=len(checks),physical_initializations=4,physical_steps=0,total_collection_count=152)))


if __name__ == '__main__': main()
