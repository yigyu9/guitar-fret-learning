# 전체 곡 공동 학습 시도 결과

전곡 학습 경로를 구현하고 **2환경·PPO8회·4096전이 학습**을 정상 완료했다. 두 환경 모두 **67음 전체를 포함한1969tick=32.8166667초를 물리 실패 없이 완주**했다. 그러나 압현은 두 환경에서 첫 음만 성공했고, 양손 협응은0/67이다. 전곡 학습이 실행되는 것과 전곡을 연주할 수 있게 된 것은 구분해야 한다.

코드는 `/home/ajou/yigyu/3/guitar_learning/song/`에 있다. 기존 단음 `joint/`와 원모델·검증 기록은 보존했다.

## 실제 결과

`training_v2/report.json`, `song_report.json`, `episodes.jsonl`, `analysis_v1.json`이 근거다.

| 훈련 중 episode | 안전 완주 | 음별 압현 기준 | 시간창 내 타현 | 압현과 타현 결합 | 원50/100ms 음악 매칭 |
|---|---:|---:|---:|---:|---:|
| 환경0 |32.8167초/1969tick|1/67|0/67|0/67|0/67·0/67|
| 환경1 |32.8167초/1969tick|1/67|2/67|0/67|0/67·0/67|

이 표는 stochastic 학습 중의 두 궤적이다. rollout 사이에 정책이 갱신됐으므로 최종 `final.pt` 고정정책을 전곡 평가한 결과가 아니다. 전곡 성공 episode는0/2다.

음별 압현 성공은 note0뿐이다. note0의 clean audible 유지율은 환경0 약76.73%, 환경1 100%였고, 다른66음은 clean audible 유지가0이었다. 전체음 평균 clean 유지율은 각각1.1452%·1.4925%다. 이 분포는 전곡의 프렛·손가락 전환을 아직 배우지 못했음을 보여준다.

환경1은 note14와19에서 목표현·방향의 유효 타현을 기록했고 오차는 각각+128.762ms/+40.397ms였다. 그 순간 clean 압현이 없어 협응과 원50/100ms 음악 매칭에는 포함되지 않았다. 환경0/1의 별도 wrong crossing은2/6회였다. 이 수치는 새로운 완화±0.5초·note 종료 이전 조건이며 원엄격판정과 다르다.

![음별 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/note_outcomes_v1.png)

초록은 해당 기준 충족, 회색은 미달이다. 주황 테두리는 원자료의 재타현 묶음을 펼친 note42/43이다. 이 구간 외에도 거의 모든 음에서 압현에 실패했으므로 빠른 재타현 한 곳만으로 현재 저성능을 설명할 수 없다.

## 실행과 검증

- sampled/logged/durable/committed 모두4096, discarded0/unresolved0.
- 실제PPO update8회, 모두 KL guard 재시도0, accepted KL0.00204~0.01634, actor_lr6.25e-7 유지.
- wall 약1034.37초(17.24분), 수집 처리량약3.98전이/초. 최소 가용메모리24.58GiB.
- physical failure0, guard violation0, 물리 flag 오류0, cleanup 오류0.
- 두 worker 모두 scene 생성·종료각1회, episode reset기록2개. 원native identity/속성 유지, persistent 감사 통과.
- 각worker는 전곡을 끝낸 뒤 다음episode에서79tick=1.3167초를 추가수집했다. 전체4096전이=2×(1969+79)다. 이 짧은 후속구간을 추가 전곡 완주나 새 음 성공 분모로 세지 않았다.
- 입력1753개 현재SHA 변경0. 과거169/6/15/11/20개 source/evidence묶음과 이전 평가/공동학습 입력1702/1740개도 변경0. 상세는 `final_inputs_audit_v1.json`.
- CPU41개 통과(`cpu_tests_v3.log`), 별도 코드·실제소스 초기화·완료 원자료 검수도 통과(`review_v1.md`, `runtime_review_v1.md`).

최종 모델은 `training_v2/final.pt`다. `checkpoint_load_audit_v1.json`에서 원500입력/67목표/32.8167초 계약과PPO config로 **모델·Adam·RNG를 strict load**하여 update8/actor Adam35/value Adam19 상태를 확인했다. 체크포인트 SHA는 `f75f4ff1add887c37b7738708eec5040b4be564a65a42980a455d12f4337c817`이며 읽기 전후 동일했다. 이는 불러오기 검증이며 새로운 native 전곡 평가가 아니다.

## 무엇을 바꿨는가

