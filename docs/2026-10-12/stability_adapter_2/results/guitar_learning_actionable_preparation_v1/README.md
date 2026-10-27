# 앞2초를 음악적 준비에 사용하는 정책 제어

기존 정책 비참여 정착2초를 제거하고 reset 직후부터 정책이 음악 목표를 관측하고 행동하도록 구현했다. 기존 유한 자세 유지 제어는 계속 작동하며 앞2초의 행동·보상·안전 비용을 PPO 학습 전이에 포함한다. 이는 새 학습 경로의 연결 검증이며 조기 압현 준비나 정밀 타이밍 학습의 완성을 뜻하지 않는다.

## 시간과 코드

| 항목 | 이전 | 현재 |
| --- | --- | --- |
| 초기 native 정착 | 2초 | 0초 |
| 정책 행동 | 5초·300tick | 7초·420tick |
| timing pre-roll | 1초 | 3초 |
| reset부터 첫 press/onset | 4.00/4.12초 | 4.00/4.12초 |
| 전체 episode | 7초 | 7초 |

첫 타현 시각을 앞당기거나 준비 실패 때문에 뒤로 미루지 않았다. 기존 정책 준비1초도 보존했다. `pre_roll_s`는 기존 음악 태스크 시간표에 더하는 오프셋이며, 그 숫자가 첫 타현 시각은 아니다.

권장 실행은 [train_actionable_preparation.py](/home/ajou/yigyu/3/guitar_learning/train_actionable_preparation.py), 평가는 [evaluate_actionable_preparation.py](/home/ajou/yigyu/3/guitar_learning/evaluate_actionable_preparation.py)다. [환경](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py)은 [v5 초기화](/home/ajou/yigyu/3/guitar_learning/environment_v5.py)와 기존 접촉·시뮬레이터 재사용 구현을 계승한다. [Actor 이전](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_transfer.py)은 같은 손·같은 단계·원 목표·행동/안전 조건만 허용하고 시간 이력 정규화 열을7/5로 보정한다. 기존505개 입력의 순서·정규화, 전체536입력·39출력과 네트워크 크기는 유지했다. Critic·optimizer·counter는 새로 시작하며 strict resume는 완화하지 않았다.

[설계·보상·실행 명령](/home/ajou/yigyu/3/guitar_learning/ACTIONABLE_PREPARATION.md) · [왼손 설정](/home/ajou/yigyu/3/guitar_learning/configs/left_actionable_preparation_v1.json) · [오른손 설정](/home/ajou/yigyu/3/guitar_learning/configs/right_actionable_preparation_v1.json). 현재 설정은 N1/H420/업데이트1의 연결 검사 예산이다.

## 첫2초가 실제로 사용되는가

실제 평가 원자료와 PPO의 `rollout_first.pt`에서 다음을 확인했다.

- native 정착0초, reset local step0, 첫 실행의 실제 `gym.get_sim_time`0. 재시작에서는 동일 장면을 유지하고 누적 시계7초를 보존하면서 episode local step만0으로 돌렸다. 숨겨진2초 진행이 없었다. `simulate/fetch` API의 호출 수를 별도로 계측했다는 주장은 하지 않는다.
- 첫 관측부터 음악 목표가 보이며 최초120개 전이에 모두 정책 행동이 있었다. 학습 buffer state는 `(420,1,536)`이고 시각은0에서 시작한다. 첫 실제 physics sample은 local step1이다.
- 초기 결정적 평가의 처음2초에 활성 관절 최대 변화는 LH0.147343/0.146955rad, RH0.093458/0.093629rad였다. 반대 손의 정책 출력은0이다. 실제 관절 움직임과240Hz 비용이 기록됐다.
- LH 준비 보상은 최초2초의 원 target candidate 연속 접촉시간×0.2다. 이전·현재 표본이 모두 양성인 구간만 적분하며 실패가 있는 제어tick의 양성 준비 보상은 억제한다. RH는 기존 준비 guide를 사용한다. 기존 접촉·타현·음악 성공 판정은 유지했다.
- 이번 초기/최종 정책의 LH 첫2초 접촉과 `preparation_contact` 보상은 **0**이었다. 움직일 수 있는 학습 구간으로 연결됐다는 증거와 조기 접촉 준비를 학습했다는 증거를 구분한다. PPO 수집의 RH 첫2초 guide 보상 합계는0.02846836이었다.

