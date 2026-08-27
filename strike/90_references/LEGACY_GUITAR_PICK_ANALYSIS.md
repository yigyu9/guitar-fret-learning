# Xu guitar 오른손 pick 구현 분석과 이식 결정

> 조사 대상은 `related_work/guitar`의 실제 코드·에셋·reference motion·checkpoint다. 이 문서는
> “기존 연구가 물리 피크를 어떻게 구현했는가”에 대한 답과, 현재 strike S0가 무엇을 그대로 쓰고
> 무엇을 고쳐야 하는지를 고정한다. 최종 갱신: 2026-07-23.

## 결론

Xu 구현에는 손에서 분리된 **물리 plectrum이 없다**. `RH:pick`은 `RH:index2` 아래
`(0.007, -0.048, -0.005) m`에 붙은 geometry·질량·관성·joint 없는 marker body다. 줄도
`G:stringN→G:stringN_end` 두 marker가 정하는 선분이며, 레거시 detector는 이전 프레임과 현재
프레임의 pick marker를 이은 선분이 각 줄의 xy 직선과 만나는지 계산한다.

따라서 첫 구현은 이 연구의 **swept marker 아이디어**를 보강한 `pick_only_v1`이 적합하다. 피크의
두께·회전·잡기·미끄러짐·현 휨을 이미 구현된 사실처럼 취급하면 안 된다. 그것들은 S0가 안정된 뒤
별도 물리 pick V2로 올린다.

| 항목 | 레거시 사실 | 현재 결정 |
|---|---|---|
| pick | index2 고정 point marker | S0에서 유지하되 `virtual_pick`임을 명시 |
| string | 양 끝 marker가 만든 선분 | 실제 finite segment를 detector 정본으로 사용 |
| 사건 | 프레임 간 xy 교차와 z 깊이 | 조건을 보강한 one-shot `RELEASE` 사건 |
| CONTACT/LOAD | 상태가 없음 | pick S0 필수 phase로 만들지 않음 |
| 목표 | detector·reward·goal 소비가 한 함수에 결합 | detector와 matcher를 분리 |
| style | wrist/finger pose discriminator | 정확도 gate 뒤 선택적 prior로만 사용 |
| checkpoint | 27DOF 부유손 정책 | 30DOF 어깨 이하 우팔 정책에 직접 로드 금지 |

## 1. 물리 모델의 실제 범위

### 1.1 `RH:pick`은 피크 모양 물체가 아니다

[right_hand_guitar.xml](../../related_work/guitar/assets/right_hand_guitar.xml)의 `RH:pick` body는
`RH:index2`의 자식이다. 주석 처리된 capsule 외에는 geom도 inertial도 joint도 없으므로 다음 정보가
존재하지 않는다.

- 피크 끝과 밑동을 구분하는 orientation
- face/edge, 두께, attack angle
- 질량·관성·충돌·마찰
- 엄지와 검지 사이의 grasp, slip, regrip

즉 정책은 “피크를 잡는” 것이 아니라 검지에 고정된 점을 움직인다. self-collision이 꺼진 현재
환경에서도 엄지-검지 contact force를 실제 grip의 증거로 사용할 수 없다.

### 1.2 줄은 충돌 현이 아니라 marker 선분이다

레거시 [right_hand_guitar.xml](../../related_work/guitar/assets/right_hand_guitar.xml)에서
`G:string1..6`과 `G:string1_end..6_end`는 geometry 없는 marker body다. 현재
[guitar_asset.xml](../../tab2body/assets/guitar_asset.xml)의 보이는 capsule도
`contype=0, conaffinity=0`인 시각화용이라 접촉력을 만들지 않는다. `G:pluck_range`는 별도의 넓은
box이며 줄 자체가 아니다.

이 때문에 S0에서 “현 접촉력”, “실제 변형량”, “피크가 현을 저장했다가 놓는 탄성 에너지”를 측정할 수
없다. S0의 strike는 marker 궤적에서 복원한 기하 사건이다.

