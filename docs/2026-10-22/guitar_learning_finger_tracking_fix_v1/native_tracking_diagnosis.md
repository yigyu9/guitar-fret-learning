# Native finger tracking diagnosis — read-only

현재 근거로 **마찰 때문에 약 1.19 N·m가 소모된다거나 gain 부족이라고 결론낼 수 없다.** 가장 우선할 진단은 두 축을 가진 기저 관절의 native 목표/회전좌표 해석이다. 실제 원인은 아직 확정되지 않았고 이 조사에서 소스·물리·gain을 바꾸거나 GPU/GL을 실행하지 않았다.

## 속성과 적용 경로

- `guitar_learning/gpu/scene.py:193–210`: pinned `native_PD_properties` 전체를 복사한 뒤 GPU left의 LH21 stiffness/damping만 교체하고, actor 속성 readback 전체의 정확한 일치를 검사한다. 모든 LH21의 friction=0, armature≈0.01, 엄지5 effort=4/나머지16 effort=20, velocity=100, driveMode=1(POSITION)이다. 현재 유효 gain은 일반 손가락 K12/D1.5, 엄지 K8/D1.25다. 관절별 원본/유효값·한계는 동반 JSON에 모두 기록했다.
- `guitar_learning/core/finger_control.py:7–12`가 그 profile의 원천이다. `native_run/prepared/visual_initial.json`의 K20/D5는 override 전 pinned 초기 metadata이므로 현재 K20/D5로 해석하면 안 된다. 기존 실행은 초기화 readback 검사를 통과했지만, post-prepare actor별 PD dump와 DOF solver force는 저장하지 않았다.
- `guitar_learning/gpu/control.py:462–464`는 POSITION 축에 외부 effort를 0으로 만든다. 손가락은 native POSITION drive를 이용한다. armature는 관성 항이며 정지 오차만으로 마찰 토크로 바꿀 수 없다.
- `guitar_learning/assets/tab2body/assets/smpl_mpl_hands_body.xml:226–258`: ring/pinky base는 같은 body에 x/z 두 hinge를 선언한다. 각 source joint는 K10/D0.2/armature0.01, frictionloss 선언은 없다. ring z한계 ±20°, LH pinky z는 −20°..40°다. 두 축이 같은 몸체에 있다고 gain까지 하나를 공유한다고 단정할 수 없다. source K10이 actor override와 별개 passive spring으로 남는지도 현재 자료로는 증명되지 않았다. source motor gear20을 현재 native PD torque 배수로 해석하지 않았다.

## 실제 기록의 좁은 재검산

아래는 prepared probe의 1초 pulse 후 0.5초 hold 끝(physics step360)이다. 초기 상태와 목표는 기존 원자료에서 읽었으며 새 물리실험은 없다.

| case / 축 | q−target (rad) | qd (rad/s) | 실제 증분/목표 증분 | cos²(base x/2) | 기하식 예측 q 잔차(rad) |
|---|---:|---:|---:|---:|---:|
| 2 / LH:ring1_z | -0.020850092 | 0.000111453 | 0.840276 | 0.839456 | 0.000107107 |
| 3 / LH:ring1_z | 0.032359816 | -0.002751302 | 0.838263 | 0.839456 | 0.000238527 |
| 10 / LH:pinky1_z | -0.099215741 | 0.001992570 | 0.503883 | 0.504113 | -0.000045986 |
| 11 / LH:pinky1_z | 0.082150817 | -0.008686153 | 0.486961 | 0.504113 | 0.002746146 |

case10의 pinky1/2/3 native net-contact norm은 전체 3초 내내 모두 0이다. hold 끝 scalar `12*(target−q)−1.5*qd`는 약 1.1876이지만, 이는 scalar PD 가정으로 계산한 표현일 뿐 실제 drive/마찰 토크 측정이 아니다. 최종 원래 목표 복귀 후 오차는 +0.000310rad다. case11은 pinky3 peak3.0523N이며 hold 동안 peak1.1809N이고, 다른 기저축 x가 상한에 도달한다. 따라서 case11을 순수한 마찰 검사로 쓰면 접촉과 다축 한계 반응을 섞게 된다. net-contact=0은 관절 내부 구속력·중력·다른 링크와의 동적 결합이 없다는 의미가 아니다.

