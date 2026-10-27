# 최신 손별 모델의 양손 공동 실행과 PPO

기존563 상태 BC 두 개를 초기화로 사용하여 하나의 자유 기타 환경에서 동시에 실행한다. 별도의 출력 합성망은 없다. 왼손33축·오른손6축을 연결한39차원 목표를 같은60Hz tick에 한 번 제출하고 실제240Hz 네 표본으로 양손 판정을 갱신한다. 하체는 기존 유한 유지 제어를 사용하며 학습 정책이 하체 동작을 새로 생성하는 구조는 아니다.

## 관측과 초기화

- 기존 손별563 상태·토큰·정규화·이력 의미를 각자 보존한다.
- 공동 이력6개를 더해 Actor 입력은 각569, 중앙 reward/cost Critic 입력은1132다.
- Actor는 자기 손563와 공동6개만 받는다. 기존 Actor의 새 입력6열은0이므로 이전 출력이 초기화 때 보존된다.
- 검증된 BC의 해당 Actor와33/6축 std만 이전한다. 공동 Critic·Adam·PPO update는 새로 시작한다. 양손 Actor 모두 공동 PPO에서 학습한다.
- strict resume는 새 architecture와 전체 계약·PPO config를 정확히 비교한다. 원563 checkpoint를 strict resume로 읽거나 성공·optimizer를 상속하지 않는다.

## 성공과 보상

손별 Timing/QualityLedger를 원래 의미대로 유지하고 공유 action-change/안전 비용은 한 번만 적용한다. 왼손 postnote hold 상쇄·clean audible 보상·첫2초 능동 준비, 오른손 준비/타현/복귀 보상도 유지한다.

공동 성공에는 두 손의 전체 품질 성공과 협응 성공이 모두 필요하다. 협응은 이번 실제 물리 표본의 accepted crossing ID, 목표 현·방향·stage 시간창 및 note 종료 이전, 이전/현재 두 표본의 clean 압현을 함께 확인한다. 최초 올바른 협응에+1, 압현과 결합되지 않은 accepted crossing에는-.5다. 같은 ID는 중복 보상하지 않는다. 실패tick의 모든 양성 보상을 억제한다. 원 MusicLedger의50/100ms 결과는 완화stage 성공과 별도다.

가슴 접촉 지속은 필수 성공조건이 아니다. Root 고정, 하체 유한 제어,105/97/8, 자유 기타·중력ON·스트랩OFF, 원gain/limit/안전종료를 보존한다. 기타에 직접 힘을 가하거나 실행 중 상태를 덮어쓰지 않는다. 실제 현 압력·진동·음향을 검증하는 것은 아니다.

## 파일과 실행

- `environment.py`, `metrics.py`: 단일 환경·양손 원관측·보상·공동 판정.
- `policy.py`, `transfer.py`, `settings.py`: 두 Actor/중앙 Critic, 원4회 평가 증거 및 모든 source SHA 검증, 설정.
- `evaluate.py`: 고정 두 전문가 또는 joint PPO를1~4회 deterministic 실행하고 streaming 원자료·최종 결과·안전 preflight를 저장.
- `proofs.py`: 실제 완주·안전·입력 불변 증거를 검사한다. 음악 성공은 학습 시작의 선행조건으로 요구하지 않는다.
- `train.py`, `worker.py`: 기존 persistent worker/PPO/자원감시·로그를 연결한다. 실행 시작8GiB, 실행 중 최소6GiB 가용메모리, 평가case600초/전체3000초 제한.

프로젝트 루트에서 rl38 Python을 사용하며 Isaac Gym을 NumPy/Torch보다 먼저 import한다. native 실행에는 rl38의 lib 경로가 필요하다.

```bash
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:$LD_LIBRARY_PATH
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.experiments.joint.evaluate \
  --settings docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/fixed_experts_settings_v1.json \
  --out /tmp/guitar_joint_fixed_new --episodes 1
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.experiments.joint.train \
  --settings docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_smoke_settings_v1.json \
  --out /tmp/guitar_joint_train_new
```

출력 경로는 새 디렉토리여야 한다. fresh PPO 설정은 `joint.preflight_gate`로 이 두 전문가의 실제 안전 완주 증거를 지정한다. 재개는 `--resume /절대경로/final.pt`, PPO 평가는 evaluate에 `--run /절대경로/학습디렉토리`를 추가한다.

학습은 `learning_metrics.jsonl`, `episodes.jsonl`, `training_summary.json`, `report.json`, `persistent_audit.json`, `joint_report.json`, `final.pt`와 체크포인트를 저장한다. 실제 로그 파일명과 수치는 결과 디렉토리 README에서 확인한다. `joint_report`는 손별/협응/전체 공동 성공·원50/100ms 음악·물리 실패를 분리하며 전체 nested 증거는 `episodes.jsonl`의 원본을 참조한다. 평가는 매60tick과 episode 끝에 진행을 출력한다.
