# PALM_RATE 초기 스트랩 길이 조합 통합 검수

검수일: 2026-10-07. 범위는 새 저장 분석기·plotter, 현재 초기 audit·기대 reference·네 실행·여섯 비교행과 provenance, 계획·매뉴얼·결과·누적 문서다. 기존 동결 검수·코드·원자료를 수정하지 않았으며 reviewer native 실행·source query는 없다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 1N의 작은 기타 최대오차 감소와 LH 이탈 증가는 관측 tradeoff이며 새 길이 채택·안정화 성공의 근거가 아니다.

## 원자료·공통조건 독립 대조

- 초기 audit는 네 fresh 초기화/0 rollout step이고, 새 native는 1/2N 각각 24/120step의 네 fresh 실행·총288step이다. 실행 메타의 PALM_RATE mode·exit0·선언 출력 집합을 확인했다. 여섯 비교행 중 0N 두 행은 실제 기존 readback 0.1초·sensor 0.5초 기록 재사용이다.
- 기대 reference는 원본 초기/제어 필드와 audited LA를 담으며 해당 길이의 측정 통계가 아니다. Raw5 symlink는 quiescent 원본을 읽는 reference 입력이다. 실제 새 rollout과 baseline 재사용을 구별한다.
- 여섯 행의 native 13개 계약, 공통 full initial states와 q·목표·box, 25/121 표본·24/120 control 및 contact coverage와 6/30 update schedule을 대조했다. 각 길이의 states/trace/controls/contacts/hands/queries/leg_torques 7개 short prefix가 exact다.
- 네 새 실행 전체에서 전달 목표의 ±0.15rad cap·native/C02 box·0.02rad/update 및 네-tick hold와 단조 anti-windup mask 이력을 확인했다. 실제 scalar 한계 위반 약0.030297–0.030300°는 목표 제한과 구별된다.
- 기타 world p/q 오차·LH source-center 이탈·contact 행을 독립 재계산했다. LA 고정과 전체 pre-step route 위치·속도 기반 케이블 법칙, 다음 trace의 last-applied tension 및 초기법칙 장력도 일치한다. 0/1/2N label은 runtime 일정 장력이 아니다.

## 분석 보완·수치

Analyzer가 같은 PALM_RATE mode와 실제 short 어깨 contact0에 따른 hold selection을 명시 검증하도록 보완됐다. `comparison_validated.json`의 여섯 계약·136개 입력 SHA가 통과했고 최초 수치는 그대로다. 기존 producer는 최초 comparison의 SHA와 일치하는 별도 보관본으로 유지됐다.

0.5초 0/1/2N의 기타 최대오차는 36.091149/36.077130/36.087686 mm 및 4.761921/4.757473/4.770926°다. 1N−0N 최대값 간 차이는 −0.014019358 mm/−0.004447834°이며 LH 이탈은 +0.003779406 mm다. LH contact 행은 모두0이고 0.5초 RH 행은135/130/116이다. 행 수는 힘·연속 지지·인과 증거가 아니다.

## 최종 매체·문서

지원 plot CLI를 새 `/tmp` 출력에 실행해 2357×1453 canonical PNG byte/RGBA 일치, 136 upstream·7 direct·3 trace 및 producer/output SHA를 확인했다. 그림을 직접 열어 위 absolute scalar 오차와 아래 동일 시점 `1/2N−0N` scalar 차이의 단위·부호·전체 범위를 확인했다. 아래 곡선은 최대값 간 차이·변위 벡터·제어 보정량이 아니다.

README:9·13–24·34, CHANGED_FILES:4–12, VISUAL_REPORT:882·888·890, PALM_PRELOAD_COMPARISON:45·PLAN:979·adapter README:447의 수치·실행 수·현재 링크가 맞는다. 품질 매뉴얼:45–48은 모든 실제 값의 표시·비영 표기·raw exact 판단·실재 파일/줄 확인 규칙이며 물리·제어 조건을 바꾸지 않는다.

Source 중심과 landmark 기반 normal은 해부학적으로 교정된 접촉점·법선이나 물리 지지 인증이 아니다. 초기 각·root·기타 Z+5mm/기존 회전·PD/solver·PALM_RATE는 유지했고 새 길이는 채택하지 않는다. 1초는 미측정이며 0.5초 순위를 후기에 승계하지 않는다. 어깨 PD 변경도 승인 전·미적용이다. 현재 소단계 검수를 완료하며 본 runtime_review를 동결한다.
