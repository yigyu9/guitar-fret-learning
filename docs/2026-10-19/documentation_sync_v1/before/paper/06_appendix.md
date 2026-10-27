# 부록

논문 제목: **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**

본문에서 사용한 관절 구성, 관측 차원, 좌표·시간 규약과 학습 설정을 기술한다. 구현 및 실험 자료의 대응은 [근거 색인](/home/ajou/yigyu/3/paper/evidence_index.md)에 제시한다.

## A. 용어와 연구 범위

| 용어 | 정의 |
|---|---|
| 압현·타현 | 압현은 손가락으로 줄을 누르는 동작, 타현은 줄을 튕기는 동작 |
| 탭·운지 | 탭은 연주할 줄과 프렛 위치를 나타내는 표현, 운지는 그 위치를 누를 손가락의 배정 |
| Full-Body | 전신 휴머노이드와 신체·환경 지지를 포함하는 연주 장면. 현재 신체 전체의 기준 위치·방향(root)과 하체는 고정 |
| Freely Moving Instrument | 기타의 위치·방향을 고정하거나 실행 중 강제로 지정하지 않고 물리적으로 이동·회전하도록 둔 조건 |
| Actor-root | 시뮬레이터에서 물체의 위치·방향을 표현하는 기준 원점. 질량중심과 일치할 필요는 없음 |
| Fret | 왼손 압현·유지·해제를 담당하는 기술 정책의 이름. 평가에서는 지정된 손가락의 사용 여부도 검사 |
| Strike | 오른손 피크의 줄 통과와 방향·순서·타이밍, 다음 타현을 위한 회복을 담당하는 기술 정책의 이름 |
| Policy·Observation·Action | 정책은 입력 상태로부터 행동을 결정하는 함수, 관측은 정책에 제공하는 정보, 행동은 정책이 출력하는 제어 명령 |
| Canonical PlayEvent | 양손이 공유하는 연주 사건. 함께 연주할 현들의 목표 프렛과 타현 시각 등을 묶은 표현 |
| Source policy | 고정 기타에서 미리 학습한 개별 기술 정책. 공동 제어 실험에서는 매개변수를 고정하고 출력을 재사용 |
| Nominal target | 개별 기술 정책과 준비 자세에서 구성하고 허용 범위 제한(guard)을 적용한 기준 관절 목표 |
| Residual | 기준 관절 목표에 더하는 크기가 제한된 추가 보정량 |
| PD control | 관절의 목표 각도와 실제 각도 차이, 움직임의 속도에 따라 관절을 구동하는 제어 방식 |
| Native contact query | 물리 엔진에서 두 물체의 접촉 여부를 조회하는 것. 음악 판정용 압현 영역(press cell)과 피크의 줄 통과(crossing) 검출과 구별 |
| Raw contact lambda | 접촉 조회의 원시 값. 검증된 N 단위 지지력으로 환산하지 않음 |
| Dwell | 목표 압현 상태가 이어진 시간 |
| Joint music success | 같은 연주 사건에서 필요한 현들의 타현·음높이·압현 유지 시간 등 공동 판정 조건을 충족한 것. 여기서 joint는 관절이 아니라 양손의 공동 수행을 뜻함 |
| Checkpoint·Episode | 체크포인트는 특정 학습 시점의 모델과 관련 상태를 저장한 자료, 에피소드는 초기 상태부터 종료까지의 한 차례 실행 |

## B. 관절 구성과 정책 차원

관절의 이름과 순서는 자산 명세에 정의되어 있다. 상체 잔차 정책의 행동 차원은 81이며, 원본 압현·타현 정책의 행동 차원은 각각 30이다. 과거 결합 설계의 105개 슬롯은 가동 범위가 0인 8개 슬롯을 포함하는 인터페이스 차원으로, 본 실험의 제어 차원과 다르다.

