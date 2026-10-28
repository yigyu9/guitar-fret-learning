# 검지128환경 사전 대조 실제 분석

- [x] root 전체3scene 종료 통보 뒤에만 `analyze.py --root-completed` 실행. 준비/원자료/생산소스/기존4환경 결과는 변경하지 않는다.
- [x] 최종1075핀·준비검수·실제launcher3×exit0·설정·105native 각128readback·controllercap·90쌍·source/alias/loader복원·장면닫기를 확인한다.
- [x] reference/zero/random128첫시도씩 전체384음원장·실패·원9보상과 env0 trace를 검산한다. 기존 검수된4환경 비교는 분모 확대의 관찰이며 인과효과/다른손가락/128seed로 부르지 않는다.
- [x] 봉인된 probe.acceptance로 원PLAN 조건을 그대로 재계산한다. random128도 전부 공개하며 필터/새문턱을 추가하지 않는다.
- [x] 기존 trace_audit를 재사용해 env0 60Hz 세phase의 selected4 actual/target·body1/2/3합력·손목·6gate를 재구성하고, arm12 requested/native target/actual의 bounds·추종차이를 추가한다. nearest 잔차/CPU gate 차이가 있으면 보존한다. 240Hz 음원장을60Hz로 재지급하지 않는다.
- [ ] 결과/입력SHA/작은그림을 `results_v1/`에 저장하고 독립 검수 `review.json`/`verification.json`을 연결한다. PASS 후 이 분석소스·PLAN·결과·검수까지 완전동결한다. 후속 학습 분석은 별도 learning_analysis/를 사용한다.
