"""Document the saved zero-step rejection and collect its explicitly partial clips."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import sys

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/fixed_strap_source_hand_initial_v1'
OLD = D / 'results/initial_middle3_alignment_v1/native/initial_values.json'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(p): return [json.loads(s) for s in Path(p).read_text().splitlines()]
def save(p,d): Path(p).write_text(json.dumps(d,indent=2,allow_nan=False)+'\n')


def main():
    assert not (P / 'analysis.json').exists() and not (P / 'finish_execution.json').exists()
    old_index, new_index = D / 'VIDEO_INDEX_v11.md', D / 'VIDEO_INDEX_v12.md'
    update_path = D / 'video_collection_update_v11.json'
    assert not new_index.exists() and not update_path.exists()
    capture, videos = read(P/'native/capture.json'),read(P/'native/videos.json')
    old_videos = list((D/'videos').glob('*.mp4'))
    paths = [Path(__file__).resolve(), A/'SOURCE_HAND_INITIAL_EXECUTION.md',
        A/'FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md', OLD, old_index,
        P/'preparation.json',P/'proposal.json',P/'preparation_execution.json',P/'native_execution.json',
        D/'results/fixed_strap_source_compatibility_v1/joint_ranges.jsonl']
    paths += [P/'native'/n for n in ['initial_values.json','initial_grip_audit.json','report.json',
        'capture.json','videos.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl']]
    paths += old_videos + [Path(v['path']) for v in videos.values()]
    paths += [Path(p) for f in capture['frames'] for key in ['image_sha256','raw_image_sha256'] for p in f[key]]
    before = {str(p):sha(p) for p in paths}
    manifest = {}
    for p in paths:
        if p.suffix in ('.py','.md','.json'):
            dest = P/'finish_source'/p.relative_to(R)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,dest)
            assert sha(dest) == before[str(p)]
            manifest[str(p)] = dict(snapshot=str(dest),sha256=before[str(p)])
    save(P/'finish_source_manifest.json',manifest)
    initial,base = read(P/'native/initial_values.json'),read(OLD)
    audit,report = read(P/'native/initial_grip_audit.json'),read(P/'native/report.json')
    prep,proposal = read(P/'preparation.json'),read(P/'proposal.json')
    execution = read(P/'native_execution.json')
    states,trace = rows(P/'native/states.jsonl'),rows(P/'native/trace.jsonl')
    names = initial['human_joint_names']; changed = {v['name'] for v in prep['changes']}
    q = [initial['actual_initial_angles_rad'][n] for n in names]
    target = proposal['rows'][0]['expected_absolute_targets_rad']
    ranges = [json.loads(s) for s in (D/'results/fixed_strap_source_compatibility_v1/joint_ranges.jsonl').read_text().splitlines()]
    bound = {(v['kind'],v['name']):v for v in ranges if v['label'] == 'initial_aligned'}
    failed = [n for n,v in audit['checks'].items() if not v]
    checks = dict(preparation9_pass=len(prep['checks']) == 9 and all(prep['checks'].values()),
        gate_only_human_guitar_failed=failed == ['source_human_guitar_clear'] and len(audit['checks']) == 15,
        expected_exit1_zero_step_rejection=execution['exit_code'] == 1 and execution['terminal_state'] == 'initial_geometry_rejected_zero_steps',
        one_init_zero_steps=not report['completed'] and report['native_initializations'] == 1 and report['physics_steps'] == 0 and report['simulation_elapsed_s'] == 0,
        one_initial_state_no_commands_contacts=len(states) == len(trace) == 1 and states[0]['physics_step'] == 0 and not rows(P/'native/controls.jsonl') and not rows(P/'native/contacts.jsonl'),
        other76_initial_and_declared_held_exact=all(q[i] == base['initial_PD_target_rad'][i] and target[i] == base['preserved_absolute_targets_rad'][i] for i,n in enumerate(names) if n not in changed),
        actual_initial_q_expected_exact=q == proposal['rows'][0]['expected_initial_angles_rad'] == initial['initial_PD_target_rad'],
        initial_and_declared_held_all81_effective_ranges=all(bound[k,n]['effective_lower_rad'] <= value[i] <= bound[k,n]['effective_upper_rad'] for k,value in [('actual_initial',q),('held',target)] for i,n in enumerate(names)),
        fixed_LA=initial['absolute_strap_rest_length_m'] == base['absolute_strap_rest_length_m'] == 1.1018469719600776,
        G_full_initial_state_exact=initial['native_initial_state']['guitar_body_states'] == base['native_initial_state']['guitar_body_states'],
        PD_and_physics_exact=initial['PD_properties'] == base['PD_properties'] and initial['physics_parameters'] == base['physics_parameters'],
        no_FK_proposed_state='source_state' not in proposal['rows'][0] and audit['checks']['no_proposed_FK_state'],
        native0_frame_readonly=len(capture['frames']) == 1 and capture['frames'][0]['physics_step'] == 0 and capture['frames'][0]['render_preserves_states'],
        four_raw_and_overlay_PNG_exact=sum(len(capture['frames'][0][k]) for k in ['image_sha256','raw_image_sha256']) == 4 and all(sha(p) == h for k in ['image_sha256','raw_image_sha256'] for p,h in capture['frames'][0][k].items()),
        two_one_frame_partial_videos=set(videos) == {'whole_body','hands'} and all(v['ffmpeg_exit_code'] == v['ffprobe_exit_code'] == 0 and v['stream']['nb_read_frames'] == '1' and v['stream']['avg_frame_rate'] == '30/1' and abs(float(v['stream']['duration'])-1/30)<1e-6 and sha(v['path']) == v['sha256'] for v in videos.values()))
    assert all(checks.values()),checks
    analysis = dict(checks=checks,failed_initial_checks=failed,source_intersections=audit['source_intersections'],
        initial_changes=[dict(v,initial_delta_deg=math.degrees(v['initial_delta_rad']),held_delta_deg=math.degrees(v['held_delta_rad'])) for v in prep['changes']],
        physical_initializations=1,physical_steps=0,simulation_elapsed_s=0,actor_inference_calls=0,training_updates=0,
        five_second_stability_measured=False,scope='Actual initial-pose source geometry rejection; LP common radius is not PhysX penetration depth; held goals numerically validated but no post-gate command was submitted')
    save(P/'analysis.json',analysis)
    assert len(old_videos) == 142
    copies = []
    for view,v in videos.items():
        source = Path(v['path'])
        dest = D/'videos'/('fixed_strap_source_hand_initial_v1__ZERO_STEP_PARTIAL__'+view+'.mp4')
        assert not dest.exists()
        shutil.copy2(source,dest)
        assert sha(dest) == v['sha256']
        copies.append(dict(source=str(source),copy=str(dest),sha256=v['sha256'],size=dest.stat().st_size,physics_steps=0,frames=1))
    text = '# 영상 모음 갱신 v12 — 144개\n\n새 두 파일은 초기 형상 겹침으로 물리 진행 전 거절된 **0step·1frame·약0.033초 partial**입니다. 5초 경과 영상이 아닙니다. 아래 기존142영상과목록은그대로보존했습니다.\n\n'
    text += '\n\n'.join('!['+Path(v['copy']).name+']('+v['copy']+')' for v in copies)+'\n\n'
    new_index.write_text(text+old_index.read_text())
    assert all(sha(p) == h for p,h in before.items()) and len(list((D/'videos').glob('*.mp4'))) == 144
    save(update_path,dict(previous_index_sha256=before[str(old_index)],new_index_sha256=sha(new_index),previous_video_sha256={str(p):before[str(p)] for p in old_videos},copies=copies,total_count=144,producer_sha256=sha(Path(__file__))))
    log = json.dumps(dict(checks=checks,source_intersections=analysis['source_intersections'],physical_steps=0,total_collection_count=144),indent=2)+'\n'
    (P/'finish.log').write_text(log)
    save(P/'finish_execution.json',dict(command=[sys.executable,'-m','stability_adapter_2.finish_source_hand_initial'],exit_code=0,
        input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/'finish.log'),
        source_scope='stdlib saved analysis and byte-identical collection only; no simulator/actor/learning import'))
    print(log)


if __name__ == '__main__': main()