원래 후보 접촉과 맞지 않는 distal-origin 거리 보상은 사용하지 않았다. native 실행 전 해당 초안과 CPU 검토 기록을 보관하고 현재 접촉시간 보상으로 대체했다.

## 실제 검증 결과

| 검증 | 왼손 | 오른손 |
| --- | --- | --- |
| 기존 Actor의 새 조건 초기 평가 | 안전·단계 성공2/2, 음 구간 접촉 후보 유지율100% | 안전·단계 성공2/2, 최초 통과 오차57.985/104.186ms |
| 새 조건 PPO 연결 검사 | 1업데이트·420전이·안전 완주 | 1업데이트·420전이·안전 완주 |
| PPO 후 결정적 평가 | 안전·단계 성공1/1, 음 구간 유지율100% | 안전·단계 성공1/1, 최초 통과 오차86.215ms |

모든 새 조건 평가는 policy7초/420tick/1680개240Hz 표본을 완주했다. 기존 타이밍 단계1의±0.5초 기준을 사용했으며 원래 contact-conditioned 음악50/100ms 성공은 별도다. 손별 평가의 원 음악 성공은0이고 접촉 후보·기하 통과는 현 압력·진동·음향을 인증하지 않는다.

오른손의 기존 결과12.286ms보다 정밀도가 나빠졌다. 같은 새 조건 초기 첫회57.985ms와 PPO 후86.215ms를 비교해도28.231ms 악화했다. 초기 두 번째104.186ms를 골라 개선으로 설명하지 않는다. 한 번의 업데이트와 평가만으로 학습 경향이나 일반화를 판단하지 않으며, 이번 목적은 새 구간의 수집·업데이트·저장 연결 확인이다.

PPO 후 최대 기타 이동은 LH5.384mm/RH0.855mm, 발 이동은2.168mm/0.059mm였다. 모든240Hz 평가 표본에서 주요 부위 중 한 곳 이상의 지지 접촉과 양발 접촉이 유지됐고 물리 실패가 없었다. 가슴 접촉 지속·삼중 접촉률은 필수조건으로 요구하지 않았다. Root고정·하체 유한 제어·105/97/8·자유 기타/중력ON/스트랩OFF·기존gain/충돌/의자·직접 기타 보조 힘 금지를 유지했다.

## 자료와 남은 작업

- [초기 실제 평가 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/initial_native_analysis_v1.md), [PPO 후 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/ppo_native_analysis_v1.md)
- `left/right_initial_eval_v1`: 원 Actor 이전의 각2회 결정적 평가. `result.json`, `reset_*.json`, `transitions.json.gz`에 원자료가 있다.
- `left/right_ppo_smoke_v1`: 각1회 PPO 업데이트. `rollout_first.pt`, `update_000000.json`, `transitions.jsonl.gz`, `actionable_preparation_report.json`, `persistent_audit.json`, `report.json`, `initial.pt`, `final.pt`를 보존했다. 터미널 출력은 같은 이름의 `.log`다.
- `left/right_ppo_eval_v1`: 새1업데이트 정책의 각1회 결정적 평가. 결과 모델은 [LH](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/left_ppo_smoke_v1/final.pt), [RH](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/right_ppo_smoke_v1/final.pt)다. 이는 장기 학습 완료 모델이 아니다.
- [전체 CPU256개 통과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/cpu_verification_v1.json) · [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/review_v1.md)
- [이전버전/초안 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_actionable_preparation) · [문서 변경 전후 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/documentation_update_v1.json) · [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_actionable_preparation_20261018.md)

남은 작업은 새 시작 조건에서 조기 준비와 정밀 타이밍을 충분히 학습하는 것이다. 앞2초를 다시 무행동 대기로 되돌리지 않고 현재 상태를 정책이 다루도록 학습해야 한다. 여러 음 전환·필요 해제·추가 타현 억제·양손 결합은 이번에 새로 구현하거나 검증하지 않았다. 현재 비교 목표는 같은 곡의 첫 단음이며 원곡 전체29.31초 학습이 아니다.

최종 [보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/preservation_final_v1.md) · [현재 소스 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/source_final_v1.json) · [최종 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/final_verification_v1.json).
