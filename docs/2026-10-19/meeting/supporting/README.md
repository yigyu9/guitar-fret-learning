# 제작과 검증 보조 자료

교수님께 보여드릴 완성본은 상위 `result/`에 있다. 이 폴더에는 발표에 직접 넣지 않는 제작·출처 파일을 둔다.

| 경로 | 내용 |
|---|---|
|`catalog.json`|선택한 원본과 미팅용 사본의 대응·용도·조건|
|`scripts/assemble.py`|완성 미디어와 근거 기록을 복사하고 SHA를 대조하는 조립 스크립트|
|`source_records/`|초기 자세·손별 정책·전곡 시험·새 자세 진단의 원결과와 CSV 사본|
|`source_code/`|초기 자세 재생 및 quaternion 수정 그래프의 원제작 코드 참고 사본|
|`provenance/copied_files_v1.json`|원본 절대경로·사본경로·SHA·크기|
|`qa/verification_v1.json`|이미지 열기·영상 전체 decode·복사 SHA·폴더 내 문서 링크 확인|
|[guitar_model_comparison_v1/](guitar_model_comparison_v1/README.md)|추가 요청한 초기·현재 기타 동시 native 촬영의 코드·입력 해시·로그·검증|
|[initial_pose_search_v1/](initial_pose_search_v1/README.md)|기존 자세 탐색 PNG 10개·설명 9개 수집 코드와 SHA 출처|
|[contact_visualization_v1/](contact_visualization_v1/README.md)|기존 세 시점 접촉 PNG 6개·설명·접촉 요약의 수집 코드와 출처|
|[initial_pose_search_addendum_v1/](initial_pose_search_addendum_v1/README.md)|더 이른 우측 기울임·둥근 허리 PNG/영상 첫 프레임의 출처·대조|
|[current_initial_pose_v1/](current_initial_pose_v1/README.md)|현재 기준035/v14 이미지·native 영상과 별도 진단 초기 이미지의 출처·검증|
|[guitar_collision_comparison_v1/](guitar_collision_comparison_v1/README.md)|native 시각/충돌 카메라·원본 depth/segmentation·그림·수치·검증|
|[current_pose_contacts_22s_v1/](current_pose_contacts_22s_v1/README.md)|현재 준비 완료22초의 접촉11행·native PNG SHA·투영 좌표·제작 코드|
|`PLAN.md`|이번 정리의 범위와 확인 목록|

프로젝트 루트에서 다음 명령으로 원본과 사본이 같은지 다시 확인한다.

`python docs/2026-10-19/meeting/supporting/scripts/assemble.py --verify`

조립 스크립트는 원실험을 실행하지 않고 기존 완성본을 복사한다. 같은 이름에 다른 내용이 있으면 덮어쓰지 않고 중단한다. 새 판을 만들 때는 별도의 meeting 버전 폴더와 provenance 파일을 사용한다.

`source_code/`는 원본 코드의 참고 사본이다. 원모델·mesh·큰 native 기록과 원래 절대경로 의존성까지 묶은 독립 실행 배포본은 아니다. 원재생·그래프 생성은 `source_records/`의 보고서와 원프로젝트 경로를 함께 참조한다. 원문 기록의 링크는 보존을 위해 원래 프로젝트 경로를 유지한다.
