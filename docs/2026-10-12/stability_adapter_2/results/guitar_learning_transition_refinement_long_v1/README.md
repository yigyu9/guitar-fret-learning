# 단음 A 보완 정책 장기 학습 결과 — 2026-10-19

현재 예산에서는 음악적 성공률의 뚜렷한 향상을 확인하지 못했다. 원본 소스를 격리한 재개 실행 C는 정상 종료했고, 탐색 중 왼손 성공은 **56/112회(50%)**였다. 최종 누적46회 모델의 결정론적 재평가는 **3/4회**, 앞선32회 모델은 **4/4회** 성공했다. 따라서32회 모델을 별도 재생을 통과한 참조 모델로 유지한다. 4회 반복만으로 통계적 우열이나 범용 견고함을 확정하지 않는다.

## 평가 대상과 성공 기준

- 단음 A: 2번 줄·7프렛·약지. 정책 시작부터 목표를 제공하고 준비에 사용한다. 정책 실행4초, 발음 목표2.0~2.5초다.
- 발음0.5초 중 실제240Hz clean 접촉 유지90% 이상, 2.8~3.3초 해제 구간의 할당 손가락 qualified 목표 접촉 부재90% 이상, 물리 안전 통과를 요구한다. 기존40% 진행 지표를 성공으로 집계하지 않았다.
- 해제는 손 전체의 넥 이탈이나 실제 현 압력이 아니다. 타현·진동·음향 성공도 평가하지 않았다.
- 관측500·왼손 행동33·전체 행동39를 유지한다. 오른손 정책 행동은0이다. 기존 전신 유한 유지 제어 위의 왼손 학습이며 양손·두 음 전환·전곡 학습 결과가 아니다.
- Root만 고정, 하체 유한 제어,105입력/97비영범위/8영범위, 자유 기타·중력ON·스트랩OFF를 유지했다. 기타 직접 보조 힘·부착·지속 상태 덮어쓰기를 추가하지 않았다. 가슴 접촉 지속 자체는 성공 조건이 아니다.

## 실제 학습량과 실행 구분

| 구분 | 실제 수행 | 판정 |
|---|---|---|
| A: `long_training_v1` | 8회 갱신·15,360반영 전이 | 정책 학습률이256배 감소해 의도적으로 중단. 음악 성공31/64. 완료 실행으로 보고하지 않음 |
| B: `long_training_v2` | 36회 갱신·69,120반영 전이 | 실행 중 외부 공유코드 변경31개를 감지해 중단. 전체 소스 무결성 부적격 |
| C: `isolated_resume_training_v1` | B의32회 모델에서 추가14회·26,880반영 전이·새112에피소드 | **정상 종료·전체 감사 통과**. 누적 모델 번호46 |

B와C는8환경·환경당240tick·medium 모델·epoch1·minibatch2048(실제 batch1920)·Actor LR1e-7·value LR0.0003·std LR0.001·BC 가중100을 사용했다. A의epoch2/minibatch256/std LR1e-5에서 세 항목을 묶어 바꾼 실험이며 개별 변경의 인과 효과를 분리하지 않았다. Critic 갱신도 회당16회에서1회로 줄었다. C는 B와 같은 학습 계약이며 시간 한도만 변경했다.

C의1,200초 한도는 업데이트 사이에 검사한다. 마지막 수집을 마친 실제 실행은1,247.16초였다. sampled/logged/durable/committed는 모두26,880, discarded와 unresolved는0이다. 128회는 설정 상한이며 실제로 수행한 추가 갱신은14회다.

선택 모델의 계보는 **B32+C14=46회·88,320전이**다. B의33~36회와 중단 후 부분 수집은 이 계보에 합산하지 않는다. B첫32회와C의 collection 벽시계 합은58.3228분이다. 이는 한 번의 연속 정상 실행이나 시뮬레이션 시간, 전체 계보의 무결성 인증을 뜻하지 않는다. C에서 검증된 추가 실행량은26,880전이로 별도 구분한다.

## 정상 종료한 C의 결과

| 항목 | 결과 |
|---|---:|
| 완료 에피소드 | 112 |
| 왼손 성공 | 56/112 (50.0%) |
| 평균 clean 유지율 | 55.6845% |
| 유지율0 / 0초과90%미만 / 90%이상 | 46 / 10 / 56 |
| 해제 통과 | 112/112 |
| 물리 실패 / 무효 에피소드 | 0 / 0 |
| 앞7회 갱신의 성공 | 29/56 (51.8%) |
| 뒤7회 갱신의 성공 | 27/56 (48.2%) |
| 앞7회 / 뒤7회 평균 유지율 | 56.95% / 54.42% |

