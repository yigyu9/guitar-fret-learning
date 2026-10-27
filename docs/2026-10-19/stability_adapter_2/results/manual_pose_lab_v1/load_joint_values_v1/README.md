# 조작창의 저장 관절값 불러오기

저장 관절값을 선택하는 버튼을 추가했다. 새 V4는 기존 바른 앉은 humanoid 초기값을 기본으로 사용하며 기타 배치와 조작 기능을 유지한다. 이전 V1~V3, 원본 모델과 연구 실험은 수정하지 않았다.

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/open_v4.sh
```

기존 창을 닫고 다시 실행한 뒤 조작창 상단 **관절값 불러오기**에서 저장 JSON을 선택한다. 파일 선택 취소는 아무것도 적용하지 않는다. 유효한 관절값은 물리 OFF로 전환하고 실제 humanoid 초기각과 PD 목표에 적용하며 관절 속도·경과 시간을0으로 만든다. 기타의 전체 상태는 변경하지 않는다.

관절 이름으로 재정렬하므로 파일 순서가 달라도 된다. 상체81관절이 모두 있어야 하며 모델 범위를 벗어난 값은 강제로 clip하지 않고 거절한다. 불러온 값은 **시험 초기화**의 기준으로 등록되며 **원본 자세** 기준은 변경하지 않는다. GUI의 성공 안내·선택한 관절 슬라이더·물리 모드 표시를 갱신한다.

## 검증

- 동작/GUI callback 테스트9개 통과. 저장 파일 재불러오기, 순서 변경, 이름→rad map/native 형식, ON 중 로드, 기타 전체 상태 불변, 새 시험 리셋과 원본 복원, 잘못된 파일의 무변경, 파일 선택 취소, 성공 UI 갱신을 검사했다.
- 잘못된 입력은 이름 누락/중복/미등록·각도 길이·NaN/Inf·한계 초과·boolean/string·변환 불가능한 큰 정수·잘못된 native pos·손상 JSON/파일 없음을 포함한다.
- CPU native: ON8physics step(약0.0333초) 후 파일을 불러왔다. 실제81관절 pos가 파일 값과 exact, 관절 속도0, OFF 전환, 기타39강체의 전체 state 및 고정root/하체9강체의 state exact 불변, 시험 초기화 복원을 확인했다. 안정성·곡 연주·5초 완료 시험은 아니다.
- 입력 SHA 전후 일치와 이전 수동 도구 inventory·native 입력 보존을 확인했다.
- 실제 desktop 버튼·파일 선택창 렌더는 DISPLAY 부재로 확인하지 못했다. GUI callback 검사에서는 파일 선택을 mock했고 실제 native 검사는 headless CPU였다. 기존 headless CUDA/visual/articulation 로그 경고를 원문 그대로 남겼다. side conversation의 제한으로 서브에이전트 검수는 수행하지 않았다.

[테스트 로그](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/load_joint_values_v1/unit_tests.log:1) · [Native 검사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/load_joint_values_v1/native_check/checks.json:1) · [Native 로그](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/load_joint_values_v1/native_check.log:1)

## 새 파일·실제 줄

- [계획](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/LOAD_JOINT_VALUES_PLAN_V1.md:1)
- [관절값 검증·이름 정렬](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/lab_v3.py:8)
- [관절값 적용](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/lab_v3.py:40)
- [조작창 버튼·파일 선택](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/run_v4.py:10)
- [현재 실행 파일](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/open_v4.sh:11)
- [동작 테스트](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/test_joint_load_v1.py:1)
- [Native 검사 실행 코드](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/check_joint_load_native_v1.py:1)
- [최신 사용 설명](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/README_V4.md:1)