| 경로 | 관측 | 행동 | Value | 주의점 |
|---|---:|---:|---:|---|
| Fret-v2 source |420|30|6|L_Thorax3은 source 정책 행동에서 제외 |
| Strike-v2 source |303|30|1|R_Thorax3은 source 정책 행동에서 제외 |
| 공동 잔차 정책 |825|81|1|상체 보정, 루트·하체 고정 |
| 과거 G0 named ABI |별도 계약|105 slots|별도 계약|105는 정의된 슬롯 수이며, 97은 가동 범위가 0인 8개 슬롯을 제외한 수 |

원본 압현 정책의 관측은 11개 블록으로 구성되며, 차원의 합은 60 + 18 + 60 + 45 + 24 + 52 + 72 + 45 + 12 + 2 + 30 = 420이다. 타현 정책의 관측은 60 + 18 + 30 + 7 + 32 + 25 + 52 + 29 + 18 + 2 + 30 = 303차원이다. 두 정책의 관측에는 동기화 정보 필드가 포함되어 있으나, 자유 기타의 공동 음악 수행은 별도의 이벤트 판정으로 평가하였다.
[Fret 계약](/home/ajou/yigyu/3/tab2body/fret_v2_contract.py),
[Strike 계약](/home/ajou/yigyu/3/tab2body/strike_v2_contract.py),
[G0 슬롯](/home/ajou/yigyu/3/master_plan/08_shared_contracts.md).

| 상체 관절 그룹 | 관절 차원 |
|---|---:|
| Torso·Spine·Chest |9|
| Neck·Head |6|
| 왼쪽 Thorax·Shoulder·Elbow·Wrist |12|
| 오른쪽 Thorax·Shoulder·Elbow·Wrist |12|
| 왼손 손가락 |21|
| 오른손 손가락 |21|

## C. 관측 벡터와 네트워크

| 물리 상태 관측 | 차원 |
|---|---:|
| 관절각·속도·직전 최종 제출 목표 |243|
| 유효 목표 하한과 상한 |162|
| 몸통 초기각 대비 변화와 Chest 기준 회전 |15|
| 기타 위치·회전 6D·origin 선속도·각속도 |15|
| actor-root 위치 상자의 여섯 signed margin |6|
| 15개 손목·손바닥·distal·피크 표본의 G 상대 위치·속도 |90|
| 양손 손바닥의 G 상대 회전 6D |12|
| PREP·PLAY와 시간 |5|

| 음악 상태 관측 | 차원 |
|---|---:|
| required fret·관측 음높이·dwell·hit와 이벤트 상태 |28|
| 현별 crossing 잔여 시간·required mask |12|
| 방향·이벤트 시작과 종료까지 시간 |4|
| 6현 × 22프렛 press cells |132|
| 피크 detector state·rearm |12|
| 직전 피크의 G 상대 위치 |3|

잔차 정책의 관측은 물리 상태 548차원, 음악 상태 191차원, 기준 관절 목표 81차원, 스트랩 상태 5차원을 연결한 825차원 벡터이다. Actor와 Critic은 각각 825→512→256→81과 825→512→256→1 구조이며, 은닉층에는 ELU를 사용한다. Actor가 정의하는 Gaussian 행동에는 tanh 변환을 적용한다. Actor의 파라미터 575,057개, Critic의 파라미터 554,497개, 학습 가능한 log_std 81개를 합한 학습 파라미터 수는 1,129,635개이다. 동결된 원본 정책과 관측 정규화 버퍼는 이 수에서 제외한다.
[최신 네트워크 설명](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/06_StabilityAdapter2_현재_학습구조.md).

## D. 좌표와 시간 규약

| 항목 | 규약 |
|---|---|
| Quaternion | native 초기값과 주요 기록에서 xyzw. wxyz 산출물은 명시적으로 변환 |
| Guitar+x |6번줄 low-E→1번줄 high-e |
| Guitar+y |브리지→너트 |
| Guitar+z |지판·앞판 바깥쪽 |
| Source CSV 줄 번호 |0=low-E |
| Isaac 줄 번호 |5=low-E,0=high-e. 변환5−source index |
| down crossing |Isaac5→0, guitar+x 방향 |
| up crossing |Isaac0→5, guitar−x 방향 |
| 현재 제어 |60Hz, Δt=1/60초 |
| 현재 물리·공동 detector |240Hz, 관절 목표 한 번당4 physics step |
| 현재 준비 |2초, 준비 중 정책 제어와 물리는 계속 진행 |
| 영상 |원래 frame 시각과 저장 fps를 따로 기록. MP4 길이는 실제 종료시각과 다를 수 있음 |

