# StabilityAdapter 2 — 전체 상체 공동 정책 설계 v2

2026-10-11. 사용자 정정에 따라 **하체를 제외한 전체 상체 제어**와 **512 → 256 은닉층**을 기본 설계로 삼는다. 이전 왼손33/256→256 초안은 과거 제안으로 보존한다. 이 문서는 구현·환경 변경·학습 실행을 뜻하지 않는다.

## 변경 범위와 작업 순서

- [x] 저장된 native 관절 이름과 기존 Fret·Strike 모델의 은닉층 사양 확인.
- [x] 전체 상체 제어권, 네트워크와 기존 초안 대비 변경점 기록.
- [ ] 그림 대조·독립 검수·메인 문서 연결·기존 파일 보존 검사. 완료는 메인 PLAN에 기록한다.
- [ ] 후속 소단계에서 관측/행동 manifest 구현, CPU 계약 검사와 실제 행동 시험.

이 버전이 이전 초안의 제어 범위·held48·양측66 확장 순서·256 두 층 제안에 우선한다. 나머지 세부 계약은 [v1의 관측·분포·평가·체크포인트 조건](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:23)을 계승하되 아래의 전체 상체/양손 조건에 맞게 적용한다. 기존 코드·물리 조건·계획 이력은 수정하지 않는다.

## 제어권: 상체 전체 81관절

| 부위 | 정책 행동 차원 |
|---|---:|
| Torso·Spine·Chest |9|
| Neck·Head |6|
| 왼쪽 Thorax·Shoulder·Elbow·Wrist·손가락 |33|
| 오른쪽 Thorax·Shoulder·Elbow·Wrist·손가락 |33|
| 합계 |**81**|

관절 이름과 순서는 저장된 실제 native 실행의 `joint_names`에 따른다. root의 자유도와 고정 하체는 행동에 포함하지 않는다. [이름·순서 후보 및 근거 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/upper_body_action_manifest_candidate.json).

**한 Actor가 81개 PD 목표를 모두 소유하고 한 제출자만 명령을 보낸다.** 오른팔·몸통·목/머리에 별도의 고정 PD 목표 채널을 남기지 않는다. 기존 왼팔 PI·엄지 지지 제어기·Fret/Strike 제어기가 같은 관절에 따로 명령하지 않는다. 기존 정책 출력은 비교 또는 유효한 교사/참조 신호 후보이며, 사용하더라도 최종 명령의 소유권은 공동 정책에 둔다.

몸통9와 목·머리6의 움직임은 초기 기준 자세 선호와 관절별 작은 탐색·목표 변화율 비용으로 억제하는 후보를 둔다. 해당 관절을 행동에서 제외하거나 초기각에 강제로 고정하지 않는다. 몸통부터 손끝까지 실제 q/qdot와 목표-실제 오차를 측정하며, 몸통의 보정이 필요한 상황에서는 움직일 수 있어야 한다. 자세 선호의 강도와 관절별 속도 한도는 행동 시험 뒤 정한다.

root/하체 fixed-lower, self-collision, 자유 기타와 첫 pilot 스트랩OFF 조건은 유지한다. 기타 고정·외력·손 부착·실행 중 pose 덮어쓰기는 금지한다. 이 설계가 자산의 고정 하체를 다시 움직이는 것은 아니다.

## 네트워크: 512 → 256

| 구성 | 이번 기본 설계 |
|---|---|
| Actor |관측 D → Linear512 → ELU → Linear256 → ELU → 평균81|
| 행동 분포 |81차원 tanh-squashed diagonal Gaussian, 관절별 학습 가능한 log_std|
| Critic |같은 관측 D → Linear512 → ELU → Linear256 → ELU → value1|
| 가중치/알고리즘 |Actor/Critic 분리, PPO 후보. 학습률·batch·보상 가중치는 미정|
| 초기 출력 |평균 head weight=0, bias=`atanh((q_init-mid)/half)`. 경계 초기값은 조용히 clip하지 않고 차이·처리안을 보고|

프로젝트의 [기본 ActorCritic](/home/ajou/yigyu/3/tab2body/learning/models.py:211)은 Actor/Critic에 (512,256)을 기본값으로 사용한다. [Fret-v2](/home/ajou/yigyu/3/tab2body/learning/fret_v2_model.py:49)와 [Strike-v2](/home/ajou/yigyu/3/tab2body/learning/strike_v2_model.py:54)의 block encoder 뒤 fusion MLP도 (512,256)이다. 이 근거에 맞춰 이번 기본 크기를 정정한다. 새 Actor의 입력·출력과 encoder 구성은 기존 모델과 달라, 은닉층 크기가 같다는 이유만으로 가중치 호환을 주장하지 않는다.

