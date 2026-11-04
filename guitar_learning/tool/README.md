# 현재 보조 도구

새 압현 학습은 [V5 기본 실행](../README.md)을 따른다. 이 디렉토리는 V5 명시적 실행·C조합 연결, 타현 연구, 입력 준비·검사, 평가·영상·운영 도구를 모은다.

| 목적 | 현재 진입점·안내 |
| --- | --- |
| 일반 압현 학습 | `guitar_learning.train` → [실행 안내](../README.md) |
| V5 명시적 학습·평가·영상 | `tool.experiments.compact_press_v5`의 `train`, `evaluate`, `render` |
| C1~C6 압현 | `tool.experiments.press_sequence` → [전용 시각·실행](../../docs/2026-11-09/압현_v5_합성목표연결_v1/README.md) |
| V5 기본 평가·영상 | `tool.evaluation.evaluate_finger_skill`, `tool.demonstration.render_finger_skill` |
| 타현27 | `tool.experiments.right27` → [안내](experiments/right27/README.md) |
| 피크 타현·교차 시간 비교 | `tool.experiments.right_strike`, `right_strike_io_v2`, `right_strike_protocol_v3` → [연구 안내](../../docs/2026-11-03/타현실험/README.md) |
| 전신37 지지 학습 | `tool.training.train_whole_body` → [구현·실행](../docs/WHOLE_BODY_TRAINING.md) |
| 기존 오른손 재현 | `tool.training.train_legacy --hand right`; 왼손 학습은 거부하고 V5 사용 |
| 압현 합성 입력 준비·검사 | `tool.prepare_press_targets`; 기존 등록 번들은 덮어쓰지 않고 검사 |
| 곡·타현 입력 | `register_song_bundle`, `build_fret_training_data`, `build_strike_training_data`, `build_strike_plan`, `audit_strike_goal_quality` |
| 로그 점검·복구 | `inspect_gpu_training_log`, `recover_training_log`; 검증된 prefix를 새 경로에 기록 |
| 제어·접촉·자산 검사 | `validation/`; 각 도구의 실제 입력과 전용 연구 계약을 확인 |

`hand_contact_probe.py`는 현재 영상용 native 그래픽·입력 경로·인코더 종료 API만 제공한다. `press_acquisition.py`는 목표각을 직접 행동으로 바꾸는 공용 역변환만 제공한다. 두 파일은 과거 압현 실험 CLI가 아니다. `validation/wrist_position.py`는 독립 FK 검증에 필요한 손목 Jacobian·유한 목표 보정 수학을 보존한다.

이전 ablation·natural_press·song_finger_progress·short_finger_learning과 V5 이전 compact 압현 실행기는 제거했다. 과정·결과는 [간단한 이력](../../docs/history/press_before_v5.md), 원래 경로·SHA와 제거 범위는 [정리 기록](../../docs/maintenance/v5_project_cleanup_20261104/)에 남긴다. 과거 docs의 봉인 runtime을 현행 코드에서 import하지 않는다.

현재 파일 이름이나 로그에 `finger_skill`·`v3`·`v4`가 남을 수 있다. 공유 측정·직렬화 계약의 이름이며, 그 이름만으로 구형 압현 실행 경로라고 판단하지 않는다. 타현·전신과 공유하는 API는 유지한다.
