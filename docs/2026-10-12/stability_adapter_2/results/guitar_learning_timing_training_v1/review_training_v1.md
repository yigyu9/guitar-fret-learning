# 타이밍 학습 독립 검수

**최종 요약 판정: 문제없음.** 비교 설계·설정·동결 측정 경로, stage0·stage1 학습·최종 실제 평가·단계 이전 근거와 최종 종합 문서의 주장을 검수했다. 미해결 Critical·Warning·Suggestion은 없다.

## Critical / Warning / Suggestion

현재 확인된 미해결 항목 없음. 검수자는 학습 소스·설정·기존 결과를 수정하지 않았다.

## 설계와 실행 조건 확인

- `docs/plans/guitar_learning_timing_training_20261018.md`와 양손 `*_stage0_settings_v1.json`이 일치한다. 역할 외의 N2/H300/24업데이트·stage0·pre-roll1초·medium·std.02·초기actor_lr1e−5·cost1·seed7 조건은 같다. 최대 전이는 역할별2×300×24=14,400이며 실제 완료 예산은 최종 report로 확인해야 한다.
- 초기화는 검증된 같은 역할536차원 BC Actor다. 동결 `train_timing_v2`가 Actor만 새 학습에 전달하므로 기존 PPO optimizer/counter를 새 학습으로 재사용하지 않는다.
- 초기 BC·12번째 업데이트·최종 모델을 같은 준비 시작에서 비교하고, 탐색 episode와 결정적 평가를 구분한다. stage0 성공률의 포화만으로 개선을 주장하지 않고 LH의 원음 구간 유지·연속성·해제, RH의 첫 목표 통과와 최소 오차·추가 통과, 물리 안전 및 KL/실효lr를 함께 비교하는 설계가 적절하다.
- 원래 joint music 판정과 독립 손별 접촉/기하 판정을 분리한다. 동일 단음·동일 시작의 반복2회는 일반화나 양손 동시 연주·음향의 증거가 아니다.
- stage1은 새 계약의 Actor-only 이전 후 별도 실제 평가를 통과해야 학습한다. 원래 안전·물성·행동 범위를 바꾸지 않으며 이전 실패/재초기화와 직접 이전 성공을 분리해 기록한다.

## 중간 평가 실행 시 확인할 사항

`guitar_learning/train_parallel.py:185`는 checkpoint 파일명을0부터 센다. **12번째 업데이트 모델은 `checkpoint_000011.pt`**이며 metadata의 `update_in_run=12`와 payload의 업데이트 수로 확인해야 한다.

`guitar_learning/evaluate_timing.py:26`의 CLI는 `--run` 아래 `final.pt`를 평가하며 별도 `--checkpoint` 옵션은 없다. 중간 모델 평가는 새 평가용 디렉터리의 `final.pt`에 해당 checkpoint를 byte-copy 또는 symlink하고 동일 설정을 사용하거나, 기존 평가 함수를 명시 경로로 호출한다. 원 checkpoint는 수정하지 않고 평가에 사용한 경로와 SHA를 기록해야 한다.

RH 승격 조건의 “최초 목표방향 오차≤.5초”는 **절댓값 `abs(error_s) <= .5`**로 확인해야 한다. 최소 오차로 최초 오차를 대체하지 않는다. LH는 각각의 실제 평가가 coverage≥.95와 현재 단계 안전 성공을 함께 충족하는지 확인한다.

## 2차 검수 — 완료된 stage0 원자료

`analyze_stage0_v4.py`와 중간 보고서를 읽고, 별도 스크립트로 실제 update 파일·training gzip·평가 native gzip·모델 payload를 재집계했다. 분석기는 수정하지 않았다.

- 양손 각각24업데이트·14,400전이·48개 episode다. 학습 성공은 LH46/48, RH48/48이며 두 손 모두 물리 실패0, 모든 종료가 timeline_complete다. 최종 report는 completed=True, failure=None, changed_inputs와 cleanup_errors가 빈 배열이다.
- 12번째 모델은 실제 payload 업데이트12와 alias provenance의 원/복사 SHA가 일치한다. 당시 분석의 학습로그15업데이트/9,000전이와 평가모델12업데이트를 분리한 표기는 정확하다.
- 첫 RH 오차는 목표 현·방향에 맞는 원 native crossing의 첫 항으로 재계산했다. 중간 두 회 모두19.223452428ms이며 best 오차와도 같다. 첫 통과와 최소 오차를 바꾸어 보고하지 않았다.
- 중간 평가는 각300tick/1,200개240Hz 표본이고, score_time=u−1 및 매tick native/측정 physics_step 정렬이 일치한다. LH 기타 최대 편차5.658775/5.882418mm, RH.226148mm와 실제240Hz 비용 적분을 재확인했다. 학습 로그의60Hz endpoint 최대와 평가의240Hz 최대를 구분한 라벨은 정확하다.
- LH 학습의 episode당 평균 hold 보상은5.119638889, audible 성분은.44505, audible 밖은4.674588889다. 이번 실제 로그에는 안전 실패tick이 없어 `전체 hold−held_second×audible_valid_s` 집계가 유효하다. 성공46회는 audible coverage1.0, 나머지2회는0이다. 보상 증가를 원음 구간 수행 개선으로 해석하면 안 된다.