### 1.3 레거시 제어계와 현재 제어계는 다르다

레거시 오른손 단독 rig는 wrist translation 3 + wrist rotation 3 + finger 21, 합계 **27 action**인
부유손이다. 현재 strike는 `R_Shoulder/R_Elbow/R_Wrist` 9 + `RH:*` 21, 합계
**30 action**으로 어깨부터 손가락까지 제어하고 `R_Thorax`는 고정한다.

현재 [smpl_mpl_hands_body.xml](../../tab2body/assets/smpl_mpl_hands_body.xml)은 조사 시점에 레거시
full-body 동명 asset과 byte-identical이어서 body/marker 이름과 손 기하는 재사용할 수 있다. 그러나
오른손 단독 정책의 action graph, 관측, 중력 조건, task goal은 다르므로 pretrained checkpoint를 현재
actor에 직접 로드할 수 있다는 뜻은 아니다.

## 2. 레거시 타현 판정

[env.py](../../related_work/guitar/env.py)의 `ICCGANRightHand._reward`는 기타 로컬 좌표에서 다음 두
선의 xy 교점을 구한다.

```text
pick trajectory: p(t) = p0 + t(p1-p0)
string line:     q(s) = a  + s(b-a)
```

레거시의 유효 조건은 사실상 다음과 같다.

1. 두 xy 방향이 평행하지 않다.
2. `0 < t < 1`이다.
3. 교점에서 pick의 z가 string z보다 아래다.
4. training에서는 string z보다 추가로 1 mm 깊어야 `plucking_valid`다.

이 방식은 한 control frame 사이의 빠른 통과를 잡는다는 장점이 있다. 그러나 계산한 `s`에
`0≤s≤1` 조건을 적용하지 않으므로 실제 현 바깥의 **무한 연장선**도 타현으로 오인할 수 있다. 또한
training은 1 mm 깊이를 요구하지만 evaluation은 depth를 0으로 바꾸므로 판정 계약도 동일하지 않다.

다음 조건도 없다.

- down/up 방향과 across-string 최소 속도
- 허용 strike zone 또는 phrase lane
- 최대 침투 깊이와 기타 관통 분리
- 같은 프레임 복수 줄의 sub-frame 순서
- goal과 독립적인 explicit re-arm/debounce
- pick orientation, face/edge와 attack angle
- `CONTACT→LOAD→RELEASE` 상태

레거시의 현재 goal bit를 지우는 동작이 중복 억제 역할까지 겸한다. detector, 목표 매칭, error class,
reward, goal 소비가 한 함수에 결합되어 있어 rest 중 extra strike나 빠른 동일 줄 restrike를 독립적으로
검증하기 어렵다.

## 3. 레거시 goal·reward에서 배울 것

### 3.1 goal

오른손 random goal은 6줄에서 가능한 **비어 있지 않은 연속 mask 21개** 중 하나를 고르고, event
간격을 `5..44` control frame에서 뽑는다. 현재 event와 미래 4개, 총 5개를 본다.

- actor goal: `(6 string + 1 time) × 5 = 35`
- critic goal: actor goal + `pluck_correct[6] = 41`

연속 mask는 “단현→인접 다현 sweep” 커리큘럼의 합성 fixture로는 쓸 수 있다. 하지만 부분 chord의
빈 줄까지 자동으로 채우는 음악 source 규칙이나 strum 정답으로 가져오면 안 된다. 현재는 명시된
`audible/traversal/muted_mask`와 event별 timing을 우선한다.

### 3.2 reward

레거시 task reward에는 다음 항목이 섞여 있다.

- target string 근접과 올바른/잘못된 pluck
- goal이 없을 때 모든 줄에서 약 3 mm 떨어지는 rest clearance
- pick 가속도와 이동·wrist·joint smoothness
- thumb와 index2/index3 contact의 grip proxy
- `G:pluck_range` net contact force 벌점
- episode 동안 누적되는 `pluck_correct` 기반 보너스

