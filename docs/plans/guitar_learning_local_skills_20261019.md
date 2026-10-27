# 단음 해제·타현 후 동작의 국소 학습 구현

요청: 단음 진단에서 정한 개선 방향을 구현한다.

전제: 현재2시간 단음 실행과 기존 진급 watcher의169/15개 봉인 소스를 변경하지 않는다. 새 코드는 guitar_learning/local_skills에 추가한다. 기존 성공/안전 문턱과39행동/원 native 범위를 유지하며, 실제 전체7초 품질 성공을 통과한 교사 실행만 학습에 사용한다. 성공 동작이 확인되지 않으면 BC/PPO로 실패 예제를 성공처럼 넘기지 않는다.

- [x] 현재 checkpoint/제어/교사 경로를 확인하고 새 native probe·후처리 controller·캡처 형식을 구현한다.
- [x] 현재 범위 내 LH 해제와 RH 회복 후보를 CPU 검사 후 한 번에 한 native 환경으로 확인한다. policy/zero 기준선과 실제240Hz안전/품질·입력 SHA를 기록한다. 손별2개 교사 후보가 각각 전체7초 성공했고 기준선은 실패했다. 전체8개 완주에서 물리 실패0이다.
- [x] 성공한 후보만563 masked local BC에 연결하고 기존 prefix·critic/std/inactive 보존과 새 schema/엄격 계약을 CPU 검사한다. 실제 성공 자료 적합은 native 결과에 종속된다.
- [x] 정책 단독 native 평가 후에만 새 PPO warm-start를 허용하는 연결을 구현·CPU 검증한다. 기존 strictresume는 그대로이며 원실행을 몰래 전환하지 않는다. 실제4/4 통과 여부는 별도 실험이다.
- [x] 검수·결과·한계·실행법·이전버전 보존을 문서화한다.

기존32학습 worker는 유지한다. 새 feasibility 실행은 CPU 정책·native1환경만 순차 사용하고 메모리 여유8GiB 시작/6GiB 중단 보호를 둔다. 현재 baseline 실행의 설정을 바꾸지 않는다. 새로운 대규모PPO 비교/LR·gamma동시 변경은 이번 구현 범위가 아니다.

2026-10-19 01:53 KST: 새19개 CPU 검사28.903초 PASS, change-reviewer 검수 문제없음. source_v3로 left_native_probe_v2 진행 중이며 policy/zero 기준선은 전체7초·물리 실패0/음악 품질 실패다. 중단한 v1은 gzip 기록 비용 조정 전247tick에서 직접 중단한 자료로 보존했다. 그 중단을 물리 실패나 품질 성공으로 해석하지 않는다. controls/probe/learning/train/evaluate는 동결했다.

2026-10-19 02:38 KST: 양손 각1000step BC 완료. LH 정책 단독4/4 품질·안전 성공, 입력SHA 불변과 정상 종료 후 gate 생성. 별도 PPO설정의 실제 train.validate_gate도 통과했다. RH 정책은4회 평가 중 첫 시험이 성공했다. 새로운 PPO는 시작하지 않았다. 구현·교사·BC·정책 증거를 분리한 결과 README 초안과 독립 실제 증거 검수도 작성했다.

2026-10-19 02:50 KST 완료: RH도 정책 단독4/4 stage1품질·안전 성공, source 불변·정상 종료·gate 및 실제 train.validate_gate 모두 통과했다. 양손 별도 PPO 준비 설정을 보존했다. 총16회 전체7초 비교/평가를 마쳤다. RH 인정타현 오차는50.178669ms1회·108.706248ms3회이며 엄격100ms 시각조건은1/4다. 손별 시험의 joint MusicLedger matched50/100은모두0이며 양손합주 성공으로 해석하지 않는다. 새 PPO는 미실행이다. 원 장기학습은 시간예산으로 정상 종료했고 watcher의 원대상은 그대로다. 최종 입력169/6/15/11 및 양손 probe1566/평가1658개 각SHA 변경0. 결과와 실제 한계는 guitar_learning_local_skills_v1/README.md와 validation_summary_v1.json에 기록했다.
