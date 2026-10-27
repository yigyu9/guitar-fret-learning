# Python 전수 검토와 배치

변경 전 Python 385개 모두의 역할·정적 import·정의 목록을 검토했다. 모델/자산/문서/CAS를 포함한 전체 목록은 inventory_before.json과 inventory_after.json에 있다. 동적 호출의 부재를 정적 참조만으로 증명하지 않으며, 미참조처럼 보이는 구현을 임의 삭제하지 않았다.

파일별 상세 정의와 참조자는 [file_review.json](file_review.json), 최종 소스 그래프는 [inventory_after.json](inventory_after.json)을 따른다. 기본 train의 보수적 정적 import closure 114개에는 tool 모듈이 없다. 함수 내부의 미실행 import도 포함하므로 실행 최소 파일 수는 아니다.

재수출만 하던 environment.py를 보관 후 제거했다. 단일 수집 기준 구현과 압현 probe 환경은 검증 도구로 옮겼다. 버전별 환경·측정·worker는 상속/전문 계약을 재사용하므로 유지했다. 전문 실험 환경과 학습기는 일반 학습에서 실행하지 않지만 독립 도구의 동작을 위해 필요하다.

## 원래 Python 전 파일

| 이전 파일 | 현재 배치 | 분류·유지 이유 |
|---|---|---|
| `__init__.py` | [__init__.py](/home/ajou/yigyu/3/guitar_learning/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `contact_recovery/__init__.py` | [tool/experiments/contact_recovery/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/audit.py` | [tool/experiments/contact_recovery/audit.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/audit.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/audit_v2.py` | [tool/experiments/contact_recovery/audit_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/audit_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/capture.py` | [tool/experiments/contact_recovery/capture.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/capture.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/checkpoint_provenance.py` | [tool/experiments/contact_recovery/checkpoint_provenance.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/checkpoint_provenance.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/controller.py` | [tool/experiments/contact_recovery/controller.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/controller.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/dataset.py` | [tool/experiments/contact_recovery/dataset.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/dataset.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/dataset_v2.py` | [tool/experiments/contact_recovery/dataset_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/dataset_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/evaluation.py` | [tool/experiments/contact_recovery/evaluation.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/evaluation.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/native.py` | [tool/experiments/contact_recovery/native.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/native.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/protocol.py` | [tool/experiments/contact_recovery/protocol.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/protocol.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `contact_recovery/run.py` | [tool/experiments/contact_recovery/run.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/run.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `core/__init__.py` | [core/__init__.py](/home/ajou/yigyu/3/guitar_learning/core/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `core/control.py` | [core/control.py](/home/ajou/yigyu/3/guitar_learning/core/control.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/dense_environment.py` | [core/dense_environment.py](/home/ajou/yigyu/3/guitar_learning/core/dense_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/dependency_inputs.py` | [core/dependency_inputs.py](/home/ajou/yigyu/3/guitar_learning/core/dependency_inputs.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/environment_v4.py` | [core/environment_v4.py](/home/ajou/yigyu/3/guitar_learning/core/environment_v4.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/environment_v5.py` | [core/environment_v5.py](/home/ajou/yigyu/3/guitar_learning/core/environment_v5.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/fretting_environment_v2.py` | [tool/validation/fretting_environment.py](/home/ajou/yigyu/3/guitar_learning/tool/validation/fretting_environment.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `core/fretting_v1.py` | [core/fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/core/fretting_v1.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/geometry_v1.py` | [core/geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/core/geometry_v1.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/observations.py` | [core/observations.py](/home/ajou/yigyu/3/guitar_learning/core/observations.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/safety.py` | [core/safety.py](/home/ajou/yigyu/3/guitar_learning/core/safety.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/strike.py` | [core/strike.py](/home/ajou/yigyu/3/guitar_learning/core/strike.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/task_measurement.py` | [core/task_measurement.py](/home/ajou/yigyu/3/guitar_learning/core/task_measurement.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/task_measurement_v2.py` | [core/task_measurement_v2.py](/home/ajou/yigyu/3/guitar_learning/core/task_measurement_v2.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/task_sampling.py` | [core/task_sampling.py](/home/ajou/yigyu/3/guitar_learning/core/task_sampling.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/training_environment.py` | [core/training_environment.py](/home/ajou/yigyu/3/guitar_learning/core/training_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `core/whole_body_control.py` | [core/whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/core/whole_body_control.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `environment.py` | 보관만 유지 | 재수출 중복 제거 — 유일한 probe를 실제 구현의 직접 import로 전환; 원문 보관 |
| `historical_inputs.py` | [historical_inputs.py](/home/ajou/yigyu/3/guitar_learning/historical_inputs.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `imitation/__init__.py` | [imitation/__init__.py](/home/ajou/yigyu/3/guitar_learning/imitation/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `imitation/capture_imitation.py` | [tool/demonstration/capture_imitation.py](/home/ajou/yigyu/3/guitar_learning/tool/demonstration/capture_imitation.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `imitation/evaluate_imitation_v2.py` | [tool/evaluation/evaluate_imitation_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/evaluation/evaluate_imitation_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `imitation/imitation.py` | [imitation/imitation.py](/home/ajou/yigyu/3/guitar_learning/imitation/imitation.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `imitation/imitation_environment.py` | [imitation/imitation_environment.py](/home/ajou/yigyu/3/guitar_learning/imitation/imitation_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `imitation/imitation_io.py` | [imitation/imitation_io.py](/home/ajou/yigyu/3/guitar_learning/imitation/imitation_io.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `imitation/imitation_v2.py` | [imitation/imitation_v2.py](/home/ajou/yigyu/3/guitar_learning/imitation/imitation_v2.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `imitation/train_imitation.py` | [tool/training/train_imitation.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_imitation.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `imitation/train_imitation_ppo.py` | [tool/training/train_imitation_ppo.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_imitation_ppo.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `imitation/train_imitation_ppo_v2.py` | [tool/training/train_imitation_ppo_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_imitation_ppo_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/__init__.py` | [tool/experiments/joint/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/environment.py` | [tool/experiments/joint/environment.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/environment.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/evaluate.py` | [tool/experiments/joint/evaluate.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/evaluate.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/metrics.py` | [tool/experiments/joint/metrics.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/metrics.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/policy.py` | [tool/experiments/joint/policy.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/policy.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/proofs.py` | [tool/experiments/joint/proofs.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/proofs.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/settings.py` | [tool/experiments/joint/settings.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/settings.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/spec.py` | [tool/experiments/joint/spec.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/spec.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/train.py` | [tool/experiments/joint/train.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/train.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/transfer.py` | [tool/experiments/joint/transfer.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/transfer.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `joint/worker.py` | [tool/experiments/joint/worker.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/worker.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/__init__.py` | [tool/experiments/local_skills/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/controls.py` | [tool/experiments/local_skills/controls.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/controls.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/evaluate.py` | [tool/experiments/local_skills/evaluate.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/evaluate.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/learning.py` | [tool/experiments/local_skills/learning.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/learning.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/probe.py` | [tool/experiments/local_skills/probe.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/probe.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/render.py` | [tool/experiments/local_skills/render.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/render.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `local_skills/train.py` | [tool/experiments/local_skills/train.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/local_skills/train.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `music_task.py` | [music_task.py](/home/ajou/yigyu/3/guitar_learning/music_task.py) | 공용 목표 계약 — 과제/checkpoint가 실제 경로·SHA를 포함하므로 원문·경로 유지 |
| `native/__init__.py` | [native/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/control.py` | [native/control.py](/home/ajou/yigyu/3/guitar_learning/native/control.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/elbow_wrist_strike_source_v1.py` | [native/elbow_wrist_strike_source_v1.py](/home/ajou/yigyu/3/guitar_learning/native/elbow_wrist_strike_source_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/environment.py` | [native/environment.py](/home/ajou/yigyu/3/guitar_learning/native/environment.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_pose_v1/__init__.py` | [native/front_facing_pose_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_pose_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_pose_v1/runtime_v1.py` | [native/front_facing_pose_v1/runtime_v1.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_pose_v1/runtime_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/__init__.py` | [native/front_facing_ready_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/motion_v1.py` | [native/front_facing_ready_v1/motion_v1.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/motion_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/motion_v2.py` | [native/front_facing_ready_v1/motion_v2.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/motion_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/motion_v3.py` | [native/front_facing_ready_v1/motion_v3.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/motion_v3.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/protocol_v1.py` | [native/front_facing_ready_v1/protocol_v1.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/protocol_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/protocol_v2.py` | [native/front_facing_ready_v1/protocol_v2.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/protocol_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/protocol_v3.py` | [native/front_facing_ready_v1/protocol_v3.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/protocol_v3.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/protocol_v4.py` | [native/front_facing_ready_v1/protocol_v4.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/protocol_v4.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v1.py` | [native/front_facing_ready_v1/runtime_v1.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v10.py` | [native/front_facing_ready_v1/runtime_v10.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v10.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v12.py` | [native/front_facing_ready_v1/runtime_v12.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v12.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v15.py` | [native/front_facing_ready_v1/runtime_v15.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v15.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v2.py` | [native/front_facing_ready_v1/runtime_v2.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v3.py` | [native/front_facing_ready_v1/runtime_v3.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v3.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v4.py` | [native/front_facing_ready_v1/runtime_v4.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v4.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v5.py` | [native/front_facing_ready_v1/runtime_v5.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v5.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v6.py` | [native/front_facing_ready_v1/runtime_v6.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v6.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v7.py` | [native/front_facing_ready_v1/runtime_v7.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v7.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v8.py` | [native/front_facing_ready_v1/runtime_v8.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v8.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/runtime_v9.py` | [native/front_facing_ready_v1/runtime_v9.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/runtime_v9.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_ready_v1/spine_margin_inputs_v2.py` | [native/front_facing_ready_v1/spine_margin_inputs_v2.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_ready_v1/spine_margin_inputs_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/__init__.py` | [native/front_facing_strike_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/motion_v1.py` | [native/front_facing_strike_v1/motion_v1.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/motion_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/motion_v2.py` | [native/front_facing_strike_v1/motion_v2.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/motion_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/runtime_v1.py` | [native/front_facing_strike_v1/runtime_v1.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/runtime_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/runtime_v2.py` | [native/front_facing_strike_v1/runtime_v2.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/runtime_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/runtime_v4.py` | [native/front_facing_strike_v1/runtime_v4.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/runtime_v4.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/front_facing_strike_v1/runtime_v5.py` | [native/front_facing_strike_v1/runtime_v5.py](/home/ajou/yigyu/3/guitar_learning/native/front_facing_strike_v1/runtime_v5.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_play_v1/__init__.py` | [native/grounded_guitar_play_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_play_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_play_v1/motion_v1.py` | [native/grounded_guitar_play_v1/motion_v1.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_play_v1/motion_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_release_v1/__init__.py` | [native/grounded_guitar_release_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_release_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_release_v1/motion_v1.py` | [native/grounded_guitar_release_v1/motion_v1.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_release_v1/motion_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_support_v1/__init__.py` | [native/grounded_guitar_support_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_support_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_support_v1/runtime_v11.py` | [native/grounded_guitar_support_v1/runtime_v11.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_support_v1/runtime_v11.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_support_v1/runtime_v14.py` | [native/grounded_guitar_support_v1/runtime_v14.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_support_v1/runtime_v14.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_support_v1/runtime_v17.py` | [native/grounded_guitar_support_v1/runtime_v17.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_support_v1/runtime_v17.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_support_v1/runtime_v18.py` | [native/grounded_guitar_support_v1/runtime_v18.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_support_v1/runtime_v18.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/grounded_guitar_support_v1/runtime_v2.py` | [native/grounded_guitar_support_v1/runtime_v2.py](/home/ajou/yigyu/3/guitar_learning/native/grounded_guitar_support_v1/runtime_v2.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/gym_trial_recording.py` | [native/gym_trial_recording.py](/home/ajou/yigyu/3/guitar_learning/native/gym_trial_recording.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/initial_pose_noise_v1.py` | [native/initial_pose_noise_v1.py](/home/ajou/yigyu/3/guitar_learning/native/initial_pose_noise_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/initial_pose_video60_v1/__init__.py` | [native/initial_pose_video60_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/initial_pose_video60_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/initial_pose_video60_v1/replay_v6.py` | [native/initial_pose_video60_v1/replay_v6.py](/home/ajou/yigyu/3/guitar_learning/native/initial_pose_video60_v1/replay_v6.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/initial_pose_video60_v1/static_visual_v7.py` | [native/initial_pose_video60_v1/static_visual_v7.py](/home/ajou/yigyu/3/guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/lower_body_release_v1/__init__.py` | [native/lower_body_release_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/lower_body_release_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/lower_body_release_v1/common.py` | [native/lower_body_release_v1/common.py](/home/ajou/yigyu/3/guitar_learning/native/lower_body_release_v1/common.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/lower_body_release_v1/control_math_v1.py` | [native/lower_body_release_v1/control_math_v1.py](/home/ajou/yigyu/3/guitar_learning/native/lower_body_release_v1/control_math_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/lower_body_release_v1/controller_horizontal_v4.py` | [native/lower_body_release_v1/controller_horizontal_v4.py](/home/ajou/yigyu/3/guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/lower_body_release_v1/scene_v8.py` | [native/lower_body_release_v1/scene_v8.py](/home/ajou/yigyu/3/guitar_learning/native/lower_body_release_v1/scene_v8.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/native_contacts.py` | [native/native_contacts.py](/home/ajou/yigyu/3/guitar_learning/native/native_contacts.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/om_axilla_source_geometry_v3.py` | [native/om_axilla_source_geometry_v3.py](/home/ajou/yigyu/3/guitar_learning/native/om_axilla_source_geometry_v3.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/paths.py` | [native/paths.py](/home/ajou/yigyu/3/guitar_learning/native/paths.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/physics_presets.py` | [native/physics_presets.py](/home/ajou/yigyu/3/guitar_learning/native/physics_presets.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/run_joint_hold.py` | [native/run_joint_hold.py](/home/ajou/yigyu/3/guitar_learning/native/run_joint_hold.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/seated_foot_support_v1/__init__.py` | [native/seated_foot_support_v1/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/seated_foot_support_v1/__init__.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/seated_foot_support_v1/runtime_v1.py` | [native/seated_foot_support_v1/runtime_v1.py](/home/ajou/yigyu/3/guitar_learning/native/seated_foot_support_v1/runtime_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/seated_foot_support_v1/runtime_v6.py` | [native/seated_foot_support_v1/runtime_v6.py](/home/ajou/yigyu/3/guitar_learning/native/seated_foot_support_v1/runtime_v6.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/strap.py` | [native/strap.py](/home/ajou/yigyu/3/guitar_learning/native/strap.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/trial_settings.py` | [native/trial_settings.py](/home/ajou/yigyu/3/guitar_learning/native/trial_settings.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `native/upper_arm_static_geometry_v1.py` | [native/upper_arm_static_geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/native/upper_arm_static_geometry_v1.py) | 공용 물리 기반 — 준비 자세·유한 제어·접촉·렌더의 연결된 native 구현; provenance 보존 |
| `quality/__init__.py` | [quality/__init__.py](/home/ajou/yigyu/3/guitar_learning/quality/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `quality/actionable_preparation_environment.py` | [quality/actionable_preparation_environment.py](/home/ajou/yigyu/3/guitar_learning/quality/actionable_preparation_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/actionable_preparation_transfer.py` | [quality/actionable_preparation_transfer.py](/home/ajou/yigyu/3/guitar_learning/quality/actionable_preparation_transfer.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/evaluate_actionable_preparation.py` | [tool/evaluation/evaluate_actionable_preparation.py](/home/ajou/yigyu/3/guitar_learning/tool/evaluation/evaluate_actionable_preparation.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `quality/evaluate_musical_quality.py` | [tool/evaluation/evaluate_musical_quality.py](/home/ajou/yigyu/3/guitar_learning/tool/evaluation/evaluate_musical_quality.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `quality/fretting_quality.py` | [quality/fretting_quality.py](/home/ajou/yigyu/3/guitar_learning/quality/fretting_quality.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/musical_quality.py` | [quality/musical_quality.py](/home/ajou/yigyu/3/guitar_learning/quality/musical_quality.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/musical_quality_environment.py` | [quality/musical_quality_environment.py](/home/ajou/yigyu/3/guitar_learning/quality/musical_quality_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/musical_quality_transfer.py` | [quality/musical_quality_transfer.py](/home/ajou/yigyu/3/guitar_learning/quality/musical_quality_transfer.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/strike_quality.py` | [quality/strike_quality.py](/home/ajou/yigyu/3/guitar_learning/quality/strike_quality.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `quality/train_actionable_preparation.py` | [tool/training/train_actionable_preparation.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_actionable_preparation.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `quality/train_musical_quality.py` | [tool/training/train_musical_quality.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_musical_quality.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `runtime/__init__.py` | [runtime/__init__.py](/home/ajou/yigyu/3/guitar_learning/runtime/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `runtime/headless_session.py` | [runtime/headless_session.py](/home/ajou/yigyu/3/guitar_learning/runtime/headless_session.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `runtime/native_session.py` | [runtime/native_session.py](/home/ajou/yigyu/3/guitar_learning/runtime/native_session.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `runtime/persistent_environment.py` | [runtime/persistent_environment.py](/home/ajou/yigyu/3/guitar_learning/runtime/persistent_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `runtime/persistent_session.py` | [runtime/persistent_session.py](/home/ajou/yigyu/3/guitar_learning/runtime/persistent_session.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `runtime/prepared_reset_v1.py` | [runtime/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/runtime/prepared_reset_v1.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `score/__init__.py` | [score/__init__.py](/home/ajou/yigyu/3/guitar_learning/score/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `score/canonical.py` | [score/canonical.py](/home/ajou/yigyu/3/guitar_learning/score/canonical.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `score/events.py` | [score/events.py](/home/ajou/yigyu/3/guitar_learning/score/events.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `score/strike_goal_compiler.py` | [score/strike_goal_compiler.py](/home/ajou/yigyu/3/guitar_learning/score/strike_goal_compiler.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/__init__.py` | [skills/__init__.py](/home/ajou/yigyu/3/guitar_learning/skills/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `skills/skill_environment.py` | [skills/skill_environment.py](/home/ajou/yigyu/3/guitar_learning/skills/skill_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/skill_environment_v2.py` | [skills/skill_environment_v2.py](/home/ajou/yigyu/3/guitar_learning/skills/skill_environment_v2.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/skill_parallel.py` | [skills/skill_parallel.py](/home/ajou/yigyu/3/guitar_learning/skills/skill_parallel.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/skill_parallel_v2.py` | [skills/skill_parallel_v2.py](/home/ajou/yigyu/3/guitar_learning/skills/skill_parallel_v2.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/skill_settings.py` | [skills/skill_settings.py](/home/ajou/yigyu/3/guitar_learning/skills/skill_settings.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/specialist_environment.py` | [skills/specialist_environment.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/specialist_parallel.py` | [skills/specialist_parallel.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_parallel.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/specialist_policy.py` | [skills/specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/specialist_settings.py` | [skills/specialist_settings.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_settings.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `skills/train_skills.py` | [tool/training/train_skills.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_skills.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `skills/train_skills_v2.py` | [tool/training/train_skills_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_skills_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `skills/train_specialists.py` | [tool/training/train_specialists.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_specialists.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/__init__.py` | [tool/experiments/song/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/environment.py` | [tool/experiments/song/environment.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/environment.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/evaluate.py` | [tool/experiments/song/evaluate.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/evaluate.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/measurement.py` | [tool/experiments/song/measurement.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/measurement.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/metrics.py` | [tool/experiments/song/metrics.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/metrics.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/policy.py` | [tool/experiments/song/policy.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/policy.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/settings.py` | [tool/experiments/song/settings.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/settings.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/task.py` | [song/task.py](/home/ajou/yigyu/3/guitar_learning/song/task.py) | 공용 목표 계약 — 과제/checkpoint가 실제 경로·SHA를 포함하므로 원문·경로 유지 |
| `song/train.py` | [tool/experiments/song/train.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/train.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/transfer.py` | [tool/experiments/song/transfer.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/transfer.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song/worker.py` | [tool/experiments/song/worker.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song/worker.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/__init__.py` | [tool/experiments/song_reward_v2/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/environment.py` | [tool/experiments/song_reward_v2/environment.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/environment.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/evaluate.py` | [tool/experiments/song_reward_v2/evaluate.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/evaluate.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/metrics.py` | [tool/experiments/song_reward_v2/metrics.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/metrics.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/policy.py` | [tool/experiments/song_reward_v2/policy.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/policy.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/probe.py` | [tool/experiments/song_reward_v2/probe.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/probe.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/progress.py` | [tool/experiments/song_reward_v2/progress.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/progress.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/settings.py` | [tool/experiments/song_reward_v2/settings.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/settings.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/train.py` | [tool/experiments/song_reward_v2/train.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/train.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/transfer.py` | [tool/experiments/song_reward_v2/transfer.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/transfer.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `song_reward_v2/worker.py` | [tool/experiments/song_reward_v2/worker.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/worker.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tests/__init__.py` | [tests/__init__.py](/home/ajou/yigyu/3/guitar_learning/tests/__init__.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/native_input_probe.py` | [tests/native_input_probe.py](/home/ajou/yigyu/3/guitar_learning/tests/native_input_probe.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/quality_fixtures.py` | [tests/quality_fixtures.py](/home/ajou/yigyu/3/guitar_learning/tests/quality_fixtures.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_actionable_preparation_environment.py` | [tests/test_actionable_preparation_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_actionable_preparation_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_actionable_preparation_transfer.py` | [tests/test_actionable_preparation_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_actionable_preparation_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_actionable_preparation_worker.py` | [tests/test_actionable_preparation_worker.py](/home/ajou/yigyu/3/guitar_learning/tests/test_actionable_preparation_worker.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_audit.py` | [tests/test_contact_recovery_audit.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_audit.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_audit_v2.py` | [tests/test_contact_recovery_audit_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_audit_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_capture.py` | [tests/test_contact_recovery_capture.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_capture.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_checkpoint_provenance.py` | [tests/test_contact_recovery_checkpoint_provenance.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_checkpoint_provenance.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_controller.py` | [tests/test_contact_recovery_controller.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_controller.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_evaluation.py` | [tests/test_contact_recovery_evaluation.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_evaluation.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_contact_recovery_protocol.py` | [tests/test_contact_recovery_protocol.py](/home/ajou/yigyu/3/guitar_learning/tests/test_contact_recovery_protocol.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_control.py` | [tests/test_control.py](/home/ajou/yigyu/3/guitar_learning/tests/test_control.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_dense_environment.py` | [tests/test_dense_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_dense_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_dependency_inputs.py` | [tests/test_dependency_inputs.py](/home/ajou/yigyu/3/guitar_learning/tests/test_dependency_inputs.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_environment_v4.py` | [tests/test_environment_v4.py](/home/ajou/yigyu/3/guitar_learning/tests/test_environment_v4.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_fretting_environment_v2.py` | [tests/test_fretting_environment_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_fretting_environment_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_fretting_quality.py` | [tests/test_fretting_quality.py](/home/ajou/yigyu/3/guitar_learning/tests/test_fretting_quality.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_fretting_v1.py` | [tests/test_fretting_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_fretting_v1.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_geometry_v1.py` | [tests/test_geometry_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_geometry_v1.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_headless_session.py` | [tests/test_headless_session.py](/home/ajou/yigyu/3/guitar_learning/tests/test_headless_session.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_historical_inputs.py` | [tests/test_historical_inputs.py](/home/ajou/yigyu/3/guitar_learning/tests/test_historical_inputs.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_imitation.py` | [tests/test_imitation.py](/home/ajou/yigyu/3/guitar_learning/tests/test_imitation.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_imitation_contract_v2.py` | [tests/test_imitation_contract_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_imitation_contract_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_imitation_ppo_v2.py` | [tests/test_imitation_ppo_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_imitation_ppo_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_imitation_runner.py` | [tests/test_imitation_runner.py](/home/ajou/yigyu/3/guitar_learning/tests/test_imitation_runner.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_internal_native.py` | [tests/test_internal_native.py](/home/ajou/yigyu/3/guitar_learning/tests/test_internal_native.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_internal_score.py` | [tests/test_internal_score.py](/home/ajou/yigyu/3/guitar_learning/tests/test_internal_score.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_environment.py` | [tests/test_joint_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_evaluate.py` | [tests/test_joint_evaluate.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_evaluate.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_metrics.py` | [tests/test_joint_metrics.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_metrics.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_policy.py` | [tests/test_joint_policy.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_policy.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_proofs.py` | [tests/test_joint_proofs.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_proofs.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_settings.py` | [tests/test_joint_settings.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_settings.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_train.py` | [tests/test_joint_train.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_train.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_transfer.py` | [tests/test_joint_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_joint_worker.py` | [tests/test_joint_worker.py](/home/ajou/yigyu/3/guitar_learning/tests/test_joint_worker.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_local_skill_controls.py` | [tests/test_local_skill_controls.py](/home/ajou/yigyu/3/guitar_learning/tests/test_local_skill_controls.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_local_skill_dispatch.py` | [tests/test_local_skill_dispatch.py](/home/ajou/yigyu/3/guitar_learning/tests/test_local_skill_dispatch.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_local_skill_learning.py` | [tests/test_local_skill_learning.py](/home/ajou/yigyu/3/guitar_learning/tests/test_local_skill_learning.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_local_skill_probe.py` | [tests/test_local_skill_probe.py](/home/ajou/yigyu/3/guitar_learning/tests/test_local_skill_probe.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_monitoring.py` | [tests/test_monitoring.py](/home/ajou/yigyu/3/guitar_learning/tests/test_monitoring.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_music_task.py` | [tests/test_music_task.py](/home/ajou/yigyu/3/guitar_learning/tests/test_music_task.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_musical_quality_edges.py` | [tests/test_musical_quality_edges.py](/home/ajou/yigyu/3/guitar_learning/tests/test_musical_quality_edges.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_musical_quality_environment.py` | [tests/test_musical_quality_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_musical_quality_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_musical_quality_runner.py` | [tests/test_musical_quality_runner.py](/home/ajou/yigyu/3/guitar_learning/tests/test_musical_quality_runner.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_musical_quality_transfer.py` | [tests/test_musical_quality_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_musical_quality_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_parallel.py` | [tests/test_parallel.py](/home/ajou/yigyu/3/guitar_learning/tests/test_parallel.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_persistent_audit.py` | [tests/test_persistent_audit.py](/home/ajou/yigyu/3/guitar_learning/tests/test_persistent_audit.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_persistent_environment.py` | [tests/test_persistent_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_persistent_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_persistent_parallel.py` | [tests/test_persistent_parallel.py](/home/ajou/yigyu/3/guitar_learning/tests/test_persistent_parallel.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_persistent_session.py` | [tests/test_persistent_session.py](/home/ajou/yigyu/3/guitar_learning/tests/test_persistent_session.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_policy.py` | [tests/test_policy.py](/home/ajou/yigyu/3/guitar_learning/tests/test_policy.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_ppo.py` | [tests/test_ppo.py](/home/ajou/yigyu/3/guitar_learning/tests/test_ppo.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_ppo_logging.py` | [tests/test_ppo_logging.py](/home/ajou/yigyu/3/guitar_learning/tests/test_ppo_logging.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_prepared_reset_v1.py` | [tests/test_prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_prepared_reset_v1.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_role_layout.py` | [tests/test_role_layout.py](/home/ajou/yigyu/3/guitar_learning/tests/test_role_layout.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_rollout.py` | [tests/test_rollout.py](/home/ajou/yigyu/3/guitar_learning/tests/test_rollout.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_simple_start.py` | [tests/test_simple_start.py](/home/ajou/yigyu/3/guitar_learning/tests/test_simple_start.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_skill_environment.py` | [tests/test_skill_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_skill_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_skill_environment_v2.py` | [tests/test_skill_environment_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_skill_environment_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_skill_runner.py` | [tests/test_skill_runner.py](/home/ajou/yigyu/3/guitar_learning/tests/test_skill_runner.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_smoke_metadata_v1.py` | [tests/test_smoke_metadata_v1.py](/home/ajou/yigyu/3/guitar_learning/tests/test_smoke_metadata_v1.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_environment.py` | [tests/test_song_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_evaluate.py` | [tests/test_song_evaluate.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_evaluate.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_measurement.py` | [tests/test_song_measurement.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_measurement.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_metrics.py` | [tests/test_song_metrics.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_metrics.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_environment.py` | [tests/test_song_reward_v2_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_evaluate.py` | [tests/test_song_reward_v2_evaluate.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_evaluate.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_metrics.py` | [tests/test_song_reward_v2_metrics.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_metrics.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_probe.py` | [tests/test_song_reward_v2_probe.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_probe.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_progress.py` | [tests/test_song_reward_v2_progress.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_progress.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_settings.py` | [tests/test_song_reward_v2_settings.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_settings.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_train.py` | [tests/test_song_reward_v2_train.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_train.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_reward_v2_transfer.py` | [tests/test_song_reward_v2_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_reward_v2_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_settings.py` | [tests/test_song_settings.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_settings.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_task.py` | [tests/test_song_task.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_task.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_train.py` | [tests/test_song_train.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_train.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_song_transfer.py` | [tests/test_song_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_song_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_specialist_environment.py` | [tests/test_specialist_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_specialist_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_specialist_policy.py` | [tests/test_specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/tests/test_specialist_policy.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_specialist_runner.py` | [tests/test_specialist_runner.py](/home/ajou/yigyu/3/guitar_learning/tests/test_specialist_runner.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_strike.py` | [tests/test_strike.py](/home/ajou/yigyu/3/guitar_learning/tests/test_strike.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_strike_quality.py` | [tests/test_strike_quality.py](/home/ajou/yigyu/3/guitar_learning/tests/test_strike_quality.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_task_measurement.py` | [tests/test_task_measurement.py](/home/ajou/yigyu/3/guitar_learning/tests/test_task_measurement.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_task_measurement_v2.py` | [tests/test_task_measurement_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_task_measurement_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_task_sampling.py` | [tests/test_task_sampling.py](/home/ajou/yigyu/3/guitar_learning/tests/test_task_sampling.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_timing_curriculum.py` | [tests/test_timing_curriculum.py](/home/ajou/yigyu/3/guitar_learning/tests/test_timing_curriculum.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_timing_demonstration.py` | [tests/test_timing_demonstration.py](/home/ajou/yigyu/3/guitar_learning/tests/test_timing_demonstration.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_timing_environment.py` | [tests/test_timing_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_timing_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_timing_runner.py` | [tests/test_timing_runner.py](/home/ajou/yigyu/3/guitar_learning/tests/test_timing_runner.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_timing_transfer.py` | [tests/test_timing_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_timing_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_timing_worker_v2.py` | [tests/test_timing_worker_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_timing_worker_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_tool_cleanup.py` | [tests/test_tool_cleanup.py](/home/ajou/yigyu/3/guitar_learning/tests/test_tool_cleanup.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_tool_migration.py` | [tests/test_tool_migration.py](/home/ajou/yigyu/3/guitar_learning/tests/test_tool_migration.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_train_parallel.py` | [tests/test_train_parallel.py](/home/ajou/yigyu/3/guitar_learning/tests/test_train_parallel.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_training_environment.py` | [tests/test_training_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_training_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_training_log_io.py` | [tests/test_training_log_io.py](/home/ajou/yigyu/3/guitar_learning/tests/test_training_log_io.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_training_logging_integration.py` | [tests/test_training_logging_integration.py](/home/ajou/yigyu/3/guitar_learning/tests/test_training_logging_integration.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_training_metrics.py` | [tests/test_training_metrics.py](/home/ajou/yigyu/3/guitar_learning/tests/test_training_metrics.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_training_runner_logging.py` | [tests/test_training_runner_logging.py](/home/ajou/yigyu/3/guitar_learning/tests/test_training_runner_logging.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_capture.py` | [tests/test_transition_capture.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_capture.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_contact_teacher.py` | [tests/test_transition_contact_teacher.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_contact_teacher.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_environment.py` | [tests/test_transition_environment.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_environment.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_learning.py` | [tests/test_transition_learning.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_learning.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_metrics.py` | [tests/test_transition_metrics.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_metrics.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_probe.py` | [tests/test_transition_probe.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_probe.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_probe_contact.py` | [tests/test_transition_probe_contact.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_probe_contact.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_refinement_integration.py` | [tests/test_transition_refinement_integration.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_refinement_integration.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_refinement_learning.py` | [tests/test_transition_refinement_learning.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_refinement_learning.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_refinement_reward.py` | [tests/test_transition_refinement_reward.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_refinement_reward.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_refinement_runtime_v2.py` | [tests/test_transition_refinement_runtime_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_refinement_runtime_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_refinement_serialization_v2.py` | [tests/test_transition_refinement_serialization_v2.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_refinement_serialization_v2.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_refinement_sweep.py` | [tests/test_transition_refinement_sweep.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_refinement_sweep.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_solver.py` | [tests/test_transition_solver.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_solver.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_task.py` | [tests/test_transition_task.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_task.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_teacher.py` | [tests/test_transition_teacher.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_teacher.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_teacher_proof.py` | [tests/test_transition_teacher_proof.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_teacher_proof.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_train.py` | [tests/test_transition_train.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_train.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_transition_transfer.py` | [tests/test_transition_transfer.py](/home/ajou/yigyu/3/guitar_learning/tests/test_transition_transfer.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_validation.py` | [tests/test_validation.py](/home/ajou/yigyu/3/guitar_learning/tests/test_validation.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `tests/test_whole_body_control.py` | [tests/test_whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/tests/test_whole_body_control.py) | 회귀 검사 — 동작·입력·안전·checkpoint 검증 유지 |
| `timing/__init__.py` | [timing/__init__.py](/home/ajou/yigyu/3/guitar_learning/timing/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `timing/evaluate_timing.py` | [tool/evaluation/evaluate_timing.py](/home/ajou/yigyu/3/guitar_learning/tool/evaluation/evaluate_timing.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `timing/timing_curriculum.py` | [timing/timing_curriculum.py](/home/ajou/yigyu/3/guitar_learning/timing/timing_curriculum.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `timing/timing_demonstration.py` | [tool/demonstration/timing_demonstration.py](/home/ajou/yigyu/3/guitar_learning/tool/demonstration/timing_demonstration.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `timing/timing_environment.py` | [timing/timing_environment.py](/home/ajou/yigyu/3/guitar_learning/timing/timing_environment.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `timing/timing_transfer.py` | [timing/timing_transfer.py](/home/ajou/yigyu/3/guitar_learning/timing/timing_transfer.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `timing/train_timing.py` | [tool/training/train_timing.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_timing.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `timing/train_timing_v2.py` | [tool/training/train_timing_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_timing_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/__init__.py` | [tool/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/_rendering.py` | [tool/_rendering.py](/home/ajou/yigyu/3/guitar_learning/tool/_rendering.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/_strike_goal_compiler.py` | [tool/_strike_goal_compiler.py](/home/ajou/yigyu/3/guitar_learning/tool/_strike_goal_compiler.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/_strike_goals.py` | [tool/_strike_goals.py](/home/ajou/yigyu/3/guitar_learning/tool/_strike_goals.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/audit_musical_quality_v2.py` | [tool/audit_musical_quality_v2.py](/home/ajou/yigyu/3/guitar_learning/tool/audit_musical_quality_v2.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/audit_strike_goal_quality.py` | [tool/audit_strike_goal_quality.py](/home/ajou/yigyu/3/guitar_learning/tool/audit_strike_goal_quality.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/build_fret_training_data.py` | [tool/build_fret_training_data.py](/home/ajou/yigyu/3/guitar_learning/tool/build_fret_training_data.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/build_strike_plan.py` | [tool/build_strike_plan.py](/home/ajou/yigyu/3/guitar_learning/tool/build_strike_plan.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/build_strike_training_data.py` | [tool/build_strike_training_data.py](/home/ajou/yigyu/3/guitar_learning/tool/build_strike_training_data.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/recover_training_log.py` | [tool/recover_training_log.py](/home/ajou/yigyu/3/guitar_learning/tool/recover_training_log.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/register_song_bundle.py` | [tool/register_song_bundle.py](/home/ajou/yigyu/3/guitar_learning/tool/register_song_bundle.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/render_pick_grip_v1.py` | [tool/render_pick_grip_v1.py](/home/ajou/yigyu/3/guitar_learning/tool/render_pick_grip_v1.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/render_timeline.py` | [tool/render_timeline.py](/home/ajou/yigyu/3/guitar_learning/tool/render_timeline.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/render_timing_video_v1.py` | [tool/render_timing_video_v1.py](/home/ajou/yigyu/3/guitar_learning/tool/render_timing_video_v1.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/run_fretting_probe_v3.py` | [tool/run_fretting_probe_v3.py](/home/ajou/yigyu/3/guitar_learning/tool/run_fretting_probe_v3.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/song_bundles.py` | [tool/song_bundles.py](/home/ajou/yigyu/3/guitar_learning/tool/song_bundles.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `tool/validate.py` | [tool/validate.py](/home/ajou/yigyu/3/guitar_learning/tool/validate.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `train.py` | [train.py](/home/ajou/yigyu/3/guitar_learning/train.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `train_parallel.py` | [training/runner.py](/home/ajou/yigyu/3/guitar_learning/training/runner.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/__init__.py` | [training/__init__.py](/home/ajou/yigyu/3/guitar_learning/training/__init__.py) | 공용 패키지 — 현재 import 경계 유지 |
| `training/monitoring.py` | [training/monitoring.py](/home/ajou/yigyu/3/guitar_learning/training/monitoring.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/parallel.py` | [training/parallel.py](/home/ajou/yigyu/3/guitar_learning/training/parallel.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/persistent_audit.py` | [training/persistent_audit.py](/home/ajou/yigyu/3/guitar_learning/training/persistent_audit.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/persistent_parallel.py` | [training/persistent_parallel.py](/home/ajou/yigyu/3/guitar_learning/training/persistent_parallel.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/policy.py` | [training/policy.py](/home/ajou/yigyu/3/guitar_learning/training/policy.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/ppo.py` | [training/ppo.py](/home/ajou/yigyu/3/guitar_learning/training/ppo.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/ppo_diagnostics.py` | [training/ppo_diagnostics.py](/home/ajou/yigyu/3/guitar_learning/training/ppo_diagnostics.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/recording.py` | [training/recording.py](/home/ajou/yigyu/3/guitar_learning/training/recording.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/rollout.py` | [tool/validation/rollout.py](/home/ajou/yigyu/3/guitar_learning/tool/validation/rollout.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `training/start.py` | [training/start.py](/home/ajou/yigyu/3/guitar_learning/training/start.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/train_persistent.py` | [tool/training/train_persistent.py](/home/ajou/yigyu/3/guitar_learning/tool/training/train_persistent.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `training/training_log_format.py` | [training/training_log_format.py](/home/ajou/yigyu/3/guitar_learning/training/training_log_format.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/training_log_io.py` | [training/training_log_io.py](/home/ajou/yigyu/3/guitar_learning/training/training_log_io.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/training_metrics.py` | [training/training_metrics.py](/home/ajou/yigyu/3/guitar_learning/training/training_metrics.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `training/training_reports.py` | [training/training_reports.py](/home/ajou/yigyu/3/guitar_learning/training/training_reports.py) | 공용 학습 기반 — 현재 환경·정책·수집·기록·명시적 이전에서 공유 |
| `transition/__init__.py` | [tool/experiments/transition/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/capture.py` | [tool/experiments/transition/capture.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/capture.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/contact_teacher.py` | [tool/experiments/transition/contact_teacher.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/contact_teacher.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/environment.py` | [tool/experiments/transition/environment.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/environment.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/evaluate.py` | [tool/experiments/transition/evaluate.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/evaluate.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/learning.py` | [tool/experiments/transition/learning.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/learning.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/metrics.py` | [tool/experiments/transition/metrics.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/metrics.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/policy.py` | [tool/experiments/transition/policy.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/policy.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/probe.py` | [tool/experiments/transition/probe.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/probe.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/probe_contact.py` | [tool/experiments/transition/probe_contact.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/probe_contact.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/solver.py` | [tool/experiments/transition/solver.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/solver.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/task.py` | [tool/experiments/transition/task.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/task.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/teacher.py` | [tool/experiments/transition/teacher.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/teacher.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/train.py` | [tool/experiments/transition/train.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/train.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/train_with_teacher_proof.py` | [tool/experiments/transition/train_with_teacher_proof.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/train_with_teacher_proof.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/transfer.py` | [tool/experiments/transition/transfer.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/transfer.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition/worker.py` | [tool/experiments/transition/worker.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition/worker.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/__init__.py` | [tool/experiments/transition_refinement/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/capture.py` | [tool/experiments/transition_refinement/capture.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/capture.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/environment.py` | [tool/experiments/transition_refinement/environment.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/environment.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/evidence.py` | [tool/experiments/transition_refinement/evidence.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/evidence.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/policy.py` | [tool/experiments/transition_refinement/policy.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/policy.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/ppo.py` | [tool/experiments/transition_refinement/ppo.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/ppo.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/reward.py` | [tool/experiments/transition_refinement/reward.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/reward.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/run.py` | [tool/experiments/transition_refinement/run.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/run.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/settings.py` | [tool/experiments/transition_refinement/settings.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/settings.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/sweep.py` | [tool/experiments/transition_refinement/sweep.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/sweep.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement/worker.py` | [tool/experiments/transition_refinement/worker.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement/worker.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/__init__.py` | [tool/experiments/transition_refinement_runtime_v2/__init__.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/__init__.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/activation.py` | [tool/experiments/transition_refinement_runtime_v2/activation.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/activation.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/audit.py` | [tool/experiments/transition_refinement_runtime_v2/audit.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/audit.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/evidence.py` | [tool/experiments/transition_refinement_runtime_v2/evidence.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/evidence.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/observer.py` | [tool/experiments/transition_refinement_runtime_v2/observer.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/observer.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/run.py` | [tool/experiments/transition_refinement_runtime_v2/run.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/run.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/serialization.py` | [tool/experiments/transition_refinement_runtime_v2/serialization.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/serialization.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |
| `transition_refinement_runtime_v2/worker.py` | [tool/experiments/transition_refinement_runtime_v2/worker.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/worker.py) | 선택 실행 도구 — 기본 손별 PPO에서 사용하지 않는 전문 실행/지원 코드 |

## 구문이 같은 함수 후보

8줄 이상 최상위 함수 중 AST가 같은 후보 묶음은 2개다. 파일 전역값·의존 구현·호출 계약이 다를 수 있어 중복 기능으로 단정하거나 합치지 않았다. 이번 변경에서 분리한 공용4함수는 보관 원문과 AST가 정확히 같다. 후보별 파일/함수/위치는 file_review.json에 남겼다.
