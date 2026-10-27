# 단음 해제·타현 후 동작의 국소 학습 결과

기존 단음 정책에서 실패하던 **LH 음 종료 후 해제와 RH 추가 타현 억제**를 같은 환경 안에서 수행할 수 있는 교사 행동을 확인하고, 그 행동을 원 정책에 BC로 적합했다. 양손 각각 교사 후보2개가 원 품질·안전 조건을 통과했다. 이후 **보조 제어 없는 학습 정책도 양손 각각4/4회 stage1 품질·안전을 통과했고, 실제 PPO 초기화 증거 검사까지 통과했다. 새 PPO는 아직 실행하지 않았다.** 교사 성공·BC 행동 오차 감소·정책 실행 성공은 별도 증거로 기록한다.

구현·계약·전체 실행법은 [local_skills 코드 안내](/home/ajou/yigyu/3/guitar_learning/local_skills/README.md), 배경은 [단음 정량 진단](../guitar_learning_single_note_diagnosis_v1/README.md), 작업 범위는 [계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_local_skills_20261019.md)에 있다.

2026-10-19 02:50 KST 최종 집계: [기계 판독용 실제 검증 요약](validation_summary_v1.json), [전체 입력 보존 대조](preserved_inputs_check_v2.json). 교사 비교8회와 정책 단독8회, 총16개의 전체7초 실행을 완료했다. 중단한 초기 probe247tick은 이 분모에 포함하지 않는다.

## 유지한 조건과 구현

원105입력 축 중97개 비영범위·8개 영범위를 유지하며, 학습 관측563·정규화 행동39·medium망을 사용한다. Root 고정·원 하체 유한 제어·자유 기타·중력ON·스트랩OFF다. native 정착0초+정책7초,60Hz 행동420개/240Hz 물리1680표본이며 처음2초도 정책 행동과 안전 판정을 수행한다. 가슴 접촉 지속은 필수가 아니며 기타 이탈·회전·접지 등 기존 안전 기준을 유지한다.

- [controls.py](/home/ajou/yigyu/3/guitar_learning/local_skills/controls.py)와 [probe.py](/home/ajou/yigyu/3/guitar_learning/local_skills/probe.py): 원 정책으로 시작하고 LH는 음 종료 뒤, RH는 첫 인정 타현 뒤에만 후보 행동으로 바꾼다. 기존39행동·관절 범위·평활화·속도 제한을 통과하며 기타 직접 보조 힘·부착·실행 중 상태 덮어쓰기를 사용하지 않는다. 후보는 한 번에 native환경 하나로 순차 실행한다.
- [learning.py](/home/ajou/yigyu/3/guitar_learning/local_skills/learning.py): 정상 종료한 부모 탐색과 전체7초 품질·안전 성공 case만 받는다. 행동 직전 관측/실제 발행 행동/원 정책 행동/개입 마스크420행과 원 checkpoint·전체 계약·자료SHA를 검증한다. 선택 손의 Actor encoder/head만 학습하며 critic·std·반대손·buffer·전역RNG는 보존한다. 손실은 국소 교사 행동MSE와 비개입 구간 원 정책 행동MSE를 동등 가중한다.
- [evaluate.py](/home/ajou/yigyu/3/guitar_learning/local_skills/evaluate.py)와 [train.py](/home/ajou/yigyu/3/guitar_learning/local_skills/train.py): 보조 제어 없이 실제 정책4회 모두 원 품질·안전에 성공한 경우에만 새 PPO 초기화를 허용한다. gate와 실제 결과·지표·소비 입력SHA, BC/원 checkpoint/자료/역할/계약을 대조한다. 새 PPO에는 선택 Actor/std만 이전하고 critic·optimizer·counter·RNG는 새로 시작한다. 기존 PPO strict resume 계약은 완화하지 않는다.

여기서 품질은 기존 stage1±0.5초 안의 손별 조건이다. LH는 clean audible 유지와 최종 해제, RH는 준비된 타현·추가/잘못된 타현 없음·최종 회복을 함께 요구한다. 실제 현 압력·진동·음향 또는 양손 합주 성공 인증은 아니다.

