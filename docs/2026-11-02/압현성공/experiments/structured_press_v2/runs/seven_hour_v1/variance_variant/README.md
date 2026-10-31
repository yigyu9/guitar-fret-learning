# 목표 손가락 탐색 분산 비교 v1

기존 검지 A100 모델에서 B100으로 이전하는 동안 **목표 손가락4축의 Gaussian 표준편차 배율만** 변경한다. 주 비교는 `factor=.05`, 보조 비교는 `.1`이다. 팔12축의 탐색, 보상9항, 물리/실패 기준, 초기 B 후보, 제어 및 학습률 규칙은 동일하다. 새 정책 schema는 `guitar_learning.structured_variance_policy.v1`이다.

기존 원문3148개를 SHA가 같은 새 runtime으로 복사했다. 검지 A100 체크포인트도 `runtime/transfer_inputs/index_A100.pt`로 복사했다. 원본/복사본 SHA는 `517dc84dc322af2d76b787f0bba3fcccbda357674e18c185bc964b0f3b6954db`이다. 원래 runtime과 원래 체크포인트는 수정하지 않는다.

## 분포 계약

기존 `StructuredPolicy.forward`와 손가락 표준편차 하한0.1을 적용한 뒤, 목표 손가락4축에만 `log_std += log(factor)`를 적용한다. 따라서 factor.05의 유효 하한은0.005이며 다른 축은 그대로다. 평균·가중치·행동의 의미는 바뀌지 않는다. 표본화, PPO logp, entropy, analytic KL 모두 이 같은 forward 결과를 사용한다. 실행 행동에만 잡음을 축소하거나 과거 schema를 재사용하는 방식이 아니다.

원래 base B 정책의 `initialize_from`이 기존 A100의 전체 identity/입력/인접 이전을 먼저 검증한다. 검증된 가중치만 새 schema의 B 정책에 옮긴다. 임시 B 생성과 원본 검증은 `torch.random.fork_rng(devices=[])` 안에 있어 추가 CPU 난수 소비를 남기지 않는다. source의 optimizer/RNG를 이전하지 않으며 새 Adam·seed7로 시작한다. 복사한 A100 입력은 생성 계보에 기록한다.

## 실행

GPU 작업이 비어 있을 때 새 `runtime`을 작업 디렉토리로 사용한다. Python 및 Isaac Gym 환경은 기존 연구와 같다.

```bash
python -B -m guitar_learning.tool.experiments.variance_variant train --factor .05 --updates 100 --seed 7 --out ../runs/index_B_factor005_seed7
python -B -m guitar_learning.tool.experiments.variance_variant evaluate --checkpoint ../runs/index_B_factor005_seed7/J/initial.pt --out ../runs/eval_initial_fixed4242
python -B -m guitar_learning.tool.experiments.variance_variant evaluate --checkpoint ../runs/index_B_factor005_seed7/J/final.pt --out ../runs/eval_final_fixed4242
python -B -m guitar_learning.tool.experiments.variance_variant evaluate-free-v9 --checkpoint ../runs/index_B_factor005_seed7/J/final.pt --out ../runs/eval_final_free_v9
python -B -m guitar_learning.tool.experiments.variance_variant render --checkpoint ../runs/index_B_factor005_seed7/J/final.pt --out ../rendering/index_B_factor005_final
```

학습은 large/64환경/H32이며100회당204,800개 제어 전이다. 평가와 영상은 저장된 새 schema·factor를 엄격히 검증한다. 다른 factor의 체크포인트나 기존 schema의 체크포인트를 그대로 재개하는 것은 허용하지 않는다. 기존 base 체크포인트는 명시적인 가중치 이전 경계를 통해서만 사용한다.

B 평가는 고정reset seed4242로 pool 생성 직전과 원래 strict load 직후에 재시드한다. 각32환경의 실제 q105/초기 유지 목표와 후보 정체성을 기록한다. 기존 대조군의 고정reset 평가와 `variance_reset_protocol.assert_same_initial_conditions`로 실제 조건이 같은지 확인해야 한다. 동일 seed라는 사실만으로 paired 비교가 성립하지 않는다.

초기 모델 감사에는 A100과 active_mask를 제외한 모든 모델 tensor의 정확한 동일성, CPU/CUDA RNG SHA, 기존 대조군 초기 모델이 있으면 그 RNG 동일성도 기록한다. 자유 v9 평가는 새 B schema의 원본 identity를 검증한 후 같은 factor·가중치를 유지하면서33축/원래v9/지원해제 조건으로 명시 이전하는 평가다. 지원 조건의 B 성과와 합산하지 않는다.

## 검증 범위와 비교 기준

CPU 검사7개는 다음을 확인했다.

- 선택4축만 sigma/floor 배율 적용, 팔 및 평균 불변
- 실제 표본화 logp·entropy·analytic KL의 분포 일치
- 실제 PPO1회 갱신의 유한값과 역전파
- 복사한 A100의 엄격한 입력/identity 검증과 가중치 이전
- 대조군과 새 정책의 초기 CPU RNG 및 원시 모델 tensor 동일성
- 다른 factor/기존 schema 체크포인트 거부
- 새 B schema에서 자유 v9로의 엄격한 모델 이전

아직 GPU 학습/평가 결과는 없다. 학습 중 변화하는 정책의 에피소드 성공률과 고정 모델의 잡음 평가 성공률은 구분한다. 동일 A100·seed7·100회 예산의 기존 B100 대조군과 새 B100을 고정reset32 평가로 비교한다. 핵심 지표는 안전달성, 실패를0점 처리한 clean 유지, 오압현, 실패 비용, 최초 접촉, 관절 움직임이다. `.05` 잡음 평가가 좋다는 사실만으로 `.05` 학습도 좋아질 것이라고 결론내리지 않는다.

`copy_manifest.json`은 원본3148개와 복사 출처, `source_seal.json`은 신규 원문까지 포함한 SHA를 기록한다. 감사 SHA는 `validation.json`에 기록한다. 검증 이후 소스 변경은 새로운 버전에서 진행한다.
