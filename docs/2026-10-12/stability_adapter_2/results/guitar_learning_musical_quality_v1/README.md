# 음악적 품질 보완 구현과 실제 연결 검증

**구현과 학습 연결 검증을 완료했다. 새 음악적 성공 조건을 만족하는 정책이 완성된 것은 아니다.** 현재 첫 단음·손별 task의 판정·보상·성공·관측을 보완했고, 기존 물리·유지 제어·실패 한도·원자료는 보존했다.

- [구현 규칙·보상·입출력·실행법](/home/ajou/yigyu/3/guitar_learning/MUSICAL_QUALITY.md)
- [학습 진입점](/home/ajou/yigyu/3/guitar_learning/train_musical_quality.py) / [평가](/home/ajou/yigyu/3/guitar_learning/evaluate_musical_quality.py)
- [압현 분류](/home/ajou/yigyu/3/guitar_learning/fretting_quality.py), [새 측정기](/home/ajou/yigyu/3/guitar_learning/task_measurement_v2.py), [타현 준비·추가·회복](/home/ajou/yigyu/3/guitar_learning/strike_quality.py)
- [품질 보상·이력](/home/ajou/yigyu/3/guitar_learning/musical_quality.py), [환경 연결](/home/ajou/yigyu/3/guitar_learning/musical_quality_environment.py), [Actor 이전](/home/ajou/yigyu/3/guitar_learning/musical_quality_transfer.py)

## 구현한 차이

원 positive 접촉과 금지 압현이 없는 clean 접촉을 분리하고, correct/wrong/missing을 기록한다. 목표현의 높은 프렛은 금지하며, 지정 목표를 누른 상태의 낮은 프렛 동시 접촉은 허용한다. 다른 현·지지 부위·불명확한 경계를 일괄 오압현으로 세지 않는다. 실제 MusicLedger·타이밍·첫2초 준비 보상에 clean을 사용하므로 새 경로의50/100ms eligibility도 바뀌었다. 과거 결과를 덮어쓰지 않는다.

음 구간 미접촉·중단·해제 지연을 감점하고 실제 목표현 clear를 해제 보상과 완료 조건에 연결했다. 기존 note-end 뒤 유지 보상과 timing-only 성공 보너스는 상쇄하고 audible clean 달성 보너스로 대체했다. 타현은 준비 전 성공을 차단하고 추가/재무장 차단 통과를 중복 없이 감점하며 마지막 현재 회복 상태를 검사한다. 현 위로 들어 올려 돌아오는 XY 통과는 적격 타현과 구분한다.

품질 이력27개를 더해 상태563=536+27, 행동39·native0초/정책7초다. 선택 손 Actor/std만 명시적으로 이전하고 새 입력 열은0, critic/optimizer/카운터는 새로 시작한다. strict resume는 완화하지 않았다. 모든 항은 실제 반환 reward·episode 합계·PPO transition과 성공 지표까지 연결했다.

## 검사

[전체 CPU 최종 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/cpu_tests_final_v1.txt): **297개 PASS / 140.310초**. 기존256개와 새41개다. 동시 오류 veto·프렛 경계·움직이는 기타·준비/추가 통과·리프트·해제·보상 상쇄/합계·실패 tick·관측·reset·모델 이전/strict resume·새 worker의 logger를 검사했다. 기록 재생/합성 CPU 검사와 실제 동역학은 구분한다.

독립 검수의 동결본 focused6개도 통과했다. [검수 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/review_v1.md).

## 실제 native 실행

양손 각1환경·H420·PPO1업데이트를 실행하고 저장한563 모델을 strict load해 각1회 결정적 평가했다. 훈련840전이+평가840전이, 완료4실행은 각각7초이며 물리 실패는0이었다. 출처 자체536의 update1에서 Actor만 가져와 새 initial0→final1로 진행했다.