기타 상대 속도는 좌표계 원점의 선속도를 기준으로 계산한다. 물리 엔진이 제공하는 질량중심의 선속도는 각속도와 원점까지의 변위를 이용하여 원점 속도로 변환한다. 스칼라 관절각의 변화, 부모와 자식 강체 사이의 상대 회전, 세계 좌표계에서의 방향은 서로 다른 측정량이며, 관절 이름에 포함된 x/y/z는 세계 좌표계의 회전축을 직접 나타내지 않는다.

기타 초기 quaternion과의 각도는 quaternion 부호 동치를 고려한 SO(3) 거리다.
이 값은 허용 회전 집합까지의 거리와 구별된다. 위치 이탈은 기타 강체의 기준 원점(actor-root)에서 계산하며, 형상의 중심이나 질량중심을 사용한 거리와도 구별한다.

## E. 제어 및 학습 설정

| 설정 | 실험 설정 |
|---|---:|
| 몸통·머리·팔·손가락 보정 한도 |0.03 /0.10 /0.30 /0.20rad |
| 목표 변화율 |0.10 /0.50 /1.00 /1.50rad/s |
| 팔 nominal guard |reset preload±0.15rad |
| 왼엄지 nominal guard |reset preload±0.10rad |
| 몸통 effective target |native limit∩reset q_ref±5° |
| Adam learning rate |3×10⁻⁵ |
| PPO epoch·minibatch |4·128 |
| Policy/value clip |0.2·0.2 |
| Value/entropy weight |0.5·0.001 |
| Gradient norm/KL 상한 |1.0·0.02 |
| γ·λ |2^(−1/600)·2^(−1/60) |
| 병렬 생산 rollout |4환경×256step=1024 transitions |
| 초기 노이즈 smoke |4환경×64step=256 transitions |
| 정상 tick reward |0.1×max(−8,raw_sum) |

새 정책의 초기 log_std는 몸통·머리에 −5, 팔·손가락에 −4로 설정하였다. 이는 tanh 변환 전 잠재 행동 분포의 값으로, 관절각의 표준편차와 다르며 학습 과정에서 갱신된다. 관측 정규화 통계는 likelihood와 KL 비교 중 고정하였다.
[관절 보정](/home/ajou/yigyu/3/stability_adapter_2/deadline_bounded_residual_v1.py),
[guarded PPO](/home/ajou/yigyu/3/stability_adapter_2/deadline_guarded_ppo_v3.py).

체크포인트에는 모델 가중치와 함께 관측·행동 구성, 정규화 통계, 제어 설정, 원본 정책 식별 정보, optimizer와 난수 생성기의 상태 및 학습 진행 기록을 저장한다. 초기 교란 실험은 기존 정책과 정규화 통계를 가져오되 optimizer와 진행 카운터를 새로 초기화하였다. 따라서 이 조건은 동일한 물리 상태에서의 실행 재개와 구별된다.

## F. 입력 자료와 평가 범위

대표 자유 기타 실험의 곡은 등록된 `02_Jazz1-200-B_solo` 번들이다. 해당 manifest에는
입력 hash가 있지만 provenance 필드는 빈 객체이므로, 현재 파일만으로 검수된 입력 전체가
무수정 자동 전사에서 왔다고 확정할 수 없다. 원시 오디오 기반 성능을 주장하려면 자동 생성,
annotation 사용, 사람이 수정한 부분을 분리한 입력 manifest가 필요하다.
[대표 번들 manifest](/home/ajou/yigyu/3/data/song_bundles/02_Jazz1-200-B_solo/manifest.json).

