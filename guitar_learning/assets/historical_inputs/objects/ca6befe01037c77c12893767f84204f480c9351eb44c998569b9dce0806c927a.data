# 사전 준비와 시간창 단계 학습

**현재 권장 타이밍 경로는 `guitar_learning.tool.training.train_actionable_preparation`이다.** [앞2초를 정책 준비에 사용하는 구현·실행법](/home/ajou/yigyu/3/guitar_learning/docs/ACTIONABLE_PREPARATION.md). native 정착0초·정책7초로 전환해 첫2초도 음악 목표를 보고 행동·보상·안전 비용을 PPO에 수집한다. 기존 첫 타현 시각4.12초와 총7초를 유지하며 원래 유한 지지 제어·안전 기준은 유지한다. 이하 native정착2초 경로는 이전 구현·재현 기록이다. 새 초기화에서 오른손 정밀도 변화와 조기 접촉 미달이 있어 기존 성공을 그대로 상속하지 않는다.

현행 타이밍 구현은 `guitar_learning.tool.training.train_timing_v2`과 `guitar_learning.tool.evaluation.evaluate_timing`이다. 실제 성공 동작에서 출발하되, 넓은 시간 허용창에서 시작해 악보 시각에 맞추는 별도 단계다. 이전 손별 hold/cross의 시간 무관 성공과 구분한다. 실제 구현 검증과 실패는 [이번 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_curriculum_v1/README.md)를 정본으로 삼는다.

## 준비 시간과 시계

기존 native 정착2초를 유지하고, 그 후 정책이 실제로 손을 움직일 수 있는 pre-roll1초를 추가했다. 정책 시각u는0부터 시작하고 곡 시각t=u−1이다. 실행 목표의 press/onset/end에는 같은1초를 더한다. 원 목표·source시각과 provenance를 보존하고, 원래50/100ms 음악 판정은 같은 상대 시각에 대해 동작한다. 준비 구간에도 행동 범위·기타와 하체의 물리·240Hz 측정·안전 종료를 그대로 적용한다. 상태를 계속 덮어쓰거나 정책을 대신해 손을 옮기지 않는다.

전체 정책 구간은5초(기존4초+pre-roll1초), 기본 수집 길이는300제어tick이다. 일반적인1~2초 native 정착 설정과 정책 pre-roll은 별개다. pre_roll_s를 바꿀 때는 새 계약으로 검증해야 하며, 준비시간 증가 자체를 성공으로 간주하지 않는다.

## 단계와 판정

| stage_index | 오른손 시간창 | 왼손 초기 연속 유지 요구 |
| --- | --- | --- |
| 0 | onset ±1.5초 | 약50ms |
| 1 | ±0.5초 | 음 길이의40%, 현재 약92.88ms |
| 2 | ±0.2초 | 음 길이의60%, 현재 약139.32ms |
| 3 | ±0.1초 | 음 길이의80%, 현재 약185.76ms |
| 4 | ±0.05초 | 원onset~end 구간 전체 연속 유지 |

왼손0~3단계는 확장된[press−허용창,end+허용창] 안에서 원래 지정 손가락·현·프렛의 접촉 후보를 연속 유지해야 한다. 요구 길이는 min(음 길이,max(50ms,음 길이×비율))이다. 마지막 단계는 원onset~end 전체 구간이 연속 유효해야 한다. 접촉이 없는 시간을 유지로 계산하지 않고, 이전·현재 양성 표본 사이만 적분한다.

오른손은 원래 깊이·속도·영역·재준비 판정을 통과한 지정 현·방향의 실제 기하 통과를 사용한다. 단계별 허용창 안의 통과 한 번에 성공 보상을 주고, 중심 시각에 가까워지는 추가 보상은 누적 상한을 둔다. 반복 통과로 성공 보상을 계속 얻지 못하며 잘못된 통과·추가 통과·미스를 별도 기록한다. 정확한 타이밍의 한 손 기하 통과와 왼손 조건까지 만족한 원 음악 매칭은 서로 다른 지표다.

실행 중 단계는 고정한다. 평가가 확인된 후 다음 stage_index의 새 설정·출력으로 Actor만 이전한다. 자동 단계 승격·자동 양손 결합은 수행하지 않는다. 기존PPO counter/optimizer를 다른 목적의 학습 이력으로 재사용하지 않는다.

## 지지 기준과 입력·초기화

사용자 변경 기준에 따라 가슴 접촉 지속이나 삼중 접촉률은 성공 필수조건이 아니다. 기존 기타 편차/회전·주요 지지 전체 상실·양발 접지/이동·관절속도 안전 조건은 유지한다. Root고정·하체유한제어·105/97/8·기타자유/중력ON/스트랩OFF·기존gain/충돌/의자·39출력범위는 그대로다. 접촉 부위별 비율은 진단으로 기록한다.

관측은 기존505개 필드의 순서와 정규화(time4/count960)를 보존하고, 새 보상에 필요한 타이밍 이력31개를 붙인536차원이다. 이벤트64×24·우선2×24와 역할별39출력(LH33/RH6)은 같다. stage/window/pre-roll/유지/달성/미스/정밀도·통과 이력이 같은tick말의 관측에 반영되므로 보상의 진행 상태를 숨기지 않는다.

