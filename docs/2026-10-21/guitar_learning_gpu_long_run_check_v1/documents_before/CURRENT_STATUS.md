# 프로젝트 현재 상태 — 2026-10-21

기준일: **2026-10-21**. 새 손별 기본 실행은 `guitar_learning.train`의 GPU PhysX·CUDA 배치 제어/접촉 후보/보상/PPO 경로다. [현재 명령과 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md) · [GPU 전환 검증](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1/README.md). 기존 CPU checkpoint와 성과는 새 GPU 계약에 상속하지 않는다.

추가 무행동 진단에서 대규모GPU 배치의 물리·지지 제어 안정성 회귀를 확인했다. CPU1/GPU2는2초 동안 실패0, GPU1024는817개 환경에서1781회 실패였다. 이는 학습 탐색만으로 설명할 수 없으며 정확한 내부 원인 분리는 남아 있다. [비교 영상·원자료](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_failure_video_v1/README.md). 현재 기본128을 안정 학습 권장값으로 해석하지 않는다.

2026-10-21 GPU v2는기타를1개자유강체로표현하고기존39개마커를복원한다. 질량·COM·관성과89개충돌형상을유지하고두비물리proxy의충돌을완전히제외했다. 큰수치폭발은완화됐으나느린기타이탈이남아완전안정화로분류하지않는다. [원인분리·수정·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1/README.md). GPU v1 checkpoint도새물리계약으로strict resume하지않는다.


아래 수치와 공동/전곡 실험은 **2026-10-19까지의 CPU 물리 기반 연구 결과**다. 전곡 첫 학습은8업데이트까지 완료했으며 학습 중 수집과 별도 평가를 구분한다.

논문 작업 제목은 **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**다. 연구 분야는 Computer Graphics의 물리 기반 동작·제어이며, 오디오에서 만든 연주 목표를 자유 기타와 휴머노이드의 상호작용으로 실행하는 문제를 다룬다. 사람 동작과의 유사성은 아직 정량 평가하지 않았다.

## 현재 물리 조건과 제어 범위

- Root만 고정한다. 하체 관절은 원 가동범위와 유한한 유지 제어를 사용한다.
- 입력/목표 채널105개, 비영 가동범위97축, 원 영범위8축을 구분한다. 영범위가 실제 측정 움직임의 엄밀한0을 보장하지 않는다.
- 정책 출력은 왼팔·왼손33축과 오른팔꿈치·손목6축을 합한39축이다. 하체를 포함한105축 전체를 신경망이 학습하는 구조는 아니다.
- 기타는 자유 강체·중력 ON·스트랩 OFF다. 기타 직접 보조 힘·부착·실행 중 상태 덮어쓰기를 사용하지 않는다.
- 가슴 접촉 지속·삼중접촉률은 현재 학습 성공의 필수조건이 아니다. 기타 이탈·회전·접지·관절 안전은 계속 측정한다.
- 물리 240Hz, 정책 60Hz다. 각 목표를 네 물리 표본에서 평가하며 실패 tick의 양성 보상을 억제한다.

학습 실행은 기존035 설정과v14 준비 상태를 사용한다. [기준 설정](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json) · [준비 자세의 값·이미지·영상](/home/ajou/yigyu/3/paper/initial_pose/current_v3/README.md). 별도 자세 연구나 날짜별 영상의 최신 후보가 학습 입력에 자동 적용된 것은 아니다.

## 경로별 구현과 검증

| 경로 | 관측/행동 | 초기화와 학습 | 실제 확인 범위 |
|---|---|---|---|
| 손별 초기 정책 | 상태563, 행동39 중 해당 손만 학습 | 자유 기타의 손별 성공 궤적 BC와 손별 PPO | 최신 BC는 각 손4/4 평가 통과. 두 손 동시 성공은 별도 |
| `guitar_learning/joint/` | 공동 상태1132, 각 Actor 입력569, 행동33+6 | 두 Actor와 중앙 reward/cost Critic. 검증된 손별 Actor/std 이전, 공동 Critic·Adam 새로 시작 | CPU 34개, 2환경 840전이·PPO 1업데이트, 저장 모델의 실제 재평가 완료 |
| `guitar_learning/song/` | 공통 상태500=기본468+곡 이력32, 행동33+6 | 기존 Actor의 동일한 물리 460열·토큰 encoder·head·std만 초기값으로 사용. 새 음악/이력 40열은 0, Critic·Adam 새로 시작 | 실제4096전이·PPO8회 완료, 안전 전곡2회 완주. 음악적 전곡 성공0/2 |

