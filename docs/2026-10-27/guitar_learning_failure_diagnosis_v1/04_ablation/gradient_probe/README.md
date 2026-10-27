# Frozen checkpoint 보상별 첫 정책 기울기 진단

구현과 CPU 자체 검증, 체크포인트50·100·300의 실제 GPU 측정을 완료했다. [측정 결과와 그림](RESULTS.md)을 확인한다. 활성 `guitar_learning` 코드를 수정하지 않았으며 [승인된 설계](../GRADIENT_PROBE_PLAN.md)를 따른다.

## 계산과 범위

- strict loader로 같은 short-finger v2 계약의 checkpoint50·100·300을 읽는다. 원래 설정128환경·H32를 유지하고 하나의 collector로32틱 배치를7회 연속 수집한다. 각 체크포인트는 별도 새 출력 디렉토리에서 직렬 실행한다.
- 기존 callback에서 최종 계수가 적용된 보상9항만 읽는다. 매틱 합계를 실제 보상과 확인한다. `K1`, valid4096, tick·episode ID 대응, true terminal next value0, 실제240Hz 물리896step을 검증한다.
- `GAE(r_i,0,0)`9개와 reward critic residual, `-cost_weight * 실제 cost GAE`를 분리한다. 각 배치 전체4096개에서 공통 combined 표준편차를 사용해 정규화한다. 성분별 자체 표준편차로 나누지 않는다.
- 원래 선택4축 likelihood와 actor parameter를 사용한다. 11개 성분 기울기의 합을 실제 clipped PPO surrogate의 첫 기울기와 비교한다. 큰 모델의 메모리를 줄이기 위해256개씩 계산하지만, 각 목적함수 분모는4096이며 batch 전체 정규화가 유지된다. float32 계산·합산, CPU float64 통계를 사용한다.
- shared finger encoder, 지정 손가락 head, active std4, inactive std12 및 전체 그룹의 norm·total과의 signed dot/cosine·상쇄 정도를 저장한다. inactive std는0이어야 한다.
- `trainer.update`, optimizer step, gradient clipping, parameter 갱신을 수행하지 않는다. 체크포인트와 모델 state·source/evidence·진단 스크립트의 전후 불변성 및 scene 종료를 확인한다.

같은 진단 seed `20261027`을 strict load **이후** 설정한다. 같은 난수 seed가 정책 차이에 따른 물리 궤적 차이까지 제거하지는 않는다. 이 결과는 새로 수집한 frozen-policy 상태분포의 국소 기울기이며, 과거 학습 gradient의 복원이나 성능의 인과적 기여율이 아니다. raw reward 크기·표준편차나 gradient norm 비율을 인과적 백분율로 해석하지 않는다.

## 실행과 산출물

GPU 소유권을 받은 후 아래처럼 한 체크포인트씩 실행한다. checkpoint300은 해당 실행의 `final.pt`이며 payload update가300인지 검증한다. 기존 경로를 덮어쓰지 않는다.

```bash
taskset -c 0-13 env \
  PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
  PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
  LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-} \
  OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 KMP_AFFINITY=disabled OMP_PROC_BIND=false \
  /home/ajou/miniconda3/envs/rl38/bin/python \
  /home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/gradient_probe/support/run_probe.py \
  --checkpoint /ABSOLUTE/TRAIN/evaluation_000050.pt \
  --out /ABSOLUTE/NEW/probe_cp50
```

`batch_01..07.npz`에는 보상9항·reward/cost value와 next value·11개 raw/정규화 advantage·원래 total advantage·duration/done/episode ID·local/source 시각만 저장한다. 전체 observation·native body trajectory·거대한 gradient vector는 저장하지 않는다. `batch_*.json`은 검산 오차, 배치별 기울기 그룹 통계와 실제 완료 에피소드를 담는다. `settings`, `training_contract`, `invocation`, RNG hashes, parameter 이름/shape, 입력 전후 SHA 및 `report.json`을 함께 남긴다. NPZ 성분 순서는 `actor_parameters.json`에 명시한다.

## CPU 검증

[CPU 결과](cpu_self_test.json)는 true terminal의 bootstrap 제거, truncation의 bootstrap 유지·carry 차단, ragged duration, 보상/GAE/정규화 가법성, cost0일 때 critic residual, 표준편차0 처리, 합성 Gaussian likelihood에서 기울기 가법성 및 chunk 대 전체 목적함수 동일성을 검사한다. 모델 state와 parameter `.grad` buffer도 바뀌지 않았다. 기울기 합의 최대 오차는 약 `2.38e-7`이었다. native 물리나 실제 체크포인트에서의 성과 증거는 아니다.

원시 보상 합 허용 오차는 `atol=rtol=2e-6`, GAE·정규화 합은 각각 `2e-4`, 기울기 합은 `atol=2e-5, rtol=5e-4`다. 실제 오차를 결과에 모두 남기고 기준을 넘으면 중단한다. ratio1 검증 허용 절대 오차는 `2e-5`다. total 또는 성분 norm이 `1e-12` 이하면 cosine은 null로 기록한다.