본 논문에 보고한 물리 실험은 등록된 연주 목표를 조건으로 한다. 압현·타현과 공동 음악 이벤트의 지표는 등록된 목표 대비 물리 수행을 평가하며, 원음 대비 전사 오류는 별도로 평가하지 않는다. 과거 전사기의 frame F1과 note F1, 운지 규칙 위반 수 및 코드 인식 수치는 본 실험과 동일한 입력 이력·평가 분할에서 재평가되지 않았으므로 현재 전체 시스템의 성능으로 제시하지 않았다.

## G. 재현 자료

실험의 재현 자료는 다음 다섯 범주로 구성된다. 각 결과의 조건과 원자료는 근거 색인에서 연결한다.

1. 실행 계획과 source·입력 hash, 실제 초기값, 자산·물성·PD·solver·스트랩 조건.
2. 정책 checkpoint와 관측·행동·nominal·보상·종료 계약, seed와 초기 분포.
3. 최종 제출 목표와 실제 q·qdot, 기타 pose·속도, press/crossing·joint event 원자료.
4. 종료 원인과 실제 물리시각, native frame·영상·camera·후처리 구분.
5. 실행 검증과 정정본, 동일 조건 비교의 시작점·공통 시간 구간.

실험 당시의 소스 스냅샷과 실패 기록을 보존하고, 후속 정정 자료를 함께 제공한다. 척추·왼손 철수 비교의 접촉 분석은
[README_V2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README_V2.md)에 수록된 오른손목·손 접촉의 보완 결과를 반영하였다. 원래의 소스 스냅샷과 실험 결과 파일은 [근거 색인](/home/ajou/yigyu/3/paper/evidence_index.md)에서 참조할 수 있다.

## H. 자산 출처

OM 도면과 파생 자산의 출처 및 사용 조건은
[저작권 검토 자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/LICENSE_RESEARCH_NOTES_V1.md)와
[자산 attribution](/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/ATTRIBUTION.md)을 따른다.
이 자료는 형상 구성의 출처를 설명하며, 실제 악기의 질량분포나 재료 물성을 측정한 자료는 아니다.

## I. 프렛 기하와 압현 영역

프렛의 음악적 번호와 압현을 판정하는 공간 영역은 구별된다. 개별 Fret 구현은 각 현의 두 끝점으로 현 방향을 구성하고, 자산의 너트와 1–22번 프렛 marker를 그 방향에 투영한다. 인접한 프렛 경계에서 wire의 반폭을 제외한 구간을 압현 cell로 정의한다. 이 계산은 실제 자산의 marker 배치를 사용하므로, 정해진 길이를 임의의 구간 비율로 나누어 프렛을 생성하는 과정과 다르다. [프렛 기하 계산](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1893).

손가락의 접근 목표점과 성공으로 인정하는 영역도 구별된다. 현행 Fret 코드의 기본 접근점은 cell의 상한 경계(cell_hi)에서 구간 내부로 길이의 20%만큼 이동한 지점이다. 같은 프렛에서 여러 현을 눌러야 하는 경우에는 손끝 사이의 간격을 고려하여 접근점을 cell의 10–90% 범위 안에서 조정한다. 한편 길이 방향의 위치 점수는 cell 내부 10–90% 구간에 동일한 값을 부여한다. 따라서 프렛 중앙에 가까울수록 압현 점수가 계속 높아지는 모델은 아니다. 실제 압현 성공은 길이 방향의 위치 외에 구현된 다른 압현 조건도 함께 검사한다. [wire 폭과 접근점 설정](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1305), [같은 프렛의 다중현 목표 조정](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:217), [위치 점수](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:70), [압현 조건의 결합](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:2305).

이 설명은 현행 기하·판정 구현에 해당한다. 과거 Fret 체크포인트의 성능은 각 평가 당시 코드와 조건에 따른 값으로 보고하며, 현행 위치 규칙을 모든 과거 평가에 소급하여 적용하지 않는다. 또한 이 기하 판정은 줄의 진동이나 버징을 계산한 음향 품질 평가가 아니다.
