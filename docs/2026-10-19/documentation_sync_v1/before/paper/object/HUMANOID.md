# 휴머노이드의 구성과 사양

## 모델과 원본 관계

원본은 `tab2body/assets/smpl_mpl_hands_body.xml`의 SMPL 몸체와 MPL 디테일 손을 결합한 휴머노이드다. 현재 자유 기타 실험에는 `stability_adapter_2/assets/humanoid_fixed_lower.xml` 파생 모델을 사용한다. 몸통과 팔다리의 단순 기하 형상, 손의 상세 메시를 결합하며 피부·연부 조직·의복 변형 모델은 없다.

원본에는66개 body,105개 scalar 관절, Pelvis의 freejoint1개가 선언돼 있다. 원본 자산 README의 “106관절”은 freejoint 선언을 더한 수이며,105개의 제어 채널과 구분한다. 일부 원본 무릎·발가락 scalar 관절은 range 폭0으로, 선언된 관절 수가 모두 독립적으로 움직일 수 있는 관절 수를 뜻하지 않는다.

현재 파생 모델은 양쪽 Hip/Knee/Ankle/Toe의24개 scalar 관절을 제거했다. 해당8개 link의 당시 native 상대 위치·회전을 XML에 넣어 앉은 하체 모양을 유지했다. 하체 body와 충돌 형상을 없앤 것은 아니다. 상체·양팔·손의81개 scalar 관절 정의와 기존 geom은 유지했으며,66개 body 선언도 유지된다. Pelvis freejoint 선언은 남지만 현재 실행에서는 humanoid actor의 root를 `fix_base_link=True`로 고정한다.

![저장된 Isaac Gym 초기 전신 화면](/home/ajou/yigyu/3/paper/object/images/humanoid_native_reference.png)

이 이미지는 `left_neck_near_initial_v1/native_hold_v4`의 실제0초 프레임이다. 고정 하체와 상세 손을 보여주는 참고 화면이며, 진행 중인 두 블록 받침 실험의 최신 자세나 접촉 성공을 뜻하지 않는다.

## 관절 계층과 수

주요 연결은 `Pelvis → Torso → Spine → Chest`다. Chest에서 `Neck → Head`와 양쪽 `Thorax → Shoulder → Elbow → Wrist → 손바닥·손가락`으로 분기한다.

| 구간 | scalar 관절 수 | 구성 |
|---|---:|---|
| Torso·Spine·Chest | 9 | 각 link3축 |
| Neck·Head | 6 | 각 link3축 |
| 양쪽 Thorax·Shoulder·Elbow·Wrist | 24 | 한쪽12관절 |
| 양손 손가락 | 42 | 한쪽21관절: 엄지5 + 나머지4손가락 각각4 |
| **현재 합계** | **81** | root의 세계 자유도와 제거한 하체24관절 제외 |

한쪽 Thorax부터 손가락까지는33관절, 양쪽 합계66관절이다. 따라서 과거 한쪽33관절 제어 범위와 현재 상체 전체81관절 사양을 혼동하지 않는다. 손바닥은 손목에 붙은 고정 body이며 별도의 scalar 관절은 없다.

관절별 각도 한계와 축은 [81관절 표](/home/ajou/yigyu/3/paper/object/JOINT_SPECIFICATIONS.md:1)에 모두 기록했다. 예를 들어 Torso의 `_x/_y/_z` XML 축은 각각`[1,0,0]`, `[0,0,1]`, `[0,1,0]`이다. 이름 suffix는 세계 좌표축도 아니고 항상 같은 로컬 축을 뜻하는 공통 규칙도 아니다. 손가락은 각 관절의 실제 XML axis를 따른다.

## 형상과 신체 치수

몸통·목·팔·다리는 주로 capsule과 box이고, 손목·손바닥·손가락은 mesh다. humanoid body 아래의 geom 선언은 capsule15개, box6개, mesh34개다. 바닥 plane1개는 신체 형상에 포함하지 않는다. body 선언에는 마커와 형상 없는 프레임도 포함돼 있어66 body가66개 충돌 조각을 뜻하지 않는다. importer가 만드는 실제 shape 수와 충돌 제외는 실행 기록을 따른다.

