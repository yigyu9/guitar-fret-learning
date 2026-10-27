# 접촉점 비교 이미지 최종 검수

2026-10-17. 독립 검수자 `current_pose_materials_review`.

**요약 판정: 문제없음.** Critical / Warning / Suggestion: 없음.

v1→v2 변경은 카메라 확대, 시점 제목, 부위별 고정 라벨과 연결선 및 사용하지 않는 import 제거에 한정된다. 원 접촉 선택·좌표 변환·분석값은 바뀌지 않았다.

[최종 PNG](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v2/recorded_contacts_29s.png)를 직접 확인했다. 정면/비스듬한 시점, 시각 메시/source 충돌 형상 비교, 가슴·상완·허벅지·척추 라벨이 읽힌다. 가까이 있는 가슴·척추 마커는 분리된 라벨과 연결선으로 구분된다. 가림을 무시한 점 투영, lambda=0 제외, 점 크기가 힘이 아니라는 범례가 표시된다.

[README_v2](/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/README_v2.md)는 양성 raw 7행과 중복 점, body-local 변환, COM 미가산, source/cooked 구분을 정확히 설명한다. `0.0754mm`를 해당 특징점에서 visible triangle까지의 최대 unsigned 거리로 제한하며, 전 메시 간격이나 cooked 표면 비교로 확대하지 않는다.

render_report의 네 패널은 각각 106 body readback, 위치 오차 0m, 회전 최대 `4.002966042486721e-16rad`, clock 0을 기록한다. 원 입력 보존 검사는 root의 최종 검증을 따른다. 앞선 좌표·분석 사전 검수는 유지하며 렌더러나 분석을 다시 실행하지 않았다.

- render_v2.py SHA-256: `79a82c2b57bf684f57cbc115dc5e2bcce25d1af8cc2f155514b9525eff38ac69`
- 최종 PNG SHA-256: `4b3d67dd15ecb407a43244c15601da962b6b4f85d8028312f961e34e30a53e42`

검수자는 이 문서만 작성했다.
