from pathlib import Path
import json
from datetime import datetime

b=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1')
f=b/'training_long_v1'
u=sorted(f.glob('update_*.json'))
r={'time':datetime.now().strftime('%H:%M:%S'),'updates':len(u)}
if u:
    a=json.loads(u[-1].read_text())
    r.update(committed=a['journal']['committed'],episodes=a['learning_total']['completed_episodes'],
        successes=a['learning_total']['quality_successful_episodes'],
        physical_failures=a['learning_total']['physical_failure_episodes'],
        last_success=a['learning_window']['quality_successful_episodes'],
        actor_lr=a['actor_lr'],kl_retries=a['kl_retries'])
p=f/'status.json'
if p.exists():
    s=json.loads(p.read_text())
    r['phase']={k:s.get(k) for k in ('phase','update_index','ticks')}
for n in ('final_deterministic_v1','final_stochastic_v1'):
    p=b/n/'result.json'
    if p.exists():
        a=json.loads(p.read_text())
        r[n]={'completed':a['completed'],'success':len(a['successful_cases']),'failure':a['failure']}
    else: r[n]=len(list((b/n).glob('case_*/partial_result.json')))
if (f/'report.json').exists():
    a=json.loads((f/'report.json').read_text())
    r['final']={k:a.get(k) for k in ('completed','stopped','failure','optimizer_updates','committed_updates_in_run')}

import os
log=b/'fresh_process_pid_observations_v1.jsonl'
seen=set()
if log.exists():
    for line in log.read_text().splitlines():
        a=json.loads(line);seen.add((a['pid'],a['start_ticks']))
active=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        args=(p/'cmdline').read_bytes().decode().split('\0')
        if 'guitar_learning.contact_recovery.run' not in args or '--case-index' not in args:continue
        out=Path(args[args.index('--out')+1])
        if str(b) not in str(out) or 'fresh6' not in str(out):continue
        stat=(p/'stat').read_text().split(') ',1)[1].split()
        a=dict(pid=int(p.name),ppid=int(stat[1]),start_ticks=int(stat[19]),out=str(out),protocol_case_index=int(args[args.index('--case-index')+1]),observed_local=datetime.now().isoformat())
        active.append(a)
        if (a['pid'],a['start_ticks']) not in seen:
            with log.open('a') as stream:stream.write(json.dumps(a)+'\n')
    except (FileNotFoundError,PermissionError,ValueError,IndexError):pass
r['fresh_active']=[{'pid':a['pid'],'protocol_case':a['protocol_case_index'],'out':Path(a['out']).parent.name} for a in active]
for name in ['baseline_fresh6_v1','final_fresh6_v1']:
    p=b/name/'result.json'
    if p.exists():
        a=json.loads(p.read_text());r[name]={'completed':a['completed'],'children':len(a['children']),'success':sum(c.get('successful_cases',0) for c in a['children']),'failure':a['failure']}
    elif (b/name).exists():r[name]=len(list((b/name).glob('process_*/result.json')))

print(json.dumps(r))
