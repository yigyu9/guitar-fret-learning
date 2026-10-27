# 교정 자세의 양발 접지와 좌석 높이 조정

2026-10-16. 사용자: 하체가 안정적으로 바닥에 닿도록 조정하며 앉는 cube 크기도 변경 가능. 기존 source4/play phase는 불변 보존. 새 결과는 /home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/seated_foot_support_v1, 새 코드는 /home/ajou/yigyu/3/stability_adapter_2/seated_foot_support_v1.

## 판단과 가정

현재 source4 발 source box minZ: LAnkle21.173/LToe19.949/RAnkle25.727/RToe25.785mm. 이전 실제5초 시험의 step>0 foot 접촉0. Root고정이므로 cube만 낮추면 발은 내려가지 않는다. Root고정은 실행 중 고정으로 유지하되 초기높이를 변경한다. 상체·기타를 공통 수직 이동해 humanoid 상대 좌우배치/넥방향을 보존하고, 좌석 fullheight도 같은 양으로 줄여 앉은 상대높이를 보존한다. cube 바닥z0이므로 halfheight는 공통변위의 절반만 변경한다.

## 단계와 사전 판정

- [ ] source V1: 공통 초기Z −28mm, cube full .400×.280×.492→.400×.280×.464m, root .592→.564m. Hip/상체/zero8는 그대로, 양쪽 Knee_x/Ankle_xyz/Toe_x만 bounded IK로 bottomface z=.5mm·수평 목표. 기존 질량·형상·가동범위·gain/cap은 변경하지 않는다. source target는 cooked 접촉 성공과 구분한다.
- [ ] source 감사: 새 높이/의자 크기를 실제 사용. q105/97range/zero8·변경 소유권·형상 측정과 발 proxy 틈/기울기 확인. 초기 관통 −.1mm 미만, 각 Ankle/Toe bottomspan≤1mm, source minZ .1..1mm 목표. lower-leg와 의자/상대다리의 새 교차를 점검하고 기존겹침은 별도 보존.
- [ ] native 정지5초: 기존 controller_horizontal_v4와 scene8을 새 초기root/chair로만 확장. 새 경로에 원자료240Hz/목표60Hz/실제3뷰30fps·입력SHA 저장. 실패도 저장. 실행 중 Root/의자exact, 하체finite·원8zero·기타FREE/중력ON/strapOFF, no guitar force/attachment/perstep state overwrite.
- [ ] 접지 진단: t0제외 및 settle1..5초 각각 양발 ground positive-lambda 비율·동시비율, Ankle/Toe별 빈도, 접촉 위치/normal/lambda(단위未변환), sourcebox z범위·bottomspan·기울기·종료1초 속도·이동. 양발 동시에 positive≥95%, 각sole높이 종료1초 −1..3mm·tilt≤2°, 종료1초 linear speed≤.02m/s/angular≤.2rad/s·bodyorigin ptp norm≤3mm를 발 접지/정지 목표로 삼는다. native lambda를 측정N 또는 자유Root 균형 증명으로 부르지 않는다.
- [ ] 전체 자세·기타 유지도 별도 대조: 기존 몸통5°/옆3°, 넥3°, 기타몸통변위30mm/회전5°, 가슴·위팔 실제접촉기준을 숨기지 않는다. 발 개선이 기존 연주 안정 실패를 자동 해결하지 않는다. 5초 후속 동작은 정지 접지 확인 후 필요 시 같은9초 결합 진단으로만 진행, 새PPO/15초해제 금지.
- [ ] change-reviewer 독립 검수, root 보존 감사·소스/입력/로그 봉인, 현재 안내 갱신. 각 소비 leaf/code/output는 수정하지 않고 후속 버전으로 진행.

## 역할

Root: 물리 후보/코드/실행/계획·결과/최종감사. play_path: 의자/Root/FK 경로 읽기 탐색. play_analysis: 새 접지 분석기만 담당(별도 구현 brief). review_probe: 독립 변경 검수만. 서로의 파일과 기존 phase를 수정하지 않는다. 프로젝트의 2026-10-07 자율 실험 지침과 현재 사용자 조정 지시로 승인 대기를 반복하지 않는다.
