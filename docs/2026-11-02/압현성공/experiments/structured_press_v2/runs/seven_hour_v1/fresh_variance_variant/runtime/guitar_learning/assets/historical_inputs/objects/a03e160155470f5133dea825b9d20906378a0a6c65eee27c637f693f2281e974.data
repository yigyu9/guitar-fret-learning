# 압현·타현 음악적 품질 보완

현재 새 실행 진입점은 `guitar_learning.tool.training.train_musical_quality`와 `guitar_learning.tool.evaluation.evaluate_musical_quality`다. 기존 actionable preparation의 자유 기타 물리·초기 자세·39행동·처음부터 정책 준비·7초 horizon을 유지하며, 판정·보상·성공 조건과 그 이력 관측을 새 계약으로 연결했다. 이전 성공률을 새 조건의 성공률로 상속하지 않는다.

## 구현 범위와 규칙

현재 지원 대상은 원래 곡의 첫 단일 fretted 목표와 손별 학습이다. 전곡 화음·바레·뮤팅은 아직 이 task에 포함하지 않는다. 기타는 자유 강체·중력ON·스트랩OFF, Root 고정·하체 외부 유한 제어이며 기존 gain·자산·지지/접지 비용·실패 조건은 바꾸지 않았다. policy39는 LH33와 RH elbow/wrist6이고 RH 손가락 파지 목표는 계속 유지한다.

### 압현

[fretting_quality.py](/home/ajou/yigyu/3/guitar_learning/quality/fretting_quality.py)는 원 접촉 evidence의 양성lambda·witness·유한 현 lane·높이와 실제 fret body/cell을 사용한다. 신호는 실제 현 압력·음향의 인증이 아니다.

| 상태/접촉 | 새 규칙 |
|---|---|
| correct | 지정 목표 접촉이 있고 확인된 금지 압현이 없다. |
| wrong | 목표현의 더 높은 프렛 접촉, 목표 finger 부재 상태의 다른 finger 할당, 목표 접촉 없이 다른 목표현 fret만 접촉한 경우를 구분한다. |
| missing | 목표를 만족하는 접촉도 확인된 금지 압현도 없다. 다른 현 접촉만 있는 경우는 이 상태와 별도 incidental 진단을 함께 가진다. |
| 같은 현의 낮은 프렛 동시 접촉 | 지정 목표 접촉이 있으면 허용한다. |
| 연주하지 않는 다른 현 접촉 | 진단으로 기록하고 일괄 감점하지 않는다. 단음의 다른 현 접촉을 실제 뮤팅/소리 오류로 인증하지 않는다. |
| 모호한 접촉/경계 | uncertain으로 남기며 그것만으로 오압현을 확정하거나 양성 목표를 무효화하지 않는다. |
| 가슴·팔·허벅지 등 지지 접촉 | LH finger2/3 넥 접촉 필터에서 제외하므로 오압현 수로 세지 않는다. |

원 `positive_target_candidate`와 새 `clean_target_candidate`를 모두 남긴다. [task_measurement_v2.py](/home/ajou/yigyu/3/guitar_learning/core/task_measurement_v2.py)는 clean을 실제 MusicLedger/타이밍/준비 보상 eligibility에 전달한다. 따라서 새 경로의 50/100ms 기록도 eligibility가 더 엄격해졌으며 과거 지표와 동일한 판정이라고 설명하지 않는다. 옛 원자료는 재분류해 덮어쓰지 않는다.

fret7 body의 접촉점이 명목 cell8로 조금 넘어가도 기존±2mm 허용 안이라면 그 이유만으로 higher-fret 오류로 바꾸지 않는다. root 접촉의 귀속이 불명확한 경우도 uncertain이다. 해제는 지정 손가락 후보만 False인지가 아니라 **목표현의 qualifying LH finger 넥 접촉 전체가 사라졌는지**로 판단한다. 다른 finger/낮은 fret/귀속이 모호한 목표현 접촉이 남으면 완전 해제로 인정하지 않는다.

### 타현

[strike_quality.py](/home/ajou/yigyu/3/guitar_learning/quality/strike_quality.py)는 원 기하 detector를 감싼다.

- 목표 down/up에 맞는 출발쪽에서3mm 이상 분리되고 원 depth/zone/유한 현 조건을 만족하는 연속2관측 뒤 준비 상태를 얻는다. 타현 시점의 관측을 소급해 준비로 인정하지 않는다.
- 준비 전의 목표 통과는 성공 경로에서 차단하고 별도 기록/감점한다.
- 첫 적격 목표 통과 이후 추가 목표 통과는 extra로 기록/차단한다. 잘못된 현·방향의 적격 통과는 기존 timing 감점에 전달한다.
- 재무장 대기만으로 차단된 실제 depth/zone/speed 충족 통과도 기록한다. unprepared/extra에 이미 포함한 ID는 다시 감점하지 않고 나머지만 별도 감점한다.
- depth/zone/speed를 만족하지 않는 단순 XY 통과는 진단으로 남긴다. 특히 현 위로 들어 올려 돌아오는 동작을 추가 타현으로 일괄 감점하지 않는다.
- 타현 뒤 목표 현과3D로3mm 이상 분리된 연속2관측이 회복이다. 현재 회복 상태는 다시 접근하면 해제되며, 과거 한 번 회복한 이력과 구분한다.

이는 피크 기준점의 기하 준비/통과/분리다. 실제 피크 물체를 엄지·검지로 누르는 힘·마찰·이탈은 구현하지 않았다.

## 실제 최종 보상

