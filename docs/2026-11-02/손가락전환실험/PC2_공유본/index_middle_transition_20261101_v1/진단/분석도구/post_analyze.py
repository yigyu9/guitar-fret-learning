"""Read-only completed evaluation diagnostics; does not select or alter training."""
from pathlib import Path
import json,gzip,hashlib,collections,math
D=Path(__file__).resolve().parents[2];state=json.loads((D/'status.json').read_text());result={}
for record in state['results']:
 path=Path(record['evaluation']);m=record['metrics'];n=m['episodes'];ids={};meta=json.loads((path/'episode_metadata.json').read_text())
 for line in (path/'episodes.jsonl').read_text().splitlines():
  e=json.loads(line)['episode'];ids[e['env_id']]=e['finger_control_diagnostics']['episode_id']
 counts=[collections.Counter(),collections.Counter()];distance=[[],[]];height=[[],[]];A_pressed=[x['contact'] for x in m['notes']]
 with gzip.open(path/'finger_control_trace.jsonl.gz','rt') as stream:
  for line in stream:
   v=json.loads(line);e=v['natural_preparation']['transition']
   for i in range(n):
    if e['all_env_episode_ids'][i]!=ids[i]:continue
    t=e['all_env_episode_time_s'][i]
    for j,(a,b) in enumerate(((3.,4.5),(5.25,6.75))):
     if not a-1e-8<=t<b-1e-8:continue
     counts[j]['observed']+=1
     pos=e['all_env_position_geometry'][i][j];facing=e['all_env_facing_geometry'][i][j];loaded=e['all_env_assigned_loaded'][i][j];candidate=e['all_env_candidate'][i][j];wrong=e['all_env_wrong'][i][j];raw=e['all_env_raw_candidate'][i][j]
     bucket='position_missing' if not pos else 'facing_missing' if not facing else 'load_missing' if not loaded else 'wrong_veto' if wrong else 'effective_candidate' if candidate else 'other_rejection'
     counts[j][bucket]+=1;counts[j]['loaded']+=loaded;counts[j]['raw_positive']+=raw;counts[j]['wrong']+=wrong
     distance[j].append(e['all_env_distance_m'][i][j]);height[j].append(e['all_env_height_m'][i][j])
 nominal=n*360;summary=[]
 for j in range(2):
  c=counts[j];c['planned_physics_endpoints']=nominal;c['unobserved_after_failure']=nominal-c['observed'];assert c['unobserved_after_failure']>=0
  summary.append(dict(counts=dict(c),nearest_distance_mean_m=sum(distance[j])/len(distance[j]) if distance[j] else None,nearest_height_mean_m=sum(height[j])/len(height[j]) if height[j] else None,scope='nearest sample distance/height is separate from any-sample position/facing/load candidate flags; not mixed into a witness'))
 raw=json.loads((path/'metrics.json').read_text());first=[]
 from_sys=None
 # completed episode dynamic ledger values include contact_done; no metadata needed for these fields.
 for line in (path/'episodes.jsonl').read_text().splitlines():first.append(json.loads(line)['episode'])
 first.sort(key=lambda x:x['env_id']);qualified=sum(bool(x['left_note_ledger']['values']['contact_done'][0]) and t['release_by_B_onset'] for x,t in zip(first,m['transitions']))
 key=f"{record['profile']}_s{record['seed']}_u{record['updates']}_{record['mode']}";result[key]=dict(denominator=n,note_diagnostics=summary,absence_proxy_count=m['release_by_B_onset_count'],prior_contact_then_release_count=qualified,scope='absence alone is not successful release if A never contacted',trace_sha256=hashlib.sha256((path/'finger_control_trace.jsonl.gz').read_bytes()).hexdigest())
(D/'진단/causal_summary.json').write_text(json.dumps(dict(schema='index_middle.post_analysis.v1',analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),evaluations=result),indent=2))
lines=['# 검지→중지 실패 원인 분리','','완료된 평가만 읽기 전용으로 분석한다. 이 분석은 훈련 소스·평가 판정·사전 후속 선택 규칙을 바꾸지 않는다.','', '|평가|목표|위치탈락|방향탈락|하중탈락|오압현veto|유효후보|미관측|','|---|---|---:|---:|---:|---:|---:|---:|']
for key,v in result.items():
 for j,x in enumerate(v['note_diagnostics']):
  c=x['counts'];lines.append('|%s|%s|%d|%d|%d|%d|%d|%d|'%(key,'A' if j==0 else 'B',*[c.get(k,0) for k in ('position_missing','facing_missing','load_missing','wrong_veto','effective_candidate','unobserved_after_failure')]))
 lines.append(f"\n{key}: A압현경험후해제 {v['prior_contact_then_release_count']}/{v['denominator']}; 단순부재proxy {v['absence_proxy_count']}/{v['denominator']}.\n")
lines+=['','모든 표는240Hz endpoint 개수다. 연속clean이나음전체유지의적분지표를대체하지않는다. 판정위치/방향조건은동일표본결합을사용하고최근접거리표본과혼합하지않는다. 합력은특정충돌쌍·현압력과구분한다.']
(D/'문서/CAUSE_ANALYSIS.md').write_text('\n'.join(lines));print('diagnosed completed evaluations',len(result))
