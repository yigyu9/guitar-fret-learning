# 초기 자세 후보 탐색 결과

**이번 탐색의 정지 초기 배치·오른손 타현 시험용 후보는 `margin_only`다. 왼손을 옮겨 다시 잡는 동작까지 안정적인 초기 자세는 확보하지 못했다.** 기존 기본 초기값은 바꾸지 않았다.

기존 near 자세를 기준으로 몸통을 더 숙이기보다 관절 한계 여유, 오른 위팔 접촉 배치, 기타 넥 축 회전±2°, Torso_z±2°를 비교했다. Source7개 중5개가 형상·한계·이산 타현 경로 검사를 통과했다. 이 중4개의 정지5초와3개의 동일16초 왼손 동작, 정지 최선 후보의 타현5초 및 정지 재현5초, **총9회 native 시험**을 수행했다. Source상 clearance는 cooked 물리나 연속 경로 인증이 아니다.

## 측정 결과

BB는 기타 바디 bounding-box 중심이다. 아래 이동·회전은 각각 초기 대비 norm/SO3 최대이며240Hz 실제 상태와 정규화 quaternion으로 계산했다. 서로 다른 순간의 최대값일 수 있다.

| 후보 | 시험 | 물리 경과(s) | BB 이동(mm) | 회전(°) | 결과 |
|---|---|---:|---:|---:|---|
| margin_only | static | 5.000 | 3.287 | 0.819 | 완주 |
| roll_m2 | static | 5.000 | 6.067 | 2.353 | 완주 |
| roll_p2 | static | 5.000 | 20.857 | 4.728 | 완주 |
| torso_p2 | static | 5.000 | 3.999 | 1.159 | 완주 |
| margin_only | left | 9.967 | 112.825 | 29.122 | 보호 중단 |
| torso_p2 | left | 6.433 | 62.826 | 28.493 | 보호 중단 |
| roll_m2 | left | 10.017 | 116.170 | 30.141 | 보호 중단 |
| margin_only | strike | 5.000 | 5.116 | 2.203 | 완주 |
| margin_only | static_repeat | 5.000 | 3.287 | 0.819 | 완주 |

`margin_only` 정지 반복은 초기값·trace·접촉·최종 effort 명령·최종 상태5개 원자료 SHA가 모두 같았다. 타현에서는 R_Elbow/R_Wrist6 DOF만 목표를 변경했고 원본 판정기의 RELEASE가6→1 /1→6 순으로 검출됐다. 실제 명령 시간창 down3.2–3.55초/up3.75–4.45초로 집계했다. 기존 분석기의 up≥3.95초 집계는 앞의1·2번 줄을 제외하므로 원자료와 함께 보존하고 [시간창 보충](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/strike_actual_windows_v1.json)으로 구분한다. 이 타현은 checkpoint 연결이나 곡 연주 학습이 아닌 스크립트 IK 검증이다.

## 지지 상태와 한계

- 정지 후보는 왼팔·손 무접촉418/1200표본이다. 타현에서는337/1200표본만 무접촉(863표본 접촉)이며 오른 손목·손 접촉은0/1200이다. **왼손 도움 없는 안정성을 이 결과로 주장하지 않는다.**
- 왼손 세 후보는 모두 actor-root 이동20cm 안전 한계를 넘어 중단됐다. 각각 margin_only205.923mm, torso_p2 203.210mm, roll_m2 210.964mm다. actor-root와BB는 회전 중심 차이로 이동량이 다르다. 이때 SO3는 모두35° 미만이다.
- margin_only의 A잡기3–4.5초에는 엄지+다른 손가락의 양의 raw lambda 동시 접촉360/360, A놓기6–7초에는 왼팔·손 무접촉240/240이었다. 그러나 A놓기 중 오른손 접촉97/240, B이동7–8.5초에는 오른 중지 끝 접촉360/360이었다. 기타가 기울면서 원치 않는 오른손 지지가 생겼으므로 양손 독립 지지 성공으로 부르지 않는다. B접근은 시작했지만 B유지·해제까지 마치지 못했다.
- torso_p2는6–7초 놓기 목표 중6–6.433초104표본만 관측됐다. 이를1초240표본 완주로 계산하지 않는다. roll_m2도 B유지·해제를 완료하지 못했다.
- 이전 near16초37.288mm/14.516° 완주 결과는 이전 참고로 보존한다. 이번 새 후보가 그 동작 안정성을 개선했다고 결론 내리지 않는다. 이번은 초기 관절 여유와 공통 기타좌표 손목 목표를 맞춘 비교다.

