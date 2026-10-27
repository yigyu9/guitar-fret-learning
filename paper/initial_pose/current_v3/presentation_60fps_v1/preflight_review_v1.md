# 60fps 저장 상태 재생 구현 사전 검수

2026-10-17. 독립 검수자 `current_pose_materials_review`.

**요약 판정: 문제없음.** 아래 v5 구현에 대해 GPU 미리보기 단계로 진행할 수 있다. 실제 렌더링의 성공이나 영상 품질을 승인한 결과는 아니다.

## 검수 대상

- [replay_v5.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/replay_v5.py), SHA-256 `55b40d257a43251099bf3096b99e9501aa33d6cd46cdee30aeae9227f5a13740`.
- [test_cpu_v5.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/test_cpu_v5.py), SHA-256 `6177c6c21c5eb3247635fe6d5373ccc718511efd0b61f67eb3aaea84c37b3493`.
- [제작 기준](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/BRIEF.md).

## 발견 사항과 수정 확인

1. v1은 전환 카드 60프레임을 `output_frame`에 반영하지 않아 재접촉 구간의 출처 프레임 번호가 실제 MP4와 60프레임 달랐다. v5는 측정 프레임과 인코딩 프레임을 구분한다. 재접촉 첫 프레임은 측정 인덱스 1380, 인코딩 인덱스 1440이며 마지막 인코딩 인덱스는 1979다.
2. v4는 현재 불러온 scene 모듈을 원 `attempt.json`에서만 찾았다. 실제 두 실행의 attempt에는 runtime_v12/v15가 없어 생성자 실행 전 실패하는 것을 CPU에서 재현했다. v5는 원 attempt와 support_wrapper의 SHA 맵을 경로 정규화 후 병합하고 동일 경로의 SHA 충돌을 거부한다. 실제 두 실행의 원 모듈 SHA를 찾는 회귀 검사와 충돌 거부 검사가 추가됐다.
3. 초기 구현의 loaded_assets 비교는 경로와 옵션만 확인했다. v5는 원 실행의 expected SHA와 현재 scene 코드·설정·XML·선언 mesh 바이트를 별도로 비교한다. 원 attempt와 wrapper, 제작 기준, 자막 폰트도 실행 전후 입력 보존 대상이다.

## 독립 확인

- CPU 계약 검사 6개를 독립 재실행해 모두 통과했다. 표본 선택, 누락 거부, 물리 API 차단, 프레임 번호, 실제 원 맵 병합, SHA 충돌 거부를 포함한다.
- 실제 압축 states240 원자료를 v5 선택기로 읽어 free_strike 17–40초에서 1,380개(4080–9596 step), regrasp 40–49초에서 540개(9600–11756 step)를 확인했다. 구간 끝은 제외하며 보간하지 않는다. 1,920개 실제 상태와 60개 전환 카드로 총 1,980프레임·33초다.
- 구현자가 생성한 import-only 출처 기록의 각 실행 172개 항목을 원 expected 맵 및 현재 파일 SHA와 독립 대조했다. 불일치 0이며 원 자산 106개를 포함한다. 이 대조는 기록의 바이트 일치 확인이고 GPU scene 생성은 아니다.
- `simulate`, `fetch_results`, `apply_*`를 생성자 이전에 차단한다. DOF 및 인체·기타·의자 body 상태를 저장값으로 복원하고 허용 오차를 검사하며, 그래픽 갱신 뒤 상태 불변과 integration 0을 검사한다.
- 개별 실행을 구간 자막과 1초 전환 카드로 구분한다. 재생은 native camera와 깊이 검사를 적용한 여섯 현 overlay이며 새로운 물리 성공을 주장하지 않는다.

Critical / Warning / Suggestion: 현재 미해결 항목 없음.

## 다음 확인 범위

실제 GPU 미리보기에서 native setter가 저장한 articulated body·DOF 상태를 허용 오차 내 복원하는지, 그래픽 갱신 후에도 유지되는지 확인해야 한다. 17초·타현 중·복귀 후 화면에서 머리·기타·양손·발이 보이고 상단 자막이 신체를 가리지 않는지 확인한다. 최종 산출 뒤에는 60fps·1,980프레임·33초, 전환 경계, 기록된 인코딩 프레임과 원자료 대응, 입력 SHA 불변을 검사한다.

검수자는 GPU scene 생성·렌더·물리 실험·학습을 실행하지 않았다. 기존 코드와 자료를 수정하지 않았으며 이 검수 문서만 새로 작성했다.