명시적BC/PPO Actor이전은 기존 관측·행동·안전과 원 목표가 같은지 검사한다. 505→536에서는 활성Actor의 첫 입력행렬에0열31개만 추가하며 활성Actor의 나머지 가중치와 활성std를 전달한다. Critic·optimizer·counter는 새로 만든다. **이는 같은 입력에서의 함수 보존이지, 바뀐 시간 입력에서의 실제 성공 보장이 아니다.** 실제 직접 이전에서 LH실패가 확인되어 새 시간 관측으로 교사 궤적을 다시 학습하는 초기화 경로도 사용한다.

536→536의 다음 단계 전달은 기존 타이밍 이력을 유지한다. 동일 실행의 `--resume`은 정확한 새 계약·PPO설정 검증을 그대로 사용한다. stage/pre-roll/목표/안전이 다른 체크포인트를resume로 억지로 이어 붙이지 않는다.

## 실행

기본 시작 설정은 [왼손](/home/ajou/yigyu/3/guitar_learning/tool/training/configs/left_timing_stage0_v1.json)과 [오른손](/home/ajou/yigyu/3/guitar_learning/tool/training/configs/right_timing_stage0_v1.json)이다. source actor와 kind(bc/ppo)를 명시한다. 기본 설정은 새536차원 타이밍 관측으로 다시 초기화해 실제 평가2/2를 통과한 BC모델을 가리킨다. 이전505모델의 직접 이전에서 왼손 안전 실패가 있었으므로, 상태 확장만으로 성공했다고 간주하지 않는다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.training.train_timing_v2 \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/training/configs/left_timing_stage0_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/새_왼손_타이밍_실행
```

최종 평가는 `python -m guitar_learning.tool.evaluation.evaluate_timing --run /절대/학습출력 --out /절대/새평가 --episodes 2`다. 이전 초기화 자체를 검사하려면 `--initialization /절대/모델 --settings /절대/설정`을 사용한다. 출력 경로는 새 디렉토리여야 한다.

학습에는 기존checkpoint/전이/업데이트/진행/자원/재사용lifecycle 기록에 timing_report.json을 추가한다. 평가에는 실제 정책 행동·행동 직전 관측·두 시계·매tick4개 native/음악/안전 측정·완료/실패를 남긴다. timing 성공, 원래 손별 증거, contact-conditioned music50/100ms는 따로 기록한다.

이번 구현의 한 음·동일 시작 검증은 압력·음향·일반화·양손 결합의 완성이 아니다. 과거 실행과 소스는 archive/20261018_before_timing_curriculum에 보존했다.

## 바뀐 시간 입력에 맞춘 교사 초기화

직접 이전한 Actor가 새 시간 입력에서 불안정하면 `timing_demonstration`으로 기존 scripted 성공 행동을 새 관측에서 다시 수집한다. 원래240행을 순서대로 재생하고 마지막 행동을60행 유지해300행을 만든다. 다른 행동을 임의로 보간하거나 기타 상태를 덮어쓰지 않는다. 실제 새 환경에서 안전한5초 완주와 해당 타이밍 단계 성공을 확인한 자료만 BC학습으로 읽는다.

```bash
python -m guitar_learning.tool.demonstration.timing_demonstration capture \
  --settings /절대/타이밍설정.json --teacher /절대/기존교사디렉토리 --out /절대/새교사재생
python -m guitar_learning.tool.demonstration.timing_demonstration fit \
  --settings /절대/타이밍설정.json --dataset /절대/새교사재생 --out /절대/새BC초기화 --steps 2000
```

원teacher의240×505 loader는 그대로 보존했다. 새timing자료는300×536 전용검증을 사용한다. BC는300행전체batch로활성Actor만학습하고Critic/반대손/std불변을검사한다. 원래고유BCschema로별도저장하며PPO업데이트수는0이다. 수치fit목표와실제정책성공은별도로검증한다. 새BC를사용할때설정의actor_initialization을새actor_initialization.pt로,kind를bc로바꾼새파일을만들고실제평가한다.

## 실제 학습 결과와 권장 기록

**2026-10-18 손별 타이밍 학습 완료:** [실제 학습·로그·모델·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/README.md). stage0±1.5초 각24회와 stage1±0.5초 각12회, 총43,200전이를 학습했다. 학습 목표 성공은 LH70/72·RH72/72, 물리 실패0이며 최종 결정적 평가는 양손 각각2/2 안전 성공했다. LH 음 구간 접촉 후보 유지율100%, RH는 같은 stage1 안에서 최초 기하 통과 오차15.712→12.286ms로 소폭 개선됐다. 추가 down/up와 양손 음악 성공0은 남아 있다. 동일 단음·같은 준비 시작의 결과이며 전곡·음향·일반화 성공과 구분한다.

stage1은 stage0 최종 Actor만 이전하고 Critic·optimizer·counter를 새로 시작했다. stage1 최종 checkpoint의 업데이트 counter는12이며 Actor 계보상 누적36회와 구분한다. 다음 학습은 최종 모델과 settings를 별도로 참조하고, 새 단계 계약에서는 실제 이전 평가 후 진행한다. 기존 학습 코드·초기 모델·실패·중간 모델은 보존했다.
