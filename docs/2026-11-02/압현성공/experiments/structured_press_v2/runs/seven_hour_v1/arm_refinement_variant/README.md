# 손가락 함수 보존형 팔 세부 학습

같은 검지 A100에서 factor0.1·seed7·large/64환경/H32/B100으로 이전하면서 **학습 가능한 actor 가중치 범위만** 변경한다. 대조군은 `variance_variant/runs/index_B_factor010_seed7`이다. 기존 B 초기 모델이 현재 최고 성능이므로, 이 실험은 그 모델을 자동 대체하지 않는다.

손가락의 `core.finger_encoder` 전체와 그 안의 event encoder, 네 `core.finger_heads`, `core.finger_log_std`, 공유 `actor_extra` 전체를 고정한다. Actor optimizer는 `core.support_encoder`, `core.support_head`, `core.support_log_std`만 갱신한다. 독립적인 `core.value_encoder`, reward/cost critic, `value_extra`는 그대로 학습한다. 두 optimizer의 파라미터 집합은 겹치지 않는다.

이는 관절 각도 고정이 아니다. 동일한 관측에 대한 손가락 평균·표준편차 함수를 보존하며, 팔 이동과 접촉으로 관측이 변하면 손가락 출력도 변한다. 손가락의 실제 목표각·물리 운동·탐색은 유지한다. B 활성 mask는 팔12축+목표 손가락4축의 총16축이며, free-v9는 기존과 같은33축이다. 손가락 움직임 비용, 보상9항, 물리, 성공 판정, KL guard, 적응 학습률 규칙을 변경하지 않는다.

새 정책 schema는 `guitar_learning.arm_refinement_policy.v1`이다. `settings.arm_only_refinement`와 architecture에 고정/학습 범위를 명시한다. 기존 분산 정책 schema를 그대로 재사용하지 않는다. 원래 A100 이전 검증과 새 schema의 B→free-v9 identity 검증을 유지하며, factory alias는 실행 후 반드시 복구한다. 새 모듈은 실행 입력 pin에 명시적으로 포함한다.

## 실행

아래 명령은 이 디렉토리의 `runtime`에서 기존 Isaac Gym Python 환경으로 실행한다. 출력 경로는 존재하지 않아야 한다. 이 작업에서는 GPU 실행을 하지 않았다.

```bash
python -B -m guitar_learning.tool.experiments.arm_refinement train --factor .1 --updates 100 --seed 7 --out ../runs/index_B_arm_refinement_seed7
python -B -m guitar_learning.tool.experiments.arm_refinement evaluate --checkpoint ../runs/index_B_arm_refinement_seed7/J/initial.pt --out ../runs/eval_initial_fixed4242
python -B -m guitar_learning.tool.experiments.arm_refinement evaluate --checkpoint ../runs/index_B_arm_refinement_seed7/J/final.pt --out ../runs/eval_final_fixed4242
python -B -m guitar_learning.tool.experiments.arm_refinement evaluate-free-v9 --checkpoint ../runs/index_B_arm_refinement_seed7/J/final.pt --out ../runs/eval_final_free_v9
python -B -m guitar_learning.tool.experiments.arm_refinement render --checkpoint ../runs/index_B_arm_refinement_seed7/J/final.pt --out ../rendering/index_B_final
```

B 평가는 고정 reset4242와 실제32환경 q/initial_hold 캡처를 재사용한다. 대조군과 실제 초기값이 정확히 같은지 확인한 뒤 비교한다. 동일 seed만으로 대응을 주장하지 않는다. 새 initial checkpoint는 A100과 active_mask 외 모든 tensor가 같아야 한다. 또한 기존 factor0.1 대조군의 실제 initial.pt와 모델 전체 및 CPU/CUDA RNG가 정확히 같아야 하며 실행 후 감사에서 불일치를 오류로 처리한다. CPU 테스트는 CUDA RNG를 새로 생성하지 않으며 실제 GPU 초기화 감사는 실행 후 이루어진다.

## CPU 검증과 한계

실제 복사 A100을 엄격하게 이전한 large 정책에서 PPO actor+value 갱신 후 고정 샘플의 손가락16축 μ·log_std와 고정 가중치가 bitwise 같고 팔 μ는 변하는지 검사한다. 다른 관측에서 학습된 손가락 출력이 변하는지도 확인한다. 원래 분산 정책 생성과 새 정책 생성의 CPU 난수 소비 및 가중치가 같고, 실제 대조군 initial.pt의 모든 모델 tensor가 같은지 확인한다. 엄격한 새 B→free-v9 이전, 기존 schema 거부, settings 누락 거부와 factory 복구도 검사한다.

현재는 단일 검지·동일 목표·seed7 비교다. 손가락 함수 보존이 실제 수행 향상을 보장하지 않는다. 팔이 관측 분포를 바꾸면 기존 손가락 함수가 적응하지 못할 수도 있다. 고정 B 초기/최종 평가와 free-v9 평가, 학습 중 물리 실패·9항 보상·비용을 분리해서 판단한다. 기존 B0 최고 모델도 항상 함께 비교한다.

`copy_manifest.json`은 기존 분산 runtime 원문3152개 및 A100 체크포인트 출처를, `source_seal.json`은 새 모듈/검사를 포함한 전체 원문 SHA를 기록한다. 이전 runtime과 원래3148개 코드는 변경하지 않는다.
