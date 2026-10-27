# Fresh large1024/H32 long-training preflight

2026-10-22 현재436 Python source를 읽어 작성한 실행 전 검토다. 이 문서는 새 학습/평가의 성공 보고가 아니며, 작성 과정에서 GPU/GL/native 학습·소스 수정을 하지 않았다. 실제 실행과 원자료 보존·분석·전신 영상은 root가 수행한다. 기존435 smoke100과 이전2000회 결과는 시간/저장공간 참고이며 현행436의 성과를 보증하지 않는다.

## 실행과 예산

현재 진입점은 `guitar_learning/train.py → training/start.py → training/gpu_runner.py`다. 프로젝트 루트에서 아래 환경과 명령을 사용한다. `train2000`은 **존재하지 않는 새 디렉토리**여야 한다. fresh이므로 `--resume`을 넣지 않는다. 아래는 root의 최초 실행 명령이며, 이미 생성된 현재 `train2000`에 다시 실행하지 않는다. 일반 기본값128/medium은 변경하지 않고 이번 실행에만1024/large를 명시한다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export PYTHONFAULTHANDLER=1
/home/ajou/miniconda3/envs/rl38/bin/python -B -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu --size large \
  --num-envs 1024 --horizon 32 --updates 2000 \
  --checkpoint-every 100 --seed 7 \
  --out /home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/train2000
