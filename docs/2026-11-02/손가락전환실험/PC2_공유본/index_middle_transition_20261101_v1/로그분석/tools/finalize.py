from pathlib import Path
import json,hashlib,datetime
L=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
state=json.loads((L/'status.json').read_text());assert len(state['completed'])==6
assert not json.loads((L/'identity_integrity.json').read_text())['changed']
for q in (L/'runs').glob('*/report.json'):
 x=json.loads(q.read_text());assert x['completed'] and x['failed_episodes_in_denominator'] and not x.get('failure') and not x.get('changed_inputs') and not x.get('cleanup_errors')
for q,n in [('analysis_tests_final.log',6),('related_tests.log',34)]:
 t=(L/'logs'/q).read_text();assert f'Ran {n} tests' in t and t.rstrip().endswith('OK')
for q in ('REPORT.md','FINDINGS.md','VIDEO_GUIDE.md','REVIEW_FINAL.md','summary.json','potential_check.json','identity_integrity.json'):assert (L/q).is_file()
now=datetime.datetime.now().astimezone().isoformat();state.update(stage='complete',current='',analysis_completed_at=now,report='REPORT.md',tests={'analysis_cpu':6,'related_existing_cpu':34},independent_review='REVIEW_FINAL.md',original_integrity={'sealed_files':13943,'artifact_files':756,'changed':0},new_training=False,adopted_changes=False,repeat_AB={'N32':[0,0,0],'N128':[1,28,56]},final_candidates='No adopted improvement; diagnostic proposals only')
(L/'status.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
(L/'PROGRESS.md').write_text(f'''# 진행 기록\n\n마지막 갱신: {now}\n\n현재 단계: 완료. 예상 종료 시각 대신 실제 종료 시각을 위에 기록했다.\n\n완료: 원본 지침/원장 검토,26개 평가 집계,6개 모델 identity/학습 지표,240Hz 관절/기하/접촉 시간 분해,mean32/128 각3회 추가 평가,정확한60Hz 보상항·할인potential 검산,독립 검수,관련40개 CPU 검사,원본 SHA 확인,9개 그래프와 보고서.\n\n결론: 평균 중지의 오정렬·자기 오압현,지원 축 요청 포화,128환경 평가 변동. 확정된 현상과 인과 가설은 FINDINGS/REPORT에서 분리했다.\n\n다음 작업: REPORT의 최대3개 후속 계획. 이번 요청에서는 추가 학습/보상·제어 변경/공유 코드 반영을 하지 않았다. 실행 중 GPU 작업은 남아 있지 않다.\n''')
files={str(p.relative_to(L)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(L.rglob('*')) if p.is_file() and p.name!='output_manifest.json'}
(L/'output_manifest.json').write_text(json.dumps({'schema':'index_middle.raw_analysis.outputs.v1','completed_at':now,'files':files},ensure_ascii=False,indent=2));print('analysis complete;',len(files),'analysis artifacts hashed')
