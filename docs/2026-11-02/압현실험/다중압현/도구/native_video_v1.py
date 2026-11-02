"""One guarded native camera episode from the unchanged completed pilot model."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

MULTI = Path(__file__).resolve().parents[1]
STUDY = MULTI/'학습_인접2지_v1'
sys.path.insert(0, str(STUDY/'도구'))
from study_queue_v2 import ROOT, GPU_UUID, digest, verify_manifest, gpu_query
from parallel_resources_v1 import readiness, SINGLE_STATE, _state
from parallel_queue_v1 import impact, stop_own_group

MANIFEST = STUDY/'설계/native_video_v1.json'
PILOT = STUDY/'로그/parallel_v1/pilot_env2'
CHECKPOINT = PILOT/'J/final.pt'
OUT = MULTI/'로그/실제시뮬영상_v1'


def verify():
    manifest = verify_manifest(MANIFEST)
    video = manifest['native_video']
    report = json.loads((PILOT/'job_report.json').read_text())
    if (report.get('completed') is not True or report.get('job_id') != 'pilot_env2' or
            report.get('case_id') != 'index_middle_same' or
            Path(report['checkpoint']).resolve() != CHECKPOINT or
            report['checkpoint_sha256'] != digest(CHECKPOINT) or
            video['checkpoint_sha256'] != digest(CHECKPOINT) or
            video['environments'] != 1 or video['first_episode_only'] is not True or
            video['training_updates'] != 0):
        raise ValueError('Native video/pilot checkpoint identity mismatch')
    return manifest


def child():
    manifest = verify()
    ready, reason, resource = readiness()
    if not ready or os.environ.get('CUDA_VISIBLE_DEVICES') != GPU_UUID:
        raise RuntimeError('Native camera refused before Gym import: '+reason)
    import isaacgym  # Must precede Torch and NumPy.
    import torch
    from guitar_learning.portability import localize
    from run_job_v2 import runtime
    payload = torch.load(CHECKPOINT, map_location='cpu', weights_only=False)
    with runtime(MANIFEST, manifest) as runner:
        runner._validate_metadata_schema(payload['metadata'])
        runner._validate_pins(payload['metadata'])
        settings = localize(payload['metadata']['settings'])
        experiment = settings.get('experiment', {})
        if (experiment.get('case_id') != 'index_middle_same' or
                experiment.get('common_window_s') != [3.3, 4.8] or
                experiment.get('target_ids') != manifest['native_video']['target_ids'] or
                settings['song_training']['episode_duration_s'] != 5.5 or
                settings['song_training']['control_ticks'] != 330):
            raise ValueError('Native video target identity mismatch')
        from guitar_learning.tool.demonstration.render_finger_skill import render
        result = render(CHECKPOINT, OUT/'capture', scope='full_song', num_envs=1)
    verify()
    if not result.get('completed') or not result.get('native_pixels'):
        raise RuntimeError('Native camera capture/lifecycle verification failed')
    (OUT/'capture_resource_before.json').write_text(json.dumps(resource, ensure_ascii=False, indent=2))


def parent():
    manifest = verify()
    ready, reason, resource = readiness()
    if not ready:
        raise RuntimeError('Native camera resource gate: '+reason)
    OUT.mkdir(parents=True, exist_ok=False)
    baseline = _state()
    (OUT/'single_before.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2))
    command = [manifest['python'], '-B', str(ROOT/'scripts/tab2body.py'), '--cache-root',
               str(ROOT/'.runtime/cache'), 'run', str(Path(__file__).resolve()), '--child']
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=GPU_UUID, PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    started = time.monotonic(); process = None; failure = None; measured = None
    capture_report = None; final_state = None
    try:
        with (OUT/'native.stdout.log').open('xb') as stream, (OUT/'resources.jsonl').open('x') as samples:
            process = subprocess.Popen(command, cwd=str(ROOT), env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            query_errors = 0
            while process.poll() is None:
                verify()
                current = _state()
                measured = impact(baseline, current)
                if measured['severe']:
                    raise RuntimeError('Existing sweep delay/error guard: '+repr(measured))
                if time.monotonic()-started > 240:
                    raise TimeoutError('Single camera episode wall-time limit exceeded')
                try:
                    gpu = gpu_query('uuid,memory.free,utilization.gpu', 'gpu')
                    row = next(r for r in gpu if r['uuid'] == GPU_UUID)
                    free = float(row['memory.free [MiB]'].split()[0])
                    if not math.isfinite(free) or free < 2048:
                        raise MemoryError('Camera capture free GPU memory below2GiB')
                    query_errors = 0
                    samples.write(json.dumps(dict(epoch=time.time(), gpu=row,
                        single_finished=current['finished'], impact=measured))+'\n'); samples.flush()
                except (OSError, subprocess.TimeoutExpired, RuntimeError):
                    query_errors += 1
                    if query_errors >= 3:
                        raise RuntimeError('Repeated GPU monitoring failure')
                time.sleep(3)
        if process.wait() != 0:
            raise RuntimeError('Native camera failed; see native.stdout.log')
        capture_report = json.loads((OUT/'capture/report.json').read_text())
        if not capture_report['completed'] or not capture_report['native_pixels']:
            raise RuntimeError('Incomplete native camera report')
        verify()
        final_state = _state()
        measured = impact(baseline, final_state)
        if measured['severe']:
            raise RuntimeError('Final existing sweep delay/error guard: '+repr(measured))
    except BaseException as error:
        failure = repr(error)
        if process is not None:
            stop_own_group(process)
        raise
    finally:
        current = final_state if final_state is not None else json.loads(SINGLE_STATE.read_text())
        measured = impact(baseline, current)
        summary = dict(completed=failure is None, failure=failure, command=command,
            resource_before=resource, wall_s=time.monotonic()-started, impact=measured,
            native_pixels=bool(capture_report and capture_report.get('native_pixels') and capture_report.get('frames', 0) > 0),
            capture_completed=bool(capture_report and capture_report.get('completed')),
            training_updates=0, first_episode_only=True,
            source_manifest_sha256=digest(MANIFEST), checkpoint_sha256=digest(CHECKPOINT))
        (OUT/'guard_report.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        (OUT/'single_after.json').write_text(json.dumps(current, ensure_ascii=False, indent=2))
        print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', action='store_true')
    args = parser.parse_args()
    child() if args.child else parent()
