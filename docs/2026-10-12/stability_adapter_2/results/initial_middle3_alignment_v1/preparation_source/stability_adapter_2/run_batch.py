"""Sequential local trials, immutable inputs and restartable per-attempt records."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from .trial_settings import validate_settings, source_hashes


def manifest(value):
    if not isinstance(value,dict) or set(value)!={'control_steps','trials'}:
        raise ValueError('manifest requires control_steps and trials only')
    if type(value['control_steps']) is not int or value['control_steps']<0:
        raise ValueError('control_steps must be a nonnegative integer')
    if not isinstance(value['trials'],list) or not value['trials']:
        raise ValueError('trials must be a nonempty list')
    result = {'control_steps':value['control_steps'],'trials':[]}
    ids = set()
    for trial in value['trials']:
        if not isinstance(trial,dict) or set(trial)!={'id','initial_settings'}:
            raise ValueError('trial requires id and initial_settings only')
        name = trial['id']
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',name) or name in ids:
            raise ValueError('trial ids must be unique path-safe names')
        ids.add(name)
        result['trials'].append({'id':name,'initial_settings':validate_settings(trial['initial_settings'],require_length=True)})
    return result


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temp.replace(path)


def completed_report(path, trial, steps, hashes):
    report = json.loads(path.read_text())
    if (report.get('completed') is not True or report.get('initial_settings')!=trial['initial_settings']
            or report.get('control_steps')!=steps or report.get('source_sha256')!=hashes
            or not report.get('checks') or not all(report['checks'].values())):
        raise ValueError('completed report does not match the frozen trial: '+str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_batch(out, inputs, max_trials=None, resume=False):
    inputs = manifest(inputs)
    out.mkdir(parents=True,exist_ok=True)
    with (out/'.batch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        checkpoint = out/'checkpoint.json'
        fingerprint = hashlib.sha256(json.dumps(inputs,sort_keys=True,allow_nan=False).encode()).hexdigest()
        hashes = source_hashes()
        if checkpoint.exists():
            if not resume:
                raise FileExistsError('batch exists; use --resume with unchanged inputs')
            state = json.loads(checkpoint.read_text())
            if state['manifest_sha256']!=fingerprint or state['source_sha256']!=hashes:
                raise ValueError('resume refused: manifest or runtime sources changed')
            if json.loads((out/'manifest.json').read_text())!=inputs:
                raise ValueError('saved manifest was changed')
        else:
            if resume or (out/'manifest.json').exists():
                raise ValueError('no valid checkpoint; preserve partial batch and use a new directory')
            state = {'manifest_sha256':fingerprint,'source_sha256':hashes,'completed':{},'attempts':[]}
            save(out/'manifest.json',inputs)
            save(checkpoint,state)
        count = 0
        for trial in inputs['trials']:
            name = trial['id']
            if name in state['completed']:
                saved = state['completed'][name]
                digest = completed_report(out/saved['report'],trial,inputs['control_steps'],hashes)
                if digest!=saved['sha256']:
                    raise ValueError('completed report was modified')
                continue
            # A report may have committed just before the parent was interrupted.
            recovered = False
            for attempt in state['attempts']:
                path = out/attempt['path']/'report.json'
                if attempt['trial_id']==name and attempt['status']!='failed' and path.exists():
                    digest = completed_report(path,trial,inputs['control_steps'],hashes)
                    state['completed'][name] = {'report':str(path.relative_to(out)),'sha256':digest}
                    attempt['status'] = 'completed'
                    save(checkpoint,state)
                    recovered = True
                    break
            if recovered:
                continue
            if max_trials is not None and count>=max_trials:
                break
            previous = [a for a in state['attempts'] if a['trial_id']==name]
            for a in previous:
                if a['status']=='running':
                    a['status']='interrupted'
            directory = out/name/('attempt_'+str(len(previous)+1).zfill(4))
            # Preserve a directory created just before a checkpoint write was interrupted.
            number = len(previous)+1
            while directory.exists():
                number += 1
                directory = out/name/('attempt_'+str(number).zfill(4))
            directory.mkdir(parents=True,exist_ok=False)
            record = {'trial_id':name,'path':str(directory.relative_to(out)),'status':'running'}
            state['attempts'].append(record)
            save(checkpoint,state)
            save(directory/'settings.json',trial['initial_settings'])
            with (directory/'run.log').open('w') as log:
                process = subprocess.run([sys.executable,'-m','stability_adapter_2.run_trial',
                    '--settings',str((directory/'settings.json').resolve()),'--out',str(directory.resolve()),
                    '--steps',str(inputs['control_steps'])],stdout=log,stderr=subprocess.STDOUT,
                    pass_fds=(lock.fileno(),))
            record['returncode']=process.returncode
            record['status']='failed' if process.returncode else 'completed'
            if process.returncode==0:
                path=directory/'report.json'
                digest=completed_report(path,trial,inputs['control_steps'],hashes)
                state['completed'][name]={'report':str(path.relative_to(out)),'sha256':digest}
            save(checkpoint,state)
            if process.returncode:
                raise RuntimeError('trial failed; raw attempt preserved: '+name)
            count+=1
        print(json.dumps({'completed':len(state['completed']),'total':len(inputs['trials']),
                          'new_trials':count,'checkpoint':str(checkpoint)},indent=2))
        return state


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--max-trials',type=int)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.max_trials is not None and args.max_trials<0:
        parser.error('max-trials must be nonnegative')
    run_batch(args.out,json.loads(args.manifest.read_text()),args.max_trials,args.resume)


if __name__=='__main__':
    main()
