# 동일 조건 0.5초 원자료·산출물 독립 검수

- 검수일: 2026-10-07
- 범위: 이번 PI/RATE_PI/PALM_RATE 원자료, 후속 analyzer·plotter·계획·README·CHANGED_FILES·VISUAL §41·PLAN §49.
- 편집: 이 기록만. 이전 code_review와 frozen 결과 보존. native 초기화·rollout·source query 실행 없음.

## 요약 판정: 문제없음

- Critical: 없음.
- Warning: 없음.
- Suggestion: 표의 기타 오차가 전체 구간 최대값임을 명시한 교정과 fresh 초기화 표현을 확인했다. 남은 finding 없음.

## 독립 원자료 검증

- 각 121개 상태/query/trace와 120개 control/contact, 30회 60 Hz 갱신의 시점을 확인했다. PI의 이전 동일 자세 3초 run 중 0.5초 5배열 prefix와 세 조건 각각 이전 0.1초 7배열 prefix가 exact다. 초기 native 전체 state도 같다.
- 90개 update의 PI 오차·적분, 각 anti-windup iteration의 raw 값·단조 mask·적분 복구·최대 25회 종료, PALM RHS·regularizer·목적함수와 자유/활성 축 KKT 조건을 독립 대조했다.
- 실제 float32 전달 목표·갱신 사이 유지, 총 ±0.15 rad/diagnostic box 및 직전 전달 목표 기준 ±0.02 rad rate를 확인했다. 갱신 시간은 제출 직전 `(physics_step-1)/240`이다.
- 저장 raw J/실제 q의 tangent 변환과 COM→source shift를 대조했다. 726개 양손 source 중심을 native pose와 초기 local offset에서 독립 재구성했고, 363개 landmark normal proxy를 재계산했다.
- 360개 장력 적용을 직전 pre-step route의 원본 tension-only 법칙으로 재계산했다. 고정 rest length 1.1010801317960974 m를 유지하며 post-step route와 적용 시점을 혼동하지 않는다.
- 실제 scalar-limit 최대 초과는 세 조건 공통 0.030300427°다. PI-demand/applied mismatch는 92/96/116개 physics sample이며 별도 active-bound 축 집계와 일치한다. 목표 제한을 실제 상태 제한 인증으로 보지 않는다.
- LH–기타 contact 행은 모두 0이다. RH 행/서로 다른 physics sample 수는 PI 127/35, RATE_PI 97/31, PALM_RATE 135/36이다. contact 행은 힘·관통 깊이·연속 지지나 원인의 증거가 아니다.
- 기타 state equality는 RATE_PI/PALM_RATE 모두 false이며 실제 전체 저장 state와 일치한다. 같은 오른팔 알고리즘에도 전달 목표 차이는 최대 0.000629574 rad다.

## Analyzer·매체·문서

- 후속 6개 계약 검사·21개 이전 prefix·138개 입력 SHA를 확인했다. 새 analyzer의 배열/step/time/30 update/121 finite torque coverage와 이전 producer 보존 경계는 실행 전 검수와 일치한다.
- 지원 plot CLI를 새 `/tmp`에서 실행했다. PNG 2108×1401이 canonical과 byte/RGBA exact이며 직접 4개 panel을 확인했다. comparison·138 embedded·22 consumed JSON·producer·출력 SHA가 current다.
- 거리 mm/회전 degree/목표 변화 rad와 시점이 원자료에 일치한다. false 기타 equality를 허용하고 실제 raw와 recorded bool 일치만 검사하며, 차이 관측 footer를 사용한다.
- README 11행의 최대 기타 오차, 17행의 최대값 차이, 25행의 각 fresh 초기화 설명을 확인했다. CHANGED의 runner 29/analyzer 18행, VISUAL 이미지 848/설명 850행 및 계획 결과·PLAN §49·프로젝트 README도 수치와 경계에 일치한다.

## 최종 판정 및 동결

PALM_RATE는 RATE_PI보다 손 중심 최대 이탈을 25.134781 mm 줄였지만 90.540508 mm가 남는다. 최대 기타 위치 오차는 0.400491 mm 늘고 회전 오차는 0.243864° 줄어 tradeoff다. 실제 왼손 지지·초기 기타 자세 유지·안정 연주 성공으로 채택하지 않는다. Normal은 해부학적 부호 미검증 proxy이며 이번 1초/새 gain·box·PD는 미실행이다. 남은 finding 없이 이 기록을 동결한다.
