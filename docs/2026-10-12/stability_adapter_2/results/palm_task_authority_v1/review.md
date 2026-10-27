# 저장 Palm task 범위 독립 검수

2026-10-07. 새 분석/plotter, authority 원자료·provenance·그림·관련 문서와
EXPERIMENT_WORKFLOW의 이번 품질 규칙만 검수했다. 다른 공유 파일은 수정하지 않았다.
검수자는 저장 자료 계산·순수 CLI만 실행했으며 native/query/controller 실행은 없다.

요약 판정: 문제없음. 독립 world 축의 국소 선형 범위 분석이며 동시 도달성 인증은 아니다.

## Critical / Warning / Suggestion

- Critical: 없음. 분석 수식·계산 코드에 수정 요구 사항 없음.
- Warning 해결: 결과 README:9/누적38절의 빨간 선은 `p_goal−p_current`다.
  `A(q_play−q_actual)`는 interval의 base 항이며 필요한 실제 변위와 다르다.
  README:19도 각 저장 시점 q_actual에서 구성한 3×12 A로 바로잡았다.
- World XYZ 표시와 local linearization을 구분했다. Containment는 관측값이며,
  결과가 범위 밖이라는 이유로 그림 생성을 거부하는 gate를 제거했다.
  품질 매뉴얼 :40–43의 field/단위/frame/shape/도출값 대조 규칙은 이번 수정과 일치한다.

## 독립 확인

- 3개 계약 검사·76개 명시 입력 SHA가 현재 파일과 일치했다. 기존 보정±0.15rad와
  C02±0.3∩native bounds를 delta 좌표로 옮긴 하한/상한과 열12개가 일치했다.
- SciPy 회전 미분으로 각 시점 tangent를 재구성하고 COM→source shift를 대조했다.
  25시점마다 12차원 box의 4096 모서리를 열거한 extrema가 analytic min/max와
  일치했다(최대 차이1.81×10⁻¹¹m). SVD 차이는3.73×10⁻¹¹m/rad 미만이었다.
- Step24 필요 world 변위는[-9.389475,23.138609,41.648954]mm다.
  Singular values는[0.653877653,0.619258465,0.203808618]m/rad이며,
  25개 표본의 각 축 containment와 표의 envelope/공통 interval 해석이 일치했다.
- Saved-only 분석 module CLI는 전체 JSON이 같았다. 최종 plot 지원 CLI exit0,
  PNG2340×864 byte/RGBA exact와 직접 시각 QA를 확인했다. Authority JSON·76 inputs·
  producer·출력 manifest SHA가 일치했고 false-containment 순수 fixture도 loader가 받아들였다.
- 새 변화율 제한은 계산에 없으며, 기존 자료만 읽고 목표·모델·물리·제어를 바꾸지 않았다.

## 최종 판정 및 동결

축별 interval 통과는 동일 delta의 세 축 동시 달성·비선형 FK·실제 drive·접촉·기타 안정성을
입증하지 않는다. 위치 제어 승인 대기는 그대로다. 미해결 finding 없이 이 기록을 동결한다.
