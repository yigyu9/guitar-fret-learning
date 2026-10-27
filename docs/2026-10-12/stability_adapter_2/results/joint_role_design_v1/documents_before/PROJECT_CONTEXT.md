# 프로젝트 현재 상태 — 2026-10-10

## 최신 방향 변경 전신 관절 제어와 root 고정

사용자는 최종적으로 root를 제외한 전신 관절을 사용하며 초기 자세 유지도 제어 역할에 포함하기로 했다. 새 음악 환경은 하체 관절이 제거된 fixed-lower 대신 하체를 포함한 관절 feedback 제어를 목표로 한다. 연주 정책 출력39개와 기준 자세 유지66개를 합친105채널 목표·유한 PD 명령의 CPU 계약을 `music_pipeline_v3`에 구현하고5개 테스트를 통과했다. 원본 관절 한계가0인8축은 유지하므로105채널과97개의 비영 가동 범위를 구분한다.

현재 초기 자세 연구와 아래81채널 native 실행은 기존 조건으로 보존한다. 새로운105차원 초기 배치·물리 관측·native 제어 연결은 초기 자세 연구와 함께 후속 구현한다. 이번 결과를 이미 전신 native 제어·연주를 달성한 것으로 설명하지 않는다. 신경망이 모든 관절 목표를 학습한다는 주장과도 구분한다. [구현·검증과 논문 표현 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wholebody_control_v1/README.md).

## 2026-10-15 지지 자세 역할을 반영한39행동 파이프라인

가슴·오른쪽 상완·허벅지가 기타를 지지하고 오른손 손가락은 피크 그립을 유지하는 사용자 조건을 반영했다. 새 `music_pipeline_v2`는 왼팔·손33과 오른쪽 팔꿈치·손목6만 정책 출력으로 두며, 지지부15·오른손21·목/머리6의 목표각은 초기 기준을 유지한다. 실제 상태를 강제로 고정하는 것이 아니다. 왼손의 필수 기타 지지 목표는 부과하지 않는다.

음악24특징·진행8상태, 현재/임박 deadline 직접 경로, actor/value 파라미터 분리, 짧은 음과50/100ms 독립 기록, minibatch KL 제한과 전체 update 복원을 구현했다. CPU26개 테스트가 통과했고 기존 native 입력1333개는 보존됐다. 상세 환경·물리 관측 ABI·안정성 비용과 새 학습 연결은 초기 자세 확정 후 진행한다. 아래54행동 구현은 이전 실행 이력이다. [구현·근거·검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/music_pipeline_v2/README.md).

## 2026-10-15 선행 설계 검토와 사용자 답변

파이프라인 학습 가능성 검토 후 설계를 보완했다. 명시적 상대 목표 오차·연주 진행 상태, 짧은 음과 전환에 맞는 판정, 시간 기반 미래 창, 공동 actor/value 분리, 안정성 budget 목적과 첫-step KL 제어를 후보 설계에 반영했다. 실제 코드·선택 곡·관련 연구 근거와 비교 실험은 [상세 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pipeline_learning_design_v2/README.md)에 기록했다. 환경·학습 소스와 기존 결과는 변경하지 않았으며 성능 개선은 아직 실험하지 않았다.

최종 타이밍은 ±50ms를 주 지표로, ±100ms를 초기 진단으로 확정했다. 우선 곡은 `05_BN2-131-B_solo`로 변경했다. 안정적인 초기 자세 연구가 마무리되기 전까지 이 작업은 모델 파이프라인 설계에 집중한다. 이후 기존 fret·strike 환경 구조를 참고하여 새 환경을 상세 구현한다. 아래 첫 음악 파일럿은 이전 실행 결과이며 추가 환경 변경·native 학습을 즉시 계속하는 지시가 아니다.

[모델 파이프라인 설계 초안](/home/ajou/yigyu/3/docs/plans/music_model_pipeline_20261015.md) · [확정된 확인 사항](/home/ajou/yigyu/3/docs/FRESH_MUSIC_USER_REVIEW.md). 현재 추가 사용자 답변 대기 항목은 없다.

## 2026-10-15 이전 native 구현과 파일럿:54행동 음악 정책

이전 음악 파일럿의 재현 진입점은 `stability_adapter_2/fresh_music_v1/launch_v4.sh`다. 실제 오디오 유래 연주 계획과 native 상태744차원에서54개 관절 목표를 출력한다. 기존 정책 및 아래 Stage A 가중치를 가져오지 않고 scratch16갱신·4,096전이를 학습했으며 이번 실행의 오류·제외 전이는0개다. 단음·두 이벤트·8개 이벤트의 시간축을 연결했고, 실제 관절·기타 궤적과 영상을 저장한다. root·하체 고정, 자유 기타, 스트랩 OFF 조건이다.

동일 단음 단회 평가에서 목표 marker 평균거리154.192→154.101mm로 실질 개선은 미미하고, 접촉·기하 유지0초다. 연주 성공과 전신 동적 제어는 아직 입증하지 않았다. 후속 과제는 약15cm의 첫 프렛 도달 가능성·접근/접촉 학습 구조와 높은 PPO 변화량을 검증하는 것이다. 현재 새 음악 checkpoint는 `fresh_music_v1/pilot_b16_v4/checkpoint_0016.pt`이며 아래 Stage A checkpoint와 과제·관측 계약이 다르다.

[최신 구현·결과·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/README.md) · [사용자 확인 사항 한 곳](/home/ajou/yigyu/3/docs/FRESH_MUSIC_USER_REVIEW.md). 아래 항목은 이전 연구 이력으로 보존한다.

## 2026-10-14 최신 사용자 변경: 기존 정책 없이 새 학습

