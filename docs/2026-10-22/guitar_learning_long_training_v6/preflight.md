# 보상 v6 장기 학습 실행·검산 사전 검토

2026-10-22의 동결된 436 Python을 기준으로 한 CPU 읽기 검토다. GPU·native·GL 실행이나 활성 소스 변경은 하지 않았다. 실제 실행과 감시는 root가 담당한다. 이 문서는 2000회 완료나 성능 향상 보고가 아니며, 동적인 실행 상태는 [운영 상태](OPERATION_STATE.md), [진행 기록](progress.jsonl), [GDB 로그](train2000_gdb.log)에서 확인한다.

## 고정된 실행

진입점은 `guitar_learning.train → training.start → training.gpu_runner`다. 이번에는 **fresh** large1024/H32/seed7/2000회, 체크포인트 간격100을 명시한다. 일반 기본128/medium은 바꾸지 않는다. 아래는 최초 실행을 재현하는 명령이며, root가 이미 사용 중인 출력 디렉토리에 다시 실행하면 안 된다. 새 재현 실행은 존재하지 않는 별도 `--out`을 사용한다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1 PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
/home/ajou/miniconda3/envs/rl38/bin/python -B -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu --size large \
  --num-envs 1024 --horizon 32 --updates 2000 \
  --checkpoint-every 100 --seed 7 \
  --out '/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v6_long/train2000'
