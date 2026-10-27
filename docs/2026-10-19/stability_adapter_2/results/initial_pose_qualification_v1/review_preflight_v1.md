# 초기 자세 적합성 시험 사전 검수

요약 판정: **문제없음 — 실행 대상 V2 기준**. 미해결 Critical 0건, Warning 0건.

## 범위와 정정

최초 요청된 runner V1·source V4·leaf 계획 및 추가 분석기를 검수하고, 최초 native V1의 0-step 실패 뒤 작성된 runner V2의 차이도 확인했다. V1은 기존 FocusedRecording이 필요로 하는 `OM_appearance` 카메라가 없어 최초 capture에서 실패했다. 이 카메라 의존성을 최초 정적 검수에서 놓쳤다. V1 실패/원본은 보존하고 V2를 실행 대상으로 삼는다. 실제 안정성·타현·접촉 성공은 실행 후 원자료로 별도 판단해야 한다.

## 확인 결과

- [source V4](/home/ajou/yigyu/3/stability_adapter_2/prepare_initial_pose_qualification_v4.py:30)는 이전 14초 기록의 실제 81각과 기타 pose를 새 환경의 초기 형상으로 사용한다. 미세한 L_Wrist_y 한계 보정 0.0000438094rad, 기타 world 위치 보정 [+1.846939,+0.415309,−1.359105]mm를 기록한다. 속도·solver history의 이어달리기와 구분한다. 원래 near 비교 설정도 별도로 남긴다.
- source V4의 1,085개 before 입력 SHA는 현재 파일과 모두 일치한다. config/실제 XML·mesh 선언을 포함하며 후보와 설정은 새 source_v4 경로다. 후보 source_clear·한계·최대 5mm 보정 및 지정 body capsule gap≥0.15mm를 확인한다. Chest/R_Shoulder/R_Hip gap은 약0.20mm다. 이는 source 근사 및 일부 waypoint 검사이며 native 비관통·전체 연속경로·수동평형 인증은 아니다.
- [V2 초기 검증](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py:35)은 q_ref exact·관절한계·속도0·human/G FK·source_clear를 검사하고 초기값/PD/질량을 기록한다. 기존 유한 human effort 제어를 상속하고 최종81 명령을 별도로 저장한다. 기타 pose/외력을 지속 설정하는 새 경로는 없다. root/하체 상태 보존·상태 비유한/속도·기타 actor-root 안전 범위 guard를 유지한다.
- [V2 카메라 수정](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py:53)은 추가 전용 OM_appearance만1280×960으로 만든다. 상속 FocusedRecording이 첫 capture에서 위치를 설정하며 StringTrialRecording의 초기 appearance depth 규격과 맞는다. front/right_side/top 기록 카메라1280×720와 충돌하지 않는다. 기존 V1과의 diff는 이3줄뿐이며 제어/형상 변경이 아니다.
- [left cycle 시작](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py:111)은 첫2개 VALUES행을 [0,1,0]으로 설정한다. 2×3 배열 broadcast가 정상이다. 초기 wrist_G에서 [.070,.080,0]을 뺀 base와 release offset을 합치므로 t=0–2 목표는 실제 초기 분리 손목 위치다. 이후 A 접근/해제/B40mm 이동 순서에 기존 rate/model/IK gate를 사용하고, 타현은별도 EW6 실행이다.
- 이전 body_side_lean_axilla witness는 상속 초기화/진단에서 읽히지만 two_block 제어가 이전 raw axilla task를 뺀 후 새 right_block witness task로 대체한다. source V4는 현재 witness를 다시 계산한다. 기존 witness 기록을 이번 실제 접촉점/측정 힘으로 해석하면 안 된다.
- [분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_initial_pose_qualification_v1.py:23)는 원시240Hz 기타 상태에 초기0초를 추가해 BB body centre 및 정규화SO3를 계산한다. 단계별 기준을 새로 잡는 구간 변화와 전체 초기 대비 변화를 구분한다. 왼팔/손 범위에 L_Hip을 섞지 않으며 thumb+other 양의 행·raw접촉free를 구분한다. 목표각 rate/limits/다른채널 exact와 최종 노력 cap를 확인한다. 실제각 overshoot는 측정량으로 보고한다.
- 분석 before map의 덮어쓰기 가능성을 처음 제기했으나 [공통 save](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_noise_v1.py:16)가 `open('x')`를 사용함을 확인해 철회했다. 기존 before 기록 재시도는 실패하며 덮어쓰지 않는다.
- V1/V2 runner·source V4·분석기의 AST 문법 검사를 통과했다. 검수자는 소스/설정/기존 결과를 수정하지 않았다. GPU 물리 실행과 결과 판정은 root가 수행한다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v1.py`: `545786030ed57852fe0e02daa20509177b49752143fd0a25e87e6dc2a11d3911`
- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py`: `8726cfed0af3c2d1d2e41954f58ecd5672038c0274ff072221b7a7485e64814c`
- `/home/ajou/yigyu/3/stability_adapter_2/prepare_initial_pose_qualification_v4.py`: `54bce2810e771d4f361daf501844f418b084d2e247baf2f5b57dbd5469cb21cb`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_initial_pose_qualification_v1.py`: `c449b1f21518654d443376e6a30e9d9e974ed35201e7e9d5fdb5f668a8c988bf`
- `/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_QUALIFICATION_PLAN_V1.md`: `a699bcf1a3591a77f84b9f6c313de8b663796e4db7bb34dc09df305dc3e3f8a6`
