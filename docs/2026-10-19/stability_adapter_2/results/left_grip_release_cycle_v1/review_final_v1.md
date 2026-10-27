# 왼손 그립·해제 사이클 독립 최종 검수

요약 판정: **문제없음**. Critical 0건·Warning 0건. 두 번의16초 진단과 원자료 분석, 선호 산출물 README_v2/INDEX_v2를 확인했다. 최종 봉인 verifier 소스도 검수했으나, 이 보고 작성 시 verifier의 최종 실행 및 root 결과 문서 작성은 아직 root의 후속 단계다. 그 검증 결과를 이 보고가 대신 인증하지 않는다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음. 사용자에게 전체 사이클의 자세 변화와 마지막 놓기 구간의 안정성을 구분해 설명하는 현재 산출물 표현을 유지할 것을 권장한다.

## 실제 원자료 확인

- 두 native report는 각각3840physics/960control step, 실제16초, 금지 호출0, 입력 변경 없음, 스트랩OFF·오른팔 타현OFF를 기록한다. 오른팔의 유한 지지는 유지되므로 완전 수동 평형 시험은 아니다.
- V2 endpoint/contact step1..3840, torque step0..3839, target step0..3836(4간격)을 직접 대조했다. 분석 V2가 이 연속성을 assert하며 손목 실제 상태와 기타 상태의 같은 endpoint를 사용한다.
- 접촉 원자료를 독립 재집계했다. A3–4.5초와 B10–11.5초 각각360/360표본에서 엄지+다른 손가락 양의 lambda 동시 접촉이다. A6–7초240/240, B13–16초720/720표본은 실제 왼팔/손 접촉-free다. 단순 동작 명령으로 성공 판정하지 않는다.
- V1의 L_Hip 포함 prefix는 분석에서 명시적으로 제거하고 원자료를 보존했다. V2 recorder 자체는 LH:* 또는 정확한 L_Thorax/L_Shoulder/L_Elbow/L_Wrist만 분류한다.
- V2 최종 human81 torque3840행을 직접 읽고 finite·각 모델 effort cap 이내임을 확인했다. 25N/2Nm virtual task는 왼팔12 토크에만 추가되며 other69 effort를 유지한다. 최종 목표는 contract의 model/rate 범위로 제한되고 other48 target이 보존된다. guitar 강제 wrench/부착/pose 덮어쓰기 경로가 없다.
- 최종 제출 벡터의 권위 자료는 left_cycle_efforts.json이다. V2 body_effort_rows와 left_wrist_tracking_rows에 superseded_by=left_cycle_efforts.json이 실제 저장돼 있다. V1의 잘못된 final 설명은 별도 v1_evidence_scope_correction.json으로 명시하고 과거 파일을 수정하지 않았다.
- 2초 대비 최대 기타 BB 중심 이동22.264167mm/회전9.796429°다. 마지막13–16초 구간의13초 대비 최대 변화0.018699mm/.006618°만을 전체 사이클 안정성으로 일반화하지 않는다. A 열린 구간은.415495mm/.136481°다.
- A/B 평균 손목 위치의 현재 G넥 축 차이36.726988mm, 같은 축 시계열 extent44.168172mm를 구분한다. 후자는3차원 경로 길이 또는 전체 위치 범위가 아니다.
- 2초 이후3360/3360실제 endpoint에서 오른 위팔/오른 허벅지 접촉이 각각 존재한다. 놓기 중 기타 유지는 이 실제 사람 지지와 유한 제어 아래의 결과다.
- V1/V2 initial_values JSON과 전체 trace 파일 SHA가 동일함을 직접 확인했다. 비교 소스는 기타 root p/q equality를 검사하며 결과도 exact다. 이는 동일 조건 재현이며 강건성·곡 연주·force closure 인증이 아니다.

## 산출물 및 봉인 구조

- 선호 README_v2/INDEX_v2의32개 전체 Markdown 목표가 모두 존재한다. 두 copy_manifest의 각11개 이미지/영상 source–copy–recorded SHA를 직접 대조해 모두 동일함을 확인했다. A 유지 전신/놓기 손 이미지도 직접 열어 장면과 촬영 범위를 확인했다.
- 잘못된 첫 README/INDEX는 과거 기록으로 보존하고, 최종 진입점은 수정된 successor를 사용해야 한다. 선호 문서의 root/하체 고정·자유 기타·범위 수치 및 실제 시간 설명은 원자료와 일치한다.
- verifier는 두 native 실행의 사전 pin, capture step0..3840(step8),481frame, render-preserves-state, PNG/MP4 SHA 및 분석 입력을 검사한다. 두 영상 복사 manifest와 comparison 입력 SHA/initial/trace equality, V1 정정 자료 source SHA 및 producer-before-input SHA도 검사한다.
- 현재 main 문서 변경은 실제 before 복사본과 SHA를 대조한 append-prefix로만 허용한다. 다른 승인 스레드가 앞서 main README에 fresh_learning_v1 내용을 prepend한 경계는 별도로 선언하므로 과거 봉인까지 연장 인증하지 않는다. V1의 직접 A/config.json 실행 전 pin 누락도 명시하며 V2에서만 before/after 인증한다.
- 분석/비교/봉인 Python AST parse 통과. Producer provenance 두 파일의 기록된 입력 SHA도 현재 원자료와 일치한다. 리뷰어 자체 GPU 물리 실행은0회다.

## 검수 시점 파일 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/left_grip_release_cycle_v2.py`: `54bb38d2e7f8372dfd1a613c3b3ea6ceaf833e134f3ea1550cc4bf82bbaba335`
- `/home/ajou/yigyu/3/stability_adapter_2/run_left_grip_release_cycle_v2.py`: `1f90067a8ecabe9053ef0f1df64805926eb6ee4ab2f0a126bf6e2f2225c09ad0`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_left_grip_release_cycle_v2.py`: `3329f5d0293cca6f928b652c5f2fd4103173ff89a96680c4f2e635d99b3a2a1e`
- `/home/ajou/yigyu/3/stability_adapter_2/compare_left_grip_release_cycle_v1.py`: `6401106c52e19a03cf2a0b31d1c0df84c55b5c0bbcc2e54caa72fb0344d72204`
- `/home/ajou/yigyu/3/stability_adapter_2/verify_left_grip_release_cycle_v1.py`: `ae510ae9bfd18f3f06f9e4618e94f017fb15eeb2d493a04c1ef18e9f43fda686`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/analysis_v1.json`: `7a3d67c1c5259edf03749a5b53506d5eb0a7f5e482c6c4d63ec7c6c25c8e0bb3`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/analysis_v2.json`: `0907f7b5e2c94df131de001d46d916b31962e1a58295d85532e10ec8c29dabaa`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/repeat_comparison_v1.json`: `3b9a4724fae98521562befe9b91877c35a39db78e763b14933cf2a3cc8c00494`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/v1_evidence_scope_correction.json`: `6f4aa62ed45438ebaa41bd7276d1112352151d496be38e9c44eb235244adbbc5`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/artifacts_v1/README_v2.md`: `2a3bd1bd11640c0adf08711dddceba225f6fd2b2c780f7729dacce327d69c766`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_grip_release_cycle_v1/INDEX_v2.md`: `c53d8a9c11c5139e61f45e9a6e9025140bf588c0fccf6817ba9f786e8ce3948b`