## 완료한 native 교사 탐색

원 모델은 손별 장기 실행의 고정 [LH checkpoint_000024.pt](../guitar_learning_resource_long_v1/long_left_v1/checkpoint_000024.pt)와 [RH checkpoint_000024.pt](../guitar_learning_resource_long_v1/long_right_v1/checkpoint_000024.pt)다. 파일번호24와 checkpoint 내부의 누적 PPO update는 다르며 실제 누적값은 LH29·RH27이다. 정확한 전체 가중치를 불러 결정적으로 실행했으며 optimizer/RNG를 재개한 실험은 아니다. 표의 각 행은 별도7초 episode 한 번이다.

| 손·case | 원 품질 | 물리 실패 | 관측한 결과 | 교사 개입tick |
| --- | --- | --- | --- | --- |
| LH policy | 실패 | 0 | clean audible1.0, 최종 해제 실패 | 0 |
| LH zero | 실패 | 0 | clean audible0, 목표 수행 없음 | 0 |
| LH left_return_reference | 성공 | 0 | clean audible1.0, 해제 완료, late0.187383초 | 158 |
| LH left_return_reference_open_flex | 성공 | 0 | clean audible1.0, 해제 완료, late0.254050초 | 158 |
| RH policy | 실패 | 0 | accepted1, extra1, wrong1, recovered=true | 0 |
| RH zero | 실패 | 0 | accepted0, recovered=false | 0 |
| RH right_hold_last_command | 성공 | 0 | accepted1, extra0, wrong0, recovered=true | 168 |
| RH right_hold_applied_target | 성공 | 0 | accepted1, extra0, wrong0, recovered=true | 168 |

원자료: [LH finalized result](left_native_probe_v2/result.json), [RH finalized result](right_native_probe_v1/result.json). 8개 모두420tick 완주, 물리 flags 정상, 입력SHA 불변, 금지 호출0, cleanup_error=null이다. RH교사 최초 인정 타현 오차는 약+64.596ms로 이 단계 허용창 안이다. RH평가의 비활성 LH clean값을 RH성공률에 섞지 않는다.

이 결과는 기존 제어 범위 안에 성공 행동 경로가 있음을 보여준다. 같은 시작의 소수 후보 결과이며 독립된 다양한 초기 상태에서의 성공률 추정은 아니다. episode 경계의 native 상태 복원은 숨은 PhysX solver/contact cache까지 동일하게 복원했다는 인증이 아니다.

## 완료한 BC와 정책 평가 상태

선택 자료는 [LH return_reference](left_native_probe_v2/left_return_reference/result.json), [RH hold_last_command](right_native_probe_v1/right_hold_last_command/result.json)다. 각각 전체420행 중 국소/비개입 구간을 나누고 CUDA에서1000step, 학습률0.0001, 그룹별batch120으로 적합했다. 새 BC형식은 `guitar_learning.local_skill_bc.v1`이며 PPO update는0이다.

| 손 | 국소/보존행 | 국소MSE 초기→최종 | 최종 국소 최대절대오차 | 최종 보존MSE / 최대절대오차 |
| --- | --- | --- | --- | --- |
| LH | 158 / 262 | 0.1566873 → 0.00002555494 | 0.09598488 | 0.00005853462 / 0.07156301 |
| RH | 168 / 252 | 0.001995756 → 0.0000001105551 | 0.001712650 | 0.00000003379549 / 0.003102005 |

근거: [LH BC report](left_bc_v1/report.json), [RH BC report](right_bc_v1/report.json), [LH 관절별 적합 진단](left_bc_v1/action_fit_diagnostics.json). 수치는 기록된 교사 관측에서의 정규화 행동 오차다. 비개입 구간 오차는0이 아니며 실제 정책 궤적의 앞부분을 완전히 보존했다는 뜻도 아니다.

