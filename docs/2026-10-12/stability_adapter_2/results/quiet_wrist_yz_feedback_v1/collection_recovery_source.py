"""Verify saved collection outputs after a wrapper metadata failure; no rerun."""
from pathlib import Path
import hashlib
import json
import shutil

R = Path(__file__).resolve().parents[1]
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/quiet_wrist_yz_feedback_v1'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    output = P / 'collection_recovery.json'
    invocation = P / 'collection_recovery_invocation.json'
    snapshot = P / 'collection_recovery_source.py'
    assert not any(p.exists() for p in [output, invocation, snapshot])
    original = read(P / 'collection_invocation.json')
    manifest = read(P / 'collection_source_manifest.json')['files']
    update = read(D / 'video_collection_update_v16.json')
    paths = {Path(p) for p in original['input_sha256_before']}
    paths.update(Path(v['copy_path']) for v in manifest)
    paths.update(Path(v['copy']) for v in update['copies'])
    paths.update([Path(__file__).resolve(), P / 'collection_invocation.json', P / 'collection_wrapper_failure.json',
                  P / 'collection.log', D / 'VIDEO_INDEX_v17.md', D / 'video_collection_update_v16.json'])
    before = {str(p): sha(p) for p in sorted(paths, key=str)}
    shutil.copy2(Path(__file__).resolve(), snapshot); assert sha(snapshot) == sha(Path(__file__).resolve())
    save(invocation, dict(input_sha256_before=before, source_snapshot=str(snapshot),
        scope='ONE saved-output recovery audit; direct stdout, no collector or simulation invocation'))
    before[str(invocation)] = sha(invocation)
    failure = read(P / 'collection_wrapper_failure.json')
    checks = {}
    checks['original_wrapper_failure_honestly_preserved'] = (
        failure['wrapper_terminal_exit_code'] == 1 and failure['collector_exit_code'] is None
        and failure['collector_wall_seconds'] is None and not (P / 'collection_execution.json').exists()
        and sha(failure['wrapper_path']) == failure['wrapper_sha256']
        and sha(P / 'collection_invocation.json') == failure['invocation_sha256']
        and sha(P / 'collection.log') == failure['log_sha256']
        and failure['collector_reruns'] == failure['native_reruns'] == failure['analysis_reruns'] == 0)
    checks['all_original_prerun_inputs_current_exact'] = all(sha(p) == h for p, h in original['input_sha256_before'].items())
    checks['all_selected_source_copies_exact'] = all(sha(v['original_path']) == sha(v['copy_path']) == v['sha256'] == v['copy_sha256'] for v in manifest)
    checks['collector_source_and_archive_exact'] = (
        sha(R / 'stability_adapter_2/collect_wrist_yz_feedback_videos.py') == original['collector_sha256_before'] == update['producer_sha256']
        and sha(P / 'artifacts/collection_producer.sh') == sha(P / 'artifacts/collection_producer.sh.archived') == original['wrapper_sha256_before'])
    checks['166_prior_videos_and_index_preserved'] = len(update['previous_video_sha256']) == 166 and all(sha(p) == h for p, h in update['previous_video_sha256'].items()) and sha(D / 'VIDEO_INDEX_v16.md') == update['previous_index_sha256']
    checks['170_total_and_four_new_exact_copies'] = (len(list((D / 'videos').glob('*.mp4'))) == update['total_count'] == 170
        and len(update['copies']) == 4 and {(v['trial'], v['view']) for v in update['copies']} == {(c, w) for c in ['off', 'on'] for w in ['hands', 'whole_body']}
        and all(not v['partial'] and sha(v['source']) == sha(v['copy']) == v['sha256'] == v['copy_sha256'] for v in update['copies']))
    checks['new_index_exact_and_prior_content_retained'] = sha(D / 'VIDEO_INDEX_v17.md') == update['new_index_sha256'] and (D / 'VIDEO_INDEX_v17.md').read_bytes().endswith((D / 'VIDEO_INDEX_v16.md').read_bytes())
    checks['new_copies_native_video_metadata_complete'] = True
    for condition in ['off', 'on']:
        report = read(P / 'native' / condition / 'report.json'); videos = read(P / 'native' / condition / 'videos.json')
        checks['new_copies_native_video_metadata_complete'] &= report['completed'] and report['failure'] is None and report['physics_steps'] == 1200 and report['frame_count'] == 151 and not report['constraint_violations'] and all(report['checks'].values())
        for view, video in videos.items():
            stream = video['stream']
            checks['new_copies_native_video_metadata_complete'] &= video['ffmpeg_exit_code'] == video['ffprobe_exit_code'] == 0 and stream['nb_read_frames'] == '151' and stream['avg_frame_rate'] == '30/1' and abs(float(stream['duration']) - 151 / 30) < 1e-6 and sha(video['path']) == video['sha256']
    after = {p: sha(p) for p in before}; checks['inputs_unchanged'] = before == after
    assert all(checks.values()), checks
    save(output, dict(checks=checks, input_sha256_before=before, input_sha256_after=after,
        wrapper_terminal_exit_code=1, collector_exit_code=None, collector_wall_seconds=None,
        selected_source_copies=len(manifest), collector_reruns=0, native_calls=0, physics_steps=0,
        scope='Saved collection completeness and preservation verified; missing original collector exit/timing remain unknown, not reconstructed'))
    print(json.dumps(dict(checks=len(checks), videos=170, collector_reruns=0)))


if __name__ == '__main__': main()
