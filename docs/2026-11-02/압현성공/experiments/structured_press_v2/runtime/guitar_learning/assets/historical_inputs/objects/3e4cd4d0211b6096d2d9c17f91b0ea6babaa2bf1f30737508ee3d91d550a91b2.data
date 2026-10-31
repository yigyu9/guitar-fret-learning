# 시작부터 음악적 준비를 수행하는 학습 경로

현재 권장 진입점은 `guitar_learning.train_actionable_preparation`, 평가는 `guitar_learning.evaluate_actionable_preparation`이다. 기존에 정책이 참여하지 않았던 앞2초를 정책의 행동·관측·보상·안전 비용 구간에 포함한다. 이전 타이밍 경로와 과거 결과는 재현용으로 보존했다.

## 바뀐 시간표

| 항목 | 이전 경로 | 새 경로 |
| --- | --- | --- |
| native 정착 | 2초 | 0초 |
| 정책 구간 | 5초·300tick | 7초·420tick |
| timing `pre_roll_s` | 1초 | 3초 |
| reset부터 첫 press 목표 | 4초 | 4초 |
| reset부터 첫 onset 목표 | 4.12초 | 4.12초 |
| reset부터 episode 종료 | 7초 | 7초 |

`pre_roll_s`는 기존 음악 태스크 시간표에 더하는 오프셋이며 첫 타현 시각 자체가 아니다. 기존 정책 준비1초도 이번에는 보존해 앞2초의 전환 효과를 분리했다. 첫2초에 준비가 끝나지 않았다고 악보 시각을 연기하지 않는다.

reset은 저장된 준비 상태를 한 번 복원하고 물리를 진행하지 않은 채 첫 관측을 반환한다. 정책은 첫 native step부터 허용된 손 관절 목표를 제출하며 원래 유한 자세 유지 제어가 계속 작동한다. 첫 관측부터 음악 목표·기타 상대 위치·시간 조건이 보이고, 처음120개 제어 전이도 일반 PPO buffer에 수집된다. 이전22초 자세 탐색·검증 절차를 실행하지 않는다.

## 준비 보상과 안전

왼손에는 최초2초의 지정 목표 유효 접촉시간×0.2를 준비 보상으로 추가했다. 기존 target candidate의 이전·현재240Hz 표본이 모두 유효한 실제 구간만 적분한다. 단독 양성 표본이나 접촉 공백을 유지시간으로 계산하지 않으며 최대값은0.4다. 로그 key는 `preparation_contact`, 원자료 각 표본에는 `preparation_contact_reward`를 남긴다. 오른손은 기존 기타 상대 타현 준비 guide를 처음부터 사용한다. 두 손의 기존 타이밍 성공·원 음악50/100ms 판정은 바꾸지 않았다.

성공 교사도 distal body 원점 거리 기준을 만족하지 않았던 기존 근거에 따라 단순 손끝 원점 거리 보상은 다시 사용하지 않았다. 검토 중이던 거리 보상 초안은 native 실행 전에 폐기·보관했다.

모든240Hz 표본에서 기타 이탈·회전·접지·관절속도 등 원래 비용과 종료를 그대로 평가한다. 실패가 있는 제어tick은 양성 준비 보상을 전부 억제한다. Root고정·하체24축 유한 유지·105/97/8 구분·자유 기타/중력ON/스트랩OFF·기존gain/충돌/의자·행동39를 유지한다. 기타 직접 힘·부착·지속 상태 덮어쓰기는 사용하지 않는다.

## 기존 모델과의 관계

입력536·출력39와 망 크기는 같다. 새 시작 상태·시간 분포가 달라 기존 모델의 성공을 상속하지 않는다. 명시적 Actor 이전은 다음만 허용한다.

- 같은 손·같은 타이밍 단계·같은 원음과 제어/안전 계약.
- 기존 native2/pre-roll1에서 새 native0/pre-roll3으로 이전하거나, 같은 새 계약 사이의 이전.
- 정규화가5초에서7초로 변한 타이밍 이력 입력 열의 가중치를7/5로 보정. 기존505개 입력의 순서·정규화는 유지.
- 활성 손 Actor/std만 복사. 새 Critic·optimizer·PPO counter는 별도로 시작.

이 보정은 같은 raw 관측값에 대한 정규화 보정이며 바뀐 시작 상태의 동작 보장은 아니다. `--resume`은 원래의 엄격한 계약 검사를 그대로 사용하므로 이전 경로 체크포인트를 새 경로로 억지로 이어 붙이지 않는다. 구형505 정책·단계/안전/원목표 변경은 이 이전 경로에서 거절한다.

## 실행과 기록

현재 [왼손 설정](/home/ajou/yigyu/3/guitar_learning/configs/left_actionable_preparation_v1.json)과 [오른손 설정](/home/ajou/yigyu/3/guitar_learning/configs/right_actionable_preparation_v1.json)은 N1/H420/업데이트1의 연결 검증 설정이다. 장기 수렴을 검증한 설정으로 설명하지 않는다. 새 출력 폴더를 지정한다.

```bash
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.train_actionable_preparation \
  --settings /home/ajou/yigyu/3/guitar_learning/configs/left_actionable_preparation_v1.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/새_준비_학습_실행
```

평가는 `python -m guitar_learning.evaluate_actionable_preparation --run /절대/새학습출력 --out /절대/새평가 --episodes 2`다. Actor 이전 자체의 평가는 `--initialization /절대/모델 --settings /절대/설정`을 사용한다.

기존 update/checkpoint/전이/자원/재사용 감사에 `actionable_preparation_report.json`을 추가했다. 이 파일에 처음2초의 전이 수·nonzero 행동 수·보상 합계를 기록한다. 실제 비용과 관절운동·접촉은 전이·native 평가 원자료로 확인한다.

## 검증 결과의 범위

전체 CPU256개 검사를 통과했다. 기존 정책의 새 조건 초기 평가에서 양손 각2/2회 안전하게7초를 완주했다. 첫2초 각120tick 모두 정책 행동이 있었고 실제 활성 관절 움직임·비용·목표 관측을 확인했다. 왼손은 원음 구간 접촉 후보 유지율100%였지만 처음2초의 목표 접촉과 준비 접촉 보상은0이었다. 오른손 최초 오차는57.98/104.19ms로 이전12.29ms보다 커졌다.

따라서 앞2초의 학습 참여와 안전한 연결은 확인됐으나 조기 압현 준비나 기존 정밀도를 달성한 학습 완료 결과가 아니다. 손별1업데이트 연결 검증과 후속 실제 평가 수치는 [이번 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/README.md)를 따른다. 실제 압력·음향·여러 음·전곡·양손 결합·일반화는 별도 검증 대상이다.

구현 파일은 `environment_v5.py`, `actionable_preparation_environment.py`, `actionable_preparation_transfer.py`, `train_actionable_preparation.py`, `evaluate_actionable_preparation.py`다. 테스트는 `tests/test_actionable_preparation*.py`에 있다. 기존 소스와 초안은 [보관 폴더](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_actionable_preparation)에 원경로·SHA와 함께 보존했다. 현행 코드에서 archive를 import하지 않는다.
