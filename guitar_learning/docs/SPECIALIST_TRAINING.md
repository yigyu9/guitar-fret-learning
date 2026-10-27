# 손별 사전학습 → 전문가 결합 → 공동 적응

현재 목표는 한 음의 왼손 압현과 오른손 타현을 각각 학습할 수 있게 하고, 두 기능을 같은 자유 기타 환경에서 결합하는 것이다. 구현·연결 확인과 실제 학습 성공은 구분한다. 이 구조가 기존 동시 학습보다 빠르게 수렴하는지는 아직 비교하지 않았다.

## 단계와 실제 성공의 의미

| 실행 단계 | 정책 제어 | 반대 손 | 성공 조건 |
| --- | --- | --- | --- |
| `left` | 왼팔12 + 왼손21 | 기준 목표의 유한 제어 또는 결정적 오른손 전문가 | `[press_s,end_s]` 안에서 올바른 손가락·현·프렛의 실제 접촉 후보를 연속50ms 이상 유지하고, 안전하게 시간표 종료 |
| `right` | 오른팔꿈치·손목6 | 기준 목표의 유한 제어 또는 결정적 왼손 전문가 | 지정 현·방향의 유효한 기하 타현이 onset ±50ms 안에 발생하고, 안전하게 시간표 종료. 왼손 접촉은 전제하지 않음 |
| `joint` | 양손39 | 두 전문가를 모두 불러와 함께 갱신 | 기존 접촉 조건이 포함된50ms 음악 매칭을 만족하고 안전하게 시간표 종료. 기존 음악 유지·해제 지표도 계속 기록 |

왼손 첫 단계는 **시간 창 안의50ms 연속 접촉**이다. onset부터 음 끝까지 지속 압현하거나 제때 해제하는 능력을 인증하지 않는다. 유지 시간·최장 연속 시간·접촉 획득·해제는 별도로 기록한다. 오른손은100ms 매칭과 시간 무관 현/방향 통과도 별도로 기록하지만 단계 성공은50ms 기준이다. joint의 단계 성공도 **타현 시점의 접촉 조건을 포함한 strict 매칭**이며, 음 전체 유지·해제의 완수를 함께 인증하지 않는다. 접촉 후보는 현 압력·음향을, 피크 기하 통과는 실제 현 진동을 인증하지 않는다.

`provisional_success`는 중간 성취, `stage_success`는 안전하게 `timeline_complete`까지 끝난 결과다. 시간 제한 종료나 안정성 실패는 완료 성공이 아니다. 안전 실패가 발생하면 성공 플래그와 유효 성취를 무효화하고, 이전에 관측한 접촉·타현 이력은 보존한다. 기존 `music`에는 원래 양손 음악 판정이 그대로 남는다. 예를 들어 오른손 단독 성공과 양손 음악 매칭0은 동시에 가능하다.

## 네트워크와 제어

- 상태468, 이벤트64×24, 우선 이벤트2×24, 행동39를 유지한다. 왼손·오른손 모두 신체 전체·기타·음악 상태를 읽는다.
- Actor는 손별로 **인코더와 출력층 전체가 독립**이다. Critic은 전체 상태를 읽는 공통 Value 인코더와 reward/cost 출력으로 구성한다. medium 전체 파라미터는2,892,112개다. 기존 공유 Actor 망보다 커진 이유는 인코더 분리이며 용량 부족을 확인했다는 뜻이 아니다.
- 단독 단계의 반대 손은 정규화 행동0으로 기준 목표를 유지한다. 실제 관절을 잠그지 않는다. 비활성 손의 비영 행동은 물리 실행 전에 거부한다.
- 전문가와 적응할 때 반대 손은 결정적 출력으로 움직이며 **인코더·출력층 전체 가중치가 동결**된다. 실제 관절은 유한 제어로 움직인다.
- 탐색 잡음·log probability·entropy·PPO 갱신은 학습하는 손의 채널에만 적용한다. 비활성 채널의 analytic KL 기여는0이다.
- 이번 구조에서 신경망 출력은39축이다. 지지·오른손 파지·목/머리42축과 하체24축은 기존 유한 제어를 사용한다. 신경망이105축을 모두 학습한다는 뜻이 아니다.

## 모든 단계에 적용하는 안정성

Root 고정, 하체 유한 제어,105 입력/비영범위97/원래 영범위8, 자유 기타·중력ON·스트랩OFF를 유지한다. 모델·초기 자세·gain·충돌 정책·의자와 준비2초는 변경하지 않았다. 기타 직접 보조 힘·강제 부착·지속 상태 덮어쓰기는 추가하지 않았다. 시뮬레이터는 worker마다 한 번 생성하고 episode 경계에서 준비 상태를 복원한다.

기존240Hz 안정성 비용과 물리 실패 판정을 그대로 적용한다. 기타 위치·회전, 발 이동, 지지·접지 이탈, 관절 속도를 검사한다. 학습 설정은 양의 안정성 비용 가중치를 요구한다. 단독 단계의 실패 tick에서는 양의 손 보상도 억제한다. 비용은 PPO 목적의 페널티이며 안전한 정책을 수학적으로 보장하는 제약은 아니다.

