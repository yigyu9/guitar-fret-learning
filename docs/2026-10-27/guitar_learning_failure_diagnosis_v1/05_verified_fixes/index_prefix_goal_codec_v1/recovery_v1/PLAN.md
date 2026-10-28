# 목표각 fit 종료 기록 오류의 분리와 저장본 재사용 감사

2026-10-28. 원 fit child는34.572980315초 뒤 exit1이며 후속평가는 실행되지 않았다. 원 codec.py:221의 종료 감사가 import되지 않은 sys.modules를 참조했다. initial.pt·offline_errors.json·parameter_invariants.json은 저장됐으나 inputs_after.json/goal_codec_report.json은 없다. 정상 완료라고 재분류하지 않는다.

## 1. 원 실패와 산출물 CPU 감사

- 원2023 준비·source·reference128 독립PASS·02 parent/로그·fit 파일/모델을 그대로 보존한다. 원경로의 누락 보고서를 만들거나 원codec에import를추가하지 않는다. 재fit도하지않는다.
- 원 parent는 fit child1/exit1·evaluate없음이고 traceback의 유일한 오류가 해당sys NameError인지 고정 SHA와 확인한다. 다른오류·학습중오류·추가파일오염은 수용하지 않는다.
- 1000개 유한 손실, 원6구간·학습분할·목표label, 원fresh73 초기 동일성 근거, 저장73tensor 유한/허용변경·critic/std/나머지정확·cost2zero·PPO optimizer empty/update0·새GoalPolicy architecture/metadata·입력before현재SHA를 검산한다. CPU model 검산과 실제 native full strict load 근거를 구분한다.
- checkpoint의 저장 뒤 새GPU strict load를 수행하고 parameter_invariants를 기록한 다음finally에서 실패하는 원소스 흐름과 실제 산출물을 대조한다. 원보고서가 없다는 한계와 exit1을 새 collection_recovery/fit_recovery 기록에 명시한다. 원 모델 bytes/schema/metadata를 바꾸지 않는다.

## 2. 별도 evaluate 전용 준비와 검수

- 원 gate('fit')의 reference128/독립PASS/입력검증은 그대로 수행하고, 위 단일 알려진 종료 오류에 대한 새 독립 감사PASS를 추가해 evaluate만 허용한다. 전역strict 검사를 완화하지 않는다.
- 기존 GoalPool/GoalPolicy/원checkpoint의fullnative strict load·원9항/제어/범위/속도/guard·native105/90/원128기준을 사용한다. 원모델경로는 유지하고 평가출력만 recovery_v1/runs/evaluate로 분리한다. aliases는finally복원한다.
- CPU 준비·경계/오염/이중오류·출력보호 검사와 change-reviewer PASS 뒤 root만1회 평가한다. 새학습/기준변경/NN에참고각주입은 없다. 같은1000회 원incremental 비교와원실패를분리한다.

## 재발 방지와 완료 기준

문법 검사만으로 미정의 이름을 검출할 수 없다. 새코드는 가능한 정적미정의이름검사와 실제 종료 기록 경로의 관련 검사를 수행한다. 원오류를 고치지 않은 채 보존한 사실을 명시하고, 회복경로가 다른오류까지수용하지않는지검증한다. 종료자료가온전하지않으면평가를중단하고이유를보고한다.

- [ ] 원실패·1000회 모델 산출물 감사와 독립 검수
- [ ] evaluate전용 준비·명시적 회복수용·출력/strict 경계 검수
- [ ] root1회 NN-only128·실제 원장/기하/모델/원기준 분석·독립 검수