기존 Fret·Strike 및 잔차 가중치를 더 이상 새 학습에 사용하지 않는다. 기존 파일은 재현용으로 보존한다. `stability_adapter_2/fresh_learning_v1/`의 공유 Actor(support15/fret33/strike6)·보상/비용 Critic 두 개를 새로 초기화해 Stage A 지지·작은 손 이동부터 학습한다. 몸통9개도 제한된 정책 제어 범위에 포함한다. 루트·하체 고정, 내부 충돌, 스트랩 OFF, 자유 기타 조건과 PD·중력 보상·제한된 근위부 지지 제어는 유지한다. 이 단계는 압현·타현·곡 연주 성공을 뜻하지 않는다.

2026-10-15 첫 Stage A 파일럿: 누적64갱신·16384개 학습 전이를 완료했다. 검증 오류4구간367개 전이는 제외해 보존했다. 단회5초 평가에서 palm RMS20.438→6.772mm였다. 현재 체크포인트는 새 학습 결과의 `recovery64_v1/checkpoint_0064.pt`다. 물리 검증 잔차의 원인과 다수 목표 일반화는 미해결이며 실제 음악 과제로 확장하기 전 확인이 필요하다.

최신 실행 상태와 재시도·저장 정책은 [새 학습 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/README.md), 세부 계약은 [새 학습 계획](/home/ajou/yigyu/3/docs/plans/fresh_guitar_learning_20261014.md)을 따른다. 아래 고정 기타 정책 전이·Residual 연결 방향은 이전 이력으로 보존한다.

오디오→탭·운지→Fret·Strike→동기화→기타 안정화→전신 연주가 전체 흐름이다.
전체 목표·우선순위·검증 순서는 [전체 연구 메인 계획](/home/ajou/yigyu/3/master_plan/README.md:14), 실행 환경은 [README](/home/ajou/yigyu/3/README.md:1)를 따른다.

## 현재 작업: 자유 기타 연주 전이와 안정화

- 새 실험·구현·계획은 `stability_adapter_2/`, 결과·로그·이미지·영상은 `docs/2026-10-12/stability_adapter_2/`에 저장한다.
- 목표는 사용자 허용 범위 안에서 실제 압현·타현을 수행하는 것이다. 초기 p/q의 정확한 복귀나 WAIT → REACH → GRIP → TRANSPORT를 필수 과정으로 두지 않는다.
- Humanoid root·하체는 고정, Torso/Spine/Chest 9관절은 PD 목표 유지, Thorax 이하 양팔·양손66관절은 주요 제어 범위다. 가동 권한과 학습 action 차원은 구분한다.
- 기타는 자유 물리 상태다. 기타 고정·강제 손 부착·지속 pose 덮어쓰기·기타 pose servo는 사용하지 않는다. 스트랩은 시험별 ON/OFF를 명시한다.
- 현재 체크포인트 시험은 최소2초 준비 후 원본 첫 done 또는 보호 중단까지 환경 시작부터 녹화한다. 고정5초 cap을 두지 않는다.
- 원본 Fret/Strike 계약을 유지한 개별 native 연결·제어권 분리·영상 기록은 구현했지만, 양손 통합·보정 학습·지속 연주 성공은 미완료다.
- 최신 결과는 CPU PhysX·Isaac Gym native camera 진단이다. GPU 학습/원본 환경의 동등성과 실행 자원은 별도 확인한다.
- 기존 `stability_adapter/`, 관련 계획·산출물, 공용 자산과 체크포인트는 보존한다. 이전 경로의 3초 WAIT와 초기점 복귀 목표는 현재 실험 조건이 아니다.

## 확인된 최신 결과

- [Strike 2초 전환](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md:1): 2초 준비 후 제어, 3.55초에 잘못된 타현4회로 원본 실패 종료. 적시 타현1회이며 완주가 아니다.
- [Fret 손가락/팔 목표 분리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md:1): 초기 이탈은 줄었으나 압현0%, 지속 성공0/27, finger_back 실패. 팔 목표 유지는 진단이며 최종 연주에서 팔을 계속 묶지 않는다.
- [기존 길이 스트랩 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md:1): 고정 rest 1.1018469719600776m, PLAY 계산 장력0N·압현0%. 첫 native crash와 재시험을 보존했고 최초 crash 원인은 미확정이다. 한 길이 결과를 모든 스트랩 조건에 일반화하지 않는다.

## 다음 소단계

원본 고정 기타 성능과 전이 계약 차이를 확인하고, 현재 기타 기준 왼손 손목·목표 프렛 오차와 실제 접촉면을 시각화한다. 측정 근거에 따라 손가락 정책을 보존하는 제한된 팔 접근 보정을 설계하고 한 음의 압현·유지를 검증한다. 형상 원인이 확인되면 원본 자산을 보존한 별도 버전에서 필요한 부위만 보정한다.

단일 압현·타현 → 이벤트 전환 → 짧은 구절 → 곡 순서로 확대한다. 연주·허용 범위·자세/물리 지표를 분리 평가하고 제어권·최종 목표/history 계약을 검증한 뒤 보정 학습 구조를 결정한다.

핵심 문서:

- [파트 실행 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)
- [결과·영상 모음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:1)
- [최신 실행 결과 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/CONTINUOUS_WORK_STATUS.json:1)
- [이전 경로의 기록](/home/ajou/yigyu/3/docs/2026-10-12/README.md:1): 보존용이며 현재 구현 기준으로 승계하지 않는다.

## 다른 모듈

| 영역 | 문서 |
|---|---|
| 오디오·운지 | [Stage1](tab2fingermapping/README.md) |
| 왼손 압현 | [Fret](fret/README.md) |
| 오른손 타현 | [Strike](strike/README.md) |
| G0 계약·결합 | [Full 구현 상태](full/03_implementation/STATUS.md) |
