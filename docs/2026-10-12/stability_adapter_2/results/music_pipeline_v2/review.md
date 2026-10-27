# 39행동 음악 파이프라인 구현 검수

2026-10-15. change-reviewer의 읽기 전용 코드 검수다. 본 파일만 작성했고 구현·테스트·타 담당자 문서·이전 결과를 수정하지 않았다. 소스나 테스트를 직접 실행하지 않았으며, root가 보존한 검증 로그와 입력 SHA를 대조했다.

## 요약 판정

문제없음. 현재 우선05 곡을 사용하는 CPU 모듈·합성 통합 검증 범위에서 미해결 Critical 또는 실행 차단 사유를 발견하지 못했다. 검수 중 지적한 준비 dwell과 update 실패의 부분 상태 문제는 실행 전에 수정되었다. loader와 release의 제한은 공개 계약으로 관리한다. 이 판정은 native 물리 환경·기타 지지·곡 학습 성능의 인증이 아니다.

## 코드 확인

- [control.py:28](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/control.py:28): 왼팔12+왼손21+오른쪽 팔꿈치/손목6=39개의 정책 출력과 지지부15+오른손21+목/머리6=42개의 기준 목표 유지가 겹치지 않는 native81 집합을 이룬다. 이름으로 인덱싱하므로 native 배열 순서와 행동의 의미 순서가 달라도 제어권을 유지한다. 하체 DOF는 이81 벡터에 없다.
- [control.py:117](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/control.py:117): 기준각 주변의 비대칭 유효 범위, 평활화, 관절별 rate cap 순서가 맞다. held42의 오염을 조용히 수리하지 않고 거부한다. 외부 입력 배열 변경이 계약을 바꾸지 않도록 복사·read-only 처리하며 metadata에 q_ref·native 한계·rate·범위를 남긴다. 실제 관절/기타 state를 고정하거나 native API를 호출하지 않는다.
- [music.py:75](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/music.py:75): 선택 시작 인덱스와 연속 구간이 명시적이며 미지원 이벤트가 포함되면 ID와 함께 거부한다. 기존 코드의186D·4이벤트 metadata를 신규24필드/초 단위 창의 계약으로 오인하지 않도록 제거·대체했다. 서로 다른 owner의 같은 줄 audible 충돌은 거부하고 현재와 미래 준비 목표를 별도 record로 보존한다.
- [music.py:125](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/music.py:125): 기타 좌표계의 목표 상대 위치·속도를 caller가 제공해야 한다. 누락/비유한 값과 토큰 용량 초과는 오류다. 현재 종료가 가장 임박한 목표와 유효한 가장 가까운 strict deadline의 두 직접 경로가 추가되며, 동시에 유지 중인 나머지 목표도 attention 집합에서 사라지지 않는다.
- [music.py:203](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/music.py:203): 연속 유효 접촉시간은 준비 구간을 포함하고 held 시간만 audible 구간 교집합으로 적분한다. 측정 구간 중복을 거부하며 gap/invalid 접촉에서 연속성을 끊는다. 23.2ms 음에100ms의 최소 hold를 강제하지 않는다. 실제 측정 구간 전체의 유효성은 외부 환경의 책임이다.
- [music.py:225](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/music.py:225): ±50ms와 ±100ms에 별도 일대일 match 집합을 사용한다. 넓은 창의 조기 crossing이 좁은 창의 정시 기회를 소모하지 않는다. 동일 crossing ID 재사용과 한 ledger에서 한 crossing/target의 중복 사용을 막는다. 실제 crossing·기하·접촉 유효성은 caller가 검증한다.
- [policy.py:43](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/policy.py:43): actor/value encoder 파라미터가 분리되고 역할 출력은33/6이다. masked padding과 all-masked 집합의 null context가 처리된다. 현재/deadline 직접 특징은 pooling과 별도로 전달한다. 초기 actor mean0·log_std−3과 안정적인 tanh log probability가 구현되어 있다. 선형 출력 분할 자체를 별도 협력 알고리즘으로 주장하지 않는다.
- [ppo.py:31](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/ppo.py:31): terminal의 bootstrap은0이고 truncation의 마지막 실제 관측은 bootstrap하되 다음 에피소드의 GAE를 잇지 않는다. 음악/비용 advantage를 원단위에서 결합한 후 함께 정규화한다. 유한 비할인 episode budget에는 cost_gamma=1을 요구하며, 유효 완료/물리 실패 episode만 선택적 multiplier 갱신에 사용한다.
- [ppo.py:149](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/ppo.py:149): 매 actor minibatch 뒤 전체 rollout 상태에서 old→new analytic Gaussian KL을 확인한다. 초과 시 해당 actor/Adam을 복원하고 학습률을 줄여 유한 횟수 재시도하며, 소진하면 명시적으로 실패한다. 평균 sampled-state KL 기준을 개별 상태·제어기 출력이나 물리 안전 보장으로 설명하지 않는다.
- [ppo.py:93](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/ppo.py:93): critic 단계를 포함한 오류에서 전체 model·양쪽 optimizer·비용 계수·update count·Torch CPU/CUDA RNG를 복원한다. actor만 바뀐 채 이전 update count로 checkpoint가 남는 경로를 방지한다. [checkpoint 경로](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v2/ppo.py:200)는 신규 schema/architecture/input/control/config를 대조하고 model·두 Adam·비용 계수·counter·RNG를 저장한다. 기존 파일을 덮어쓰지 않으며, 이전54행동 schema는 거부한다.