근접·smoothness 아이디어는 후보 진단이나 bounded shaping으로 참고할 수 있다. 반면 영구
`pluck_correct` 보너스, goal-dependent debounce, `G:pluck_range`의 상대·접촉점 미상 net force,
self-collision OFF에서의 thumb-index force는 현재 reward 정본으로 복사하지 않는다.

## 4. reference motion과 dataset의 한계

### 4.1 style clip은 release 정답지가 아니다

[right_hand_motions.yaml](../../related_work/guitar/assets/right_hand_motions.yaml)은
120 Hz의 `scale.json` 4,749 frame과 `strum.json` 278 frame을 묶는다. 유효 길이는 각각 약
39.57 s와 2.31 s다. 두 weight가 `null`이라 loader는 길이 비례로 표본화하며, scale/strum 비율은 약
**94.5%/5.5%**다.

discriminator 입력 key link는 wrist와 손가락 마디이고 `RH:pick`은 포함하지 않는다. JSON frame에도
`RH:pick` key나 attack/release label이 없다. pick marker 궤적은 index2 FK에서 간접적으로 생길 뿐이다.
따라서 이 clip은 다음 용도로만 쓴다.

- wrist/finger posture seed
- 속도·곡률·follow-through 후보 envelope
- scale과 strum의 선택적 style prior
- 리타게팅 또는 trajectory teacher

타현 시각, 정확한 방향, 성공 string, re-arm의 정답 oracle로 쓰지 않는다. 단순 FK 재생에 현재 finite
crossing 조건을 적용한 로컬 감사에서도 검출은 scale 약 10~11회, strum 1회로 희소했다. 검출 위치
`y_g≈[-0.323,-0.314] m`는 현재 preferred zone 중앙을 지지하는 참고값이지만, clip 전체를 정확한
strike label로 바꾸거나 detector threshold를 이 값에 맞춰 보정할 근거는 아니다.

### 4.2 raw mocap도 전용 pick/event annotation이 없다

[dataset](../../related_work/guitar/dataset/README.md)의 `Pick*.csv`와 `Strum.csv`는 손·기타 marker의
3D 위치 열이다. 전용 plectrum tip/base marker, attack timestamp, struck-string label은 없다. occlusion은
`nan`으로 기록된다. 따라서 원시 CSV도 자세와 궤적 분포를 얻는 자료이지 RELEASE 정답지가 아니다.

라이선스는 **CC BY-NC-ND 4.0**이다. 비상업·저작자 표시·변경물 공유 제한을 실제 데이터/파생물 배포
전에 별도로 확인한다.

## 5. 좌표 변환과 checkpoint 주의

[env.py](../../related_work/guitar/env.py)의 `observe_iccgan` parent-link 분기에는
`quatconj(orient)`를 계산한 직후 원래 `orient`로 덮어쓰는 알려진 버그가 있다. 고정 기타에서는
일관된 상수 오차를 정책이 흡수할 수 있어 학습이 동작했지만, 움직이는 G1/G2 기타에서는
기타-상대 불변성을 깨뜨린다. 현재 구현은 반드시 [base.py](../../tab2body/env/base.py)의
`to_guitar_frame`/역회전 계약을 사용하며 이 버그를 checkpoint 호환 목적으로 되살리지 않는다.

`pretrained/right_hand`는 다음 차이 때문에 direct load 대상이 아니다.

- 27 action 부유손 ↔ 30 action 어깨 이하 우팔
- 고정 base·중력 제거 ↔ 좌식 전신·중력
- 레거시 goal/reward/detector ↔ 새 event/matcher 계약
- 잘못된 parent-frame 관측 ↔ 수정된 기타 로컬 관측
- pick-only style 자료 ↔ 어깨·팔꿈치와 후속 fingerstyle까지 포함할 정책

