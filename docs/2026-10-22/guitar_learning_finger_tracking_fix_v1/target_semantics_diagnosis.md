# Multi-axis target semantics — read-only evidence

현재 자료는 **두 노출 축의 숫자와 실제 전체 회전이 같지 않을 수 있음**을 보여준다. 이것만으로 target의 Euler/rotvec 오입력이나 숨은 자유도 버그를 확정할 수는 없다. 공개 PhysX에는 2-DOF spherical의 잠긴 축을 내부 구속식으로 처리하며 drift를 허용하는 설계가 실제 존재한다. 현재 Gym 바이너리와 그 공개 소스의 정확한 일치는 아직 확인하지 않았다. active435·기존 봉인 자료·구동 gain·물리는 변경하지 않았고 새 native/GPU/GL 실행도 하지 않았다.

## 현 프로젝트의 관측과 API

`guitar_learning/assets/tab2body/assets/smpl_mpl_hands_body.xml:226–258`은 ring1/pinky1 한 body에 x/z 두 hinge를 둔다. `gpu/scene.py:190–210`은 native DOF 순서를 검사하고 POSITION 속성을 설정·동등 readback 검사한다. 현재 Python은 native105 위치 목표를 전달하며, 부모/자식 quaternion을 별도 목표로 전달하지 않는다. 실제 import 후 joint type은 이번 N6 도구가 `get_actor_asset → get_asset_joint_names/get_asset_joint_type → get_joint_type_string`으로 기록한다. 그 결과 전에는 XML의 두 hinge 선언만으로 내부 표현을 단정하지 않는다.

로컬 SDK의 `isaacgym/docs/programming/physics.html:180,266–267`은 DOF 단위 목표와 POSITION PD를 설명한다. `isaacgym/docs/api/python/gym_py.html:2834–2850`은 asset joint type 조회를 제공한다. 같은 문서의 `set_dof_position_target_tensor`와 `set_actor_dof_position_targets`는 scalar DOF 목표 경로이며, 현재 조사의 공개 Gym Python API에서는 articulation의 특정 관절에 직접 quaternion drive나 locked-axis ERP를 지정하는 경로를 확인하지 못했다. rigid-body attractor로 우회하면 새로운 외력을 더하는 것이므로 현재 제약을 보존하는 최소 수정으로 취급하지 않는다.

기존 prepared case2/10의 body106을 CPU SciPy Rotation으로 읽었다. palm→finger1 상대회전의 초기 고정 오프셋은 `Rzero=Exp([qx0,0,qz0])^-1 Rrelative0`로 보정했다. 아래는 `Rrelative Rzero^-1`의 회전 log이며, 주입/새 물리가 없다.

| case | 시점 | 보정 log(x,y,z) rad | log의 x/z와 native q 최대 차이 | Exp([qx,0,qz])와 실제 회전 차이 |
|---|---|---|---:|---:|
| ring1_z+ /2 | hold 끝 1.5s | (0.833108407, −0.047020006, 0.328216175) | 0.000001866rad | 0.045464765rad |
| pinky1_z+ /10 | hold 끝 1.5s | (1.560906491, −0.099682700, −0.088170636) | 0.000000439rad | 0.089835236rad |

같은 방식의 초기 y는 수치상 0이고, 복귀 끝 3s에는 각각 +0.000118273/−0.000082574rad다. 따라서 초기 frame-offset만으로 그 중간 회전 차이를 설명할 수 없다. 동시에 x/z가 log 성분과 맞으므로 현재 명령을 무조건 RxRz Euler로 재해석해야 한다는 근거도 없다. 두 숫자에서 생략된 y를 0이라고 가정한 FK가 실제 손가락 pose와 달라질 수 있다는 점은 별개의 확정 관측이다.

raw 입력은 `guitar_learning_ring_pinky_probe_v1/native_run/prepared/case_002.npz`, `case_010.npz`이며 SHA는 `native_tracking_diagnosis.json`에 있다. 보정 오프셋을 쓰지 않은 root의 상대 log와 약 2.6–4.5e−5rad 차이가 나지만 같은 현상을 보인다. 임계값을 느슨하게 해 성공으로 바꾸거나 N6 결과를 미리 성공 처리하지 않았다.

## 공식 공개 구현에서 확인한 내용

