#!/usr/bin/env python3
"""Create a text-only corrected README V2; preserve all V1 media and records."""
from pathlib import Path
import hashlib, json, math

BASE=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1')
ART=BASE/'artifacts_v1'
VIDEO=Path('/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1')
IN=ART/'README_V1.md'; OUT=ART/'README_V2.md'; PROV=ART/'provenance_v2.json'; SCRIPT=ART/'build_archive_v2.py'
ANALYSIS=BASE/'native_analysis_v3.json'
HOLD_ROWS=BASE/'native_hold_v4/media/left_wrist_tracking_rows.json'
PAIR_ROWS=BASE/'native_pair_v1/media/left_wrist_tracking_rows.json'
PAIR_CONFIG=BASE/'native_pair_v1/media/left_wrist_tracking_configuration.json'
PAIR_REPORT=BASE/'native_pair_v1/report.json'
PAIR_ANALYSIS=BASE/'native_analysis_v3.json'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return h.hexdigest()
def rec(p):
 p=Path(p); s=p.stat(); return {'sha256':sha(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}

inputs=[IN,ART/'provenance_v1.json',VIDEO/'manifest_v1.json',VIDEO/'INDEX_V1.md',ANALYSIS,HOLD_ROWS,PAIR_ROWS,PAIR_CONFIG,PAIR_REPORT]
before={str(p):rec(p) for p in inputs}
text=IN.read_text(encoding='utf-8')
replacements=[
 ('이 자료는 왼손 33개 관절로 이루어진 초기 배치 후보 하나를 두고, native hold 네 조건과 두 체크포인트 연결 한 조건을 기록합니다. 다섯 조건은 초기 native 전체 상태가 같았고, 새 물리 실행·모델 변경·학습은 수행하지 않았습니다.',
  '이 자료는 앞서 수행된 native hold 네 조건과 두 체크포인트 연결 한 조건, 총 다섯 실제 native 실행의 기록을 정리합니다. 다섯 조건의 초기 native 전체 상태는 같았습니다. 이번 문서·미디어 정리 단계에서 추가 물리 실행은 0회이며, 새 모델 변경과 학습도 없습니다.'),
 ('`LH:palm`은 기타 기준 +X(넥 쪽), 엄지는 −Z(기타 뒤쪽)',
  '`LH:palm`은 기타 G 기준 +X(넥 아래면 쪽), 엄지는 −Z(기타 뒤쪽)'),
 ('hold_v4에서 손목 task는 인간 관절 토크 계산에 쓰인 가상 힘 요청이며 최대 요청 30 N입니다. 기타에 가해진 힘이나 접촉력 측정값이 아닙니다.',
  'hold_v4 손목 task의 30 N은 인간 관절 토크 계산에 쓰이는 가상 힘 요청의 상한입니다. 원본 `virtual_force_request_W_N` 1200개 행의 벡터 norm을 직접 계산한 최대 요청은 16.962012 N(step 577)입니다. 이 값은 기타에 가해진 힘이나 실제 접촉력 측정값이 아닙니다.'),
 ('26개 paired inference tick 뒤 총 물리 2.433333초, 584 step에서 첫 source 종료 조건으로 멈췄습니다.',
  '준비 구간은 physics step 0–479(2.0초)였고, step 480부터 손목 tracking task는 비활성화됐습니다. 그 뒤 26개 paired inference tick을 거쳐 총 물리 2.433333초, 584 step에서 첫 source 종료 조건으로 멈췄습니다.'),
 ('기록된 joint-resolved event는 2건, 현 crossing counter는 4건입니다.',
  '기록된 공동 음악 평가의 정산 event는 2건이며 두 건 모두 `joint_success=false`였습니다. 현 crossing counter는 4건입니다.'),
 ('손목 위치 과제 오차는 88.67049 mm였습니다. 이 연결 시험에서 hold4의 정지 결과를 재현하지 못했습니다.',
  '종료 직전 기록된 88.67049 mm는 step 583에서 비활성화된 손목 task의 초기 기타 G 기준 손목 목표에 대한 관측 이탈입니다. 활성 준비 과제의 추적 오차가 아니므로 hold4의 17 mm 추적 결과와 직접 비교하지 않습니다.'),
 ('다음 후보는 기타 기준 왼손 READY 상태를 준비 구간에 만들되, 손목·손가락 안전 제한을 유지하는 것입니다. 그 후속 시험은 이 자료에 포함되지 않습니다.',
  '다음 후보는 오른쪽 pick을 현재 기타 G 기준 READY 위치로 옮기고 현 교차에 진입시키면서, 왼쪽 Fret 손의 음별 압현을 확인하는 것입니다. 이 후속 시험은 이 자료에 포함되지 않습니다.'),
]
for old,new in replacements:
 assert text.count(old)==1, old[:100]
 text=text.replace(old,new)
text += '\n\nV2는 소비된 V1 설명의 범위·좌표 방향·손목 요청 힘 표기·연결 종료 해석을 바로잡은 문서입니다. V1, 그림, 원본 실행 자료, 영상 사본 및 manifest는 보존했습니다.\n'
# Compute force-request vector norm directly from source rows and verify documented value.
hold=json.loads(HOLD_ROWS.read_text())['rows']
force_values=[(math.sqrt(sum(float(v)**2 for v in row['virtual_force_request_W_N'])),row['physics_step']) for row in hold]
force_max,force_step=max(force_values)
assert abs(force_max-16.96201244486998)<1e-10 and force_step==577
pair=json.loads(PAIR_ROWS.read_text())['rows']
assert pair[480]['physics_step']==480 and pair[480]['enabled'] is False
assert pair[-1]['physics_step']==583 and abs(pair[-1]['point_error_m']-0.08867049094734)<1e-12
analysis=json.loads(PAIR_ANALYSIS.read_text())['cases']['native_pair_v1']
assert analysis['joint_resolved_events']==2 and analysis['joint_string_crossings']==4
OUT.write_text(text,encoding='utf-8')
after={str(p):rec(p) for p in inputs}
assert before==after
prov={
 'task':'README 문구 보완 전용; 소비 V1 및 미디어·manifest 불변',
 'physics_runs':0,'training_updates':0,'video_copies_or_reencodes':0,
 'correction_summary':[
  '문서 정리 단계의 추가 native 실행 0회를 과거의 다섯 실제 실행과 구분.',
  '손바닥의 G +X 방향을 넥 아래면으로 명시.',
  '30 N 요청 상한과 원본 rows에서 계산한 16.96201244486998 N 최대 요청을 구분.',
  'pair physics step 480/2초부터 wrist tracking 비활성화 및 종료점 88.67049 mm의 기준·해석 한계를 설명.',
  '양손 공동 음악 이벤트 용어와 후속 READY/압현 점검을 바로잡음.'
 ],
 'computed_from_raw_rows':{'source':str(HOLD_ROWS),'field':'virtual_force_request_W_N','norm_max_N':force_max,'physics_step':force_step},
 'inputs_before_after':{str(p):{'before':before[str(p)],'after':after[str(p)],'unchanged':before[str(p)]==after[str(p)]} for p in inputs},
 'producer':{'path':str(SCRIPT),'sha256':sha(SCRIPT),'bytes':SCRIPT.stat().st_size},
 'output':{'path':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size}
}
PROV.write_text(json.dumps(prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'README_V2':rec(OUT),'provenance_v2':rec(PROV),'producer_sha256':sha(SCRIPT),'inputs_pinned':len(inputs),'all_inputs_unchanged':all(x['unchanged'] for x in prov['inputs_before_after'].values()),'hold4_force_norm_max_N':force_max,'step':force_step},ensure_ascii=False))