## 검수 중 해결된 사항

1. 초기 구현은 audible overlap만 dwell에도 더해 onset 전 준비 접촉시간이0으로 보였다. 실행 전 수정본은 dwell과 held 적분을 분리했고 pre-onset 준비 회귀 검사가 추가되었다.
2. 초기 PPO는 value optimizer 오류 시 actor와 일부 critic/Adam이 변경된 상태로 이전 update count가 남을 수 있었다. 실행 전 전체 update transaction을 추가했다. value optimizer가 실제 한 step을 수행한 직후 강제 오류를 내는 회귀 검사에서 model·양쪽 Adam·Torch RNG·count의 복원을 확인한다.

두 수정은 최초 CPU 실행 이전에 이루어졌으며, 소비된 runtime 소스를 사후 수정한 것으로 설명하지 않는다.

## 실제 검증 기록

[cpu_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/cpu_v1/result.json)은26개 중24개 통과·2개 오류였다. 두 오류는 초기 자세 JSON의 PD_properties가 열별 배열인데 테스트가 행별 목록으로 순회한 fixture 문제다. 원래 test_control.py/test_integration.py와 실패 로그는 보존되어 있다.

runtime을 변경하지 않고 신규 test_control_v2.py/test_integration_v2.py와 검증 wrapper를 만들어 [cpu_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/cpu_v2/result.json)에서26개 모두 통과했다. 현재 검증 대상은 control8 + music9 + policy3 + PPO5 + integration1이다. root 보존 로그에서 GAE 경계, KL 실패의 기존 Adam 복원, value 실패 transaction, budget 설정, checkpoint/RNG 재개, 실제05 B/C/D 입력과39→81 목표 연결을 확인했다. 최초 실패가 없었던 것으로 바꾸거나 무차별 test discovery 전체가 통과했다고 주장하지 않는다.

최종 검증의 사전/사후 입력54개 SHA map이 같고, 현재 파일을 독립 재대조해 변경 없음을 확인했다. 보존된 wrapper는 Python AST 검사와 기존 native 입력1,333개의 무변경도 보고한다. 검수자가 테스트·native를 재실행하지는 않았다.

통합 테스트는 실제05 곡과 기존 후보의 이름·기준각을 읽지만,332D 상태·기하·보상·비용은 합성 fixture다. 이 테스트의 PPO step을 실제 물리 수집 또는 곡 학습 전이로 집계하지 않는다. 원래 native ABI나 최종 reset 자세를 확정한 결과도 아니다.

## 공개된 제한과 후속 연결 조건

- `from_bundle()`은 legacy B 선정 경로를 provenance에 재사용하므로 곡에 지원되는 단일 fretted B 후보가 필요하다. 현재05는 만족한다. B 후보가 없는 곡의 일반 C/D 지원은 아직 없다는 README 제한으로 관리하며, 다른 곡으로 확대하기 전 loader 계약을 보완해야 한다.
- `release(target_id,time)`는 caller의 최종 target retirement 선언이다. 순간적인 접촉 손실은 interval의 valid IDs로 표현한다. ledger가 해제 시각·물리적 손가락 분리 자체를 검증하지 않으므로 새 환경이 종료·실제 해제 조건을 검사해야 하고, released=True만으로 음악 성공을 판정하면 안 된다. README가 이 caller 계약을 명시한다.
- 지지부15와 오른손 그립21은 고정된 actuator 목표이며 실제 몸·기타의 고정이나 지지력·파지 인증이 아니다. 정책이 지지부를 능동 보정하는 권한은 현재 없다. 허벅지 지지는 외부 fixed-lower 자산·접촉 계약에서 검증해야 한다.
- 현재는 CPU 모델/ledger/목표/PPO 모듈 검증이다. 최종 물리 관측·좌표/scale·접촉 surface·실제 목표 도달·cost 단위/분모/실패 비용·budget·native 오류 처리는 새로운 환경 계약에 남아 있다. scalar multiplier 기능을 전체 안정성 제약 보장으로 해석하지 않는다.

[결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/README.md)는 위 한계와 이전54행동 파일럿을 구분한다. 현재 사용자 조건에 따른39행동 시작 구조의 구현은 확인했으며, 초기 자세 연구 완료 뒤 실제 상호작용과 음악·안정성 성능은 별도로 검증해야 한다.
