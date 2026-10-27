# 팀원 보고 기타 자세의 현재 환경 적용 진단

이번 소단계에서 세 번의 독립 native 실행과 저장 자료 후처리를 수행했다. 팀원 자세 설명을 현재 humanoid 초기 상태에 재구성해 현재 수평 배치와 비교했다. 세 실행은 각각 1,200 step(5.0 simulation seconds), 151 native 표본이며 영상은 case마다 전신/손 두 시점, 각 5.033초다. 세 시작 상태의 humanoid 관절각은 같고, Pelvis와 하체 고정, self-collision, 중력·자유 기타, strap OFF, 기존 팔 24 DOF bounded PI와 torso PD를 유지했다.

## 비교 결과

| 배치 | 초기 기타 바디 중심 (오른쪽/앞/위, cm) | 넥 고도 | 최대 actor-root 위치 변화 | 최대 회전 변화 | 종료 위치/회전 변화 | 최초 기타-바닥 접촉 | 왼손 접촉 step |
|---|---:|---:|---:|---:|---:|---:|---:|
| 현재 수평 배치 | (16.9585, 24.5012, 10.8973) | 0° | 62.438 mm | 15.540° | 34.364 mm / 4.620° | 없음 | 1200/1200 |
| 팀원 보고 기준 재구성 | (17.0000, 24.5000, 8.0000) | 22° | 1381.178 mm | 122.985° | 1381.177 mm / 122.922° | 0.8833 s | 0/1200 |
| 팀원 보고 중앙 후보 재구성 | (20.0000, 29.5000, 9.0000) | 19.5° | 1306.791 mm | 154.357° | 1306.791 mm / 154.357° | 0.5875 s | 0/1200 |

위치 변화는 초기 기타 actor-root 위치 대비 최대 유클리드 거리이고, 회전 변화는 초기 자세와의 최단 회전각이다. 표와 본문의 최대·종료 변화량은 모두 30 Hz로 저장한 151 native 표본에서 계산했으며 240 Hz 전체 physics step의 최대값은 아니다. 왼손 접촉 step 수는 raw contact 관측 횟수로, 힘의 크기·지지력·연주 성공을 증명하지 않는다. 두 재구성 후보의 2초 이후 추가 최대 변화는 각각 0.0005 mm/0.000061°와 0.0002 mm/0.000021° 수준이다. 이는 기타가 바닥에 떨어진 뒤 거의 움직이지 않는 상태와 일치하며, 연주 자세가 안정적으로 유지됐다는 뜻은 아니다. 반대로 현재 수평 배치는 2초 이후 최대 추가 변화 1.852 mm/0.298°였고 바닥 접촉은 기록되지 않았다.

![세 조건의 실제 native 카메라 t=0초와 5초 비교. 팀원 보고 두 조건의 기타는 종료 시 바닥에 놓여 있으며 고정 카메라 화면 가장자리로 일부 잘릴 수 있다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/native_comparison.png)

![세 조건에서 저장된 native 151표본을 사용한 actor-root 위치·회전 변화. 수직 점선은 2초이며, 낙하 후 평탄해진 구간은 유지 성공으로 해석하지 않는다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/pose_changes.png)

## 실제 실행 영상

아래 MP4는 각 native 실행에서 저장한 실제 Isaac Gym 카메라 기록이다. 전신 시점은 자세와 지지 변화, 손 시점은 양손 및 기타 주변을 살피기 위한 보조 관찰이다. 두 시점 모두 물리·접촉 인증을 대신하지 않는다.

### 현재 수평 배치

![현재 수평 배치의 실제 native 전신 영상, 5.033초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/current_control/images/whole_body.mp4)

![현재 수평 배치의 실제 native 손 시점 영상, 5.033초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/current_control/images/hands.mp4)

### 팀원 보고 기준 재구성

![팀원 보고 기준 재구성의 실제 native 전신 영상, 5.033초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_reference/images/whole_body.mp4)

![팀원 보고 기준 재구성의 실제 native 손 시점 영상, 5.033초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_reference/images/hands.mp4)

### 팀원 보고 중앙 후보 재구성

![팀원 보고 중앙 후보 재구성의 실제 native 전신 영상, 5.033초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_center/images/whole_body.mp4)

![팀원 보고 중앙 후보 재구성의 실제 native 손 시점 영상, 5.033초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/native/reported_center/images/hands.mp4)

## 배치 재구성과 해석 범위

팀원 원본의 초기 관절각, 정확한 body-center/pivot 정의, 회전 순서와 fret_041000 실행 식별 정보가 제공되지 않았고 해당 체크포인트 이름을 가진 run도 둘이다. 그래서 세 조건 모두 현재 humanoid 초기 관절각을 사용하고, 기타 위치·방향만 달리해 직접 적용 가능성을 비교했다. Pelvis 기준 오른쪽은 local −X, 앞은 local −Y, 위는 local +Z로 두었다. 기타 바디 중심 offset은 기존 `[0, −0.4, −0.0217] m` 정의를 썼고, 보고 기준은 `(17, 24.5, 8) cm / 고도 22° / 방위 0° / roll 0°`, 중앙 후보는 `(20, 29.5, 9) cm / 고도 19.5° / 방위 0° / roll 10°`로 바디 중심 pivot에 재구성했다. 따라서 이것은 원 팀원 시험 재현이 아니며 팀원 시각 판정이 틀렸다는 결론도 아니다.

세 초기 배치에서 source convex 교집합은 기타–인체 및 기타–의자 쌍에서 0건이었다. 사람–의자 쌍은 이 검사 범위가 아니다. 이는 원본 source 형상 query 결과일 뿐, PhysX cooked 형상의 관통 깊이나 실제 접촉 인증이 아니다. 저장된 native readback에서는 세 조건 모두 관절각 후보 일치·native 한계 내·Pelvis `BASE` 고정·기타 중심 기록 일치가 통과했고 최대 관절각 오차는 `5.34695e−8 rad`였다.

현재 수평 조건과 비교한 이 세 표본만으로 후보 영역 전체, 임의의 6축 조합, 자연스러움, 도달성, 안전성 또는 연주 성공을 인증할 수 없다. 보고 기준·중앙 후보에서 큰 이동과 바닥 접촉이 관측된 것은 현재 손 관절각을 그대로 둔 이 재구성의 직접 적용 한계다. 이는 팀원 원 실험의 반증이 아니다. 접촉 로그에서 최초 바닥 접촉은 기타 `G:body`로 확인되며 `G:pluck_range` ground 접촉도 포함될 수 있다. 이 환경 proxy의 ground 접촉을 실제 악기 형상의 충돌 보증으로 확대하지 않는다. 접촉 lambda를 물리 단위 힘이나 실물 관통 깊이로 환산하지 않았다. 로그의 `Could not load visual geom`, `Incomplete articulation` 경고도 기록된 한계이며, native readback과 카메라 캡처가 성공했다는 사실은 실제 재질·형상 재현을 보증하지 않는다.

정해진 후속 단계는 원 팀의 입력과 좌표 정의를 확보·대조한 다음 해당 기타 후보에 맞춰 왼손 초기각을 함께 재배치해 보는 것이다. 이번에 그 재배치나 현재 허용범위 변경, 추가 물리 실행이 이루어진 것은 아니다. 상세 입력·분석·보존 source 및 정확한 위치는 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/FILE_INDEX.md:1)을 참조한다.

[독립 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/review.md:1)과 [root 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/final_verification.json:1)을 참조한다. 최종 SHA inventory 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/artifact_inventory.json`.
