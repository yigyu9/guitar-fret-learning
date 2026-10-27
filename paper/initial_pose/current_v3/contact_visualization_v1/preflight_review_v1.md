# 접촉점·형상 비교 이미지 사전 검수

2026-10-17. 독립 검수자 `current_pose_materials_review`.

**판정: 문제없음. 단일 비교 이미지 렌더링 진행 가능.** 실제 점·라벨의 구분과 투명 형상 가독성은 출력 후 확인한다.

검수 소스:

- [analyze_v1.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_contacts_v1/analyze_v1.py), SHA-256 `cc961fd2b6800c48523524518a7c39525c3b6c91a70ccc0918cbd472d2f023bd`.
- [render_v1.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_contacts_v1/render_v1.py), SHA-256 `8b0c847d3df3162e920ffa64cb5583de65c1a897dac8a8b334780f3e93593147`.

접촉 localPos는 해당 body pose와 직접 합성하고 COM을 더하지 않는다. 분석은 같은 step의 상태와 접촉을 사용하며 원 raw contact를 보존한다. 29초 기타–인체 raw 8개 중 양성 7개만 표시하고 중복 위치와 zero lambda를 구분한다. Chest·R_Shoulder·R_Hip뿐 아니라 Spine도 표시한다. 이전 독립 좌표 검수와 일치한다.

원 XML과 선언 mesh를 expected SHA로 대조한다. 현재 G:body의 mesh scale을 반영하고 local geom 변환이 없는 것을 assert한다. 거리는 최근접 삼각형 거리이며 시각 mesh 1개와 collision mesh 63개의 개별 삼각형을 대상으로 한다. collision union의 외부 경계나 PhysX cooked 표면 거리가 아니다. 두 거리의 차이를 실제 표면 사이 간격으로 해석해서는 안 된다.

렌더러는 원 source의 visual 선택과 저장 body pose 배치를 재사용한다. 충돌 overlay는 접촉한 인체 부위와 G:body의 source 선언을 사용하며 contype/conaffinity 0인 visual-only geom을 제외한다. 현행 대상에 support proxy는 포함되지 않는다. 점은 가림을 무시한 2D 투영임을 범례와 보고서에서 밝히며 힘·면적이나 고유 접촉점 수로 표시하지 않는다.

독립 CPU 확인:

- 분석 입력 116개 SHA 재검사: 불일치 0.
- 29초 양성 7개·zero 1개, 양측 body-origin feature 차이 최대 `8.093078038059183e-8m` 확인.
- 양성 접촉점의 visible source 삼각형까지 unsigned 거리 최대 `0.0753460435563546mm`, collision 개별 삼각형까지 최대 `0.0759584283137085mm` 확인. 이 지점들의 작은 거리를 전 형상의 일치나 cooked 표면 검증으로 확대하지 않는다.
- 두 카메라의 좌표축과 fovy 34도 투영을 독립 계산했다. 모든 양성 점이 카메라 전방이며 450×270 패널의 표시 범위 안에 있다.
- 시간 적분 호출은 없으며 원 코드·입력은 변경하지 않는다. 사전 검수에서는 GPU·Renderer를 호출하지 않았다.

Critical / Warning / Suggestion: 미해결 항목 없음. 검수자는 이 문서만 새로 작성했다.