가능한 재사용 방식은 checkpoint actor를 통째로 이식하는 것이 아니라, 레거시 rollout에서 얻은
`pick/wrist/finger` 기타 로컬 궤적을 teacher로 저장하고 현재 팔의 IK/retarget target, hand posture
초기화, 제한적 behavior cloning 또는 진단 reference로 쓰는 것이다. 성공 판정은 새 detector로 다시
계산한다.

## 6. 현재 S0에 채택할 detector 계약

현재 pick S0는 공개 motor phase `READY→APPROACH→RELEASE_RECOVER`와 별도로 다음 내부 상태만 가진다.

```text
ARMED ──유효 swept crossing──> RELEASE pulse ──> WAIT_REARM
  ^                                                   |
  └──── 물리 separation + 방향/이력 + 최소시간 ───────┘
```

프레임 `k-1→k`의 pick 위치를 `p0,p1`, 줄 양 끝을 `a,b`라 하면 다음을 모두 만족해야 release
후보다.

```text
p(t) = p0 + t(p1-p0),  0 < t ≤ 1
q(s) = a  + s(b-a),    0 ≤ s ≤ 1
```

1. xy 교차 분모가 epsilon보다 크고 finite 값이다.
2. 교점이 실제 string segment 내부이며 zone/phrase lane quality를 계산한다. K2 보정 전에는
   zone을 hard reject 조건으로 쓰지 않는다.
3. across-string 속도가 최소값보다 크다.
4. 지정된 경우 방향이 맞다. 정본은 `down=+x_g`, `up=-x_g`다.
5. 교차 z가 최소 depth를 만족한다. 1 mm는 초기 후보일 뿐 GPU 보정 전 확정값이 아니다.
6. 과도한 depth/기타 관통은 성공과 별도 진단한다.
7. detector가 `ARMED`다.

emit record에는 최소 `agent, string, subframe_t, direction, crossing_pos_g, depth,
across_speed, zone_quality`를 넣는다. detector는 현재 goal을 읽지 않는다. matcher가 이후
string/agent/direction/window를 확인해 하나의 목표에만 배정하고, 남는 crossing을 FP로 분류한다.

`CONTACT`와 `LOAD`는 marker만 있는 pick S0의 필수 상태가 아니다. signed-gap/load proxy는 진단으로
남길 수 있지만, 물리 현/피크가 없는 상태에서 가짜 접촉 phase를 성공 조건으로 만들지 않는다.
fingerstyle V2의 pad detector나 물리 pick V2에서는 `armed→contact→load→release`를 별도 적용할 수
있다.

## 7. 검증 순서와 V2 경계

S0는 다음 순서로 검증한다.

1. CPU 합성 궤적으로 finite `t/s`, endpoint, 평행선, 양방향, 속도, depth, re-arm oracle test.
2. scale/strum reference replay로 좌표·분포를 진단하되 event 정답으로 학습하지 않음.
3. GPU에서 6줄×양방향×여러 timestep의 합성 sweep과 rest/jitter/왕복 오타 probe.
4. detector와 matcher를 분리한 뒤 reward adversarial audit.
5. 단현·한 방향부터 PPO를 시작하고 6줄, 양방향, timing, restrike, 인접 전환, strum으로 확장.
6. 정확도 gate를 통과한 뒤에만 style discriminator/BC를 켜고 정확도가 후퇴하지 않는지 비교.

물리 pick V2는 다음을 **함께** 제공할 수 있을 때 재개한다.

- tip/base 또는 blade frame으로 정의되는 orientation과 attack angle
- collision 가능한 mesh, 질량·관성·마찰과 contact 안정성
- 엄지-검지 grasp constraint 또는 slip/regrip 상태
- string deflection/compliance와 force/energy release의 검증 가능한 관측
- face/edge 및 pick 두께를 반영한 detector
- marker S0와 물리 V2의 동일 곡 A/B 정확도·안전·자연스러움 비교

이 조건 전에는 “실제 피크 접촉을 구현했다”고 주장하지 않고
**kinematically plausible virtual-pick release**라고 표현한다.
