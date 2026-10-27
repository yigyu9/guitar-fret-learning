# 초기 Palm Jacobian–FK 독립 검수

2026-10-07. 이번 새 FK 측정·좌표 비교·plotter와 원자료, provenance, 관련 문서만 검수했다.
검수자는 저장 자료의 수치 계산과 순수 CLI만 실행했다. Native 초기화·query·rollout을
재실행하지 않았으며, 다른 공유 파일이나 기존 검수 기록을 수정하지 않았다.

요약 판정: 문제없음. 현재 초기 자세의 미분 계측 근거이며 runtime 제어·안정성 인증은 아니다.

## Critical / Warning / Suggestion

- Critical: 없음. 측정과 좌표 변환 코드에 수정 요구 사항 없음.
- Warning 해결: plotter의 위치 오차 m/rad→mm/rad 환산 누락을 수정했다.
  `plot_palm_fk_coordinates.py:62/:75`의 ×1000과 최종 그림·단위가 일치한다.
  이전 그림·producer는 보존하고 `artifacts_validated/`를 최종 산출물로 구분한다.
- Suggestion 해결: body-origin 가설은 source 중심 자체가 origin이라는 뜻이 아니라,
  선형 Jacobian의 기준점을 origin으로 가정해 source 중심으로 옮긴 비교다.
  최종 결과 README와 누적36절에서 이 가설과 COM 기준 비교를 명확히 구분했다.

## 독립 확인

- 23개 fresh 초기 저장 상태에서 실제 native DOF q=목표, 속도0, steps0을 확인했다.
  Thorax_x forward/Thorax_z backward/다른10열 central 차분과 실제 q 간격,
  각 probe의 보존·승인 box 검사, raw 6개 계약 검사·93개 입력 SHA가 일치했다.
- 저장 양끝 위치와 SciPy world 상대회전 log로 12열 FD를 독립 재계산했다.
  네 초기 3좌표 블록 및 zero/tiny case의 SO(3) tangent 검증 오차는 2×10⁻¹⁰ 미만이다.
  native 블록에 tangent를 오른쪽 곱하고 COM→source point shift하는 부호가 맞다.
- 좌표 비교 3개 검사·98개 입력 SHA가 통과했다. 독립 계산 source 최대 오차
  0.000274298693m/rad, angular 0.000194956546rad/rad가 기록과 일치했다.
  canonical rl38 interpreter의 saved-only coordinate CLI는 전체 JSON이 같았다.
- 지원 plot CLI를 새 `/tmp`에서 실행해 exit0을 확인했다. 최종 PNG 2520×936은
  canonical과 byte/RGBA가 같았고 직접 시각 QA를 마쳤다. 93/98 embedded 입력,
  raw/coordinate JSON·producer·출력 SHA와 로그 축·관절군 최대 norm 집계가 일치했다.
- 현재 계획·제안은 raw 오차와 보정 후 오차를 구분하고 SDK spherical 예제를
  같은-body MJCF importer/native DOF velocity의 일반 증명으로 확대하지 않는다.

## 최종 판정 및 동결

COM 기준과 tangent 해석은 현재 초기 왼팔12의 수치 차분이 지지한다. Runtime 조회 시점·
속도 대응은 별도 미검증이며 새 위치 task·변화율 제한은 사용자 확인 전이다.
코드·수치·물리 해석에 미해결 finding은 없다. 이 기록을 동결했으며 이후 편집하지 않는다.
