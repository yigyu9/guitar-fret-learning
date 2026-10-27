"""Run current large/1024 finger skill until the requested KST morning deadline."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
from types import SimpleNamespace

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
DEADLINE = datetime(2026, 10, 27, 9, 0, tzinfo=KST)
SAVE_RESERVE_S = 120.
UPDATES_PER_RUN = 3000


def write(name, value):
    path = OUT/name
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def main():
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    state = dict(state='starting', pid=os.getpid(), started_at=datetime.now(KST).isoformat(),
        requested_stop_at=DEADLINE.isoformat(), save_reserve_s=SAVE_RESERVE_S,
        size='large', num_envs=1024, horizon=32, checkpoint_every=250,
        learning_family='finger-skill', wrist_termination='v2', runs=[], failure=None)
    write('status.json', state)
    try:
        manifest = json.loads((ROOT/'docs/2026-10-27/guitar_learning_wrist_recovery_v2/support/native_source_manifest.json').read_text())
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha for path,sha in manifest.items())
        write('source_manifest.json', manifest)
        write('launch.json', dict(**state, launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            initialization='fresh; no old checkpoint transfer',
            curriculum='initial3000-update budget; strict extensions preserve original25% exposure threshold',
            deadline_check='runner wall budget at update boundaries; reserve120seconds for final saving'))
        import isaacgym
        from guitar_learning.training.start import settings_document, run
        resume = None
        while True:
            available = (DEADLINE-datetime.now(KST)).total_seconds()-SAVE_RESERVE_S
            if available <= 0:
                state['state'] = 'deadline_reached'
                break
            index = len(state['runs'])+1
            current = OUT/('run_%02d'%index)
            settings = settings_document(size='large', num_envs=1024, horizon=32,
                updates=UPDATES_PER_RUN, checkpoint_every=250, seed=7)
            settings['max_wall_seconds'] = available
            state.update(state='running', active_run=str(current), resumed_from=str(resume) if resume else None)
            write('status.json', state)
            print('START', current, 'KST', datetime.now(KST).isoformat(), 'wall_budget_s', available, flush=True)
            report = run(settings, SimpleNamespace(out=current, resume=resume))
            stage = report['stages'][-1]['report'] if report.get('stages') else None
            if report.get('failure') or stage is None or not stage.get('completed'):
                raise RuntimeError('run did not finish with a verified saved stage; inspect its report')
            resume = Path(report['final_checkpoint'])
            assert resume.is_file()
            state['runs'].append(dict(path=str(current), checkpoint=str(resume), stopped=report['stopped'],
                updates=stage['updates_in_run'], transitions=stage['transitions']))
            state['final_checkpoint'] = str(resume)
            write('status.json', state)
            if report['stopped']=='wall_budget':
                state['state']='deadline_reached'
                break
            if report['stopped']!='updates_complete':
                raise RuntimeError('unexpected run stop: '+report['stopped'])
        state['ended_at']=datetime.now(KST).isoformat()
        write('status.json', state)
        print('FINISHED', state['state'], datetime.now(KST).isoformat(), flush=True)
    except BaseException as error:
        state.update(state='failed', ended_at=datetime.now(KST).isoformat(),
            failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()))
        write('status.json', state)
        raise


if __name__=='__main__':
    main()
