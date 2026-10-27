# 독립 사전 검수 V2

요약 판정: **문제없음**. Critical 0건·Warning 0건. V2는 V1의 제어 물리를 유지하며 접촉 분류·로그 scope·사전 입력 SHA 누락을 새 소스로 수정한다. 실제 V2 안정성·재현성은 실행 후 검증 대상이다.

## Critical

없음.

## Warning

없음.

## Suggestion

- `/home/ajou/yigyu/3/stability_adapter_2/analyze_left_grip_release_cycle_v1.py:28`: 시간은 저장된 physics_step 대신 행 번호/240으로 산출하며 25행은 endpoint/contact step 동일성만 확인한다. 누락·중복 행이 있는 다른 실행을 재사용 분석할 때 오인하지 않도록 endpoint가1..N, effort가0..N−1, target이4step 간격인지 assert하는 작은 강화가 가능하다. 이번 V1 원자료는 검수자가 실제로3840개 연속 endpoint/effort와960개 연속 target을 확인했으므로 현재 결과에 오류는 없다.

## 확인한 변경 및 분석

- V1 대비 V2 diff를 확인했다. 궤적·IK·gain·finite cap·duration는 동일하고, 왼팔/손 접촉 분류·실제 상속 encode save patch·A/config.json 사전 SHA 추가·V2 진입점 선택만 바뀌었다. 기존 소스/원자료는 수정되지 않는다.
- `left_grip_release_cycle_v2.py:88`: LH: 전체와 L_Thorax/L_Shoulder/L_Elbow/L_Wrist만 분류하므로 L_Hip을 제외한다. 오른쪽 접촉 보조분류는 기존 범위를 유지한다.
- `left_grip_release_cycle_v2.py:130`: 실제 MRO encode 소유자인 tracking.save도 patch하므로 pre-cycle tracking 벡터가 left_cycle_efforts에 superseded된다고 명시한다. V1 검수 Warning의 원인을 해소한다.
- `run_left_grip_release_cycle_v2.py:39`: 직접 환경 config와 두 계획서·selected native actualinitial·OMmass source를 사전 pin에 포함한다. independent fresh_learning_v1 제외 조건을 유지한다.
- 제어는 사람 left12에만25N/2Nm 가상 task를 Jᵀ로 합산하고 각 모델 effort cap으로 제한한다. other69 effort/other48 target 검사 및 상속 guard·model/rate 제한을 유지한다. 기타 강제 힘·부착·상태 덮어쓰기 경로가 추가되지 않았다.
- Analyzer는 실제 원시 contact를 왼팔/손 body로 재분류하고 양의 lambda 엄지+다른 손가락 동시성만 잡기 지표로 세며, 모든 query contact(0lambda 포함)가 없는 연속 구간만 놓기로 센다. force closure나 압현 성공으로 과장하지 않는 scope다.
- BB 바디 중심을 actor-root와 구분해 단계 시작/초기/2초 대비 이동·SO3 회전을 계산한다. 실제 손목의 기타localY 이동 extent를 따로 저장한다.
- V1 실제 접촉 쌍을 확인했다: hold_A/B의 thumb3+index3 양의 접촉이 각각360표본씩 있으며 L_Hip은 분석에서 제외된다. 실제 endpoint1..3840 / effort0..3839 / target0..3836(step4)을 각각 확인했다.
- 세 새/분석 Python AST parse 통과. config strict JSON와 initial_candidate/native_reference SHA 검증 통과. 검수자 GPU 물리 실행은0회; V2 재현성은 root 실행 뒤 검증한다.

## 검수 파일 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/left_grip_release_cycle_v2.py`: `54bb38d2e7f8372dfd1a613c3b3ea6ceaf833e134f3ea1550cc4bf82bbaba335`
- `/home/ajou/yigyu/3/stability_adapter_2/run_left_grip_release_cycle_v2.py`: `1f90067a8ecabe9053ef0f1df64805926eb6ee4ab2f0a126bf6e2f2225c09ad0`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_left_grip_release_cycle_v1.py`: `b3af88cb1dca65462e39ab8c7cb7f6b721ea83a30ddd495aee4b021d5f0463e5`
- `/home/ajou/yigyu/3/stability_adapter_2/LEFT_GRIP_RELEASE_CYCLE_PLAN_V2.md`: `d041ec215135494cfc33fe75db12db6b984e0a00284bada66237a355efb3734c`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/config_v1.json`: `585ce83b94359b2275e40479bb14af9f3b584a4c61a5197427707089c5d2d88c`