앞뒤7회는 겹치지 않는다. 동일 조건의 시간상관이 있는 소표본 기술통계이므로 개선·악화를 확정하는 검정으로 사용하지 않는다. 기존 helper의 first8/last8은 두 업데이트가 겹치므로 주 비교로 쓰지 않았다. C의 local index0..13은 누적 optimizer33..46에 대응한다.

![C 추가 학습의 누적 모델 번호별 추세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_analysis_final_v1/global_learning_curves_v2.png)

## 실패는 어디에서 발생했는가

실패56회 모두 음 시작 직전200ms의 준비 접촉 누적 시간이0이었다. 41회는 clean 접촉을 전혀 관찰하지 못했고,10회는 발음 구간에 늦게 처음 접촉했으며,5회는 음이 끝난 뒤 처음 접촉했다. 오압현만 발생한 실패13회, 미압현만 발생한 실패43회였다.

`prepare_ready_s`는 준비 완료 시각이 아니라, 마지막200ms에서 두 끝점 모두 접촉 조건을 만족한 구간의 누적 기간이다. 준비 접촉 부재가 모든 실패에서 관찰됐지만 이것만으로 실패 원인을 확정하지 않는다. 유지율이 부분적으로 남은 실패10회 중3회에서는 첫 clean 이후에도 추가 미확인 구간이 있었다. 접촉 획득뿐 아니라 이후 유지·회복도 점검해야 한다. 이 기록만으로 조기 해제와 재접촉 상실의 원인을 완전히 구분할 수는 없다.

물리240Hz의 총107,520표본에서 기타 최대 변위는3.610mm, 최대 회전은0.5393도였다. 전체 주요 지지 접촉의 동시 소실과 양발 접촉 소실은 없었다. 오른상완 접촉은 한 에피소드에서4.167ms 이탈했고, 가슴 접촉 부재는 전체 시간의 약74.5%였다. 가슴·삼중 접촉률은 진단이며 현재 실패 조건으로 사용하지 않았다. 이 결과는 고정 Root·기존 유지 제어·이 단음의 국소 탐색 범위에 한정된다.

## 정책 갱신과 시간 사용

C에서 Actor LR1e-7·std LR0.001은 유지됐고 KL 재시도는0이었다. KL은약3.59e-5~3.00e-4로0.005 상한 아래였다. 반복적인 학습률 감소로 정책이 멈춘 A의 현상은 재발하지 않았다.

탐색 std 평균은0.003000585→0.003002197로 거의 그대로였다. 성공 시연의 행동 MSE는2.319e-8→3.608e-8이었다. 이는 시연 관측에서의 오차이며 전체 상태공간의 정책 변화나 관절각 변위가 아니다. 작은 BC 오차가 접촉 성공 보존을 보장하지도 않는다. BC와PPO의 개별 gradient는 기록하지 않아 BC 가중100이 학습을 지배한다고 확정할 수 없다.

가중 cost advantage의 표준편차는 reward advantage의 약1.2~6.8%였다. 현재 전역 통계에서 안정성 비용이 학습 신호를 압도했다는 근거는 없다. 특정 상태의 gradient나 하드 종료 영향을 배제한다는 뜻은 아니다.

C의 collection은1,234.98초, PPO update 합은1.088초였다. 시간은 대부분 시뮬레이션·전이 수집 경로에 사용됐다. 이 계측만으로 물리 계산·프로세스 통신·직렬화·로그의 개별 비중을 구분하지 못한다. 약1시간의 collection에도 모델 계보는46회 갱신에 해당하므로, 충분히 수렴한 실험이라는 주장은 하지 않는다.

## 저장 모델의 별도 native 재평가

| 모델 | 성공 | 각 반복의 유지율 | 해제·물리 안전 |
|---|---:|---|---|
| B checkpoint32 | 4/4 | 100%,100%,100%,100% | 모두 통과 |
| C final46 | 3/4 | 100%,0%,100%,100% | 모두 통과 |

각 평가는 새 프로세스 안의 같은 persistent 환경에서 네 번 reset한 결정론적 실행이다. 최종46의 두 번째 반복은 런타임 오류가 아니라 실제 압현 실패다. 평가 전체는 끝까지 정상 완료했고 소스·물리 플래그·런타임 감사도 통과했다. 교사 개입은 없었다.

