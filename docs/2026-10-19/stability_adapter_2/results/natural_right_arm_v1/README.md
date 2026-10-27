# 참고 사진에 따른 오른팔 자세 수정

상완이 몸 앞을 가로지르는 이전 안정 후보를 연주 자세로 채택하지 않는다. 사진처럼 상완을 몸 오른쪽에 두고, 팔꿈치를 바깥·아래에 두며 전완이 바디 앞을 지나도록 초기 관절각을 바꿨다. **초기 팔 모양은 개선됐지만 스트랩 없이 왼손을 떼고 자유 기타를 유지하는 데는 실패했다.**

## 초기 자세와 영상

![수정한 초기 오른팔 — Isaac Gym](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/initial_native.png)

[초기값 전체](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/initial_values.json:1), [사진·이전 자세·수정 자세 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/artifacts_v1/README_v1.md:1). 오른손은 타현 위치 근처지만 이 시험에 fret·strike 체크포인트는 연결하지 않았다. 왼팔은 비접촉 목표를 유지했다.

![전체 0–5초 — 자세 유지 강도 조정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/whole_body.mp4)

[손 근접 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v2/front160mm/media/hands.mp4). 151프레임/30fps이며 실제 물리는 0–5초 1200step 계속됐다. 인코딩 길이5.033초는 처음과 마지막 프레임을 포함하기 때문이다. 영상 정착이 목표 만족을 뜻하지 않는다.

## 5초 비교 결과

| 조건 | 바디 BB 중심 이동 | 기타 actor-root 이동 | 전체 회전 SO3 | 머리 접촉 표본 | 판정 |
|---|---:|---:|---:|---:|---|
| 자연 팔 초기 자세·낮춘 제어 강도 | 163.447mm | 287.455mm | 62.320° | 0/1200 | 기타 유지 실패, 팔 모습 검토용 기준 |
| 같은 초기값·전완 world 기준점 위12mm | 194.398mm | 264.687mm | 76.809° | 812/1200 | 큰 회전·머리 접촉으로 거절 |

[첫 비교 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v1/verification.json:1), [위12mm 비교 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/analysis_v2/verification.json:1), [위12mm 전체 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v3/front160mm_lift12mm/media/whole_body.mp4). 바디 중심은 소스 바디 bounding box의 중심이며 질량중심과 다르다. 회전은 축별 각도 변화가 아닌 초기 대비 SO3 상대 회전 크기다. 접촉 표본은240Hz native query 존재 여부이며 접촉력·지지 비중이 아니다.

첫 조건의 전완 접촉1077/1200, 왼팔·손 및 머리 접촉0/1200이었다. 오른어깨3개의 scalar 관절각은 목표 대비 최대1.40° 이하 변화했다. DOF 이름의 x/y/z를 world 회전축으로 해석하지 않는다. 두 번째 조건은2→5초1.690mm/0.646°로 작아졌지만 이미 크게 이탈한 자세에서 머리에 접촉해 정착했다.

## 설정과 한계

root·하체 완전 고정, 기타 free, 스트랩 OFF, 왼손 잡기 없음. 오른팔12관절만 EFFORT 제어하고 other69는 POSITION 목표를 유지했다. 기타에 직접 외력을 적용하거나 런타임 pose를 덮어쓰지 않는다. 전완의 한 world 기준점을 인간 관절 토크로 유지하며 기타 회전 feedback은 아직 없다. 점 힘 요청30N은 측정 접촉력이 아니다. 이탈 플래그는 관측 래치이며 토크 차단이나 종료를 뜻하지 않는다.

초기 기타 회전은 기존과 같고 위치는 기존 낮은 후보보다 world 오른쪽8.052mm·앞109.437mm·아래19.842mm다. 어깨는 기준 초기값 대비±0.55rad, 손목은 각 scalar[-0.35,+0.35]rad 안에서 선택했다. 소스 겹침 검사를 통과했지만 PhysX cooked 형상의 관통 인증은 아니다. 팔꿈치 하강80mm는 단일 참고 사진에 근거한 확정 기준이 아니어서 이번 **시각 진단에만**60mm를 사용했다. 실제 후보 하강64.051mm·외측252.155mm였다.

처음 높은 제어 강도의 native_v1은0.125초의 물리 후 다음 step 진입에서 속도 검증에 걸려 중단했다. [실패 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/native_v1/front160mm/failure.json:1)은 보존했으며 전체5초 영상으로 취급하지 않는다. native 진단은 중단1회·완료2회이고 학습은 실행하지 않았다.

## 다음 작업

수정된 자연 팔 모양을 기준으로 삼되 유지 성공 초기값으로 등록하지 않는다. 전완이 실제 바디 상단과 허벅지 지지를 함께 만들도록 기타의 앞뒤 배치를 다시 맞추는 것을 우선한다. 이때 어깨·손목 큰 회전으로 돌아가지 않는다. 이후 현재 기타 회전을 관측해 작은 인간 관절 보정을 추가하고, 필요하면 왼손 넥 지지와 비교한다. 실제 지지점과 자연스러움을 확인한 뒤 연주 제어를 연결한다.

[현재 실행 계획](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_RIGHT_ARM_REFERENCE_PLAN_V7.md:1), [실행 구현](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v7.py:73), [검증 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_natural_right_arm_v1.py:19). 변경 파일 전체 경로·실제 줄 번호는 [색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/CHANGED_FILES_v1.md:1)에 기록한다.