| 손 | 실제 학습 | 최종 결정적 평가 | 새 성공 | 남은 동작 | 평가 기타 최대 이동 | 평가 발 최대 이동 |
|---|---|---|---|---|---|---|
| 왼손 | 420전이·PPO1회 | 7초·420tick | 0/1 | 음 구간 clean100%, 해제 미완료 | 5.551053mm | 4.116630mm |
| 오른손 | 420전이·PPO1회 | 7초·420tick | 0/1 | 목표1회·추가1회·반대방향1회, 최종 회복 | 0.955531mm | 0.078086mm |

두 평가 모두 timing-only 달성은 True지만 새 quality gate는 False다. **이전에 놓친 동작을 실제로 검출하는 연결 검증이며, 성공률 개선·수렴의 증거는 아니다.** 왼손 해제와 오른손 불필요한 통과를 추가 학습해야 한다.

왼손 평가는7초 전체에서 correct964/missing716표본이었고 음 구간 clean 유지율은100%다. 오른손 평가의 왼손은 비활성이므로 왼손 missing1680표본이 기록되지만, 이를 오른손에 감점하지 않는다.

실제 훈련 보상 합에서 왼손 해제 지연−1.2739, post-note 유지 상쇄−1, timing 성공 상쇄−1/audible 성공+1을 확인했다. 오른손 추가 타현−0.1·잘못된 방향−0.1·회복+0.1도 PPO 로그에 들어갔다. 양손 첫120전이 모두 목표를 보고 nonzero action을 수행했다. KL guard의 복원·학습률 축소 뒤 최종 analytic KL은 LH0.0138914/RH0.0175723으로0.02 한도 안이었다. 큰 시도 KL을 허용하도록 한도를 늘리지 않았다.

[실제 native 요약·보상 합·지표·원자료 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/native_summary_v1.json).

- 왼손: [훈련](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2) / [평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_eval_v1).
- 오른손: [훈련](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1) / [평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_eval_v1).

## 저장 궤적 비교와 실패 보존

[직전 궤적 비교 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/trace_comparison_v2.md)는 이번 native 실험과 별개다. 기존 LH의 음 구간 접촉100% 뒤 해제0/612표본, RH의 목표1회+추가1회+반대 방향1회를 보였다. 같은 행동 기록의 반사실 측정이며 새 정책 성능으로 설명하지 않는다.

기존 원형14개는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_musical_quality/manifest.json), 새 소스148개의 정확 사본은 source_v1/source_before_native_v1.json에 있다. 첫 left_native_train_v1은 설치된 ninja의 PATH가 빠져 Gymtorch import에서0전이·장면 생성 전에 실패했다. 그 자료를 남기고 PATH만 맞춰 새 폴더 v2에서 재시도했다. 실행 예제의 두 PATH줄 교정만 별도 원형 보관과 source_before_native_v2.json으로 기록했으며 생산 코드는 바꾸지 않았다.

초기 검사 실패 로그도 보존했다. post-note 보상 검사는 default stage0과 기대 stage1의 fixture 불일치를 수정했다. Actor 출력은 추가0열에 따른 float32 연산 차이를 고려한 허용오차와 별개로 원536열 정확 동일·새 열 정확0을 검사한다. 물리/성공 허용치를 바꾸지 않았다. 분석기 v1의 표본 길이 guard는 v2로 수정하고 v1 원본·결과·보관본과 수치 동일성을 남겼다.

[보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/preservation_v1.md): 기존 학습 Python115개·외부 native63개 불변, 새 실행 입력1667개 SHA 일치, 완료 실행 create/close4/4·금지 호출0. 실패를 삭제하거나 통과로 재분류하지 않았다.

물리 피크 파지·실제 현 압력/진동·음향, 전곡 화음/바레/뮤팅, 양손 결합·일반화·Root 자유 균형은 별도 범위다. 이번에는 현재 단음 학습의 판정·보상 누락을 보완했다.