| 최종24업데이트 모델 실제 평가 | LH | RH |
| --- | --- | --- |
| 안전5초·현재 단계 성공 | 2/2 | 2/2 |
| 원음 구간 접촉후보 coverage | 두 회1.0 | 해당 없음 |
| 첫 목표방향 / 최소 시간오차 | 해당 없음 | 두 회17.680343991ms / 동일 |
| 기타 최대 이동 | 5.500400 / 5.747094mm | 두 회.222710mm |
| 원 joint music50/100ms | 두 회0/0 | 두 회0/0 |

최종 평가는 각300tick/1,200physics 표본이며 source_unchanged=True다. 평가에 실제 사용한 `final.pt`의 payload와 metadata 모두24업데이트임을 확인했다. `analyze_stage0_v4.py`의 final_ready 자체에는 평가모델 업데이트수와 학습 완료수의 동등성 검사가 없으므로, 이번에는 이 조건을 별도 확인했다.

원 BC의 RH19.449144336ms 대비 최종 첫 오차는 약1.7688ms 작지만, 같은 시작2회 반복에서 관찰한 기술적 변화다. 일반화·통계적 개선·모든 지표의 일률 개선으로 확대하지 않는다. LH coverage는 초기부터1.0이어서 최종1.0만으로 개선을 주장할 수 없다.

계획한 stage1 진입의 사전 조건인 최종 현재 단계2/2 안전 성공, LH 각coverage≥.95, RH 각abs(first_error)≤.5초는 실제 stage0 결과로 충족한다.

## 3차 검수 — stage1 이전과 학습 진입

`stage1_training_decision_v1.json`의 양손 사전평가 경로·SHA를 실제 파일과 대조했다. 두 손 모두 새 stage1 계약에서 안전5초·단계 성공2/2, source_unchanged=True다. 원 native 표본을 별도 재집계해 각300tick/1,200physics와 안전 실패 없음, LH 두 회coverage1.0, RH 첫 목표방향 오차 두 회15.712060742ms를 확인했다.

`left/right_stage1_settings_v1.json`은 계획한 N2/H300/12업데이트·soft1500초·stage1±.5초이고, 초기화 경로는 같은 역할 stage0 최종24업데이트 모델이다. `timing_initialization.json`의 source SHA는 앞서 확인한 stage0 final SHA와 같다. strict_resume은None이며 재BC 초기화는 사용하지 않았다.

실제 stage1 `initial.pt`와 stage0 `final.pt` 텐서를 비교했다. 두 손 모두 활성 Actor와 해당 std가 정확히 같고, 새 업데이트 수0·Actor/Value optimizer state0·Critic 변경·계약 stage_index1을 확인했다. 따라서24업데이트 뒤에 counter/optimizer를 그대로 이어 붙인 실행이 아니다.

RH의 stage0 최종17.68034ms→stage1 사전평가15.71206ms 변화는 **추가 PPO 업데이트 전, 단계/window 등 관측 입력을 바꾼 결과**다. stage1 PPO 학습 성과로 집계하지 않는다. 계획한 사전 gate와 Actor-only 전달 절차는 충족했다. stage1의 완료 예산·실제 정책·초기 대비 변화는 다음 검수에 정리했다.

## 4차 검수 — stage1 완료와 최종 실제 평가

4개 학습 실행의 training gzip과 update 파일을 별도로 집계했다. stage1은 손별12업데이트·7,200전이·24학습 episode이며 양손 모두24/24 성공, 물리 실패0이다. report는 completed=True, failure=None, changed_inputs와 cleanup_errors는 빈 배열이다. stage0과stage1을 합치면 **43,200전이·144학습 episode**다. 평가 episode나 이전 스모크를 이 학습 합계에 넣지 않는다. 역할별 최종 stage1 counter12는 source stage0 counter24와 별도다.

최종 stage1 모델 payload 업데이트12를 직접 읽고, 실제 평가 gzip에서 다음 수치를 재집계했다.