서로 다른 관측·목표·시간·이력을 가진 checkpoint는 strict resume로 혼용하지 않는다.

## 최신 완료된 공동 실험

| 실행 | 안전7초 완주 | LH 품질 성공 | RH 품질 성공 | 공동 성공 |
|---|---:|---:|---:|---:|
| 고정된 두 BC의 동시 실행 |1/1|1/1|0/1|0/1|
| 첫 PPO rollout, 업데이트 전 수집 |2/2|2/2|0/2|0/2|
| 저장된 PPO의 결정적 재평가 |1/1|1/1|0/1|0/1|

두 환경의 840전이를 모두 PPO에 반영했고 제외 전이는 0, 실제 업데이트는 1회다. 양손 Actor와 Critic의 변경, 체크포인트 저장과 엄격 불러오기, 물리 장면 재사용을 확인했다. 고정 동시 실행의 오른손 타현은 목표보다 약 2.357초 늦었다. 이는 구현 연결의 검증이며 공동 연주의 숙련이나 성능 향상을 입증하지 않는다. [실제 결과·검수·설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/README.md).

## 전곡 확장의 현재 범위

대상곡은 `05_BN2-131-B_solo`다. 오디오 29.3063946초에 정책 준비 3초와 종료 후 0.5초를 더하고 60Hz 경계로 올려 **32.8166667초, 1969tick**으로 구성한다. 67음을 하나의 물리 에피소드에서 이어가며 PPO rollout 경계는 초기화 조건이 아니다.

정본 66이벤트 중 42번 묶음의 두 재타현은 원 note onset으로 펼친다. 두 번째 방향의 별도 원자료가 없어 묶음의 down 방향을 두 음에 상속하는 명시적 가정을 사용한다. 23.3ms 간격은 어려운 전환 조건이다. 기존 release 상한을 보존하므로 11개 음의 sustain이 원 note-off보다 총 0.8044초 짧다. 모든 음은 압현음이며 이번 범위를 열린현·바레·특수 주법의 검증으로 확대하지 않는다.

현재 [전곡 학습 최종보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/report.json)는4096전이·8업데이트 완료다. 전이 제외는0개이며2개 에피소드가32.8166667초를 안전하게 완주했다. 수집된134개 목표 중 왼손 충족2개·오른손 적시 타현2개·협응0개이며 전곡 음악 성공은0/2다. 이들은 학습 중 수집 결과이며 별도 최종 모델 평가와 구분한다. [음별 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/song_report.json)

## 논문에 쓸 수 있는 주장과 남은 일

현재 근거는 자유 기타·유한 하체 조건의 초기 자세 개별 시험, 손별 기술 초기화, 같은 장면의 양손 학습·검증 연결을 뒷받침한다. 공동 음악 성공, 전곡 음악 수행의 숙련, 다곡·다중 seed 일반화, 사람 동작 유사성, 실제 현 압력·진동·음향, Root 자유 균형·보행은 입증되지 않았다.

다음 검증은 저장 모델의 별도 평가, 음 전환과 타이밍 개선, 음별 시도와 누락, 올바른 압현과 타현의 동시성, 물리 실패와 모델 저장을 분리해 확인하는 것이다. 단음 성공과 완화 시간창의 성공을 엄격한 50/100ms 음악 성공으로 바꾸어 보고하지 않는다.

## 읽는 순서

1. [학습 안내](/home/ajou/yigyu/3/guitar_learning/README.md)
2. [논문 본문](/home/ajou/yigyu/3/paper/README.md)
3. [문서 색인](/home/ajou/yigyu/3/docs/DOCUMENT_INDEX.md)
