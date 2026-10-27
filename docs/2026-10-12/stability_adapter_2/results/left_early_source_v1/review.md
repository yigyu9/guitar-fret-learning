# 초기 왼손 source 관찰 독립 검수

- 검수일: 2026-10-07
- 범위: 이번 saved-state 분석·plotter·원자료·관련 계획·README·CHANGED_FILES·VISUAL_REPORT §39.
- 편집 범위: 이 검수 기록만. native 초기화·simulation·source query 재실행 및 기존 배치 변경 없음.

## 요약 판정: 문제없음

- Critical: 없음.
- Warning: 없음.
- Suggestion: 최종 문서의 화살표 색상과 이미지 줄 번호 교정을 확인했으며 남은 finding 없음.

## 확인한 근거

- 분석의 4개 검사와 68개 입력 SHA를 확인했다. 저장된 7개 시점의 physics step·시간·기타 p/q 오차와 접촉 행 매핑이 원자료와 일치한다.
- 저장 landmark의 cross product로 normal proxy를 독립 재계산했다. source palm 중심·기타 world/local 변환·국소 단면 하단과 상대 높이·넥 투영 범위를 대조했다.
- 0/24 step source hull의 witness 거리와 half-space feasibility를 확인하고, 독립적인 단위 변환 QP 재계산으로 초기/최종 거리와 일치함을 확인했다.
- 지원 plot CLI를 새 `/tmp` 경로에서 실행했다. 두 PNG가 canonical 파일과 byte/RGBA exact이며 입력 JSON 2개·embedded SHA 68개·producer·출력 2개의 hash를 확인했다. 두 그림을 직접 시각 검수했다.
- README 27행의 `금색 화살표`가 producer의 normal proxy 색상과 일치한다. CHANGED_FILES 6행의 이미지 위치 822/828행도 최종 누적 보고서와 일치한다.

## 해석과 승인 경계

- source convex QP unsigned gap과 backend signed query는 서로 다른 측정이다. 최종 backend 20 mm는 query cutoff이며 실제 간격이나 관통 깊이가 아니다.
- 초기 접촉 값은 `null`이고 선택된 완료 step의 왼손 접촉 행은 비어 있다. 저장 post-state source query와 native 접촉의 solver 시점을 동일시하지 않는다.
- normal은 native landmark 기반 palm-up proxy이며 해부학적 부호 검증은 미완료다. source 근접·형상 그림·접촉 행은 실제 지지력, cooked clearance 또는 원인의 인증이 아니다.
- 그림은 저장 pose의 source 형상을 CPU로 재구성한 것이다. 기존 물리·PI·gain·초기조건을 변경하지 않았고 새 위치 제어는 승인 대기다.

## 최종 확인 및 동결

최종 색상·실제 줄 번호 교정을 반영한 문서가 수치와 producer에 일치한다. 남은 finding 없이 이번 saved-state 진단 단위의 검수를 마쳤다. 이 기록은 동결하며 안정화 성공을 판정하지 않는다.