| stage1 최종 실제 평가 | LH | RH |
| --- | --- | --- |
| 안전5초·단계 성공 | 2/2 | 2/2 |
| 원음 구간 접촉후보 coverage | 두 회1.0 | 해당 없음 |
| 첫 목표방향 / 최소 오차 | 해당 없음 | 두 회12.285672521ms / 동일 |
| 기타 최대 이동 | 5.806433 / 5.757609mm | 두 회.242961mm |
| 추가 목표 down / 반대 up | 해당 없음 | 두 회각1 / 1 |
| 원 joint music50/100ms | 두 회0/0 | 두 회0/0 |

각 평가가300tick/1,200개240Hz 표본이며 native/측정 physics_step 정렬·score_time=u−1·240Hz 비용 적분이 일치하고 source_unchanged=True다. 안전 실패 이유도 없다.

같은 stage1 계약의 이전 사전평가15.712060742ms 대비 최종 첫 오차는3.426388221ms 작다. 이 비교는 추가 stage1 PPO 후의 변화이며, stage0→stage1 이전 직후의 관측 변화와 분리했다. LH coverage는 사전평가와 최종 모두1.0이다.

RH native 방향 순서는 down/up/down이고, 두 목표 down의 오차는 약.01228567초와1.13366775초다. 추가 동작은 남아 있다. stage1에서는 두 번째 down이±.5초 밖이므로 wrong_crossings로 분류되어 unnecessary_crossings가0이다. stage0의 unnecessary_crossings 감소와 직접 비교해 반복 동작 억제 성공으로 주장하면 안 된다.

stage1 LH의 episode별 평균 audible 밖 hold 보상 비율은82.827984%다. stage0의 같은 방식 집계는91.155842%지만, 단계별 보상 적분 창이 달라 총보상을 직접 비교하지 않는다. 긴 단음 유지 성공이 필요한 시점의 해제·다음 프렛 전환을 검증한 것은 아니다.

`analyze_stage1_v2.py`·기반 `analyze_stage0_v5.py`와 `stage1_final_analysis_v1.json`의 집계·counter 일치 검사·같은 stage1 사전평가 비교·해석 한계는 원자료와 정합한다. v5에는 앞서 v4에서 별도 확인했던 최종 평가 counter와 학습 완료 counter의 동등성 검사도 추가되어 있다. 최종 학습·수행 수치에 관한 미해결 Critical/Warning은 없다.

`stage1_final_analysis_v1.md`의 LH 설명 문단 뒤 RH 행에 표 헤더가 없던 표시 문제는 원본을 보존한 새 `stage1_final_summary_v1.md`와 최종 README의 완전한 표로 해결했다. 해당 RH 수치는 JSON과 원자료에 일치한다.

## 5차 검수 — 최종 종합 문서

최종 README와 새 stage1 요약, 변경된 안내 문서6개의 diff를 확인했다. `documentation_update_v1.json`에 기록된 변경 전 archive SHA와 변경 후 SHA가6개 모두 실제 파일에 일치한다. 추가 단락은 학습 결과·모델 경로·한계에 한정하며 학습 소스 변경은 없다.

종합 문서의 역할별36회 Actor 계보와 stage1 checkpoint counter12, 총43,200전이·144학습 episode, 탐색 성공 LH70/72·RH72/72, 결정적 최종 각2/2는 원자료와 맞다. BC→stage0 PPO, 단계 이전 직후 입력 변화, 같은 stage1 계약에서의 추가 PPO 변화를 분리했다. 추가 down/up와 창 축소에 따른 crossing 분류 변화, 원 joint music0, 접촉 후보와 압력/음향의 구분 및 고정 시작2회의 한계도 명확하다.

최종 stage1 각 평가의 모든240Hz 표본에서 any-support와 양발 접지율1.0을 별도 확인했다. README의 기타·발 최대 편차도 raw 값과 일치한다. 전체4개 학습 report의 collection_s와 update_s를 합산하면 수집5647.123628초·업데이트6.220154초, 두 구간 합계 중 수집99.889974%다. 따라서 “수집+PPO 업데이트 시간 중 약99.9%” 표기는 정확하며, 문서처럼 이를 물리 계산만의 시간이나 동시 실행의 실제 경과시간으로 해석해서는 안 된다.

현재 결과는 초기 성공을 유지하면서 같은 단음·준비 조건에서 RH 최초 통과 오차가 소폭 감소한 범위로 한정된다. LH의 필요한 시점 해제·다음 프렛 전환, 불필요 타현 억제, 다른 목표/시작/seed, 양손 동시 연주·음향은 검증하지 않았다는 최종 주장에 동의한다. 검수자는 이 보고서만 수정했으며 이후 수정 없이 최종 확정한다.