```

`rl38/bin/ninja`는 현재 존재한다. 이 PATH는 gymtorch extension 빌드에도 필요하다. Isaac Gym이 Torch보다 먼저 import되는 기존 진입점을 유지한다. 같은 명령을 새 phase의 GDB wrapper와 stdout 로그로 감싸 native 신호/정상 exit를 보존할 수 있다. wrapper의 실제 실행/신호처리는 root가 확인하며, 여기서 임의 signal 무시나 FPU mask 변경을 추가하지 않는다. headless native 학습에 렌더를 병행하지 않는다. OSMesa 전신 영상은 학습/평가가 끝난 뒤 저장 pose를 재생한다.

- 1 PPO update =32×1024=32,768전이, 2000회=65,536,000전이.
- 압축 raw는64,000 control-tick 행이며 각 행에1024환경 배열이 있다. native global physics step은256,000(각 step1024환경)이다.
- 각 환경의 수집 시간축은2000×32/60=1066.6667초다. H32 경계에서 곡/목표를 reset하지 않는다. 원곡67음·1969tick/32.8167초와035/v14 episode reset은 기존 그대로다.
- 초기 std≈0.049787, actor LR3e−5/value LR3e−4, cost weight/PPO config/손가락 누적 제어/기존 보상v4를 유지한다. 이번 diagnostic v2를 이유로 탐색폭이나 gain을 함께 바꾸지 않는다. native POSITION48/EFFORT57·native105/가동97/고정8, 자유 기타·240Hz 물리·aggregatev3를 보존한다.

## 저장·재개 동작

`training/gpu_runner.py:110–183`, `training/ppo.py:218–251`을 읽어 확인했다.

- `settings.json`, `inputs_before.json`, `training_contract.json`을 기록하고 `initial.pt`를 저장한다. 이번 source snapshot/manifest는 별도로436개를 동결하고 실제 inputs와 대조한다.
- 체크포인트100은 index가0부터이므로 optimizer100이 `checkpoint_000099.pt`, 200이`checkpoint_000199.pt`다. 이후1900의`checkpoint_001899.pt`까지19개 중간본, 정상 마지막은`final.pt`다. `checkpoint_001999.pt`는 만들지 않는다. 초기본을 포함해 정상 경로의 checkpoint 파일은21개다.
- save는 같은 디렉토리 임시 파일을 완성한 뒤 hard link로 최종 이름을 만든다. 기존 파일을 교체하지 않는다. 파일당 큰 optimizer 본은 약69.85MB(66.6MiB)이며 저장 도중 임시본 하나의 여유 공간도 필요하다.
- identity는 schema·architecture(전체 observation/action/control/diagnostics 계약)·PPO config와 정확히 같아야 한다. 현행436의 `left_finger_motion.v2/base_rotation` 때문에 이전435 checkpoint의 직접 strict resume를 허용하지 않는다. 차원이 같다는 이유로 예외를 넣지 않는다.
- 같은436 계약 resume는 모델·두 optimizer·cost weight·updates·Python/NumPy/Torch/CUDA RNG와 model buffer의3331 curriculum state를 복원한다. **물리 장면/곡시계/진행 중인 episode는 이어지지 않고 새로운035/v14 episode로 시작**한다. `--updates K`는 새 실행에서 추가할 횟수이며 전체 목표횟수가 아니다.
- 예: optimizer1000의`checkpoint_000999.pt`에서 전체2000을 만들려면 새 출력 경로에`--resume .../checkpoint_000999.pt --updates 1000`이다. 새 update 파일 index0과 optimizer1001을 구분하고 실제 old1000→new initial1000 nonmetadata 복원을 검사한다. 원래 로그를 수정하지 않고 저장 checkpoint에 없는 후속 update는 별도 보존한다.
- Python 예외의 `failure_last_valid.pt`는 valid/eligible 상태에서만 저장하며 중간 PPO 업데이트는 재개 가능하다고 가정하지 않는다. SIGFPE/프로세스 강제 종료/OOM kill은 finally나 failure checkpoint가 없을 수 있다. 마지막 정상 checkpoint/원자료 CRC와 저장 범위를 CPU 감사한 뒤 새 경로로만 복구한다.

## 모니터링과 검증 파일

| 파일 | 확인할 사항 |
|---|---|
| `status.json` | 현재 phase/0-based update/tick/horizon·host RAM·최신 heartbeat. 단일 status 갱신은 전체 update commit 증거가 아니다. |
| `events.jsonl` | phase 전환, resource guard, CUDA cache release 전후 free/allocated/reserved. native 사용량과 Torch reserved를 구분한다. |
| `resources.jsonl` | 약5초 간격 host MemAvailable/RSS/PSS. 상태 heartbeat 약10초. GPU 전체 여유는 events 및 최종 report와 별도 root 외부 측정에 의존한다. |
| `update_%06d.json`, `learning_metrics.jsonl` | PPO 반영 횟수·보상/비용·per-term means·KL/retry/LR/gradient·curriculum·종료 episode. 단일 last minibatch 지표와 diagnostics 집계를 구분한다. |
| `episodes.jsonl` | 안전완주/physical failure 분리,67음 ledger/4finger near·geometry·load·clean·성공,21축 운동과 새4base60Hz pose RMS/max. 미종료 episode는 성공분모에 넣지 않는다. |
| `transitions.jsonl.gz` 및 sidecar | sampled/logged/durable/committed/discarded를 구분한다.60행별 gzip member를 마감하고 각 PPO commit에서 pending member도 flush/fsync한다. 최종 전체 CRC/EOF·64,000행·65,536,000전이를 검산한다. |
| `report.json`, `song_report.json` | 2000/optimizer2000/transitions·failure없음·stopped=updates_complete·changed/missing/cleanup없음·native GPU1sim/1024env/정상 close를 함께 확인한다. `completed=True`만으로 음성과나 실제2000완료를 주장하지 않는다(코드는 wall-budget stop도 completed로 취급할 수 있음). |
| GDB/stdout·process exit | 정상 exit0와 native 정리, SIGFPE/segfault/CUDA 에러의 실제 신호를 보존한다. |

학습 진행 중에는100/250 update cohort와 필요한 prefix를 CPU stream 분석한다. 손가락별 분모·단계혼합·resume 경계를 보존하고, changing-policy 수집 평균을 고정 checkpoint 평가로 쓰지 않는다. 새 pose 진단은60Hz endpoint이며240Hz 극값이나 contact pair/압력 증명이 아니다.

## 과거 벽시간과 저장공간

읽은 기존 실제 결과:

| 참조 실행(다른 source/계약) | 실제 wall | 실행 폴더 파일 크기 | 이번 계획에 쓰는 범위 |
|---|---:|---:|---|
| press435 smoke100 |1124.4617초(18분44초)|342,097,862bytes(0.319GiB)|100회 단순20배는 약6.25시간. 새base진단 비용은 포함되지 않음. |
| surface JSONv2의 마지막 연속 resume1200 |13,110.3196초(3시간38분30초)|3,859,708,061bytes(3.595GiB)|1200→2000 단순외삽 약6.07시간/5.99GiB. 앞선3중단분/평가/영상은 이 폴더 크기에 없음. |
| 더 이전 rewardv2 단일2000 |20,485.4108초(5시간41분25초)|4,532,799,387bytes(4.222GiB)|장기실행 이력만 참고. 현행 누적제어/보상v4의 기술·학습 성공으로 상속하지 않음. |

현행은 진단 로그가 더 커지므로 **checkpoint50 참조 기준 본학습 약6–8GiB, 소스 동결/분석·고정평가·전신 영상 포함 약9–10GiB의 추가 예산**을 우선 잡는다. 이는 실측 예측범위이지 상한 보장이 아니다. 이번 checkpoint100 선택은 중간19개 약1.24GiB이고 final약66.6MiB+fresh initial약28.6MiB까지 약1.33GiB다. initial에는 optimizer moment가 아직 없어 final보다 작다. checkpoint50의41개 예산에서 약1.30GiB 절약하므로 본학습 약4.7–6.7GiB/후처리 포함 약7.7–8.7GiB가 대응하는 추정이다. source436 Python 자체는2,867,274bytes이고 asset을 전부 복제하는 예산은 별도다. source pin은 자산복제를 의미하지 않는다.

작성 때 `statvfs` 기준 현재 available13,725,622,272bytes≈12.78GiB, `MemAvailable`21,763,012KiB≈20.75GiB였다. repo와`/tmp`는 같은 filesystem이므로 `/tmp`로 옮겨도 여유 공간이 늘지 않는다. GPU memory는 이 읽기 조사에서 직접 query/실행하지 않았다. root가 실행 직전 기존 GPU 프로세스 부재·가용 VRAM을 확인한다.

초기100회까지 실제 파일 증가량과 checkpoint 크기로 다시2000회 예산을 계산하고, root 계획대로 filesystem 여유3GiB는 soft warning, 2GiB는 기술 중단 floor로 외부 감시한다. 디스크 자동 guard는 현재 runner에 없으므로 있는 것처럼 설명하지 않는다. 공간 부족 시 과거 봉인 자료를 자동 삭제/압축 덮어쓰거나 기록 detail을 실행 도중 바꾸지 않는다. 로그·원본 checkpoint·선택 결과·영상용 공간까지 분리해 확인한다.

## 기술적 중단과 성과 관찰의 구분

- 기존 host RAM4GiB floor 또는 cache 반환 후 GPU free1GiB floor, OOM/CUDA illegal access/device assert, native buffer overflow/contact 누락 경고, NaN/Inf, source/pin/contract 변조, 장면 close 실패, JSON/gzip/디스크 쓰기 실패는 기술 문제다. 해당 prefix/마지막 checkpoint를 보존하고 반복 GPU 오류가 있는 장면을 계속 학습시키지 않는다.
- 현재 runner의300초 worker-timeout 설정값이 GPU native 호출을 실제로 끊는 watchdog은 아니다. status가 멈추고 process가 살아 있는 경우 root가 stack/log/resource를 확인한다. 실제 몇 분 정상적으로 걸리는 startup/PPO와 정지 상태를 구분하고 자동 성공 처리를 하지 않는다.
- 단기 mean note count0/낮은 clean/특정 finger 정체, 낮아지는 training reward나 curriculum 정체만으로 조기 중단하지 않는다. 사용자는 충분히 긴 학습을 요청했고 기술적으로 유효한 한2000회 예산을 진행한다. 개별 episode의 기존 physical failure는 원래 terminal/reset으로 처리하며 threshold를 완화하지 않는다. 물리 실패 통계가 늘었다는 사실과 전역 수치/native 오류를 구분한다.
- 낮은 성과는 실패 원인으로 분석할 결과다. 정책이 학습했다고 미리 주장하거나 intermediate snapshot을 좋은 모델로 확정하지 않는다. 기존435의5음 zero행/0음 정책이나 이전8.30 고정평가와 현재 source436 성과를 혼합하지 않는다.

## 마지막 산출물 선택

정상 종료 뒤 CPU 전체 raw/3331 replay·checkpoint finite/two optimizer·pins·nativeclose 검산을 먼저 한다. root 계획의 초기/최종/500/1000/1500 정책을 동일 조건의 별도1024환경 첫 곡 고정 평가로 검사하고, 학습 cohort와 분리한다. 학습 checkpoint끼리는 모든1024환경을 분모로 한 평균 달성→안전 완주 수→최신 업데이트 순으로 선택하고 초기 대비 향상 여부는 따로 보고한다. raw training 평균만으로 best를 선언하지 않는다. 검증된 우수 후보를 선택하지 못하면 **검증된 final.pt**를 선택해 전신 영상을 저장한다. checkpoint 선택 사유·SHA·source 계약과 영상에 사용한 실제 pose capture SHA를 함께 기록한다. 영상은 저장된 실제 pose를 재생하며 새 동역학/정책 개선으로 취급하지 않는다.

preflight 검토 후 root는 디스크를 고려해 checkpoint100으로 결정하고 fresh2000 실행을 시작했다. 현행436 source snapshot/manifest와 기존 세 봉인의 before 무결성 자료를 새 phase에 보존한다. 실제 long run·고정 평가·영상의 완료 여부는 이후 원자료로 별도 판정하며, 지금 완료로 표기하지 않는다.