| 항목 | 값 | 측정 기준 |
|---|---:|---|
| 중립 source 전체 높이 | 1.7205m | 원본 q=0 형상의 위–아래 범위 |
| 중립 source Head 원점 높이 | 1.5697m | 원본 모델의 세계 Z |
| 어깨 원점 간 거리 | 315.955mm | 양쪽 Shoulder joint/body 원점의 거리 |
| 왼쪽 상완 길이 | 267.555mm | L_Shoulder→L_Elbow 원점 거리 |
| 오른쪽 상완 길이 | 274.827mm | R_Shoulder→R_Elbow 원점 거리 |
| 왼쪽 전완 길이 | 253.078mm | L_Elbow→L_Wrist 원점 거리 |
| 오른쪽 전완 길이 | 249.810mm | R_Elbow→R_Wrist 원점 거리 |
| Head box 외형 | 121.8×159.4×219.2mm | XML box의 각 half-size를2배한 값 |

1.7205m는 현재 앉은 자세의 높이나 실측 사람의 키가 아니다. 원본 중립 형상을 읽기 전용으로 측정할 때만 zero-width 하체 관절의 제한을 완화했으며, 실제 실행 자산을 바꾸지 않았다. 머리 box가 전체 외곽 높이에 영향을 주므로 어깨·상완·전완의 원점 거리도 함께 제시한다. 어깨 원점 간 거리는 피부 외곽 어깨너비와 다르다.

## 질량·관성과 접촉

저장된 fixed-lower native actor의 body 질량 합계는 **73.316411848kg**이다. 기준 실행의 전체 body별 질량은 [기계 판독용 사양](/home/ajou/yigyu/3/paper/object/specifications.json)의 `humanoid.native_mass_by_body_kg`에 기록했다. 손에는 explicit inertial·COM·대각 관성 선언이 있고, 몸통과 팔다리의 여러 primitive에는 density가 선언돼 있다. 질량·관성은 형상과 importer의 구성에 따른 시뮬레이션 파라미터이며 사용자나 실물 인체의 실측 질량 분포가 아니다.

현재 환경은 양손 및 비인접 팔–몸통 내부 충돌을 허용하도록 importer 필터를 조정한다. 연결부와 같은 손 내부의 기존 제외는 유지하므로 모든 body 쌍이 충돌하는 설정은 아니다. `LH:thumb_pad`는 별도의 지원 proxy이고 현재 물리 접촉에서 제외한다. 기준 native readback에서 사람/기타의 실제 friction은1.0, contact offset은약0.1mm, rest offset은0이다. XML의 `condim=1` 또는 friction 선언만으로 PhysX 실행의 손 마찰을 판정하지 않는다.

## 모델 사양과 제어 설정의 분리

XML의 stiffness·damping·armature와 실행 시 설정하는 PD/effort cap은 별개다. root·하체가 고정돼 있어도 몸통9관절은 고정 link가 아니며, 제어 목표와 실제 관절각이 다를 수 있다. 현재 연구에서는 머리 움직임은 작게, 척추 구간은 작게, Thorax부터 양손까지는 더 크게 제어하는 방향을 사용한다. 다만 POSITION/EFFORT의 소유 관절, 보정 토크와 PD gain은 진행 중인 실험별 설정이므로81관절 모델의 영구 사양으로 확정하지 않는다.

기준 저장 실행은 양팔24관절 EFFORT/나머지57관절 POSITION이다. 이 값은 여기 복사한 native reference의 조건이며 이후 몸통 제어 실험의 설정을 대표하지 않는다. XML 관절 표는 실행의 힘 명령이나 측정 토크 표가 아니다.

## 실제 파일과 근거

- [현재 하체 고정 XML 사본](/home/ajou/yigyu/3/paper/object/models/stability_adapter_2/assets/humanoid_fixed_lower.xml)
- [원본105관절 XML 사본](/home/ajou/yigyu/3/paper/object/models/tab2body/assets/smpl_mpl_hands_body.xml)
- [하체 제거·고정 변환 manifest](/home/ajou/yigyu/3/paper/object/evidence/humanoid_fixed_lower_manifest.json)
- [저장된 초기81각·native body 이름·PD](/home/ajou/yigyu/3/paper/object/evidence/native_initial_reference.json)
- [native 인간 질량·COM과 제어 참고값](/home/ajou/yigyu/3/paper/object/evidence/humanoid_native_effort_reference.json)
- [native shape 속성](/home/ajou/yigyu/3/paper/object/evidence/native_shape_reference.json)

원본 실행 자산은 [fixed-lower XML](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml)이며 원본과 공용 자산은 보존했다.
