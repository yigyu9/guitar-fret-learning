# 추가 20/30mm source 탐색 사전 검수

요약 판정: **문제없음 — 새 source2 CPU 탐색 진행 가능**. Critical 0 / Warning 2 / Suggestion 0. 신규 수락 후보나 native 접촉 회복의 인증은 아니다.

## 변경 확인

보존된 source1과 source2의 diff는 다음 세 항목뿐이다.

- [계획 입력:40](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v2.py:40): 새 `RIGHT_BODY_APPROACH_PLAN_V2.md` 핀.
- [출력:50](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v2.py:50): 배타 생성할 `search_v2` 경로.
- [탐색:53](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v2.py:53): 현재 waist 기준에서 몸 쪽 이동 20/30mm 두 값.

수평 축·허벅지 높이 재맞춤·현재 회전 보존·39개 초기각 범위/모델 교차·finger42 고정·팔꿈치 ±5° 여유·full source LP·6 capsule·waist/손목/머리/자연 팔 수락 조건은 같다. actual guitar XML mesh 69개 및 manifest 추가 항목, human37 입력 핀과 종료 SHA 검사도 유지된다. controller/asset/물리 변경은 없다. Python AST를 통과했고 source/native/학습을 검수자가 실행하지 않았다.

[계획 V2:18](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BODY_APPROACH_PLAN_V2.md:18)는 추가 수락 후보의 정지 시험을 최대 두 번으로 한정하고, 후기 두 블록 접촉이 회복되지 않으면 팔꿈치 시험을 생략한다고 명시한다. 기존 source1·계획·출력은 보존한다.

## Warning

1. [수락 검사:94](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v2.py:94)는 초기 source proxy 안전·근접 조건이며 실제 cooked 지속 접촉이나 힘 기여를 뜻하지 않는다. 20/30mm 위치 변경과 초기 IK 각도 변화가 함께 있으므로 실제 개선을 위치 하나의 원인으로 확정하지 않는다. 후보/config와 native 후기 원자료는 완료 후 별도로 검수한다.
2. [기존 분석 실패 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/analysis_3mm_v1_failure.json:1)은 과거 baseline attempt가 현재 main PLAN SHA를 엄격 비교해 거절한 1건이다. 허가된 append의 원문 prefix 근거와 기존 canonical 분석을 별도 사용해야 하며 과거 expected SHA를 덮어쓰면 안 된다. 이 분석 실패를 물리 재실행이나 native 실패로 집계하지 않는다. 기존 기록의 보존과 후속 새 case 감사 방식은 이번 source 조건을 완화하지 않는다.

## 확인 SHA-256

- `search_right_body_approach_v2.py`: `9eacfc435d8c63c3259ffbbba23f6e786a5d7cbb05fb2fb796cca44ba9bb88c3`
- `RIGHT_BODY_APPROACH_PLAN_V2.md`: `aa6c7ec92b82ae80c972a9b7447f6b65f3ffb57b3b8276e0a1380e5df072a5cb`

소유한 새 리뷰 파일만 작성했으며 기존 소스·자료·리뷰는 수정하지 않았다.
