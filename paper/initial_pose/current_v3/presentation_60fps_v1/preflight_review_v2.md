# 저장 관절 동작 재생 v6 사전 검수

2026-10-17. 독립 검수자 `current_pose_materials_review`.

**요약 판정: 문제없음. v6로 GPU 미리보기를 진행할 수 있다.** 이는 구현의 사전 검수이며 실제 렌더링 성공·영상 품질·모든 프레임의 오차 통과를 미리 보증하지 않는다.

## 검수 대상과 SHA-256

- [replay_v6.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/replay_v6.py): `17f6bcf5008ef1ed1334acadea31baa268ea9a8b04a5ef150dac58df353b0d09`
- [test_cpu_v6.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/test_cpu_v6.py): `d1256da4004f7bee5998761476ac15a6103bc0810ebe32b9746bd7cabac2e13c`
- [BRIEF_v2.md](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/BRIEF_v2.md): `1afa68e3ab0e8ff30e9f1fbd3290f14cde6db905450a8c4b664dcc2a38018f7e`

## 변경 검수

- 인체 rigid-body setter를 제거했다. 인체 105축 DOF 위치·속도 복원은 유지하고, 기타·의자에만 rigid-body setter를 사용한다. DOF와 기타·의자 pose의 성분 오차 한도는 각각 기존 `1e-6`이다.
- 인체 66 body의 저장 pose와 native FK pose를 모든 프레임에서 비교한다. 위치는 xyz 차이의 L2 거리(m), 회전은 정규화한 quaternion에서 부호 동등성을 처리한 SO3 최소 회전각(rad/deg)이다. 최대 위치·회전 오차와 각 body 이름을 프레임별로 기록하고, 전체 최대를 해당 실행·원래 시각·프레임과 함께 보존한다.
- 위치 `0.001m` 또는 회전 `0.1deg`를 넘으면 중단한다. 이 값은 BRIEF_v2의 영상 전용 기준이며 원래 물리·source 형상·관절 건강 기준의 변경이 아니다.
- 보고서에서 `human_body_exact_replay=False`, `human_body_velocity_certified=False`를 명시한다. 자막도 저장된 관절 동작을 재생한 두 개별 시험의 편집본으로 설명한다.
- v5의 물리 API 차단, 그래픽 갱신 전후 상태 불변 검사, 원 attempt·wrapper SHA 병합 및 자산 바이트 검사, 전환 카드 이후 인코딩 프레임 번호 계산을 유지했다.

## 독립 CPU 확인

CPU 계약 8개를 독립 재실행해 모두 통과했다. quaternion 크기·부호 동등성, 작은 회전각, 위치·회전 허용치 초과 거부, 원 SHA 맵 병합과 충돌 거부, 원시 표본 선택, 누락 거부, 카드 포함 프레임 번호, 물리 API 차단을 확인했다.

추가로 0/0.0160996/0.1/90/180/270/360도에 대한 SO3 최소 회전각과 `(0.0003,0.0004,0)m`의 위치 차이가 `0.0005m`가 되는 것을 별도 CPU 계산으로 확인했다. 코드 변경은 v5와의 diff를 중심으로 검수했다. v5의 첫 GPU 복원 실패가 이번 구현의 성공 증거로 바뀌는 것은 아니다.

Critical / Warning / Suggestion: 미해결 항목 없음.

## 후속 GPU 확인

17초·타현 중·복귀 후 미리보기에서 실제 setter 복원 오차, native FK 위치·회전 오차, 그래픽 갱신 후 상태 불변과 물리 진행 0을 확인한다. 머리·기타·양손·발이 보이는 정면 전신 구도와 자막 위치를 확인한 뒤 전체 영상을 생성한다. 최종 보고서는 모든 1,920개 실제 표본의 영상 오차 기준 통과와 입력 SHA 불변을 확인해야 하며, 전환 카드 60개를 포함한 1,980프레임·60fps·33초를 검증한다.

검수자는 이번 검수에서 GPU 호출·scene 생성·물리 실험·학습을 실행하지 않았다. 기존 소스·원자료는 변경하지 않고 이 검수 문서만 새로 작성했다.