[PhysX4.1 JointData.h 152–170행](https://github.com/NVIDIAGameWorks/PhysX/blob/4.1/physx/source/lowleveldynamics/include/DyFeatherstoneArticulationJointData.h#L152-L170)은 2-DOF spherical에 잠긴 회전축을 내부적으로 추가하고 구속식으로 처리한다. 주석은 과구속을 피하는 대신 축 오차가 생길 수 있음을 명시한다. 이는 노출된 두 축 외의 회전 성분이 관측될 수 있는 구체적인 구현 근거이며, 그 오차의 크기가 현재 요구에 적절하다는 인증은 아니다.

[PhysX4.1 ForwardDynamic.cpp 831–850행](https://github.com/NVIDIAGameWorks/PhysX/blob/4.1/physx/source/lowleveldynamics/src/DyFeatherstoneForwardDynamic.cpp#L831-L850)은 상대 quaternion의 axis-angle 벡터를 motion basis에 투영해 위치를 읽는다. 같은 파일 1319–1327행에는 TGS 후 pose에서 관절 위치를 다시 읽는 경로가 있다. 따라서 두 읽기 좌표가 전체 회전의 일부 log 성분인 동작은 공개 구현과 정합적이다. 이것이 현재 Gym의 좌표/프레임 변환까지 모두 증명하지는 않는다.

[PhysX4.1 Joint API 61–66행](https://github.com/NVIDIAGameWorks/PhysX/blob/4.1/physx/include/PxArticulationJointReducedCoordinate.h#L61-L66)은 축별 scalar target/velocity와 drive gain을 받는다. [4.1 Articulation.cpp 2351–2414행](https://github.com/NVIDIAGameWorks/PhysX/blob/4.1/physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp#L2351-L2414)은 axis target/drive를 구성하고, 2566–2608행은 별도 locked-axis quaternion 오차를 구속식으로 만든다. 이 두 경로가 유한 회전에서 서로 영향을 줄 수 있다는 것은 검사 가설이며, 이 파일만으로 현재 오차량을 계산하지 않았다.

[최신 NVIDIA PhysX main의 2064–2121행](https://github.com/NVIDIA-Omniverse/PhysX/blob/main/physx/source/lowleveldynamics/src/DyFeatherstoneArticulation.cpp#L2064-L2121)은 다축 목표 벡터로 quaternion을 만들고 회전 오차를 투영하는 구현을 보인다. 버전마다 내부 접근이 달라질 수 있으므로 이를 현재 Gym에 이미 적용된 동작이나 가져다 붙일 확정 패치로 취급하지 않는다. [공식 PhysX5.1.1 설명](https://nvidia-omniverse.github.io/PhysX/physx/5.1.1/docs/Articulations.html#articulation-joints)도 다축 quaternion 적분/잠긴 축 보정을 설명한다. MJCF importer 자체의 공개 소스는 로컬 SDK에서 찾지 못했다. 현재 native joint/frame/drive 변환의 완전한 원인은 미확정이다.

## 제약을 보존하는 가장 작은 검증·수정 후보

- 이번 N6에서 x=0/.8/1.56 세 목표, 실제 x, z 추종비, 보정 y, 자손 contact, DOF total force를 함께 비교한다. contact가 있는 행도 보존하되 무접촉처럼 합치지 않는다. 기본 POSITION48/EFFORT57, native105/가동97/고정8, 힘 한계, 준비자세035, body 수는 그대로다.
- 그 결과가 잠긴 축 구속식 수렴 문제와 맞으면 **진단 실행에서만 position iteration 4→8/16 한 항목**을 바꾸는 비교가 작은 다음 검사다. 수렴성 자체에 근거한 검사이며 기본 물리 승격안이 아니다. 과거 전신/기타 안정성 실험의 iteration 결과를 이 손가락 오차가 이미 해결됐다는 자료로 재사용하지 않는다. 숨은 y·z 오차·접촉하중·안전·비시험 목표가 함께 개선되는지 봐야 한다. 이는 source/DOF/모드를 보존하지만 physical 계약은 달라진다.
- 정확한 drive 좌표 변환은 native readback과 실제 회전의 관계가 입증될 때만 제출 경계에 최소 적용한다. 현재 x/z→회전log 투영의 일치만 보면 입력 오기입은 아직 확인되지 않았다. 생략된 y 구속 오차는 2성분 target 변환만으로 제어되지 않을 수 있다. 단순 `1/cos²(x/2)` 증폭은 기준 자세 밖/한계/접촉에서 검증되지 않았고 미보고 y를 키울 수 있다.
- bounded 목표오차 피드백은 105/모드/cap을 보존하는 별도 후보지만, 그 자체가 정확한 좌표 변환은 아니다. 추가 command bias와 논리 목표를 구분하고 clamp/anti-windup/반전/접촉 저항을 검사하기 전 기본값으로 삼지 않는다. 3축 추가, 별도 hinge body, 손 전체 EFFORT 전환은 이번 최소 범위를 넘는다.

현재 단계의 권고는 **K/D나 마찰을 올리지 않고 N6 actual 결과로 drive/constraint 의미를 좁히는 것**이다. 수정이 실제로 필요해지면 GPU-left 전용 계약을 새로 명시하고 CPU/right/공통 원본 asset 보존과 strict checkpoint 호환성 거부를 함께 검증해야 한다.
