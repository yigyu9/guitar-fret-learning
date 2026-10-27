# 06. StabilityAdapter 2 — 현행 목표와 통합 역할

> 상태: **자유 기타 환경·개별 source 전이/목표 합성 진단 구현 / 보정 학습·양손 지속 연주 미완료**

2026-10-10 전체 방향 반영. 이 문서는 마스터 플랜에서의 현재 모듈 역할이다. 구체 실행·수치·소단계 계획·구현은 [stability_adapter_2/PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1), 결과는 [산출물 모음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:1)을 따른다. [이전06 원문](/home/ajou/yigyu/3/master_plan/06_stability_adapter.md:1)은 보존된 이전 경로이며 현재 실행 조건이 아니다.

## 목표와 경계

Humanoid 초기 자세로 자유 기타의 시작 흔들림을 줄이고, 실제 압현·타현 중 기타를 사용자 허용 범위에 유지하며 이탈·미끄러짐을 관절 제어로 보정한다. 범위 내부의 작은 흔들림을 허용하고 초기 p/q로 정확히 복귀할 필요는 없다. 안정화는 음악 목표·score clock·운지 의미를 바꾸지 않으며 정지 안정성만으로 최종 성공을 선언하지 않는다.

Root/하체는 고정, Torso·Spine·Chest9관절은 기준 PD 목표 유지, Thorax부터 양쪽 손가락까지66관절을 주요 제어 범위로 한다. 주요 권한과 학습 action 차원은 다르다. 기타 고정·강제 손 부착·지속 pose 덮어쓰기·pose servo를 사용하지 않는다. WAIT → REACH → GRIP → TRANSPORT를 필수 과정으로 두지 않는다.

초기 손바닥 넥 아래면·엄지 뒷면·다른 손가락 전면 지지는 배치 선호다. 연주 중 손바닥과 모든 손가락의 지속 접촉은 강제하지 않는다. 기울어진 넥의 해당 지지 영역을 기준으로 접근·면 방향을 평가한다. 오른손은 연주 공간을 확보한다. 스트랩은 고정 길이 ON/OFF 등의 분리 비교 요인이며 한 조건의 실패를 전체 스트랩에 일반화하지 않는다.

## 필요한 관측과 보정 — 설계, 학습 manifest 미봉인

- 현재 기타 world actor-root p/q·속도와 허용 범위 여유/이탈.
- 현재 기타 기준 손목·목표 프렛·pick 접근 오차와 연주 공간.
- 관절 상태·최종 목표/편차·보정량/포화, 실제 확보한 접촉·미끄러짐 신호.
- Source 음악 readiness·실제 이벤트 결과·phase 요약. 성공은 actor의 선언이 아니다.

보정은 관절별 named target proposal로 제한한다. 원본 Fret/Strike transform을 유지한 음악 목표와 함께 중앙 제어기가 소유권·우선순위·cap·변화율·모델 한계를 적용해 하나의 최종 목표를 제출해야 한다. 실제 적용 목표와 source 정규화/history·EMA/PD 적용 순서를 일치시킨다. 기존 개별 native 목표 합성 진단을 완성된 양손 ActionArbiter runtime으로 간주하지 않는다.

허용 범위 내부에서는 특정 초기점 복원 비용을0으로 설계하고 음악 동작·자연스러운 자세를 우선한다. 경계 접근 시 부드러운 보정을 추가하고, 이탈하면 가까운 허용 상태로 복귀하는 방식을 검증한다. 작은 경계 교차/떨림으로 즉시 초기화하지 않는다. 실제 안전 중단 기준과 보정 한도는 소단계 시험에서 정하며 미검증 신호를 성공 gate로 사용하지 않는다.

## 현재 근거

- [Fret30 전이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/README.md:1): 압현 실패와 큰 초기 기타 이탈. 자산·구동/목표 계약 차이를 명시한 진단이다.
- [준비 팔9 목표 유지·Fret 손가락21](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md:1): 같은 시각 초기 이탈은 줄었으나 압현0%·유지0/27. 준비 팔 목표 고정을 최종 연주 방식으로 채택하지 않는다.
- [같은 제어의 기존 길이 스트랩 ON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md:1): 압현0%·유지0/4, PLAY 계산 장력0N. 첫 native crash 원인 미확정이며 완료 재시험과 구분한다.
- [Strike2초 전환](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md:1): 적시 타현1회 후 잘못된 타현으로 실패. 완주·양손 통합 근거가 아니다.

이 결과들은 CPU PhysX·Isaac Gym native camera 기록이며 원본 환경 성능/GPU 동등성 인증이 아니다. 원본 source qualification을 별도로 확인한다. 보정 학습은 아직 수행하지 않았다.

## 다음 실행과 검증

1. 원본 고정 기타 성능·자산/좌표/관측/action·PD/history 차이와 실행 자원을 확인한다.
2. 현재 기타 기준 왼손 손목·목표 프렛 오차와 접촉면을 시각화한다. 시각 mesh·원본 형상·PhysX 접촉을 구분하고 필요한 형상/물리 보정만 별도 버전으로 검증한다.
3. 손가락 정책을 보존하는 제한된 팔 접근 보정 OFF/ON으로 한 음 압현·유지를 평가한다. 한 번의 타현·이벤트 전환도 개별 검증한다.
4. 합성 계약·음악 보존을 확인한 뒤 작은 residual pilot, 공통 시간축의 짧은 구절·곡 통합으로 확대한다.

평가는 음악 성공·허용 범위 내 시간/최대 이탈/지속·복귀·slip/drop·관절/접촉·자연스러움을 분리한다. 현재 범위의 회전 집합 판정과 연속 시간 물리 안전은 미완료이며 초기 p/q 변화만으로 성공을 결정하지 않는다. Source checkpoint 시험은 최소2초 준비 후 원본 첫 done/보호 중단까지 시작부터 녹화한다. 실패·시간 초과·부분 영상과 정상 완료를 구분한다.
