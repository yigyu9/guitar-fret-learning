# 곡 단위 손별 GPU 학습의 실행 흐름

코드·실행 결과 확인일은 2026-10-21이다. 현재 물리 계약은 GPU aggregate v3, 왼손 보상은 v2다. 사용자 요청에 따라 기본 실행을 GPU PhysX·GPU 텐서 제어/측정/보상으로 전환했다. 이 문서의 날짜 디렉토리는 실행 날짜를 뜻하지 않는다. 이전 CPU 흐름은 [원문 보관](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1/previous_cpu_learning_flow.md), 최신 실제 GPU 검증은 [2000업데이트 실행·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md)을 따르며, [초기 전환 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1/README.md)은 과거 결과로 보존한다.

## 실행 명령

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1

python -m guitar_learning.train \
  --hand left \
  --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu \
  --size large --num-envs 1024 \
  --horizon 32 --updates 2000 --checkpoint-every 50 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_song_gpu_2000
```

`--out`은 아직 없는 새 경로다. 위 조건의 왼손 학습을 실제로 2000업데이트·65,536,000전이·5시간41분25초 동안 정상 완료했다. post-cache GPU 여유는 최저 7.374GiB·최종 8.206GiB였고 비Torch 추정 증가 136MiB 이후 일정하게 유지됐다. 전체 raw 64,000행/CRC·에피소드 대응·568입력 SHA·423소스·최종 167유한 텐서 검사도 통과했다. 이는 해당 조건의 실행 검증이며 물리 무실패나 연주 수렴을 뜻하지 않는다. 오른손 실행은 `--hand right`로 바꾸지만 위 장기 결과는 왼손에 한정된다. 선택하지 않은 손의 정책 행동은 0이며 과거 전문가 모델·BC·성공 평가를 준비할 필요는 없다.

학습 중 종료 34,069회는 곡 시간축 완료 31,524회와 물리 실패 2,545회이며, 67음 전체 과제 성공은 0회다. curriculum은 1788업데이트에 진행도 1.0(압현 단계)에 진입했고 다음 단계에는 접촉 후보 평균 60%가 필요하다. 초기/최종 고정 정책의 각 1024환경 별도 평가도 종료·입력 검증을 통과했다. 안전 타임라인 완료는 1024→1023곡, 전체 첫 곡의 평균 달성 음은 3.969→4.232/67이며 전곡 과제 성공은 모두 0이다. 두 모델의 curriculum 관측이 다르고 특정 음의 향상·저하가 공존하므로 일반적인 연주 향상이나 수렴을 뜻하지 않는다. 첫 평가의 native 종료 실패와 보완 후 정상 재평가도 [별도 평가 분석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md)에 구분해 기록했다.

기본 설정은CUDA/자동GPU물리·128환경·medium·H32·100업데이트·seed7이다. GPU가 없으면 기본 실행은 오류로 종료한다. 환경 수는1~1024이며1환경/H1처럼 총 표본이1개인 설정은 허용하지 않는다. GPU 기본 PPO minibatch는4096, epoch은2다. 모델 크기와 배치 크기가 메모리 사용에 영향을 준다.

## 곡과 PPO 수집 구간

기본 곡은67음·1969control tick·약32.8167초이며, 정책 준비3초·원곡·말미0.5초를 포함한다. native 대기시간은0이다. 물리240Hz·정책60Hz이므로 행동 한 번마다 실제 물리4단계를 진행한다.

H32는 한 환경에서0.5333초를 수집한 뒤 PPO를 갱신한다는 뜻이다. 업데이트 경계에서 물리·곡 시계·음별 원장은 초기화하지 않는다. 곡 종료나 물리 실패인 환경만 저장 초기 자세로 돌아간다. 다른 환경은 계속된다.

1024환경/H32라면 업데이트당 32,768전이다. 위 2000업데이트는 65,536,000전이·환경당 64,000control tick(약1066.7초)의 수집 예산이며 곡 재시작과 PPO 갱신을 포함한다. 실제 실행 시간은 위 5시간41분25초였으며 다른 장비의 소요시간을 보장하지 않는다. `--checkpoint-every 50`으로 50회마다 추가 저장하며 기본 간격 5는 변경하지 않는다. 실패·부분 궤적은 전곡 완주로 세지 않으며 이 예산이 67음 성공 횟수를 보장하지 않는다.

## 호출되는 코드

| 순서 | 파일 | 역할 |
| --- | --- | --- |
| 1 | [train.py](/home/ajou/yigyu/3/guitar_learning/train.py) | 사용자 진입점 |
| 2 | [training/start.py](/home/ajou/yigyu/3/guitar_learning/training/start.py) | 손·곡·모델·GPU 설정 결정, 전체 악보 확인, GPU runner 선택 |
| 3 | [training/gpu_runner.py](/home/ajou/yigyu/3/guitar_learning/training/gpu_runner.py) | 입력 SHA·모델·PPO·로그·자원 보호·저장/실패 처리 |
| 4 | [training/gpu_pool.py](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py) | 한 GPU 장면과 제어·측정 연결, terminal bootstrap과 선택 reset |
| 5 | [gpu/scene.py](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py) | 한GPU PhysX simulator의N환경·환경별aggregate·CUDA 상태/접촉힘/Jacobian·경계 reset |
| 6 | [gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py) | 유한 목표·힘·하체 stable PD/IK·중력/상체 지지 |
| 7 | [gpu/environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py) | GPU 관측512/500·240Hz 보상/안전·곡 원장·종료 |
| 8 | [gpu/geometry.py](/home/ajou/yigyu/3/guitar_learning/gpu/geometry.py) | 회전·COM 상대 운동·손가락 실제 메시 표면 자료 |
| 9 | [skills/specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py) | 선택한 손의 actor와 보상/비용 critic |
| 10 | [training/ppo.py](/home/ajou/yigyu/3/guitar_learning/training/ppo.py) | GAE·PPO·KL 보호·optimizer·strict checkpoint |
| 11 | [song/curriculum_runtime.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py) | 완료 에피소드 기반 왼손 단계,27값 checkpoint buffer |

환경별 aggregate는 68몸체·145shape 용량에 human→guitar→chair 순서로 생성하고 self-collision 및 기존 group/filter를 유지한다. 기타는 native 1강체/89shape이며 기존 39논리마커를 복원해 native 68/논리 106몸체를 구분한다. 질량·COM·관성에는 두 proxy의 기여도 남지만 두 proxy 충돌은 의자/지면을 포함해 완전히 제외한다.

관측·행동·보상·비용·수집 버퍼는GPU에 남는다. 완료 요약과 로그·모델 파일을 저장할 때 CPU로 전달한다. 환경마다 별도 Python 프로세스를 만들지 않는다.

## 초기 자세와 제어

기존035/v14의 실제 준비 snapshot에서105관절 위치·속도와 자유 기타의 자세·속도를 읽는다. Root·의자는 고정, 기타는 자유·중력ON·스트랩OFF다. reset은 에피소드 경계에서 한 번만 수행하고 실행 중 기타 상태를 덮어쓰거나 직접 기타 보조 힘을 주지 않는다.

105입력·97비영 범위·zero8, native POSITION48/EFFORT57와 기존 힘 상한을 유지한다. 왼손21은 전체 native 범위·최대4rad/s·평활화0.45·손가락K/D12/1.5·엄지8/1.25다. 엄지는 별도로 고정하지 않는다.

GPU에서 하체 기하 질량행렬·stable PD·고정 반복 DLS IK와 상체 유한 지지 제어를 계산한다. CPU solver와 수치적으로 같은 결과라고 주장하지 않으며 차이를 새 제어 계약에 기록한다. 제어가 비유한 값이거나 지지 계산을 인증할 수 없으면 물리 진행 전 중단한다. 유한하고 인증된 최근접점의 지지 방향만 정의되지 않는 경우는 `support_control_invalid` 물리 실패다. 해당 환경에 마지막 유효 힘을 현재 tick 끝까지 유지한 뒤 종료 관측으로 bootstrap하고 선택 reset한다. 정상 방향이 돌아와도 그 tick의 실패를 취소하지 않으며 양성 보상을 억제하고 기존 종료 실패 비용 +5를 부과한다.

현재 GPU 왼손은 기존 실행 중 안전 비용과 종료 실패 비용 +5를 유지하고, 물리 실패 때 남은 곡 시간에 비례한 비용을 한 번 추가한다: `5 × max(곡 길이 − 실패가 발생한 실제 control tick 뒤의 곡 시각, 0)`(초당 5). 이는 측정한 미래 비용이 아닌 고정률 absorbing-failure 모델이며 curriculum 비중으로 낮추지 않는다. CPU와 오른손 비용 계약은 변경하지 않았다.

GPU reset의 몸체 변환은 다음 실제 물리단계 전까지 native FK가 갱신되지 않을 수 있다. reset 관측에는 저장된 준비 몸체 snapshot을 사용하고, 실제 물리단계 후 native GPU 상태를 사용한다. 이 관측용 값은 몸체 상태 주입이 아니다.

## 새 GPU 압현 후보와 보상 단계

사용자가 접촉 판정까지 GPU 방식으로 재설계하는 경로를 선택했다. 새 후보는 실제 손가락 충돌 STL의 표면 샘플·현의 유한 구간·프렛 셀·해당 몸체의 접촉 합력을 사용한다. 개별 접촉 몸체 쌍이나 실제 witness가 없으므로 기존CPU clean 판정·실제 현 압력·음향 성공을 상속하지 않는다. 표면 샘플 사이의 접촉은 놓칠 수 있다. 기준과 한계는`training_contract.json`에 저장한다.

왼손은 **손목 위치 → 새 압현 후보 → 곡 시간에 맞춘 유지·전환** 비중을 성능에 따라 바꾼다. 손목 도달이 손가락 학습의 선행 gate는 아니다. 현재 모든 안전 비용·힘 상한·종료 기준은 단계에 따라 완화하지 않는다.

단계 진행도는 수집 중 고정하고 성공한PPO 후 완료 에피소드만 사용해 갱신한다. 부분 궤적·실패를 성공으로 진급시키지 않는다. 단계와 최근 이력은 모델 buffer에 포함한다.

## 수집·종료·저장

1. H32개의 행동과각4개 물리단계를 진행하며240Hz 접촉 후보·비용·실패를 측정한다.
2. 종료 관측으로 다음 가치값을 계산한다. 진짜 terminal이면 bootstrap은0이며 시간제한 truncation은 종료 관측으로 bootstrap한다.
3. 종료된 환경만 reset하고 나머지 환경의 시계·원장을 이어간다.
4. 수집 버퍼로 PPO를 갱신하고 journal의 해당 전이를 committed로 기록한다.
5. 왼손 단계와 업데이트 보고서를 저장하고 다음 구간을 수집한다.

| 출력 | 의미 |
| --- | --- |
| `settings.json`, `training_contract.json`, `inputs_before.json` | 실행 설정·새 GPU 계약·입력 SHA |
| `initial.pt` | 새 모델 또는 strict load 직후 모델·optimizer·난수·curriculum |
| `checkpoint_*.pt` | 주기적 저장 |
| `final.pt` | 정상 종료 시 최종 상태 |
| `failure_last_valid.pt` | 저장 가능한 유효 상태에서 실패한 경우의 복구 모델; 부분 PPO 갱신 중에는 생성하지 않음 |
| `transitions.jsonl.gz` | 수집된 reward/cost/종료 배열과 sampled/logged/durable/committed/discarded 구분 |
| `episodes.jsonl` | 실제 완료/물리 실패 에피소드 |
| `update_*.json`, `learning_metrics.jsonl` | PPO·보상·비용·단계와 처리 시간 |
| `status.json`, `resources.jsonl`, `events.jsonl` | 진행·가용 RAM·단계/실패 기록 |
| `gpu_scene_initial.json`, `gpu_scene_final.json` | 실제GPU flags·CUDA 텐서·장면 소유권·종료 |
| `report.json`, `song_report.json` | 실행 결과·실패·자원·원곡 완료 요약 |

`sampled`나 로그가 남았다는 사실만으로 PPO에 반영됐다고 판단하지 않는다. 실패한 부분 수집은 discarded로 기록한다. `report.completed`는 실행·소스·종료 검사를 통과한 뜻이며 연주 수렴을 뜻하지 않는다.

## 저장 모델 재개

같은GPU 물리·제어·측정·보상·모델·PPO 계약의 checkpoint로 새 출력 경로를 지정한다. 현재 GPU v3 물리 계약은 이전 GPU v1/v2 checkpoint와 호환되지 않으며, 현재 왼손 보상 v2는 이전 왼손 보상 v1과 호환되지 않는다. 상태 차원이 같아도 strict resume을 거부하며 자동 Actor 이전은 하지 않는다. 아래는 2000업데이트 저장본에서 한 번 더 갱신하는 명령이다.

```bash
python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu \
  --size large --num-envs 1024 --horizon 32 --updates 1 \
  --checkpoint-every 50 --seed 7 \
  --resume /home/ajou/yigyu/3/runs/left_song_gpu_2000/final.pt \
  --out /home/ajou/yigyu/3/runs/left_song_gpu_resume_01
```

실제 동일 조건의 2000→2001 GPU 재개에서 32,768전이·569입력 SHA를 검증했고 초기 nonmetadata 상태가 모두 정확히 복원됐다. 모델·두 optimizer·CUDA를 포함한 난수·curriculum·trainer 상태를 복원한 뒤 두 optimizer와 왼손 모델이 갱신됐으며 비활성 오른손은 유지됐다. [실제2000→2001 재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_verification.json). 물리 환경은 초기 자세에서 새 에피소드를 시작하며곡 중간 물리 상태 복원은 아니다. 기존CPU512/500 checkpoint도 새GPU 계약과 다르므로 strict load가 거부된다. 모델 크기나 다른 제어/측정 계약으로 암묵 이전하지 않는다.

CPU 물리 재현은`--physics cpu`로 명시한다. 이전 native·quality·전문 도구는 별도 재현 경로이며 새GPU 측정 성과를 상속하지 않는다.
