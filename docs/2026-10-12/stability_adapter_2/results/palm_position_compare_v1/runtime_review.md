# 승인된 3조건 0.1초 비교: 원자료·산출물 독립 검수

- 검수일: 2026-10-07
- 범위: 이번 PI/RATE_PI/PALM_RATE 원자료, 새 saved-only analyzer·plotter, 결과 문서·승인 계획·PLAN §48·프로젝트 README·VISUAL_REPORT §40.
- 편집: 이 기록만. 기존 code_review 및 frozen 배치 보존. native 초기화·rollout·source query 재실행 없음.

## 요약 판정: 문제없음

- Critical: 없음.
- Warning: analyzer의 배열 길이·시점 검사와 plotter의 관측값 pass gate는 수정 확인 후 해결했다. 남은 finding 없음.
- Suggestion: 없음.

## 독립 원자료 검증

- 세 조건의 초기 native 전체 state가 동일하다. 각 25개 state/query/trace와 24개 control/contact, 6개 60 Hz 갱신의 시점을 대조했다. PI의 states/trace/controls/contacts/leg_torques 5개 배열은 이전 동일 자세 run의 0.1초 prefix와 exact다.
- 18개 update의 실제 q에서 PI 오차·적분·최종 clipped 목표를 독립 재계산했다. RATE/PALM의 각 anti-windup iteration에서 raw 값, 단조 blocked mask, 이번 적분 복구, 종료 조건 및 최대 25회 한계를 대조했다.
- PALM의 위치 RHS·regularizer·목적함수와 자유/활성 축 KKT 조건을 확인했다. source Jacobian은 저장 raw J와 실제 q를 SciPy rotation으로 독립 변환하고 COM→source shift를 대조했다.
- 계산 목표의 float32 offset/전달값, 직전 실제 목표 기준 ±0.02 rad rate, 총 ±0.15 rad와 diagnostic bounds, 갱신 사이 목표 유지가 일치한다. 실제 scalar limit 최대 초과는 세 조건 공통 0.030300427°이며 목표 제한 통과와 구별한다.
- 72개 장력 적용을 직전 pre-step route의 원본 tension-only 법칙으로 재계산했다. rest length는 고정이고 같은 행의 post-step route를 적용 시점으로 오해하지 않는다.
- 모든 저장 기타 body state는 세 조건에서 exact다. 기타 위치·회전 오차를 재계산했고 LH/RH–기타 contact 행은 모두 0이다. source 중심의 offset 변환과 재구성 중심 차이는 약 1e-15 m 이하다.
- 오른팔은 같은 RATE 알고리즘이지만 읽은 actual 상태가 달라 전달 목표 차이 0.000132113695 rad가 존재한다. PI-demand/applied mismatch 8/12/20개 physics sample과 별도 active-bound 축 수를 독립 집계했다.

## Analyzer·그림·문서

- analyzer 34–44행은 사용 배열 25/24개, physics_step·시간 및 6개 update coverage를 검사한다. 수정 후 truncation/misaligned-query 거절 기록과 정상 canonical 재생성 기록을 확인했다. 이전 comparison/producer는 보존돼 있다.
- 현재 comparison의 5개 검사·103개 입력 SHA와 최종 plot manifest의 comparison·103 embedded·16 consumed JSON·producer·출력 SHA를 확인했다.
- 문서의 지원 plot CLI를 새 `/tmp` 경로에서 실행했다. PNG 2108×1384가 canonical과 byte/RGBA exact이며 직접 시각 검수했다. 거리 mm, 회전 degree, 목표 변화 rad 및 update 시점이 원자료와 일치한다. 기타 곡선은 실제 exact coincidence로 겹치며 시각 offset이 없다.
- README 표·선형 잔차 설명·RH 알고리즘 구분, VISUAL §40, 승인 계획 결과 87행 이후, PLAN §48 및 이미지/설명 index 838/840행을 대조했다.
- 최종 plotter는 recorded/raw 기타 state equality의 일치만 검사하고 false 관측을 허용한다. `/tmp` JSON fixture의 다른 state/trace가 로드·렌더되는지, recorded bool 불일치가 거절되는지 독립 확인했다. Footer는 실제 trace equality에 따라 바뀐다. 최종 지원 CLI 재생성도 current producer SHA와 byte/RGBA exact이며 원자료·물리 실행은 변경하지 않았다.

## 최종 판정 및 동결

PALM_RATE의 최대 손 중심 이탈 47.473935 mm는 RATE_PI의 48.835811 mm보다 1.361875 mm 작다. 마지막 선형 계산 잔차 0.689037 mm는 실제 손 이탈을 대신하지 않는다. 기타 오차는 모두 6.874401 mm/1.519676°로 같으며 물리 지지·기타 유지 개선·안정 연주를 입증하지 않는다. normal은 해부학적 부호 미검증 landmark proxy다. 이번 0.1초 비교 밖의 연장·gain/box 변경·학습은 시행하지 않았다. 남은 finding 없이 검수 기록을 동결한다.
