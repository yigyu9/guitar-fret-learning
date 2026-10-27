# 손별 실제 학습과 경과 분석

사용자 요청: 구현한 손별 구조를 실제로 학습하고 경과를 분석한다. 기존 짧은 연결용 checkpoint는 성공 전문가가 아니므로 이번 두 단독 정책은 seed7의 새 초기화에서 시작한다. 기존 실험·코드·모델·자세·보상 정의는 변경하지 않는다.

## 실행 예산과 판단

- 첫 음 고정: `05_BN2-131-B_solo`, B, physical string2/fret7/ring/down.
- 왼손/오른손을 각각 독립4환경으로 동시에 실행한다. 전체 native worker8개와 GPU정책2개. 각 H128, batch512, medium, actor_lr3e-5/value_lr3e-4, epochs2, minibatch256, std exp(-3), cost_weight1.
- 손별 soft wall1800초/최대64업데이트, 5업데이트 주기 checkpoint.4GiB 메모리 보호·10초 진행·5초 자원 표본·worker timeout300초 유지. wall 예산은 배치 경계에서 적용한다.
- 원 권장8환경/H256/batch2048과 수집 규모가 다르므로 기존 공유 Actor 실행과 수렴 속도의 통제 비교로 해석하지 않는다. 두 단독 학습의 초기 경향과 손별 실제 성공 여부를 확인한다.
- Root 고정·하체 유한 제어·105/97/8·자유 기타/중력ON/스트랩OFF·2초 준비·기존240Hz 안정성 비용/실패 종료를 유지한다. 기타 직접 보조/강제부착/지속 state overwrite 없음.
- 안정성 실패 급증·메모리 보호·비유한 값·KL 또는 worker 오류는 즉시 점검하고 유효 checkpoint/실패를 보존한다. 반복 성공이 확인되기 전 결합 학습을 시작하지 않는다.

## 체크리스트

- [x] 현재 문서·소스와 기존 최종 감사·GPU/메모리 가용 확인.
- [ ] 설정·소스·계획을 새 결과 phase에 보존하고 단독 학습 시작.
- [ ] 학습 중 손별 접촉/기하 타현·목표 거리·보상·비용·실패·메모리/PPO를 점검.
- [ ] 종료 후 committed/부분 rollout·완료 episode·초반/후반·최종 checkpoint·native lifecycle·입력 무변경 분석.
- [ ] 원자료 기반 도표·한국어 해석·다음 권고, 독립 검수와 최종 보존 감사.

결과 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1`.
왼손의50ms 접촉 후보, 오른손50/100ms 기하 타현, 통합 음악·실제 음향 성공을 구분한다. 표식 거리는 접촉 gap이 아니다. 학습 중 통계는 미완료 prefix이며 최종 감사를 대신하지 않는다.