단음 전용 ledger와7초 제한을 설정으로 우회하지 않았다. 새 `song/` 계약에서 다목표 clean 접촉, 반복 가능한 원StrikeDetector, 음별 일대일 매칭·협응/오타/누락 보상, 전체곡 시계를 구성했다. Root고정/하체유한제어/105·97·8/자유기타·중력ON·스트랩OFF와 원gain/limit/240Hz안전비용·종료를 보존했다. 기타 보조 힘이나 실행 중 상태 덮어쓰기를 사용하지 않았다.

새 상태500=원468+곡 이력32, 두Actor/중앙reward·costCritic, 출력39다. 단음의95이력을 제거하고 동일이름·scale의 물리460열과token/attention/head/std만 기존 검증BC에서 이전했다. 재정의 음악8열+곡이력32열은0, Critic/Adam은fresh다. 기존 출력을 정확히 보존하는 이전이나 성공 상속은 아니다. 실제 양손 Actor의 파라미터 변경과 업데이트4/8 체크포인트를 검수했다. 엄격한 이전 joint 체크포인트를 새song strictresume로 넣으면 명시 거부된다.

앞2초부터 정책은 실제로 행동하고 비용과 보상에 포함된다. 첫 목표가 reset에서 보이도록 lookahead4초를 사용하며 최대18/64토큰이다. rollout256tick에서 매번 초기화하지 않고 같은장면/시계/원장이 이어진다. 실제로그2048행/4096전이에서 rollout경계 시계 단절이나 중간reset은 없었다.

## 원곡과 파생 규칙

원음은 `05_BN2-131-B_solo`의29.3063946초, 매핑67음/정본66이벤트다. 모든음이프렛4~12의압현음이다. 원audio시계+정책준비3초+말미0.5초를60Hz경계로올려32.8166667초로한다. 첫onset은3.6385초, 마지막release-capped end는30.0048초다. 단음의4.12초 시작을 그대로 상속하지 않고 원곡시계를 보존한다.

`event-000042`는 원compiler가unsupported로표시한두음재타현이다. 새task에서원note_on15.7547/15.778초로펼쳐note42/43을모두포함했다. 둘째타현방향은원자료에따로없어서원aggregate방향down을각음에상속했다. 이 방향과23.3ms의짧은전환은 명시적 가정/난도 요인이며 후속 검증대상이다. 원파일은바꾸지않았다. 원release상한도유지해11개음은원t_off보다합계0.8044초짧은sustain으로평가한다. 상세67음시간표·번호·finger/fret/현·SHA는 `score_schedule_v1.json`에 있다.

## 해석과 다음 방향

이번 결과는 **전곡학습 연결과 안정성**을 확인한다. 4096전이/8업데이트만으로 전곡의 숙련이나 긴 학습의 최종 수렴을 판정할 수는 없다. 단음 하나에 맞춘 BC특징만으로 여러프렛/손가락 전환이 자동으로 풀리지 않는다는 초기 증거는 뚜렷하다. 타현을 맞혀도 clean 압현과 겹치지 않아 음악 매칭이0인 문제도 유지된다.

다음의 우선순위는 전체67음을 계속 학습대상으로 유지하면서 **다양한 프렛·손가락과2~4음 전환을 충분히 경험시키는 학습 분포**를 구성하는 것이다. 전곡의 여러구간에서 짧은연속구간을골고루학습하고, 전곡연속평가는별도로유지하는방향을추천한다. 현재 시도보다 단순히 시간만 늘리는 것이 충분한지는 아직 검증하지 않았다. 이 문서의 권고를 구현했다고 주장하지 않는다.

실제 현 압력·진동·음향, 물리 피크 파지의 정밀 검증, Root자유균형/보행, 다른곡 일반화는 이 실험의 결과가 아니다.

## 이어서 실행

현재 작업은 종료됐다. 같은전곡계약으로 이어 학습하는 설정은 `continue_settings_v1.json`(2환경/H256/최대64업데이트/약2시간)이다. 이번에 추가 장기 실행을 시작하지는 않았다. 프로젝트 루트에서 새출력경로로실행한다.

```bash
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:$LD_LIBRARY_PATH
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.song.train \
  --settings docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/continue_settings_v1.json \
  --resume docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/final.pt \
  --out docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/continued_training_v1
```

`--resume`를빼면BC특징에서freshPPO를시작한다. 평가명령은 `python -m guitar_learning.song.evaluate --settings 위설정 --run 학습디렉토리 --out 새평가경로`다. source/계약/PPO config strict 검사를 완화하지 않는다.

## 보존한 실패와 버전

`training_v1`은 설정파서혼입으로PPO초기화에서실패했고0전이/0업데이트다. 정상학습이나물리실패episode분모에포함하지않는다. 당시source_snapshot_v1과수정전archive가원본SHA를보존한다. 수정한현재파일은source_snapshot_v2/source_pins_v2가정본이며training_v2가그입력을사용했다. 실패원자료를성공결과로덮어쓰지않았다.
