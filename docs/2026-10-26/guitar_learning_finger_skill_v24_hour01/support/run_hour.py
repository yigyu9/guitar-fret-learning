"""Run the approved unchanged v24 pipeline with its existing one-hour budget."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
from types import SimpleNamespace


ROOT = Path('/home/ajou/yigyu/3')
RESULT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'


def main():
    source = ROOT/'docs/2026-10-26/guitar_learning_finger_skill_v24/support/source_manifest.json'
    manifest = json.loads(source.read_text())
    changed = [row['path'] for row in manifest
               if hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() != row['sha256']]
    if changed:
        raise RuntimeError('Validated source changed: '+str(changed))
    (RESULT/'support/source_manifest.json').write_text(source.read_text())
    import isaacgym
    from guitar_learning.training.start import settings_document, run
    settings = settings_document('left', physics='gpu', device='cuda:0', size='large',
        num_envs=1024, horizon=32, seed=7, updates=180, checkpoint_every=50,
        learning_family='finger-skill-v24', skill_phase='auto',
        skill_exploration='independent', skill_hold_ticks=1)
    settings['max_wall_seconds'] = 3600.
    args = SimpleNamespace(out=RESULT/'training', resume=None)
    print('START v24 auto large1024 H32 independent K1; pipeline wall budget3600s', flush=True)
    report = run(settings, args)
    print('END', report['stopped'], 'phase', report['final_phase'], flush=True)
    return {'stopped': report['stopped'], 'phase': report['final_phase'],
            'checkpoint': report['final_checkpoint'], 'pipeline_report': str(args.out/'report.json')}


if __name__ == '__main__':
    started = time.time()
    state = dict(status='running', pid=os.getpid(), started_unix=started)
    status_path = RESULT/'support/process_status.json'
    status_path.write_text(json.dumps(state, indent=2)+'\n')
    code = 0
    try:
        state.update(main())
        state['status'] = 'finished'
    except BaseException as error:
        code = 1
        state.update(status='error', error=type(error).__name__+': '+str(error))
        traceback.print_exc()
    finally:
        state.update(exit_code=code, ended_unix=time.time(), wall_s=time.time()-started)
        status_path.write_text(json.dumps(state, indent=2)+'\n')
    raise SystemExit(code)
