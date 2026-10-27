# 왼쪽 몸통 기울임과 겨드랑이 지지 비교

**몸통을 왼쪽4° 기울이는 초기 자세는 구현했지만, 이번 세 조건 모두 겨드랑이 지지로 기타를 유지하지 못했다.** 수정한 자연 팔 모양을 기준으로 사용하고 손목·손가락·왼팔의 초기 관절각은 보존했다. 기타는 자유 상태이며 root·하체 고정, 스트랩 OFF, 왼손 잡기 없음이다.

## 방향과 초기 자세

이번 시험의 왼쪽은 **휴머노이드의 왼쪽·기타 넥 쪽**이다. 정면 화면에서는 오른쪽으로 보인다. 화면 왼쪽·바디 쪽을 뜻하는지 방향 확인 질문은 대기 중이다. 답변이 오기 전 반대 방향을 채택하거나 같은 결과로 해석하지 않는다.

![겨드랑이에 가까이 배치한 왼쪽4° 초기 자세 — 실제 Isaac Gym](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v2/left4_nearbody/media/initial_native.png)

[전체 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v2/left4_nearbody/initial_values.json:1), [기준·기울임·조합·추가 누름 초기 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_four_conditions_v2.png). 카메라/기타 초기 위치가 다른 정성 비교이며 정확한 사진의3D 복원이나 해부학적 적합성 인증이 아니다.

## 몸만 기울이면 간격이 커졌다

같은 기타 p/q와 다른66 scalar 초기각에서 추가 Chest 왼기울임0/4/8°를 비교했다. 오른쪽 어깨가 올라가 상완 근위65%–바디 source 간격은18.523/42.256/65.897mm로 커졌다. 팔 scalar 초기각 동일은 팔 world 위치 동일을 뜻하지 않는다. Torso25%·Spine62.5%·Chest100%의 추가 world 회전 목표로 기울임을 분배하고 머리는 원 world 방향에 가깝게 보정했다. DOF 이름 suffix를 world 축으로 해석하지 않는다.

![몸통만 왼쪽으로 기울인 source 간격](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png)

[소스 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/search_v1/search.json:1). 소스 기하 간격은 실제 PhysX cooked 접촉·관통 또는 겨드랑이 지지 인증이 아니다. 상완 근위65%는 이 단순 humanoid 모델의 겨드랑이 쪽 근사이며 연질 조직이 있는 실제 겨드랑이와 다르다.

## 실제5초 조건 비교

| 조건 | 바디 BB 중심 이동 | actor-root 이동 | 전체 SO3 회전 | 상완 접촉 | 머리 접촉 |
|---|---:|---:|---:|---:|---:|
| 몸만 왼쪽4°·기타 초기값 유지 |187.876mm|258.387mm|73.904°|0/1200|782/1200|
| 왼쪽4°+기타·오른팔 소폭 초기 보정 |205.134mm|323.030mm|50.178°|0/1200|0/1200|
| 동일 조합+작은 상완 누름 제어 |203.862mm|319.918mm|49.689°|0/1200|847/1200|

세 조건 모두 기타 유지 실패다. 두 머리 접촉 조건은 채택하지 않는다. 가운데 조건은 머리 접촉이 없지만 이동·회전이 커 유지 성공 초기값으로 등록하지 않는다. 소스2차 후보는 근위 간격7.967mm로6mm 조건을 초과해 native를 실행하지 않았으며,3차에서4.696mm·Hip 최소2.596mm로 줄였지만 실제 상완 접촉은 생기지 않았다.

![왼쪽4°+초기 배치 보정의 전체0–5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/left4_nearbody_whole_body.mp4)

[세 조건 전체·손근접 영상6개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md:1), [실제0/2/5초 캡처·설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/README_V2.md:1). 실제 물리는240Hz×5초1200step, 제어60Hz×5초300회다. 영상은 최초/최종 프레임 포함151프레임·30fps로 인코딩5.033초이며 종료까지 실제 native 렌더를 저장했다. 첫 조건이2초 뒤0.614mm/0.237°만 변해도 이미 크게 이탈하고 머리에 닿은 상태에 정착한 것이므로 성공이 아니다.

BB 중심은 소스 바디 bounding box 중심이며 COM이 아니다. 전체 회전은 초기 대비SO3 크기이며 축별 Euler 오차가 아니다. 접촉은240Hz endpoint 존재 여부이며 N 힘·지지 비중이 아니다. 양의 raw lambda도 N으로 해석하지 않는다.

## 초기값·제어·검증

조합은 기타 회전을 유지하고 world X−30mm·Y−36.087mm·Z+27.674mm 초기 배치 보정과 작은 right9 조정을 적용했다. 원 자연 팔 기준Thorax±0.05rad·Shoulder/Elbow±0.25rad 안이며 Wrist3·손가락·왼팔 초기각을 바꾸지 않았다. 실제 elbow 외측 위치는 유지됐지만 팔 world orientation은 조금 달라졌다. 조합과 추가 누름 조건의 initial JSON 전체는 동일하다.

모든 조건은 전완의 초기world 기준점을 인간 right12 EFFORT로 제어하고 other69 POSITION 목표를 유지한다. 추가 누름 조건만 근위 R_Shoulder 인간 기준점의 초기 표면 반대6mm 목표를 더했다(K2000/D30/cap30N). 기존 전완도 능동 제어이므로 순수 수동 대 능동 비교가 아니다. point cap30N은 각 점별 요청 상한이며 합계30N·측정 접촉력이 아니다. 최대 상완 요청 norm21.392N이었지만 실제 상완 접촉0/1200이므로 누름 지지 성공으로 설명하지 않는다.

기타 directforce·부착·런타임 pose 쓰기는 없다. body/head는 새로운 초기 목표를 유지하며 root/lower는 모델에서 고정했다. 이탈 감지 래치는 관측값이며 토크 차단/시뮬레이션 종료가 아니다.

[첫 조건 강화 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v2/verification.json:1), [조합 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v3/verification.json:1), [두 점 합산 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v4/verification.json:1). 초기81 q·실제q·candidate SHA·POSITION69 readback/state보존·각 점 native 속도/J·총 요청/clip/제출토크·1200회 actor effort를 검사했다. 모델 전체 중력보상/전체 Jacobian 또는 물리적 유지 성공 인증은 아니다. 첫 분석기 손목 마스크 검수 한계는 새v2에서 보완했고 이전 분석도 보존했다.

## 다음 단위

방향 표현을 맞춘 뒤 실제 cooked 상완–바디 접촉 위치와 시작 직후 기타 이탈 경로를 먼저 시각화한다. 현재 결과를 지지 성공 또는 기본 학습 초기값으로 사용하지 않는다. 자연 팔 모양을 유지하면서 바디 상단·겨드랑이 쪽 상완·허벅지의 배치를 함께 맞추며, 부착이나 과도한 팔 회전으로 해결하지 않는다.

[계획1](/home/ajou/yigyu/3/stability_adapter_2/LEFT_LEAN_AXILLA_PLAN_V1.md:1), [조합 계획3](/home/ajou/yigyu/3/stability_adapter_2/LEFT_LEAN_AXILLA_PLAN_V3.md:1), [상완 누름 비교 계획4](/home/ajou/yigyu/3/stability_adapter_2/LEFT_LEAN_AXILLA_PLAN_V4.md:1). [변경 파일 절대 경로·줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/CHANGED_FILES_v1.md:1)과 각 실행 원본을 보존한다.