4회는 독립 seed 검증이 아니며 일반화 성공률 추정치로 사용하지 않는다. 현재 코드는 checkpoint를 로드할 때 저장RNG를 복원하고 매 case 다시 로드한다. 설정 seed만 바꾼 stochastic 평가를 공통 난수·독립 반복으로 해석할 수 없어 그 실험은 시작하지 않았다. 향후에는 strict load 후 case별 평가 seed를 명시하고 새 프로세스에서 대조할 필요가 있다.

참조 모델은 [checkpoint32](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/long_training_v2/checkpoint_000031.pt)로 유지한다. [최종46 모델](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_training_v1/final.pt)도 보존했다. 최종 모델이 더 우수하다는 근거는 없고, 두 모델의 통계적 우열을 확정한 것도 아니다.

## 외부 파일 변경과 재현 조건

중간 평가가 기존 BC 증거의 입력 SHA 불일치를 정상적으로 거절했다. UTC11:26:14부터 다른 작업의 공유 의존성 정리로 파일이 바뀌었으며, 호스트 B의 최종 변경 목록은31개였다. 현재 작업 폴더의 변경은 되돌리지 않았다. 중단 실행·실패 로그·부분 전이는 보존했다.

변경 전 보관본334파일로 전체 `guitar_learning` 패키지를 구성하고, B 시작 입력1,907개를 모두 원 SHA로 확인해 별도 사본을 만들었다. namespace에서 원래 절대경로에 패키지 전체와 외부 입력1,615개를 읽기 전용으로 제공했다. 실제 namespace에서1,907/1,907 SHA 일치를 확인한 뒤 C와 후속 평가를 수행했다. 기존 BC 검증·성공4회 원자료 감사·물리·관측·보상·엄격한 checkpoint 검증을 완화하지 않았다.

C는 원 optimizer/RNG를 이어받지만 새 native 에피소드에서 시작한다. checkpoint32 저장 시각이 외부 변경보다 앞선 것은 보조 정황이며 B 과거 전체 무결성의 증명은 아니다. C 및 격리 재평가의 성공이 B의 무결성 실패를 소급 복구하지 않는다. 현행 호스트 코드에서 그대로 재개하는 대신 아래 기록의 동일 격리 view를 사용해야 이번 계약을 재현할 수 있다.

C의 core/persistent/teacher-auxiliary/부모와8worker runtime 감사는 모두 통과했다. 별도 검수자가 보고서·worker SHA와 계수 구분을 확인했다. 격리 view의 코드와 원자료는 수정하지 않는다.

## 다음 작업의 우선순위

1. 단음의 **목표 접촉 획득·유지·상실 후 회복**을 별도 작은 과제로 검증한다. 실제 접촉 준비 보상을 더 이른 준비 구간에 제공하는 변경은 대조 실험으로 평가한다. 자세·자유 기타·안전 조건은 유지한다.
2. 명목 동작 한 경로의 BC 자료에서 벗어나 작은 상태 교란에서 목표 접촉으로 회복한 성공 자료를 확보한다. 단순히 탐색을 줄여 성공률만 올리는 것을 견고함 향상으로 해석하지 않는다.
3. 고정된 독립 평가 절차와 성능 기준의 checkpoint 선택을 먼저 마련한다. 마지막 저장 모델을 자동 선택하지 않는다. 수집 성능 개선은 세부 프로파일링 뒤 별도 작업으로 진행한다.

이번에는 추가 보상·정책 구조·자세 변경이나 두 음·전곡 학습을 실행하지 않았다.

## 주요 기록

- [C 최종 분석·원자료 SHA·번호 대응](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_analysis_final_v1/summary.json)
- [접촉 실패 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_analysis_final_v1/contact_diagnostics.json)
- [C 종료 검증 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_validation_v1.json)
- [두 checkpoint의 재평가 비교·SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/checkpoint_comparison_v1.json)
- [C 실제 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_settings_v1.json)
- [C 전체 종료 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_training_v1/report.json)
- [격리 입력 사본 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/frozen_execution_view_v1/manifest.json)
- [격리 실행 명령·환경·PID](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_training_v1_launch.json)
- [최종 재평가 실행 명령](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/isolated_resume_final_eval_v1_launch.json)
- [외부 변경 감지·중단 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/external_source_change_stop_v1.json)

실행 차단 보완으로 JSON 표기와SHA를 보존하는 runtime_v2를 사용했다. 동결본68개 CPU 검사와 실제 초기4회·연결 학습·저장 후 재로드 검증을 통과했다. FP 제어 상태를 변경하지 않았으며 관찰된 이상은 없었다. 기존 SIGFPE의 근본 원인을 해결했다는 뜻은 아니다. 실패한 초기 어댑터와 기존 원자료도 보존했다.
