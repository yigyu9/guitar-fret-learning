# 논문용 초기 자세 자료 정리

사용자가 요청한 `paper` 하위 자료 묶음을 만든다. 채택된 `margin_only_v1`의 원본을 보존하고 사본·출처를 함께 제공한다. 새 자세 탐색, 물리 실행, 학습은 이 작업 범위에 포함하지 않는다.

- [x] 논문 작성 원칙과 초기 자세 채택 기록, 수치·이미지·영상 출처 확인.
- [x] `paper/initial_pose`에 값·설정·이미지·영상 사본과 한국어 설명 작성.
- [x] 81관절 대응, 파일 해시, 이미지 및 영상 형식, 문서 링크 검증. 원본 사본 30개 일치, 이미지 6개·영상 8개 확인. 기타 회전은 native 원값을 정규화해 manifest와 정확히 일치함을 확인했다.
- [x] 별도 change-reviewer 검수 및 논문 자료 색인 연결. 검수 결과 Critical/Warning/Suggestion 없음.

검증 기준: 원본과 사본이 동일하고, 모든 관절값의 단위·순서가 명시되며, 15초 한 번의 왕복 타현과 후속 유지가 곡 연주로 설명되지 않는다. root/하체 고정, 스트랩 OFF, 왼손 접촉이 남는 조건을 수치·영상과 함께 명시한다. 원자료 경로의 날짜를 실험 날짜로 재해석하지 않는다.

완료 자료: [초기 자세 자료](/home/ajou/yigyu/3/paper/initial_pose/README.md), [검증 결과](/home/ajou/yigyu/3/paper/initial_pose/verification.json), [별도 검수](/home/ajou/yigyu/3/paper/initial_pose/review.md).
