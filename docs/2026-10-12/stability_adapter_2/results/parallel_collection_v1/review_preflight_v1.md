# 병렬 수집 후보 사전 독립 검수

요약 판정: **문제없음(두 경계 수정 반영 후)**. /tmp 후보 6파일과 계획을 읽기 전용으로 검토하고 기존 runner9·native8·GuardedPPO·GAE와 비교했다. 추가 native·학습 실행 없이 확인했으며 실제 N2 물리 진행·N4 CUDA 갱신·처리량·정책 품질의 통과를 인증하지 않는다.

## Critical

미해결 차단 사항 없음.

- [worker:14](/home/ajou/yigyu/3/stability_adapter_2/parallel_cpu_env_v1.py:14)는 Isaac 장면을 Torch보다 먼저 import하고 CPU baseline/native8을 사용한다. [pool:52](/home/ajou/yigyu/3/stability_adapter_2/parallel_cpu_env_v1.py:52)의 spawn은 각 물리 장면과 전역 patch를 별도 프로세스로 격리한다. runner의 Torch/native import는 main 함수 안에 있어 spawn의 main 모듈 재실행에서 CUDA 정책을 먼저 실행하지 않는다. 정책 sample·critic·optimizer는 부모 learner가 소유한다.
- [collector:19](/home/ajou/yigyu/3/stability_adapter_2/parallel_collect_v1.py:19)는 종료/절단의 final observation을 critic으로 평가한 뒤 해당 worker만 reset한다. `[T,N]` 표본과 latent/action/log_prob를 보존하고 기존 GAE·flatten·PPO를 그대로 사용하므로 종료 bootstrap 0, 절단 bootstrap 유지, 양쪽 경계의 carry 차단이 환경별로 적용된다. RMS 고정과 전체 rollout Gaussian KL≤0.02·Adam/model rollback은 기존 구현을 재사용한다. worker 오류/EOF/timeout 또는 reset 오류로 collect가 raise하면 완성 batch를 반환하지 않아 그 rollout은 optimizer에 전달되지 않는다.
- [이관:14](/home/ajou/yigyu/3/stability_adapter_2/parallel_migration_v1.py:14)는 기존 migrate_payload의 ABI core·기존 source SHA·PPO 설정 exact와 정확한 6개 추가 파일만 허용하는 검사를 재사용한다. 모델/Adam/RMS/RNG/counters를 바꾸지 않고 새 resume_scope만 병렬 수집으로 명시한다. 이는 새 독립 에피소드의 수치 상태 복원이며 과거 단일 장면의 물리 중간 상태나 난수 표본열 재현은 아니다.
- [runner 평가 child](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_training_v1.py:145)는 기존 runner9를 사용한다. 물리/시간 ABI는 바꾸지 않고 N/T는 attempt·로그·report 메타데이터에 기록한다. N4×T64는 256표본, N4×T256은 1024표본이며 미니배치128·epochs4 설정은 유지한다. 5분 복구·30분 공식 영상·11:40 협조적 cutoff 및 평가 child timeout도 기존 흐름을 유지한다.

## Warning — 수정 확인

- 기존 후보의 RMS warmstart 분기는 pool에 없는 previous_update_abi를 호출했다. [runner:98](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_training_v1.py:98)에서 해당 flag를 명시적으로 거절하고 strict/adopt checkpoint를 필수로 하여 지원하지 않는 경로의 실패를 막았다.
- 기존 후보의 중간 process.start 실패는 이미 시작한 worker를 남길 수 있었다. [pool:53](/home/ajou/yigyu/3/stability_adapter_2/parallel_cpu_env_v1.py:53)는 생성 전에 목록에 등록하고 child pipe를 finally에서 닫으며 실패 시 self.close를 수행한다. [115행](/home/ajou/yigyu/3/stability_adapter_2/parallel_cpu_env_v1.py:115)은 미시작 프로세스를 join하지 않고 연결만 닫는다. 이 두 Warning은 해결됐다.
- N/T가 달라지면 갱신당 전이 수와 GAE의 수집 구간이 달라진다. 이후 분석은 실제 transitions·N/T를 읽어야 하며 기존 단일 수집의 `updates×256` 관계를 적용하면 안 된다. 저장·cutoff는 협조적이며 무조건적인 실시간 간격이나 미래 무충돌을 보장하지 않는다.

## 증거 보완·Suggestion

[probe:15](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_probe_v1.py:15)는 초기 두 worker의 실제 native_state exact를 검사하며, [25행](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_probe_v1.py:25)은 5초 후 native scalar q 차이>0·physics1200·금지 API0·스트랩13×1200을 확인하도록 보완됐다. 초기/최종 raw 상태도 보존하므로 전체 관측의 history 차이만을 물리 상태 차이로 해석하는 문제가 해결됐다. q의 rad 차이를 world 회전축으로 해석하지 않는다. CPU7 테스트 정의에는 기존 반례와 부분 worker 생성 실패 정리가 포함됐다. 실제 native seam의 통과는 후속 실행으로 확인해야 한다.

계획의 ‘최대32 optimizer 후보’는 N4×T256·미니배치128·epochs4의 32개 미니배치 갱신 기회를 뜻한다. 각 기회의 기존 guard는 최대8회 backtracking을 허용하므로 실제 optimizer.step 시도 상한32와 구분해 설명하는 것을 권장한다.

root의 마지막 원자료 정정에 따른 재개 후보는 저장 CP315/80,640전이이며 마지막 로그319 중 미저장316..319는 복원 대상이 아니다. 앞선 CP317 추정은 사용하지 않는다. 실제 실행 wrapper는 선택한 저장 파일 SHA와 소비 입력을 고정해야 한다.

## 검수한 staging SHA256

| 파일 | SHA256 |
|---|---|
| [parallel_cpu_env_v1.py](/home/ajou/yigyu/3/stability_adapter_2/parallel_cpu_env_v1.py:1) | `7bb935831cdb950d0a3a3de6dcec24539b0db412ad22d2501e6c38a1bc60ca88` |
| [parallel_collect_v1.py](/home/ajou/yigyu/3/stability_adapter_2/parallel_collect_v1.py:1) | `4839f6dfd0bfcbd0492a2552422e80c8a07d6c6305c927bd73b9be9186b52d68` |
| [parallel_migration_v1.py](/home/ajou/yigyu/3/stability_adapter_2/parallel_migration_v1.py:1) | `3b73b7d6fa7c7863660cedb8ba03439fd1c6d71b65698517db820c88ad586ba9` |
| [run_parallel_training_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_training_v1.py:1) | `6e909ba1d2a0d116fcffc6c017fda8df58bb08fdf0470ba31b7178b21c12216a` |
| [test_parallel_collect_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_parallel_collect_v1.py:1) | `e6dca5003271f98f7a36a140fa3d484eafff2fe790963ca91e5b05f63daf12ee` |
| [run_parallel_probe_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_parallel_probe_v1.py:1) | `d93e77d31bd78231a066b35805ea019a851feb09f78b7252e44ca48a8d5c5507` |

이는 실행 전 사전 검수다. 실제 A 적용 6파일과 /tmp 후보의 모든 SHA가 동일함을 직접 확인했고 [실행 전 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/source_before_native_v1.json:1)의 6파일+계획 SHA도 현재와 일치한다. 소유한 이 새 리뷰 외 파일을 수정하지 않았다.
