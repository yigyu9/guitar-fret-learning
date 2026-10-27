# 접촉·하체 진단 및 정적 Z 비교 검수

별도 change-reviewer 최종 판정: 코드·원자료·현재 계획 문서에 남은 Critical/Warning/Suggestion 없음.
검수는 2026-10-06 수행했다. Luna의 신규 07/08 그림·설명은 제작 중이며 후속 검수한다.

- native 검사 포함 테스트 15개 독립 통과.
- 14 preset의 실제 solver/substep/drive readback 확인. 모든 초기각·기타 목표·effort cap 동일, 하체 외 gain/제어 모드 유지.
- baseline의 매 4 physics step 추출 7개 trace가 이전 batch H0와 완전히 같고, 24 step 적용 장력 0N 재현.
- isolated probe의 허용 preset/실제 solver 모순을 수정: baseline hold/off로 제한, 초기 상태·목표/gain·solver readback·실행 전후 source hash 검사. 새 verified 결과 재현.
- source-shape replay와 14개 report hash·기타 오차·raw 관절 편차/한계 계산 대조.
- 정적 Z 0/2/5/10/15mm 계산을 독립 재현. +5mm는 후보이고 native 목표는 미변경.
- 보호 대상 기존 파일 87개 size/mtime 및 2026-08-19 자료 49개 SHA 불변을 부모가 확인.

교정: contact raw body label의 root `guitar`와 별도 `G:body`를 구별했고, raw label만으로 neck mesh 개별 특정은 하지 않는다. H0 대조는 7개 sampled 상태로 정정했다. 현재 검사 통과는 물리 안정성이나 전체 PhysX clearance 성공을 의미하지 않는다.

원시 실패·기존 결과는 보존했다. 초기 하체각 변경 또는 PGS 최종 채택은 하지 않았다.

## 후속 07·08 산출물 최종 검수

별도 change-reviewer 판정: 남은 Critical/Warning/Suggestion 없음. 그래프의 body별 여러 geometry 간격은 최소값 집계로 교정했고 현 다섯 조건의 수치는 동일했다. +5mm 적용 승인 대기 문구와 절대 이미지 경로를 확인했다. 두 PNG를 임시 경로에 재생성해 픽셀 일치를 확인했으며 원본 JSON·PNG 내용과 mtime을 보존했다. 수치·단위·로그축·raw 관절각 해석도 대조했다. 실제 native Z 변경은 수행하지 않았다.

전체 변경 파일은 [절대 경로·실제 줄 번호 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/CHANGED_FILES.md:1)를 따른다.