case2/3 ring과 case10 pinky의 비율은 `cos²(base x/2)`와 약 0.00024rad 이내로 맞는다. 서로 다른 두 기저각에서 나타난 이 패턴은 다음 실험을 정하는 근거다. **그 식이 SDK 구현 원인이라는 증명이나, 역수를 곱하면 해결된다는 검증은 아니다.** 다른 관절/다른 자세/양방향·한계에서 일반화된다고 주장하지 않는다.

## 문서 근거와 확인 한계

로컬 SDK `isaacgym/docs/programming/physics.html:180,218–240,266–267`는 actor DOF drive 속성 및 POSITION PD를 설명한다. `isaacgym/docs/api/python/struct_py.html:1375–1377`는 joint-space armature와 link inertia 변경 방식의 차이를 설명한다. 현재 scene은 `use_physx_armature`를 명시하지 않으므로 이 armature 숫자가 실제 어느 내부 경로로 적용됐는지 추가 native query 없이 단정하지 않는다.

[공식 PhysX 5.1.1 articulation 설명](https://nvidia-omniverse.github.io/PhysX/physx/5.1.1/docs/Articulations.html)은 drive가 축별로 설정되고 implicit하게 풀리며, 다축 spherical은 quaternion 기반 적분과 locked-axis 보정을 쓴다고 설명한다. [공식 joint API](https://nvidia-omniverse.github.io/PhysX/physx/5.1.1/_build/physx/latest/class_px_articulation_joint_reduced_coordinate.html)는 legacy joint friction을 전달 하중에 비례하는 무차원 joint-wide 계수로 설명한다. 이 자료는 모델 해석의 근거이며, 폐쇄된 현재 Gym importer/PhysX build의 내부 passive spring이나 목표 변환을 직접 확인한 자료는 아니다. 로컬 예전 문서의 spherical 지원 예정 문구만으로 현재 asset이 지원되지 않는다고 판단하지 않았다.

## 가장 작은 다음 검증과 조건부 수정

1. root의 새 native 진단에서 `get_asset_joint_type`(로컬 API 문서 `gym_py.html:2834–2850`)와 before/after-prepare 전체 DOF 속성을 저장한다. 준비자세/현재 gains는 유지한다.
2. 상태 주입 없이 정상 action으로 기저 x를 2–3개 도달 가능한 각도로 이동·정지시킨 뒤 작은 양/음 z pulse를 준다. q/qd/제출 target, 부모·자식 상대 quaternion, 자손 전체 native contact, DOF force를 기록한다. 센서값 역시 순수 마찰/drive 성분이라고 단정하지 않는다.
3. 고정 joint-frame을 보정해 상대회전을 exp(xX+zZ), RxRz, RzRx와 비교한다. 같은 명령의 실제 회전/표현 좌표와 목표 해석을 먼저 분리한다. 필요할 때만 임시 GPU 진단 asset에서 source tested-joint K/D를 0으로 하고 실제 actor K12/D1.5를 동일하게 유지해 별도 passive 잔존 여부를 비교한다.
4. 목표좌표 부정합이 재현·확인되면 GPU left 제출 경계에 정확한 변환만 넣는 것이 후보 최소 수정이다. logical 누적목표/한계/속도/cap과 실제상태를 보존하고, 검증되지 않은 `1/cos²` 경험적 보상이나 K상향은 도입하지 않는다. 별도 passive 잔존이 확인되면 그때 GPU용 asset의 해당 요소만 교정한다. 어느 경우도 새 control/physical 계약을 명시하고 기존 checkpoint strict-load를 거부해야 한다.

공유 `default_profile()` 수정은 CPU left에도 영향을 준다(`runtime/finger_session.py:94–146`). 따라서 GPU 전용 수정의 검증에서는 CPU/right와 공통 asset을 보존해야 한다. 이번 단계에서는 모든 활성 파일을 변경하지 않았다. 반대로 아직 원인이 미확정이므로 production 수정안을 확정하지 않았다.

재계산은 sealed raw NPZ를 CPU NumPy로만 읽었다. 입력 SHA와 관절별 속성 및 정밀 수치는 동반 JSON에 기록했다. 원본 phase/manifest/source에는 쓰지 않았다.
