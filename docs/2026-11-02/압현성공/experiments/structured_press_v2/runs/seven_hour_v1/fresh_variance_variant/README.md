# 전축 fresh 학습의 목표 손가락 분산0.1 대조군

원래 `index_full33_seed7_v1`과 같은601열·원래v9 초기 분포·33활성축에서 처음부터 학습한다. 유일한 학습 요인 변경은 목표 검지4축 Gaussian sigma의0.1배 배율이다. A 체크포인트 가중치나 RNG를 이전하지 않는다. 기존 generic `VariancePolicy`와 `variant_runtime(source=None)`를 재사용하며 별도 정책 구현을 추가하지 않는다.

초기 모든 모델 tensor, 출력 평균, 팔/비목표 탐색, 가치망, 물리 상태, 보상9항, gamma, KL guard와 적응 학습률 규칙은 그대로다. 동일한 초기화 직전 RNG에서 base와 새 정책의 모델 tensor·CPU RNG가 정확히 같음을 CPU에서 확인했다. 원래 GPU pool 생성은 정책 생성 전에 RNG를 소비하므로 CPU에서 정책만 생성한 결과를 GPU initial.pt와 직접 같은 것으로 주장하지 않는다. 실제 GPU 실행 후 `initial_native_audit`가 원래 full33 initial.pt와 전체 모델 및 Python/numpy/CPU/CUDA RNG의 정확한 동일성을 확인한다.

architecture와 settings의 `fresh_variance` marker가 필수다. 같은 generic variance schema라도 기존 B 모델, marker 없는 일반 free-v9 모델, base 모델을 strict resume/evaluate에 허용하지 않는다. 새 진입 모듈은 live 입력 pin에 포함한다. 기존 runtime3152개와 그 안의 감사용 A 파일은 byteexact 사본이지만 fresh 초기화는 A 파일을 torch.load하지 않는다.

## 실행

이 디렉토리의 `runtime`에서 기존 Isaac Gym 환경을 사용한다. 출력 경로는 새 경로여야 한다. 본 준비 작업에서는 GPU를 실행하지 않았다.

```bash
python -B -m guitar_learning.tool.experiments.fresh_variance train --updates 100 --seed 7 --out ../runs/100/train
python -B -m guitar_learning.tool.experiments.fresh_variance evaluate --checkpoint ../runs/100/train/J/initial.pt --out ../runs/100/evaluate_initial
python -B -m guitar_learning.tool.experiments.fresh_variance evaluate --checkpoint ../runs/100/train/J/final.pt --out ../runs/100/evaluate_final
python -B -m guitar_learning.tool.experiments.fresh_variance train --updates 100 --seed 7 --resume ../runs/100/train/J/final.pt --out ../runs/200/train
python -B -m guitar_learning.tool.experiments.fresh_variance evaluate --checkpoint ../runs/200/train/J/final.pt --out ../runs/200/evaluate_final
python -B -m guitar_learning.tool.experiments.fresh_variance render --checkpoint ../runs/200/train/J/final.pt --out ../rendering/final
```

학습은 large/64/H32, 평가32환경, 영상4환경이다. 평가는 원래 full33와 같은 공식 결정적 최초32 episode 경로다. B 후보 전용의 fixed-reset 보정이나 추가 초기 분포 변경은 적용하지 않는다. 실패 episode를 분모에서 빼지 않는다.

100회에서200회로의 재개는 기존 공식 launch/strict resume를 사용한다. 새 initial checkpoint는 source final과 모델·두 Adam·업데이트 수·Python/numpy/CPU/CUDA RNG가 모두 정확히 같아야 하며, 실행 후 감사에서 다르면 오류를 낸다. 저장된 설정과 다른 블록 예산·seed로 암묵적으로 재개하지 않는다. 예산 확장·sampler·입력/identity 검증은 원래 실행기가 처리한다.

## 검증과 판단 범위

CPU 검사3개는 A load 없이 동일 초기화 난수 소비·전체 초기 tensor·평균·가치 동일성 및 검지17~20축 sigma만0.1배가 되는지 확인한다. 비어 있지 않은 두 Adam과 model/RNG를 실제 save/load해 정확히 복원되는지, marker 없는 base/일반 variance 모델을 거부하는지, 필수 fresh/free-v9 설정과 factory 정상/오류 복구도 검사한다.

고정 모델의 결정적 성과와 변화하는 확률 정책의 학습 중 완료 episode 성과를 구별한다. 단일 검지 목표·seed7·동일 기하의 실험이므로 새 목표 일반화 또는 과거557열 production 학습 재현으로 해석하지 않는다. 원래 full33의 초기/100/200 및 기존 B0 기준을 함께 보며 생산 코드는 유지한다. `copy_manifest.json`, `source_seal.json`, `validation.json`에 원본·새 입력 및 CPU 검증의 SHA를 기록한다.