외부 예로 [IsaacGymEnvs Humanoid SAC 설정](https://github.com/isaac-sim/IsaacGymEnvs/blob/main/isaacgymenvs/cfg/train/HumanoidSAC.yaml)은 [512,256]을 사용한다. 다만 [Humanoid PPO 설정](https://github.com/isaac-sim/IsaacGymEnvs/blob/main/isaacgymenvs/cfg/train/HumanoidPPO.yaml)은 [400,200,100]이므로, 512→256을 모든 작업의 표준이나 최적값으로 단정하지 않는다. 이번 선택은 프로젝트 사양과 상체 통합 입력에 맞춘 출발점이며 성능 검증 전이다.

## 관측과 행동 계약

관측 차원 D는 아직 미정이다. 전체81 실제 q/qdot·직전 실제 제출 목표, Chest/Pelvis 상태, 기타 pose/twist·허용범위 여유, 현재 기타 좌표계에서 양쪽 손목·손바닥·엄지·손끝/피크와 연주 목표의 관계, 음악 event·압현 detector/sustain tracker·타현 상태와 측정 마스크를 후보로 둔다. 압현/타현 목표가 없는 단계는 유효 마스크로 구분한다. 미래의 실제 성공 결과는 입력하지 않는다.

현재 기타 상대속도는 기타 병진과 회전 모두를 반영한다. 양측 native 접촉과 조회 유효 마스크를 구분하고 raw lambda를 힘N으로 사용하지 않는다. world actor-root 허용범위와 팀원의 Pelvis 상대 body-center 범위는 혼합하지 않는다. 회전 허용집합 판정은 구현·경계·특이점·q/-q 동치 검사 전 완성된 입력으로 취급하지 않는다.

행동은 81개 절대 PD 목표 요청이다. 검증한 native 관절 한계로 `q_requested=mid+half*tanh(u)`를 계산하고, 직전 제출 목표에서 관절별 변화율 제한을 적용해 81D `q_final`을 한 번 제출한다. 상체의 held 채널은0이다. 현재 60Hz 제어/240Hz 물리 조건에서 제한은 제어 주기당 한 번 적용하고 사이4개 물리step에서는 목표를 유지한다. 기존 gain·구동·재질은 첫 비교에서 유지한다.

PPO에는 sampled action/log-prob와 q_requested/q_final을 구분해서 저장하고, 다음 관측의 직전 목표는 실제 q_final이다. 초기 평균은 유효한 초기 배치를 유지하도록 정의하며 초기 탐색은 몸통·목/머리·팔·손가락별 물리 목표 변화량을 검사해 정한다. v1의 팔0.8rad/s·손가락0.3rad/s는 검증 전 후보이며 새 몸통/목 관절에 복사하지 않는다. 기존 EMA/PI를 자동 중첩하지 않는다.

## 음악 목표·기타 안정성·자연스러움

압현 유지·정시 해제·전환, 타현 시점/현/피크 경로, 기타 허용범위 이탈·복귀, 몸통·목/머리의 과한 움직임, 불필요한 충돌과 목표 변화량을 분리해 평가한다. 범위 안 초기점 복원 비용은0이고 손바닥/엄지의 영구 접촉은 요구하지 않는다. 원본 음악 판정을 완화해 개선을 만들지 않는다. 가상 피크의 타현 판정과 물리적인 오른손/팔–기타 접촉 영향도 구분한다.

첫 pilot의 음악 목표는 한 음의 압현 유지·해제부터 시작할 수 있지만, **처음부터 행동 차원은81이며 상체 전체에 제어권이 있다.** 음악 과제의 난이도만 단계적으로 늘린다. 오른손 준비 위치와 몸통 자세는 초기 soft 목표로 두고 이후 타현/양손 전환을 추가한다. 소규모 검증에서도 일부 관절 시험과 학습 정책의 전체 제어권을 혼동하지 않는다.

기존 Fret/Strike 동결 비교와 호환성 검사, 유효한 성공 구간만의 약한 교사 후보는 유지한다. 동일 구조·환경·음악 event·budget의 scratch 비교를 둔다. 교사 의존은0까지 줄일 수 있어야 한다. 상태/관측/action 의미·layer shape가 맞지 않는 checkpoint/critic/optimizer/정규화 통계는 복사하지 않는다.

## 다음 구현 단위와 기록

1. 저장된 이름/순서를 현재 환경 조회와 대조하고81관절 한계·관측 manifest·소유권을 확정한다.
2. CPU에서 Actor81/Critic1 분포, 초기 평균, 한계/rate 제한, 단일81 목표 제출과 원본 음악 신호를 검사한다. 회전 허용집합은 구현 후 별도로 검증한다.
3. 학습 없이 작은 몸통·목·팔·손가락 행동을 실제5초 native 영상으로 기록하고, 도달 가능성·충돌·기타 변화·제한기 포화를 확인한다.
4. 자원/backend와 준비·음악clock·종료 계약을 확정한 뒤 짧은 PPO pilot을 수행한다. 음악과 범위 유지가 모두 개선되는지 별도 평가한다.

checkpoint 영상은 최소2초 준비부터 정의된 평가 episode 종료까지, 순수 자세 시험은 약5초 기록한다. 준비 중 제어와 새 정책의 음악clock/episode 종료는 실행 전에 명시한다. WAIT → REACH → GRIP → TRANSPORT는 필수 과정이 아니다.

이번 단계의 변경은 새 설계 문서·그림과 메인 안내의 추가 기록뿐이다. 이전 v1/실험/legacy 경로를 보존한다. 결과·설명·검수는 [v2 결과 모음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/README.md)에 저장한다.
