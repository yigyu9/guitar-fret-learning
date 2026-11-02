"""기존 PC1 결과를 CPU로 읽어 검토 스냅샷을 만든다. 원문에는 쓰지 않는다."""
import copy,csv,gzip,hashlib,json,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path('/home/ajou/yigyu/3')
OUT=Path(__file__).resolve().parents[1]
BASE=OUT.parent
RUN=ROOT/'docs/2026-11-02/압현실험/자율개선_20261101/runs_recovery'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def load(path):return json.loads(path.read_text())
def episodes(folder,n):
 meta=load(folder/'episode_metadata.json');rows={}
 for line in (folder/'episodes.jsonl').read_text().splitlines():
  row=json.loads(line)['episode']
  for field in meta['fields']:
   cur=row
   for key in field['path'][:-1]:cur=cur.setdefault(key,{})
   key=field['path'][-1]
   if key in cur:assert cur[key]==field['value']
   cur[key]=field['value']
  rows.setdefault(row['env_id'],row)
 assert set(rows)==set(range(n))
 return [rows[i] for i in range(n)]
def audit(row):
 folder=Path(row['metrics']['evaluation']);n=row['metrics']['episodes'];report=load(folder/'report.json')
 assert report['completed'] and report['lifecycle_verified'] and report['failed_episodes_in_denominator']
 assert not any(report.get(k) for k in ['failure','changed_inputs','missing_import_pins','cleanup_errors'])
 eps=episodes(folder,n)
 values=dict(A=0,B=0,AB=0,full_duration_pair=0,physical=0,wrist=0)
 for ep in eps:
  ledger=ep['left_note_ledger']['values'];physical=bool(ep['termination']['physical_failure']);wrist=bool(ep['termination']['wrist_failure']);safe=ep['valid'] and not physical and not wrist
  values['A']+=bool(ledger['left'][0]);values['B']+=bool(ledger['left'][1]);values['AB']+=all(ledger['left']) and safe
  values['full_duration_pair']+=all(v>=1.5-1e-8 for v in ledger['clean']) and safe
  values['physical']+=physical;values['wrist']+=wrist
 for key,val in values.items():assert val==row['metrics'][key],(folder,key,val,row['metrics'][key])
 # 전체240Hz에서 원래 on-time 정의를 독립 계산한다.
 ids=[ep['finger_control_diagnostics']['episode_id'] for ep in eps];tail=[[] for _ in eps];onset=[None for _ in eps]
 with gzip.open(folder/'finger_control_trace.jsonl.gz','rt') as f:
  for line in f:
   x=json.loads(line)['natural_preparation']['transition']
   for i in range(n):
    if x['all_env_episode_ids'][i]!=ids[i]:continue
    t=x['all_env_episode_time_s'][i];c=x['all_env_candidate'][i];w=x['all_env_wrong'][i]
    if 4.45-1e-8<=t<4.5-1e-8:tail[i].append(bool(c[0] and not w[0]))
    if onset[i] is None and t>=5.25-1e-8:onset[i]=bool(t<=5.25+1/240+1e-8 and c[1] and not w[1])
 values['on_time_with_previous_tail']=sum(len(t)>=11 and all(t) and bool(b) for t,b in zip(tail,onset))
 assert values['on_time_with_previous_tail']==row['metrics']['on_time_with_previous_tail']
 cp=Path(row['checkpoint']);result=dict(condition=row['condition'],seed=row['seed'],total=row['total'],mode=row['mode'],N=n,
  checkpoint=str(cp.relative_to(ROOT)),checkpoint_sha256=sha(cp),evaluation=str(folder.relative_to(ROOT)),
  settings=load(folder/'settings.json'),action_mode=load(folder/'action_mode.json'),
  recomputed=values,mean_clean_s=[sum(ep['left_note_ledger']['values']['clean'][j] for ep in eps)/n for j in range(2)])
 return result
progress=load(RUN/'progress.json');assert progress['status']=='complete'
records=[audit(row) for row in progress['results'].values()]
repeats=[]
for variant in ('control','conservative'):
 rows=[r for r in records if r['condition'] in (variant,variant+'_last_s7_u100') and r['seed']==7 and r['total']==100 and r['mode']=='mean' and r['N']==128]
 assert len(rows)==2
 assert rows[0]['checkpoint_sha256']==rows[1]['checkpoint_sha256'];assert rows[0]['settings']==rows[1]['settings'];assert rows[0]['action_mode']==rows[1]['action_mode']
 repeats.append(dict(variant=variant,checkpoint_sha256=rows[0]['checkpoint_sha256'],settings_equal=True,action_mode_equal=True,
  AB=[r['recomputed']['AB'] for r in rows],full_hold=[r['recomputed']['full_duration_pair'] for r in rows]))
manifest=load(BASE/'공유파일목록.json');differences=[];matches=[]
for name,expected in manifest['reference_project_files'].items():
 current=ROOT/name
 if current.is_file() and sha(current)==expected['sha256']:matches.append(name)
 else:differences.append(dict(path=name,current_exists=current.is_file(),pc2_sha256=expected['sha256'],pc1_sha256=sha(current) if current.is_file() else None))
# 현재 출력은 스냅샷으로만 보존하고 원본 상태는 갱신하지 않는다.
result=dict(checked_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),status=progress['status'],finished_at=progress['finished_at'],
 records=records,repeats=repeats,reference_code_matches=len(matches),reference_code_differences=differences,
 source_records={str(p.relative_to(ROOT)):sha(p) for p in [RUN/'progress.json',RUN/'summary.json',RUN/'ANALYSIS.md',RUN/'SOURCE_VERIFICATION.json']})
(OUT/'pc1_comparison_snapshot.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (OUT/'PC1_평가재검산.csv').open('w') as f:
 fields=['condition','seed','total','mode','N','A','B','AB','full_duration_pair','on_time_with_previous_tail','physical','wrist','checkpoint_sha256']
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
 for row in records:writer.writerow({key:row[key] if key in row else row['recomputed'][key] for key in fields})
print(json.dumps(dict(evaluations=len(records),repeats=repeats,code_matches=len(matches),code_differences=differences),ensure_ascii=False,indent=2))
