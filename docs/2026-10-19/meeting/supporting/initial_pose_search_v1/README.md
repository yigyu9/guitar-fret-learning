# 초기 자세 탐색 이미지 수집 근거

완성 이미지는 [result/images/initial_pose_search](../../result/images/initial_pose_search), 발표 설명은 [초기 자세를 찾아간 과정](../../result/documents/01b_initial_pose_search.md)에 있다.

- `collect.py`: 선택한 기존 이미지·원결과 문서를 복사한 코드. 시뮬레이터와 렌더러를 실행하지 않는다.
- `manifest.json`: PNG 10개와 원결과 문서 9개의 원본·사본 절대경로, SHA256, 크기, 이미지 해상도와 검증 범위.
- `source_records/`: 당시 결과 설명 7계열과 잘못된 표현을 정정한 V2 이미지 설명 2개. 원문 그대로 보존했으므로 내부 링크는 원프로젝트를 가리킨다.
- `PLAN.md`: 수집 범위와 확인 목록.

기존 원본을 수정하지 않았고 모든 사본은 원본과 바이트 동일함을 확인했다. PNG 열기도 전부 통과했다. 새로운 이미지나 합성표를 만들지 않았으며 비교표는 원래 저장된 파일이다. `collect.py`는 이미 manifest가 있으면 중단한다. 재수집 시에는 새 버전 폴더를 사용한다.
