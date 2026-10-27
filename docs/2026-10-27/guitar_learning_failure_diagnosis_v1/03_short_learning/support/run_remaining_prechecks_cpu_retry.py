"""Serialize GPU prechecks. Existing output directories must never be reused."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

PROJECT = Path('/home/ajou/yigyu/3')
ROOT = PROJECT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1'
OUT = ROOT/'03_short_learning'
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
MODULE = 'guitar_learning.tool.experiments.short_finger_learning'
ENV = dict(os.environ, PATH='/home/ajou/miniconda3/envs/rl38/bin:'+os.environ['PATH'],
    LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
    PYTHONPATH=str(PROJECT/'isaacgym/python')+':'+str(PROJECT))
tasks = [('smoke_wrist_pos_row8_cpu14_excluded', ['train', '--teacher', str(ROOT/'02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json'),
        '--mode','position','--initial-std','.01','--size','large','--num-envs','4','--horizon','32','--updates','1','--save-every','50','--seed','7'])]
for control in ('reference', 'zero', 'random'):
    args = ['evaluate','--checkpoint',str(OUT/'smoke_wrist_pos_row8_cpu14_excluded/initial.pt'),'--control',control,'--episodes','4']
    if control == 'reference':
        args += ['--reference',str(OUT/'reference_middle_row8_v2.json')]
    tasks.append(('smoke_wrist_pos_row8_cpu14_excluded_'+control,args))
script = Path(__file__)
before = hashlib.sha256(script.read_bytes()).hexdigest()
for name, args in tasks:
    command = [PYTHON,'-m',MODULE,*args,'--out',str(OUT/name)]
    with (OUT/'support'/(name+'.log')).open('x') as log:
        subprocess.run(command, env=ENV, cwd=str(PROJECT), stdout=log, stderr=subprocess.STDOUT, check=True)
    report = json.loads((OUT/name/'report.json').read_text())
    if not report['completed']:
        raise RuntimeError('Precheck incomplete: '+name)
    result = OUT/name/'evaluation.json'
    print(json.dumps(dict(task=name, report=report, summary=json.loads(result.read_text())['summary'] if result.exists() else None)), flush=True)
assert before == hashlib.sha256(script.read_bytes()).hexdigest()
