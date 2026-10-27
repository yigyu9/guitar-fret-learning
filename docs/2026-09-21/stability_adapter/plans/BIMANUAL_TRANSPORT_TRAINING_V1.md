# Bimanual transport PPO training v1

목표: 새 오른손 SUPPORT sidecar와 force-gated 왼팔 controller를 사용해
SUPPORT에서 시작하여 5/10 mm 이상의 목표 방향 이동을 학습한다.

## 실행 계약

- 새 checkpoint로 시작한다. 이전 단일손 transport checkpoint는 resume하지 않는다.
- 접촉 복원이 장시간 안정적인 8 environments를 사용한다.
- curriculum은 SUPPORT → 5 → 10 → 30 → 50 → 100 mm이다.
- 10 update마다 checkpoint와 metrics를 저장한다.
- SUPPORT 성공률, projected progress, lateral error, 오른손 SUPPORT rate를
  함께 판단한다.

## 체크리스트

- [x] 2-update preflight와 처리시간 측정
- [x] 장시간 PPO 학습(100 updates, 204,800 simulator steps)
- [x] curriculum 진입 및 checkpoint 선정
- [ ] WAIT부터 전체 영상 렌더
- [x] 로그 분석 및 다음 수정사항 기록

학습용 병렬 환경은 WAIT/REACH를 환경별로 다시 계산하지 않고 검증된 goal
snapshot을 직접 복원한다. 병렬 계약상 boundary 표시는 REACH로 유지하지만 WAIT
settle은 생략하며, 새 snapshot 캡처에만 전체 WAIT→REACH 절차를 사용한다.

## 2026-09-29 결과

- 최종 checkpoint: `bimanual_transport_curriculum_v4_150.pt`
- 실제 저장 update: 100
- 환경 표본 / simulator step: 92,214 / 204,800
- curriculum: SUPPORT(stage 0), 승급 없음
- 최근 64 episode 성공: 17/64 (26.6%)
- 관측 최고 최근 성공률: 40.6%
- 결론: 목표 통과 보상과 미세 탐색은 교정됐지만 SUPPORT 안정성이 80%
  승급 기준에 미달했다. 다음 수정은 학습 시간 연장이 아니라 오른손 접촉이
  기타를 밀어내는 과도응답과 SUPPORT 성공 조건의 병목을 분리 진단하는 것이다.