현행 학습 실패 한계는 기타 이동80mm·회전0.35rad, 발 이동40mm, 전체 지지 또는 발 접촉 이탈 유예0.25초, 관절 속도50rad/s다. 이는 실용 초기 자세의 별도 V3 정밀 감사와 동일한 검증이 아니다. 세 지지 부위 사이의 분담 변화와 짧은 이탈은 기존대로 허용한다.

## 실행

현재 구현은 `05_BN2-131-B_solo`의 B 단음 단계만 지원한다. 기본은 첫 음(물리2번 줄·7프렛·약지·내려치기)이다. 다른 음은 `start_event_index`를 명시한다. goal pool·구절 C/D·자동 단계 승격은 이번 버전에 포함하지 않았다.

프로젝트 루트 `/home/ajou/yigyu/3`에서 실행한다. 두 설정은 각각8환경·H256·최대128업데이트·벽시계2시간의 예산을 가진다. 첫 검증에서는 별도1환경·1업데이트 설정을 사용했다. 아래 두 명령은 **각각 별도로 실행**한다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.training.train_specialists \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/training/configs/specialist_left_B_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/specialist_left_B_run_v1
```

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.training.train_specialists \
  --settings /home/ajou/yigyu/3/guitar_learning/tool/training/configs/specialist_right_B_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/specialist_right_B_run_v1
```

`--out`는 아직 없는 새 디렉토리여야 한다. 단계 내 중단 복구는 같은 설정에 `--resume /절대/경로/checkpoint.pt`를 추가한다. 역할·보상·관측·제어·PPO 설정이 달라지면 strict resume는 거부한다. 재시작은 새 native episode에서 시작하며 물리 중간 상태를 이어 붙이지 않는다.

## 전문가 결합

먼저 성공 사례와 반복성을 확보한 전문가를 고른다. checkpoint를 만들었다는 사실만으로 다음 단계로 승격하지 않는다. 각 손의 반복 성공과 기타·발·지지 안정성을 확인한 후 설정을 새 파일로 복사하고 `specialist` 항목을 변경한다.

왼손을 동결한 상태에서 오른손을 적응시키려면 다음과 같이 두 전문가의 **실제 절대 경로**를 넣는다.

```json
"specialist": {
  "role": "right",
  "left_checkpoint": "/절대/경로/왼손전문가/final.pt",
  "right_checkpoint": "/절대/경로/오른손전문가/final.pt"
}
```

양손 공동 미세조정은 `role`을 `joint`로 바꾼다. 양쪽 전문가가 모두 필요하다. 손별 인코더·출력층·표준편차를 통째로 복사하며, Critic·optimizer·업데이트 수는 새로 시작한다. 반대 방향의 적응도 `role: left`와 두 경로로 가능하다. 전체 branch를 조합한 뒤 같은 물리 환경에서 검증해야 하며, 단독 성능이 결합 후에도 유지된다고 가정하지 않는다.

이 가중치 전달에는 관측·행동·물리 종료·음악 목표의 일치가 필요하다. 단계별 reward와 `task.specialist` 차이는 허용한다. 현재 공유 Actor 모델이나 다른 음·tempo의 모델을 억지로 불러오지 않는다. source checkpoint는 요청한 단일 손 역할에서 PPO 업데이트를 완료한 자체 형식이어야 한다. 이 조건은 형식 검증이며 실제 기능 성공의 인증은 아니다.

## 저장과 확인

| 파일 | 내용 |
| --- | --- |
| `training_contract.json`, `settings.json` | 실제 관측·행동·단계·보상·물리 실패 기준 |
| `expert_initialization.json` | actor-only 가중치 전달 또는 strict resume 구분과 원본 SHA |
| `initial.pt`, `checkpoint_*.pt`, `final.pt` | 전체 Actor 두 개·Critic·활성 역할·optimizer/RNG |
| `transitions.jsonl.gz` | 매60Hz 행동·비용·안정성·원래 `music`·별도 `specialist` 지표 |
| `worker_*/audit_episode_*`, `environment/episode_*` | 초기 상태,240Hz 첫 tick 원자료, 준비·reset 근거 |
| `specialist_report.json` | 종료 후 손별 성공 에피소드·실패·원래 음악 결과를 함께 요약 |
| `report.json`, `persistent_audit.json` | 입력 무변경·물리 guard·worker 종료·sim 재사용 감사 |
| `events.jsonl`, `status.json`, `resources.jsonl`, `update_*.json` | 기존 진행·자원·PPO 로그 |

기존 `validate.py`는 공유 Actor 체크포인트 전용이다. 새 전문가 checkpoint를 이 명령에 넘기면 안 된다. 이번 버전의 실제 연결 확인은 새 실행기와 원자료를 사용했다. 전문가의 결정적 영상 평가·기술별 반복 성공 검사, 압현 지속/해제까지의 단계 확대, 접근 가능성의 성공 궤적 확보는 후속 과제다.

코드는 [specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py), [specialist_environment.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_environment.py), [실행기](/home/ajou/yigyu/3/guitar_learning/tool/training/train_specialists.py)에 있다. 기존 Python과 실행 결과는 보존했고, 이전 파일·검사·문서는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_specialists/manifest.json)에 기록했다.