[musical_quality_environment.py](/home/ajou/yigyu/3/guitar_learning/quality/musical_quality_environment.py)가 이전 timing/preparation 보상에 품질 항을 연결한다. **새 보상은 최종 반환 reward와 episode 합·PPO transition에 들어간다.**

| 항목 | 기본값 / 적용 |
|---|---|
| 오압현 점유 | LH−1.0/s, 시작부터 note end까지 |
| 미압현 점유 | LH−0.5/s, 실제 audible 구간만 |
| 접촉 중단 | LH audible 중 clean→비clean 전이마다−0.1 |
| 해제 지연 | note end+0.1초 뒤 목표현 접촉 점유−0.5/s |
| 해제 보너스 | audible clean 접촉을 최소50ms(짧은 음은 음 길이) 수행한 뒤 목표현 clear를50ms 유지하면+0.25, 한 번만 |
| 준비 전 타현 | RH ID마다−0.1 |
| 추가 타현 | RH ID마다−0.1 |
| 위 둘과 중복되지 않는 재무장 차단 통과 | RH ID마다−0.1 |
| 회복 보너스 | RH 최초 회복에+0.1, 한 번만 |
| 첫2초 준비 | 기존0.2/s를 clean 접촉의 연속 구간으로 적분. `preparation_contact.v2`에 의미 변경을 명시 |

점유 감점은240Hz 양 끝 상태의 사다리꼴 추정과 정확한 시간 구간 교집합을 사용한다. clean/해제 유지 시간은 이전·현재가 모두 조건을 만족하는 구간만 센다. feature 개수만큼 보상/감점하지 않는다.

기존 완화 시간창에는 note end 뒤에도 유지 보상을 주는 구간이 있었다. 해제 보상과 충돌하므로 새 경로는 이 **post-note hold 보상을 정확히 상쇄**한다. 또한 LH의 기존 timing-only 성공 보너스를 상쇄하고 실제 audible clean 유지가 현 단계의 required dwell에 도달할 때 한 번 지급한다. 같은 성공에 이중 지급하지 않는다. 감점/상쇄/대체 항을 reward_terms에 각각 남겨 최종 합을 재현할 수 있게 했다.

실패한 control tick에서는 새 양성 품질 항도0으로 억제하고 원 물리 비용/종료를 보존한다. 실패로 이미 제거된 기본 양성 보상을 다시 상쇄해 중복 손실을 만들지 않는다. cost critic/가중치는 별도이며 물리적 안전을 수학적으로 보장하는 것은 아니다.

## 성공 조건과 관측

- LH: 기존 연속 접촉 타이밍 단계 달성 + audible clean fraction이 현 단계 fraction 이상 + 마지막에도 목표현 해제 상태. stage1은40% 완화 단계이므로 짧은 오류가 전혀 없는 연주나 전곡 성공과 동일하지 않다. stage4는 원 음 구간 전체 clean 유지가 필요하다.
- RH: 준비된 목표 통과 + 잘못된/준비 전/추가/나머지 차단 통과0 + 마지막 현재 회복 상태.
- 둘 다 기존 물리 안전과 전체7초 완료가 필요하다. `timing_only_stage_success`를 남기고 현재 `timing.stage_success`, `specialist.stage_success`, episode 기록은 품질 gate를 적용해 일치시킨다.

기존 상태536에 품질 이력27개를 더해 **563 state + 이벤트24차원×최대64개/우선2개 +39행동 계약**이다. 원positive/clean·오/미압현·접촉 점유·중단·해제·준비·추가/차단·회복과 일회성 보너스 지급 이력을 입력에 노출한다. RH가 학습할 때는6개, LH는33개 채널만 likelihood/탐색에 참여한다. 기존 중간536 입력의 순서/scale은 유지한다.

[musical_quality_transfer.py](/home/ajou/yigyu/3/guitar_learning/quality/musical_quality_transfer.py)는 현재 자체 actionable536 PPO에서 선택 손 Actor/std만 이전한다. 첫 layer의 새27열은0, 원536열은 그대로이며 critic/optimizer/RNG/카운터는 새로 시작한다. 추가 입력의 전체 차원·순서·scale, 원 물리/행동/목표/시간/관측 계약을 검사한다. 새563 strict checkpoint는 기존 PPO의 동일 계약 resume 규칙을 사용하며 옛536 strict resume를 허용하지 않는다. 이전 Actor의 성공을 새 성공 조건으로 상속하지 않는다.

## 실행·저장 위치

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.training.train_musical_quality \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/training/configs/left_musical_quality_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/NEW_LEFT_QUALITY_RUN
```

오른손은 `right_musical_quality_v1.json`을 사용한다. 현재 설정은 각1환경·H420·1업데이트의 연결 검증 예산이며 장기 수렴 설정이 아니다. 초기 Actor는 최신 자체 actionable preparation의 hand PPO를 사용한다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.evaluation.evaluate_musical_quality \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/NEW_LEFT_QUALITY_RUN \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/NEW_LEFT_QUALITY_EVAL \
  --episodes 1
```

훈련은 기존 initial/final/checkpoint·업데이트·전이·자원/진행 로그를 유지하고 `musical_quality_report.json`에 품질 결과·최종 보상 항 합을 더한다. 평가는 원자료 `transitions.json.gz`/reset·기존 generic result와 함께 의미를 명시한 `musical_quality_result.json`을 남긴다. 성공률은 새 품질 지표로 읽고, 과거 timing-only 결과와 섞지 않는다.

실제 검사·실패·연결 결과는 [이번 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1)에 보존한다. [이전 버전 정확 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_musical_quality/manifest.json). 기존 파일은 옛 실행 재현과 공용 기반으로 남으며 새 경로는 archive를 import하지 않는다.