```

Isaac Gym을 Torch보다 먼저 불러오는 기존 진입점과 Ninja가 있는 PATH를 유지한다. 실제 실행은 root의 GDB/faulthandler 기록으로 감싼다. 분석 도구는 반대로 CUDA를 비활성화하고 CPU에서만 읽는다. 학습과 native 고정 평가·영상 렌더는 동시에 실행하지 않는다.

- 1 update는 32×1024=32,768전이, 전체는 **65,536,000전이**다. 압축 raw는 64,000 control-tick 행, native physics step은 256,000이며 각 물리 step이 1024환경을 진행한다.
- 보상 v6, 상태544, event24, 손가락별 tracking/next 우선 슬롯8, 자세 sin/cos24+valid4+idle4를 고정한다. 손가락 tracking v3의 자기4축/21 요청비용·거리계수와 soft coordination/standby 각0..0.05/s도 검사한다. 이 두 자세 credit은 음 성공이나 관절 가동범위 인증이 아니다.
- LH21 누적 목표·독립 action39, POSITION48/EFFORT57·native105/가동97/고정8, 035/v14 준비 상태, 자유 기타, 물리240Hz/제어60Hz, aggregate v3, 진단v2/base6은 유지한다. 실제 범위를 줄이거나 손가락 동작을 묶지 않는다.
- 초기 latent std=exp(−3)≈0.049787, actor LR3e−5/value LR3e−4 및 PPO·비용의 수동 튜닝은 하지 않는다. 기존 KL retry의 자동 actor LR 감소와 자동 cost weight 갱신은 그대로 유지한다. H32는 수집 길이이며 곡을32tick마다 초기화하는 설정이 아니다.

## 저장 경로와 재개

큰 학습 산출물은 **외부 로컬 디스크**의 위 `train2000` 아래에 둔다. 이것은 원격 저장소가 아니다. 계획·도구·436소스 snapshot/manifest·작은 분석/그림·모니터는 이 docs phase에 둔다. [progress.jsonl](progress.jsonl)은 외부 `run.parent`가 아니라 **이 문서와 같은 phase**의 파일이다. 원시 로그를 분석 폴더에 복사하지 않고 원본 SHA만 기록한다. [소스 동결](training_source_manifest.json)과 [실행 전 보존 목록](before_manifest.json)을 대조한다.

- `settings.json`, `training_contract.json`, `inputs_before.json`, `initial.pt`를 먼저 보존한다. checkpoint100의 중간본은 `checkpoint_000099.pt`부터 `checkpoint_001899.pt`까지19개이고, 정상 마지막은 `final.pt`다. `checkpoint_001999.pt`는 없으며 initial/final 포함 총21개다.
- 저장은 같은 디렉토리 임시 파일을 완성한 뒤 hard link로 최종 이름을 만든다. 기존 파일은 덮어쓰지 않으며 임시본 한 개의 공간도 남겨야 한다.
- strict resume는 schema·architecture의 **전체 계약**과 PPO config가 일치해야 한다. 이전 v4의 상태512/슬롯2, v5의 보상/목표 의미와는 호환되지 않는다. source 개수436이 같다는 이유로 호환 처리하지 않는다.
- 같은 v6의 모델·양 optimizer·cost weight·업데이트 수·RNG·3331 커리큘럼은 복원하지만, 물리 장면/진행 중인 곡은 이어지지 않고 새035/v14 episode로 시작한다. `--updates K`는 재개 후 추가 횟수다. 이번 계획은 이전8회 smoke를 잇지 않는다.
- 예외나 SIGFPE/OOM 뒤에는 마지막 정상 checkpoint의 유한성·실제 저장 범위와 raw CRC를 CPU 감사한 후 **새 출력 경로**에서만 복구한다. 중간 PPO나 미저장 update가 복원된다고 가정하지 않는다. [v6 단기 검증](../guitar_learning_finger_inputs_v1/README.md)의8→9 복원은 이 새 장기 실행의 향후 복원을 대신 인증하지 않는다.

## 관찰·검산

| 위치 | 확인하는 증거 |
|---|---|
| 외부 run의 `status.json`, `events.jsonl`, `resources.jsonl` | phase/heartbeat, CUDA cache 반환 후 free/allocated/reserved, host MemAvailable/RSS. status 하나는 PPO commit 증거가 아니다. |
| `update_*.json`, `learning_metrics.jsonl`, `episodes.jsonl` | optimizer 순서·성분합·KL/retry/LR/gradient/std·curriculum, 안전/실패 분리,67음 ledger와 손가락별 분모,21축 운동 및4base의60Hz 진단. |
| `transitions.jsonl.gz`와 journal | sampled/logged/durable/committed/discarded 구분, 실제 batch1024·raw64k·전이65.536M, 전체 CRC/EOF와 세 로그의 episode 연결. |
| `report.json`, `song_report.json`, `gpu_scene_final.json`, GDB | completed뿐 아니라 updates2000·stopped=updates_complete·failure/cleanup/changed/missing 없음, 실제 CUDA tensor·단일1024 GPU sim·정상 close/exit. |
| local phase의 `progress.jsonl` | `disk_free_bytes`=외부 run FS, `local_disk_free_bytes`=프로젝트 FS, `run_bytes`=외부 run 파일. 관측되지 않은 시점의 여유를 추정값으로 채우지 않는다. |

[검산 도구](verify_training.py)는 전체/선택 prefix를 스트리밍하고 3331 전체 재생·checkpoint model/양 optimizer 유한성·입력 SHA·snapshot을 대조한다. [분석 도구](analyze_training.py)는100/250 update 구간별 안전/실패·음 성공·4손가락 near/geometry/load/clean·보상/PPO·자원·새 soft 자세 credit을 저장한다. `--prefix N`은 완료된 update와 CRC가 끝난 gzip member만 읽고, 쓰는 중인 마지막 미완성 JSONL 한 줄만 별도로 제외한다. 완전한 잘못된 JSON 행을 건너뛰지 않는다. prefix는 전체 gzip EOF·native close·2000회 완료 인증이 아니다.

학습 중 정책이 바뀌므로 이 집계는 **고정 checkpoint 평가가 아니다**. 실패곡의 아직 도달하지 않은 음은 전체67음 분모에 남기고 안전곡을 별도로 비교한다. phase/최근256 gate와100/250 종료곡의 서로 다른 분모를 혼동하지 않는다. 표면/body load/target load는 접촉 pair·압력·소리 인증이 아니며 시간들이 겹칠 수 있다. 진단v2는60Hz endpoint의 equal-episode 평균이고240Hz 극값이나 pooled RMS가 아니다. 표준 raw에는 전체544/8슬롯 정책 입력 tensor가 없으므로 계약 검사를 프레임별 입력 재현으로 확대하지 않는다.

## 벽시간·공간과 기술 중단

| 읽은 실제 참조 | wall/공간 | 이번에 쓸 수 있는 범위 |
|---|---|---|
| 이전 v4 fresh2000, checkpoint100 |22,692.6797초=6.3035시간, run6,154,713,680bytes≈5.732GiB | 약6시간대 장기 예산의 근거. 보상v4/512/슬롯2이므로 v6의 속도·성과 보증은 아니다. |
| v6 large1024/H32 smoke8 |101.5345초, startup4.9171초·collection72.4705초·PPO19.6781초 | 순수 collection+PPO의2000회 단순외삽≈6.40시간. 전체 wall8회를250배하면≈7.05시간이나 startup도250번 포함하므로 예측치로 단정하지 않는다. |
| 같은 v6 checkpoint |initial39,530,768bytes, final92,108,348bytes | 중간19개+final을 같은 크기로 보면 initial 포함 약1.752GiB. 기존 v4의1.329GiB보다 약0.423GiB 증가하며 실제 크기는 다시 측정한다. |

초기 CPU 확인에서 외부 여유는 약1,685.7GiB(약1.65TiB), 프로젝트 SSD는 약4.78GiB였다. SSD만으로 이전 run 약5.73GiB를 추가 저장할 수 없어 외부 경로를 택했다. v6 main은 먼저 약6–8GiB, 고정 평가·영상 포함 전체는 약10–12GiB를 계획하되 상한으로 취급하지 않는다. 첫100회 이후 실제 로그 증가율과 checkpoint 크기로 재산정한다. 두 filesystem의 여유는 계속 바뀌며 초기값을 현재 안전 여유로 쓰면 안 된다. 실제 [disk guard event](disk_guard_event.json)가 있으면 해당 당시 여유·신호와 운영 상태를 확인한다. 이 문서는 그 실행의 정상 지속이나 복구를 가정하지 않는다.

기존 guard는 host4GiB·cache 반환 후 GPU free1GiB이며, root 외부 모니터는 프로젝트/외부 FS 각각3GiB 경고·2GiB 기술 중단 floor를 계획한다. 디스크 guard는 runner 자체가 아니라 별도 monitor의 동작이다. OOM/CUDA assert/illegal access, native buffer/contact 누락 경고, NaN/Inf, JSON/gzip 쓰기 실패, 입력 변조, 회복되지 않는 수집 정지와 close 실패는 기술 문제로 원자료를 보존한다. 낮은 음 성공·낮은 clean·단계 정체 또는 기존 threshold에 따른 개별 episode 종료만으로2000회 예산을 줄이지 않는다. 임의 gain·안전 문턱·기록량 변경이나 기존 봉인 삭제로 문제를 가리지 않는다.

정상 전체 검산 뒤 초기/500/1000/1500/final을 동일1024환경 첫 곡으로 별도 평가한다. 평가한 학습모델끼리 전체1024 평균 달성→안전완주 수→최신 순서로 후보를 선택하고, 초기 대비는 따로 보고한다. 모든20개 checkpoint의 전역 최적이라고 주장하지 않는다. 검증한 좋은 모델 또는 final의 실제 저장 pose로 전신/왼손 영상을 만들고 원자료·SHA·QA를 남긴다. 본 도구 작성 단계에서는 해당 결과가 아직 없다.