## 초기값·물리 조건

[초기값 JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_initial_values.json) / [81관절 목표·실제 초기각 CSV](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_joint_angles.csv) / [정지 실행 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v2/margin_only/config_static.json).

기타BB 중심 월드 좌표는 약 **(0.143230, −0.001173, 0.683022)m**다. actor-root 좌표 약(−0.258574, −0.005746, 0.723792)m와 혼동하지 않는다. Torso 목표(8.344,−1.884,−11.463)°, Spine(18.517,−1.418,−1.019)°, Chest(−1.966,18.205,.016)°, R_Thorax(−2.5,−8,8.505)°, R_Shoulder(−2.424,52.845,10.896)°다. 이 값은 모델 native DOF scalar이며 suffix를 월드 회전축으로 해석하지 않는다.

Root/하체 고정, 스트랩OFF, 자기충돌ON, 자유 기타·유한 상체 제어다. 몸통9+양팔24는 유한 effort 제어이며 나머지48은 POSITION 목표를 유지한다. 기록한81 effort 벡터는 제출한 명령이며48 POSITION의 최종 순토크 측정값이 아니다. 기타 고정·손 부착·외력·지속 pose 덮어쓰기는 없다. 능동 인체 지지이므로 수동 평형 증명도 아니다.

목표각 한계/변화율·effort유한/cap·변경하지 않은 목표·입력SHA·금지호출 검사를 통과했다. 관절 위치81개는60Hz기준 통계이며 [240Hz 보충](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/joint_240hz_audit_v1.json)은 active33개 위치/전체81속도다. 나머지48개의240Hz위치 기록은 없다. 후보별 작은 실제 한계 초과도 이 보충에 보존했다(최대 .026025°). 스트레스 실패를 물리 오류나 학습 성공으로 바꾸어 해석하지 않는다.

## 이미지·시작부터 종료까지 영상

[이미지·영상 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/final_v1/README_final_v3.md) / [영상 모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_search_v1/README_final_v3.md).

실제 Isaac Gym 앞·오른쪽 옆·위 전신 영상이다. 고정 크기 원은 가려진 점도 표시한 X-ray contact feature이며 채운 원은 raw lambda>0, 빈 원은0이다. 힘N·압력·접촉 면적이 아니다. 5초 물리는 초기 프레임을 포함151프레임이라30fps 재생5.033초다. 실패 영상은 얻은 마지막 카메라까지 보존하고 물리 종료와의4~8tick 차이를 영상 색인에 명시한다.

## 다음 작은 단계

상체를 더 굽히는 변경을 먼저 늘리지 않는다. 같은 지지 배치에서 **손가락을 먼저 편 뒤 손목을 물리는 해제**를 현재 동시 해제와 비교해, 해제 과정의 접촉이 기타를 기울이는 정도를 확인한다. 다음 단계 계획이며 이번에는 실행하지 않았다. 압현·양손 연주용 기본 초기 자세 확정은 그 후다.

[계획](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_PLAN_V1.md:1), [완료 기록](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_COMPLETION_V1.md:1), [변경 파일·줄 번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/changed_files_v3.md:1). 기존 `stability_adapter/`·공용 자산·과거 산출물·독립 학습 파일은 보존했다.
