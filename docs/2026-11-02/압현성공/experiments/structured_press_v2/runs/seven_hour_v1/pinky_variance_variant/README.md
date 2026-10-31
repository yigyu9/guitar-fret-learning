# 소지 탐색 분산0.1 대조군

소지 A200 체크포인트(`009d7f0f4a9c3380e1c6d630e4fb444e7d4ee6c9229df7de4789a8f68f4ca2ea`)에서 B100으로 이전한다. 기본 잡음 대조군 `pinky_B_seed7_v1/100/train/J/initial.pt`와 같은 모델·새 Adam·seed7·large/64환경/H32/100회이며, 목표 소지4축의 Gaussian 표준편차만0.1배로 만든다. 기존 generic `VariancePolicy`를 그대로 사용하므로 새 정책 구현이나 schema 우회는 없다. 기존 schema의 finger/geometry/active mask/factor 계약으로 다른 손가락 모델과 구분된다.

기존 분산 runtime3152개를 byteexact 복사한 뒤 소지 A200을 새 runtime 내부 `transfer_inputs/pinky_A200.pt`에 byteexact 복사했다. 새 진입 모듈은 올바른 소지 source를 선택하고 settings의 `pinky_variance_experiment`, source A200 설명, 소지 대조군 감사와 live 입력 pin만 추가한다. 물리·보상9항·초기 분포·손가락 평균·제어·KL guard·적응 학습률 규칙은 바꾸지 않는다. logp/entropy/KL도 같은 실제 sigma를 사용한다.

## 실행

이 폴더의 `runtime`에서 기존 Isaac Gym Python 환경으로 실행한다. 출력은 새 경로여야 한다. GPU 작업은 이 준비 작업에서 실행하지 않았다.

```bash
python -B -m guitar_learning.tool.experiments.pinky_variance train --factor .1 --updates 100 --seed 7 --out ../runs/pinky_B_factor010_seed7
python -B -m guitar_learning.tool.experiments.pinky_variance evaluate --checkpoint ../runs/pinky_B_factor010_seed7/J/initial.pt --out ../runs/eval_initial_fixed4242
python -B -m guitar_learning.tool.experiments.pinky_variance evaluate --checkpoint ../runs/pinky_B_factor010_seed7/J/final.pt --out ../runs/eval_final_fixed4242
python -B -m guitar_learning.tool.experiments.pinky_variance evaluate-free-v9 --checkpoint ../runs/pinky_B_factor010_seed7/J/final.pt --out ../runs/eval_final_free_v9
python -B -m guitar_learning.tool.experiments.pinky_variance render --checkpoint ../runs/pinky_B_factor010_seed7/J/final.pt --out ../rendering/pinky_B_final
```

B 평가의 기본 reset은4242이며 실제32환경 q/initial_hold가 같은지를 대조군과 확인해야 한다. seed만 같다고 대응을 주장하지 않는다. 최초 모델은 A200과 active_mask 외 모든 tensor가 같아야 한다. 실제 소지 대조군 initial.pt가 있으면 초기 모델 전체·CPU/CUDA RNG exact equality를 추가로 확인하며 불일치 시 오류가 난다. 아직 대조군이 없으면 report의 control_status는 `pending`이며 대응을 증명한 것으로 취급하지 않는다. 검지 체크포인트를 감사 대상으로 사용하지 않는다.

CPU 검증은 실제 소지 A200의 엄격 이전, 선택 축29~32만 sigma0.1 적용, 평균/다른 축 불변, 실제 sampled logp·analytic KL의 분포 일치, 기본 잡음 정책과 생성 난수 소비/초기 tensor 동일성, 원래 base schema 거부 및 factory 정상/오류 복구를 확인한다. CUDA 대응은 실제 GPU 실행 후 저장된 initial checkpoint로 확인한다.

단일 소지 목표·seed7 비교다. 소지 B0 및 기본 잡음 B100과 고정 B/free-v9를 구분해 비교하고 생산 코드는 자동 변경하지 않는다. `copy_manifest.json`, `source_seal.json`, `validation.json`은 원본·복사본·새 모듈의 무결성과 CPU 검증을 기록한다. 이전 runtime과 다른 실험 파일은 변경하지 않는다.