| 검증 단계 | LH | RH |
| --- | --- | --- |
| 원 조건의 교사 실행 | 후보2/2 성공 | 후보2/2 성공 |
| 선택 교사 BC 적합 | 완료, source_unchanged=true | 완료, source_unchanged=true |
| 교사 없는 결정적 정책4회 | [4/4 품질 성공·물리 실패0](left_policy_evaluation_v1/musical_quality_result.json) | [4/4 품질 성공·물리 실패0](right_policy_evaluation_v1/musical_quality_result.json) |
| 정상 종료 후 gate / 실제 train.validate_gate | [모두 통과](left_gate_validation_v1.json) | [모두 통과](right_gate_validation_v1.json) |
| gate 통과 후 새 PPO | 미실행 | 미실행 |

양손 각각420tick/7초를4회 완료했고 입력SHA 불변·정상 종료 후 gate가 생성됐다. 평가 자체와 PPO의 증거 검사 모두 실제 실행했다. LH는4회 모두 clean audible1.0·압현 해제 완료, grace 이후 release_late_s=0.179050초였다. RH는4회 모두 accepted1·extra0·wrong0·blocked0·최종 recovered=true였다. 각 모델은 한 음의 한 교사 궤적으로 학습했으며 다양한 곡/초기 상태의 성공률을 뜻하지 않는다.

**정밀 타이밍은 별도로 남아 있다.** RH 첫 인정 기하 타현 오차는 +50.178669ms가1회, +108.706248ms가3회였다. 따라서 타현 시각 오차만 보아도50ms 이내0/4·100ms 이내1/4다. 이 수치는 양손 합주 MusicLedger 성공률이 아니며, 실제 원 MusicLedger의 matched50/matched100은 이번 손별 시험에서 모두0이다. 현재4/4 성공은 선언한 stage1±0.5초와 추가 타현 억제/분리 조건의 성공이다. LH 해제 지연도0으로 줄인 결과가 아니다.

RH 표와 위 정책 설명의 `wrong0`은 손별 품질의 `wrong_native_eligible=0`을 뜻한다. 원 MusicLedger의 `wrong_crossings`는 RH 정책 네 시험에서 각각1이며 별도의 합주 판정이다. 두 지표를 같은 오타현 수로 합치거나 둘 다0이라고 설명하지 않는다.

## 재현과 다음 연결

