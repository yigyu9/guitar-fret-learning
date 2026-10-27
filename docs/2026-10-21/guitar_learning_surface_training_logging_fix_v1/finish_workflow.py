"""Continue the authorized analysis/evaluation/video after training closes."""
from datetime import datetime, timezone
import hashlib
import json
from guitar_learning.training import json_io
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

PHASE = Path(__file__).resolve().parent


def process_identity(pid):
    try:
        fields = Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()
    except (FileNotFoundError, ProcessLookupError):
        return None
    return None if fields[0] == 'Z' else fields[19]


def status(stage, **fields):
    value = dict(stage=stage, updated_at_utc=datetime.now(timezone.utc).isoformat(), **fields)
    path = PHASE/'workflow_status.json'
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json_io.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    scripts = ['verify_training.py', 'analyze_training.py', 'evaluate_checkpoints.py', 'compare_evaluations.py', 'render_video.py']
    inputs = {str(PHASE/name): hashlib.sha256((PHASE/name).read_bytes()).hexdigest()
              for name in scripts+['finish_workflow.py', 'training_source_manifest.json']}
    with (PHASE/'workflow_inputs.json').open('x') as stream:
        json_io.dump(inputs, stream, indent=2)
    try:
        run = PHASE/'resume1550'
        pid = json.loads((run/'status.json').read_text())['parent_pid']
        identity = process_identity(pid)
        if identity is None:
            raise RuntimeError('Start the supervisor while its training process is alive')
        status('waiting_for_training', training_pid=pid, training_process_start=identity)
        while process_identity(pid) == identity:
            time.sleep(10)
        result = json.loads((run/'report.json').read_text())
        song = json.loads((run/'song_report.json').read_text())
        if not result['completed'] or not result['gpu_scene']['closed'] or not song['completed']:
            raise RuntimeError('Training did not complete and close normally; preserve its report')
        for name in scripts:
            changed = [path for path, expected in inputs.items()
                       if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected]
            if changed:
                raise RuntimeError('Postprocessing inputs changed: '+str(changed))
            status('running_'+Path(name).stem)
            environment = os.environ.copy()
            if name == 'render_video.py':
                environment.update(CUDA_VISIBLE_DEVICES='', MUJOCO_GL='osmesa', LIBGL_ALWAYS_SOFTWARE='1')
            with (PHASE/(Path(name).stem+'.log')).open('x') as output:
                subprocess.run([sys.executable, '-B', str(PHASE/name)], env=environment,
                               stdout=output, stderr=subprocess.STDOUT, check=True)
        status('completed', completed=True)
    except BaseException as error:
        status('failed', completed=False, error=repr(error), traceback=traceback.format_exc())
        raise


if __name__ == '__main__':
    main()
