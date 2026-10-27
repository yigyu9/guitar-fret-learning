# 15초 초기 자세 영상 최종 독립 검수 V1

요약 판정: **문제없음**. 미해결 Critical 0건, Warning 0건. 새 실행·후처리·결과 문서의 목적과 실제 원자료가 일치한다. 검수자는 이 보고서만 새로 작성했으며 구현·원자료·기존 산출물을 수정하지 않았다.

## 실제 실행과 재현성

- [native report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/native_v1/report.json:1)의 completed=true, failure=null, 3,600 physics step/900 control/15.0초를 확인했다. 초기 zero velocity/qref/한계/FK/source-clear 검사 및 금지 호출 0을 확인했다.
- 원자료를 직접 비교해 기존 5초 실행과 initial_values 전체, trace 301행 prefix, actual_contacts 1,200행, final_efforts 1,200행, six_joint_target_rows prefix가 같음을 확인했다. controls 300행도 299행 clock.diagnostic_time_limit의 true→false 한 항목을 제외하면 같다. 이는 종료시간 5→15초 변경의 결과다. [prefix 보고](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/prefix_report_v1.json:1)와 일치한다.
- 0–2초 준비, 2–5초 기존 EW6 한 번 왕복, 5–15초 현재 기타 좌표의 마지막 waypoint 유지다. 실제 물리 실행이며 반복 재생·정지 프레임 연장·추가 타현·checkpoint 학습이 없다. 15초 마지막 카메라 표본을 기록한 뒤 종료했다.

## 제어·물리·측정

- 원자료로 오른 Elbow/Wrist 6관절 이외 75개 목표가 qref와 정확히 같고, 전체 목표의 모델/유효 범위·60Hz 변화율 한계를 만족함을 확인했다. final_efforts는 3,600행×81, 유한값이며 초기 native effort cap 이내다. 이는 제출 명령에 대한 검사이며 실제 측정 토크 인증이 아니다.
- [실행 기반 67–75행](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v3.py:67)은 실제 최종 명령의 유한값/cap과 60Hz root·하체 상태 동일성을 검사한다. 초기/최종 Pelvis 및 하체 8개 body 상태도 직접 동일성을 확인했다. 자유 기타·스트랩 OFF·자기충돌·기타 외력/손 부착/지속 기타 pose 덮어쓰기 없음의 기존 경로를 유지한다.
- raw guitar state 3,600행과 초기값에서 quaternion을 SciPy로 정규화해 BB 중심/SO(3)를 독립 계산했다. 전체 최대 **5.116316488 mm / 2.203204263°**, 최종 초기 대비 **4.873565841 mm / 2.125131063°**로 [analysis](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/analysis_v1.json:1)와 일치한다.
- guitar–human 접촉쌍을 명시적으로 분류해 왼팔·손 접촉 **3,263/3,600**, 오른 손목·손 접촉 **0/3,600**을 재확인했다. raw 접촉에는 lambda=0도 포함하며, 양의 lambda는 교정된 힘 N과 다르다. 마지막 2초의 작은 자세 변화는 유한한 능동 인체 제어와 왼손·허벅지 등의 접촉이 남는 조건이다. 왼손 독립 지지/수동 평형/학습된 곡 수행 성공으로 해석하지 않는다.
- 분석의 actual joint limit/speed 최대는 trace의 60Hz 81관절 표본이다. 이번 검수에서 이를 전체 관절 240Hz 극값으로 확대 해석하지 않았다. BB/SO(3)/접촉은 실제 240Hz 원자료다.

## 출처 보존과 영상

- 현재 SHA 재대조: wrapper 5개, native 1,318개, analysis 14개, prefix 14개, post V2 11개, annotated 1,362개, artifact before 32개 입력이 모두 일치했다. render V1은 미실행 보존되고 V2가 소비됐다. 원본 MP4의 native videos.json 사전 SHA와 현재 SHA가 같다.
- post의 451개 camera/contact 표본은 physics step 0부터 3,600까지 8 step 간격이며, 모든 capture/render 상태 보존 플래그가 true다. annotated 1,353장도 같은 native 프레임 SHA 입력에 연결된다. 이는 같은 시점의 화면에 표식/footer만 추가하는 후처리다.
- 8개 최종 MP4를 각각 ffprobe -count_frames로 검사했다. 모두 **451프레임·30fps·15.033333초**다. t=0과 t=15 표본을 포함한 재생 격자이므로 추가 물리 시간이 아니다.

| 종류 | 3개 단일 시점 | 합본 |
|---|---|---|
| 설명·접촉 Xray 포함 | 1280×940 | 1920×470 |
| clean | 1280×720 | 1920×360 |

- 7개 단순 복사의 원본/목적지 SHA가 일치한다. clean 합본은 동일 clean 3시점의 축소·hstack 재인코딩이며 별도 생성 SHA를 확인했다. clean에도 기존 깊이검사 6줄 overlay는 남고 아래 설명·범례·접촉 Xray는 없다. 순수 native 픽셀과 구분하는 문서 설명이 정확하다.

## 최종 문서·대표 이미지

- [결과 README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_long_video_v1/README.md:1) ↔ [영상 README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_long_video_v1/README.md:1)의 상호 연결과 같은 8개 영상 경로를 확인했다. 두 문서·changed_files의 절대 링크 총 44개가 존재하고 지정 줄 번호도 유효하다. main README:2521, PLAN:1437의 추가 결과 설명과 연결도 실제 내용에 맞다.
- 시작 t=0, 끝 t=15 설명 포함, 끝 t=15 clean의 PNG 3개를 실제 열어 전신 구도·동일 자세/카메라·설명/표식 유무·가독성을 확인했다. 각 복사본 SHA는 manifest의 실제 원본 프레임 SHA와 같다. 종료 이미지의 유지 단계 라벨은 관찰 구간 설명이며 본문은 15초에 실행 종료했음을 명시한다.
- artifact manifest의 사전 map SHA, 32개 입력, 3개 원본/복사 PNG, 두 권장 문서 SHA가 모두 실제 파일과 일치한다. 최대값·최종값·왼손 접촉·비학습/비반복·clean 표시 범위의 설명도 원자료와 일치한다.

Critical: 없음. Warning: 없음. Suggestion: 없음.