환경 준비와 probe 전체 명령은 [코드 안내](/home/ajou/yigyu/3/guitar_learning/local_skills/README.md#실행-순서)를 따른다. 아래는 프로젝트 루트·rl38환경에서 사용할 예이며 출력은 새 디렉터리여야 한다. `CAPTURE`, `BC_OUT`, `EVAL_SETTINGS`, `EVAL_OUT`, `PPO_SETTINGS`, `PPO_OUT`은 해당 절대경로로 지정한다.

```bash
python -m guitar_learning.local_skills.learning \
  --capture "$CAPTURE" --out "$BC_OUT" --steps 1000 \
  --learning-rate 0.0001 --batch-size 120 --device cuda:0

python -m guitar_learning.local_skills.evaluate \
  --settings "$EVAL_SETTINGS" --initialization "$BC_OUT/actor_initialization.pt" \
  --out "$EVAL_OUT" --episodes 4

python -m guitar_learning.local_skills.train \
  --settings "$PPO_SETTINGS" --out "$PPO_OUT"
```

실제 평가 설정은 [LH](left_bc_evaluation_settings_v1.json)·[RH](right_bc_evaluation_settings_v1.json)에 보존한다. `actor_initialization_kind=bc`, 정확한BC경로, `local_skills.schema=guitar_learning.local_skills.v1`을 사용한다. **평가에 사용한 설정파일은 그대로 두고**, 별도 [LH PPO 준비 설정](left_bc_ppo_ready_settings_v1.json)·[RH PPO 준비 설정](right_bc_ppo_ready_settings_v1.json)에 실제 통과한 `local_skills.evaluation_gate` 절대경로를 추가했다. 둘 다 실제 parser와 train.validate_gate를 통과했다. 평가 설정을 나중에 덮어쓰면 소비 입력SHA 검사가 실패한다. 역할·망 크기·원563 계약도 유지해야 한다.

probe/정책평가는 시작 전 여유메모리8GiB·진행 중6GiB, case600초 보호를 적용하며 정책평가 전체 한도는3000초다. 추가 native실험은 단일 환경으로 순차 실행했다. 기존32개 장기 학습은 수정하거나 중단하지 않았고, 2026-10-19 02:48 KST에 시간 예산을 마쳐 양손 모두 정상 종료했다. 새 PPO smoke/장기 학습은 실행하지 않았다. 기존 진급 watcher의 평가 대상은 원 장기 실행이며 새 BC로 바꾸지 않았다.

완료된 원 장기 실행은 손별384episode에서 LH timing-only378/384·품질0/384, RH timing-only381/384·품질0/384였다([LH](../guitar_learning_resource_long_v1/long_left_v1/musical_quality_report.json), [RH](../guitar_learning_resource_long_v1/long_right_v1/musical_quality_report.json)). 이번 BC의 결정적4회와 이 확률적 학습 episode를 같은 모집단의 성공률처럼 비교하지 않는다. 다음 단계는 새 Actor에서 PPO를 시작해 확률적 실행의 품질 유지와 타현 정밀도를 검증한 뒤 목표 음을 늘리는 것이다.

## 검사·보존·남은 범위

신규 CPU검사19개28.903초 PASS: [all_cpu_v1.log](all_cpu_v1.log). [독립 코드 검수](review_v1.md)는 구현 연결과 예외/cleanup 경로를 검수한 기록이며 이후 native 결과 전체의 인증서가 아니다.

완료 증거도 별도로 검수했다: [교사·BC·LH 정책 증거 검수](evidence_review_v1.md), [RH 최종 정책·gate·정밀 타이밍·문서 검수](evidence_review_v2.md). 두 손 모두 검수자가 parser와 실제 train.validate_gate를 독립 실행해 통과를 확인했다.

첫 [left_native_probe_v1](left_native_probe_v1/result.json)은 기록 압축 비용이 큰 상태에서139.553초/247tick에 명시적 KeyboardInterrupt로 중단했다. 성공0·cleanup 정상·source 불변으로 보존했으며 완주8개 분모에 넣지 않는다. 변경 전 probe/검사는 [archive](/home/ajou/yigyu/3/guitar_learning/archive/20261019_before_fast_local_probe)에 보관하고, 압축 수준·시간 한도 및 최종 결과 기록 수정을 [source_v1](source_v1)·[source_v2](source_v2)·[source_v3](source_v3)/[probe_inputs_v3.json](probe_inputs_v3.json)으로 구분한다. 음악·물리 성공 문턱은 낮추지 않았다.

[최종 보존 검사](preserved_inputs_check_v2.json)에서 기존 학습 소스169개·장기 실행 입력6개·curriculum 봉인15개·신규 봉인11개·양손 native probe 소비입력 각1566개·정책 평가 소비입력 각1658개를 재계산했고 모두 변경0이었다. BC/평가 전 신규 코드·검사·안내11개는 [learning_source_pins_v1.json](learning_source_pins_v1.json)과 [정확한 보관본](learning_source_v1)에 봉인했다. 각 실행의 입력SHA와 정상 종료 확인은 해당 결과에 남긴다.

아직 전곡·다른 음/초기 자세 일반화·양손 결합·정책의 장기 수렴·strict restart 실제 native시험·root 자유 균형 성공은 검증하지 않았다. 이번 단계에서 확인한 것은 기존 범위 안의 성공 교사 경로와 같은 단음에서의 학습 정책4/4 재현, 새 PPO 초기화 증거 검사까지다. 새 PPO의 수렴이나 엄격한 음악 타이밍 성공으로 확대하지 않는다. 진행 중 상태였던 README 초안은 [archive](archive/README_before_policy_results_v1.md)에 보존했다.
