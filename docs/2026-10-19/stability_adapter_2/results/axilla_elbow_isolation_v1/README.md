# 어깨 쪽 기타 받침: 팔꿈치 영향 분리

어깨에 가까운 상완으로 기타 위쪽 볼록 부분을 받치고 오른 허벅지에 얹은 초기 후보를 만들었다. 전완 점제어를 제거해 팔꿈치를 움직일 때 기타를 직접 밀지 않도록 했다. 같은 초기 실제 상태에서 정지·±2°·±5° 팔꿈치 시험을 각5초 완료했다.

| 조건 | 5초 후 바디 중심 이동 | 5초 후 전체 회전 | 실제 팔꿈치 왕복 범위¹ |
|---|---:|---:|---:|
| 정지 | 1.622 mm | 0.662° | 0.000287° |
| 목표 ±2° | 1.622 mm | 0.662° | 4.033° |
| 목표 ±5° | 1.645 mm | 0.671° | 10.083° |

¹ 실제 moving 조건의 `R_Elbow_y` scalar각2.5~5초 범위다. world축 의미가 아니다. 운동 구간은2.5~4.5초0.5Hz 한 주기이며 세 실행의 초기 native 상태와2.5초까지 trace가 정확히 같다.

±5° 시험에서 같은 시각 정지 시험 대비 기타 중심 최대차는 **0.027241mm**, 회전 최대차는 **0.009348°**다. 오른 전완·손목·손가락/머리/왼팔·손 기타 접촉은 세 시험 모두0/1200 endpoint 표본이다. 정지 후 작은 팔꿈치 운동에 대한 이번 진단은 통과했다. 큰 동작·손목·다른축·장시간·fret/strike 연주의 성공을 검증한 결과는 아니다.

## 이미지·영상

![실제 Isaac Gym 초기 자세](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/native_v4/elbow_motion5/media/initial_native.png)

![정지와 팔꿈치 ±5도 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/static_vs_elbow_motion5_side_by_side.mp4)

![팔꿈치 ±5도 전신 원본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/elbow_motion5_whole_body.mp4)

[이미지 설명과 비교 그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/README_V2.md) · [전신/근접 원본6개 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/INDEX_V1.md) · [영상 hash/frame 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/manifest_v1.json).

## 초기 값과 제어

- 몸통 목표는 기존 자연팔 기준에서 휴머노이드 오른쪽6°+앞8° 방향의 world 회전으로 적합했고 머리 world 방향을 보존했다. body9은 원 기준 scalar ±.14rad, head6 ±.22rad, 오른팔12은 모델과 Thorax±.35/Shoulder±.5/Elbow±.6/Wrist±.2rad 교집합에서 선택했다. 왼쪽/손가락54개 초기 scalar는 이전 기준과 같다. 하체·root는 기존 고정 자산을 사용한다.
- 기존 upper_bout source3 대비 기타 바디 BB 중심 world 변위[-30,-60,+17.467]mm, 넥 고도0.642°, 앞판 정면. 회전은 바디 BB 중심 기준으로 적용했으며 넥 원점 이동과 바디 중심 이동을 구분했다.
- source capsule/SAT 기준 상완 시작0~30% 간격1.313mm, 전완16.880mm, 오른 허벅지0.183mm, R_Thorax27.511mm. 전체 source 겹침 없음. 몸통8mm 조건을 원 탐색에서는 불충족해 거절했고, 별도 계획V3에서 그 조건만 진단 진입에 적용하지 않았다. 이 값은 PhysX cooked 간격 인증이 아니다.
- 오른팔12 사람 관절 EFFORT: 전체 사람 중력보상+유한 자세 PD+상완 사람 점 제어. 상완 초기 world 목표4mm 안쪽·가상 점제어 요청cap10N(K2000N/m,D30Ns/m). 전완 점제어 힘0. 오른팔12 외69 POSITION은 원 목표를 유지한다. 기타 자체의 힘·부착·pose 덮어쓰기/스트랩/왼손 그립 없음. 관절·기타 실제 state의 runtime 덮어쓰기 없음.
- 실제 contact feature를 source 상완 축에 투영한0~35%+기타 위쪽 볼록 영역 판정은1171/1200 표본이다. 전체 상완1187·오른 허벅지1196표본이며 이는 지지 힘/하중 비율이 아니다. **실제0~30% 접촉 표본은0**으로 source 목표와 혼동하지 않는다. R_Thorax 접촉0이므로 몸통 압착·해부학적 겨드랑이 인증을 주장하지 않는다.

## 검증 및 보존

240Hz×5초=1200 physics step·60Hz×5초=300 control·영상151프레임30fps(인코딩 길이5.033초)를 확인했다. 화면이 거의 멈춰도 계산은 끝까지 수행됐다. 69관절 POSITION readback·상태 보존·오른12관절 effort 소유권/한계/step당1회 호출·기타 자유/스트랩OFF guard를 유지했다. 상완 점 Jacobian의 Elbow/Wrist 열은0이며 직접 운동학 분리가 확인됐다. 간접 관성·마찰·부모 관절 영향은 남는다.

비교 v1/v2의 `native_elbow_tracking_RMSE_deg`는 moving-minus-static 실제각 증분 추종 오차다. ±5° 증분 RMSE0.042524°, 절대 moving q−target RMSE0.108712°이며 두 정의를 구분한다. 관절 초기81 scalar는 candidate와float32 exact다. 기타 초기 root p는 PhysX float32 변환 왕복에서5.96046e−8m 차이로 구 엄밀 equality가 실패해 별도 analyzer v2에1e−7m 허용치를 명시했다. 실제 physics/초기 값은 재작성하지 않았다.

초기 실행1회는 물리 시작 전 MuJoCo import의 EGLDeviceEXT 오류였다. 같은 소스로 MUJOCO_GL=disable 후 Isaac Gym 물리는 정상 완료했다. analyzer1의 출력 부모디렉토리 누락 및 초기 기타p exact guard 실패도 로그·입력을 보존하고 새경로/버전에서 해결했다. 기존 소스·공용 모델·기타 원본·이전 phase를 수정/삭제하지 않았다.

[전체 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/result_summary_v3.json) · [±2도 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/elbow_comparison_v1.json) · [±5도 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/elbow_comparison_v2.json) · [공간 판정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/contact_region_v3.json) · [초기81각/기타p·q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/diagnostic_candidate_v1/candidate.json) · [±5도 실행 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/motion_candidate_v2/config_motion5.json) · [완료 기록](/home/ajou/yigyu/3/stability_adapter_2/AXILLA_ELBOW_ISOLATION_COMPLETION_V1.md).

현재 후보는 다음 검증의 기준으로 보관한다. 기존 학습 초기 설정은 변경하지 않았다. 다음은 같은 받침을 유지하며 오른팔/손목의 연주에 필요한 범위를 단계적으로 확인한 뒤 fret/strike를 재연결하는 것이다.
