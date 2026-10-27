# 가까운 REACH에서 손바닥 방향 강화

> **폐기된 실험 기준 (2026-10-05):** 이 문서는 손바닥 방향을 강화하던 이전 실험의
> 기록이다. 현재 목표는 palm-local 중지 방향을 넥 바깥 법선에 정렬하는 것이며,
> 손바닥 법선-넥 길이축 조건은 제거했다. 아래의 구형 보상 버전·측정값은 이력 보존용이고
> 현재 설계나 재현 기준으로 사용하지 않는다. 최신 기준은
> [`LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md`](../2026-10-12/plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md)다.

사용자 승인: 2026-10-03, 수정 및 짧은 검증 진행.

목표: 기존 거리 접근을 유지하면서 넥 뒤쪽 면을 향하는 손바닥 방향을 강화한다.
기존 목표점/관측/action/전환 임계값은 유지한다. 기존 reward optimizer 재개를 허용하지 않는다.

- [x] 방향(법선·heading)을 간격·속도와 분리해 가까운 거리에서 더 강하게 보상한다.
- [x] 조건별 통과율, 가까운 구간 방향 오차, 기타 이동량을 평가에 기록한다.
- [x] 보상 경계·거리 단조성·방향 민감도와 평가 집계를 테스트한다.
- [x] change-reviewer 독립 리뷰를 반영한다.
- [x] 기존 318회 actor를 초기값으로만 사용하고 새 critic/optimizer로 짧은 비교 학습한다.
- [x] 같은 seed/noise 평가 및 영상으로 개선 여부와 한계를 보고한다.

수치 선택: position=p, 방향 점수=o, 간격/속도 점수=s일 때
score=p*(0.20+0.75*o+0.05*s).
거리 영향은 최악의 방향에서도 양수이며, 방향 오차가 속도 평균에 희석되지 않는다.
짧은 학습은 성공 증명이나 장기 실행 승인으로 해석하지 않는다.

검증 진행: CPU 전체 테스트 94개 통과. change-reviewer 오류 없음. GPU 실험은 32환경×30update, 기존 318회 actor/log_std만 초기화하고 critic·optimizer는 새로 생성. seed20261012의 noisy16 및 zero-noise1 영상을 비교한다.

첫 32×30 실험에서 거리 1.44→1.13cm, 근거리 법선36.3→43.7°, heading37.7→54.0°, 기타 최대 이동14.8→24.0cm로 회귀했다. 초기 p² 방향 벌점을 배제하고 최종 multiplicative 방향 가중치0.75로 강화하여 재검증한다. 초기 실험 artifact와 최종 실험은 별도로 보존한다.

최종 보상 버전: distance_palm_alignment_dense_v3. 초기 v2의 p² 식과 다른 critic/optimizer 재개를 막기 위해 리뷰 지적을 반영했다. 최종 검증 산출물은 docs/2026-10-12/회의/results/palm_alignment_v3_20261003/.

최종 검증 완료: 32환경×30update, 약6.2만sample. noisy16 평균최소거리1.44→2.11cm, 근거리법선36.3→40.1°, heading37.7→48.1°, 기타최대이동14.8→22.3cm. GRIP/최종성공0. 구현테스트는통과했으나 물리개선은실패했으며 새checkpoint는실험용으로보존하고 기존checkpoint를덮어쓰지않았다. 비판적한계: cold critic/optimizer 적응과 reward효과를 분리하지못했고 단일seed의짧은실험이다. comparison.json과 전후영상으로 결과를보존했다.
