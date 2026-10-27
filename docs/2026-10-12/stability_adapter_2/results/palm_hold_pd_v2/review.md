# 왼팔 PD 배율 비교 독립 검수

검수일: 2026-10-08. 소유 범위는 이 검수 기록뿐이다.
구현·원자료·기존 동결 결과는 수정하지 않았으며 추가 native 실행은 하지 않았다.

## 요약 판정

**문제없음.** Critical 없음, Warning 해소, 남은 Suggestion 없음.
첫 runner의 setter bool 누락은 검증 누락 이력으로 보존했고 별도 verified runner가 false를 즉시 거절한다. v1을 실패 실행이나 소급 검증된 실행으로 바꾸지 않았다.

## 확인한 코드·원자료 범위

- 사전·원자료 검수에서 동일 full candidate/초기 상태/상수 목표/절대 LA를 확인했다. 왼팔12 stiffness/damping만 1/1.5/2배이며 effort·driveMode·limits 등 다른 property는 보존한다. setter 전후 state/Python 제출 target과 실제 property readback을 검사하며 native 목표 getter 인증을 주장하지 않는다.
- v2 분석 6계약·466 입력 SHA를 확인했고 세 조건의 초기 상태, PD 변경 범위, 같은 배율 v1의 states/trace/tasks/contacts/controls 5배열 exact, 좌표 차이·점 오차·기타 최대 오차·접촉 step/행을 독립 대조했다. 벡터화 norm 계산의 최대 마지막 자리 차이는 1.78e−15mm였다.
- v1 3init/72step과 v2 3init/72step은 각각 처음부터 시작한 실행이며 합계6init/144step이다. 앞선 관측2init/48step과 별개다. v2 초기 기본 Python import 실패의 producer/exit1/빈 stdout 파일은 보존됐고 stderr는 도구 반환 범위임을 명시한다. rl38 후처리는 exit0, 추가 native/physics는0이다.
- 기타 최대 p/q는 5.099186/0.972608, 5.630569/1.038888, 6.145012/1.100045mm/deg다. 종료 추적점은9.113399/9.024941/9.335708mm, source 법선 gap은9.047539/9.015126/9.271041mm다. 양의 palm raw lambda는 기준 step2 1행, 증가 조건 step1–2 5행이며 그 뒤 지속되지 않는다.

## 최종 미디어·문서

- canonical 2×2 PNG를 직접 확인했다. p/q·source gap은25개 상태, lambda는24개 완료 step 기록이며 t0 lambda를 만들지 않았다. mm/deg/비환산 lambda, 0–.1초 범위와 세 배율 범례가 올바르다. source gap을 cooked clearance, raw lambda를 N 또는 지속 지지로 표현하지 않는다.
- plotter는14개 실제 입력을 읽기 전에 봉인하고 종료 후 재검증한다. 현재14입력/producer/PNG SHA가 일치하고 기록된 plot/문법 검사 exit0을 확인했다. producer_attempt_v1/v2와 각 artifacts_attempt_v1/v2의 producer·PNG SHA는 당시 manifest와 일치한다.
- v2 README/CHANGED/IMPLEMENTATION_FILES/EXECUTION_NOTES, v1 안내와 메인 README:632·PLAN:1233, dated README:389·VISUAL §68:1228/그림92를 대조했다. 파일·줄 링크가 존재하며 검증 누락/후처리 실패/실제 native 실행을 구분한다. PALM_STIFFNESS_ONLY_PLAN은 kd 유지·kp만 변경하는 미실행 계획이다.

## 검토한 source SHA

- run_palm_hold_pd_verified.py: `b62f44f7d27307d7349bec4501bafa5baf02a9aa5bc1070abea0e256a5998b30`
- analyze_palm_hold_pd.py: `b711a189fc7e9a9eba91a5494bf5f1e5df76e64d886576698c66ba216ec937b1`
- plot_palm_hold_pd.py: `4d3e51877a0e6cee2d771f164a71d864adb8b770273c5838075635d9b31bacf9`

## 한계와 최종 상태

kp와 kd를 함께 바꾼 짧은 비교이므로 각각의 영향이나 포화·중력·구동 원인을 분리하지 않는다. 실제 몸통/관절 상태는 목표 유지와 구분하며 scalar 좌표 성분은 whole-joint SO(3)가 아니다. 손 추적점 개선만으로 기타 지지·장기 안정화·연주 성공을 선언하지 않고 gain 증가를 채택하지 않는 결론은 측정과 일치한다. 남은 actionable finding은 없으며 이 검수 기록을 최종 동결한다.
