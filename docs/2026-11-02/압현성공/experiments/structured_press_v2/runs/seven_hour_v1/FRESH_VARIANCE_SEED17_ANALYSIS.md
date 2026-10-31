# 독립 seed17 fresh 분산 비교

원본 seed17 fresh full33와 목표4축 sigma0.1배만 변경한100+100회를 비교한다. A 가중치 이전이 없다. 동일 적응 LR 규칙이며 실제 LR은 KL 재시도에 따라 달라질 수 있다. 초기 전체 모델과 Python/numpy/CPU/CUDA RNG, 100→200의 모델·두 Adam·업데이트·전체 RNG를 실제 파일에서 비교한다.

| 구분 | 조건 | 상태 | 분모 | 안전성공 | safe clean초 | 실패 |
|---|---|---|---:|---:|---:|---:|
| training | control_100 | completed | 512 | 30 | 1.4173 | 0 |
| training | control_200 | completed | 512 | 408 | 2.2234 | 0 |
| training | variant_100 | completed | 512 | 179 | 1.8391 | 0 |
| training | variant_200 | completed | 512 | 412 | 2.2422 | 0 |
| evaluations | control_100 | completed | 32 | 32 | 2.5000 | 0 |
| evaluations | control_200 | completed | 32 | 0 | 0.0000 | 0 |
| evaluations | variant_100 | completed | 32 | 32 | 2.5000 | 0 |
| evaluations | variant_200 | completed | 32 | 0 | 0.0000 | 0 |

## preserved_setup_attempt

`{"status": "input_pin_setup_failure", "path": "/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/seed17/100/train/report.json", "completed": false, "training_transitions": 0, "failure": {"type": "FileNotFoundError", "message": "[Errno 2] No such file or directory: '/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/seed17/100/train/J/settings.json'", "traceback": "Traceback (most recent call last):\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/training/finger_skill_runner.py\", line 643, in run\n    result = _train_phase(settings, out/'J', schedule, resume=resume, updates=settings['updates'])\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/training/finger_skill_runner.py\", line 166, in _train_phase\n    pins = _pins(settings, out, [Path(value).resolve() for value in (resume,) if value])\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/tool/experiments/variance_variant.py\", line 119, in pins\n    return original[1](current, out, list(extra)+([TRANSFER] if source else []))\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/tool/experiments/fresh_variance.py\", line 49, in pins\n    def pins(current,out,extra=()):return previous[1](current,out,list(extra)+[Path(__file__).resolve()])\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/seed17/bootstrap.py\", line 21, in pins\n    def pins(settings,out,extra=()):return original[1](settings,out,list(extra)+creation)\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/training/finger_skill_runner.py\", line 143, in _pins\n    return pin(BASELINE_CONFIG, extra=sources)\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/native/paths.py\", line 158, in pin\n    pins = {str(path.resolve()): sha(path) for path in sorted(paths)}\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/native/paths.py\", line 158, in <dictcomp>\n    pins = {str(path.resolve()): sha(path) for path in sorted(paths)}\n  File \"/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/guitar_learning/native/paths.py\", line 136, in sha\n    return hashlib.sha256(resolve_input_path(path).read_bytes()).hexdigest()\n  File \"/home/ajou/miniconda3/envs/rl38/lib/python3.8/pathlib.py\", line 1229, in read_bytes\n    with self.open(mode='rb') as f:\n  File \"/home/ajou/miniconda3/envs/rl38/lib/python3.8/pathlib.py\", line 1222, in open\n    return io.open(self, mode, buffering, encoding, errors, newline,\n  File \"/home/ajou/miniconda3/envs/rl38/lib/python3.8/pathlib.py\", line 1078, in _opener\n    return self._accessor.open(self, flags, mode)\nFileNotFoundError: [Errno 2] No such file or directory: '/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runtime/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/seed17/100/train/J/settings.json'\n"}, "model_failure": false, "included_in_model_performance": false, "original_attempt_preserved": true}`

## source_proof

`{"status": "verified", "initial_control_exact": {"model": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true}, "strict_resume_exact": {"model": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true, "actor_optimizer": true, "value_optimizer": true, "updates": true}, "source_updates": 100, "resume_initial_updates": 100}`

## settings_proof

`{"status": "verified", "only_goal4_sigma_and_identity_changed": true, "no_A_transfer": true}`

## native_audits

`{"100": {"source": "/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runs/seed17/control_initial.pt", "source_sha256": "7896b70ad8bc33e5e8b5b5fc3c8e6aa41a054576af1e3b24fce548b218c7ba97", "strict_resume": false, "exact_equal": {"model": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true}}, "200": {"source": "/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/fresh_variance_variant/runs/seed17/100/train/J/final.pt", "source_sha256": "bd504cba636060b22d780595287156e4663ff0b9ed26c5e5cc37ea414c687cbc", "strict_resume": true, "exact_equal": {"model": true, "torch_rng": true, "cuda_rng": true, "python_rng": true, "numpy_rng": true, "actor_optimizer": true, "value_optimizer": true, "updates": true}}}`

## evaluation_source_proof

`{"control_100": true, "control_200": true, "variant_100": true, "variant_200": true}`

## gate

`{"ready": true, "reasons": []}`

## interpretation

`{"100": {"success_delta": 0, "safe_clean_delta": 0.0}, "200": {"success_delta": 0, "safe_clean_delta": 0.0}}`

학습 완료 episode는 변화하는 확률 정책의 결과이고 평가는 저장 모델의 latent-mean 결정 실행 최초32환경이다. 실패를 분모에서 제외하지 않는다. 보상9항·물리 비용·LR과 원시 분모는 JSON에 있다. 원본 진단에는 시점별 trace가 있으나 variant 공식 평가에는 없으므로 공통 비교는 비할인 episode 합계이다. variant 평가에서 환경별 q/hold를 별도 저장하지 않으므로 실제32행 물리 초기상태 exact 대응을 주장하지 않는다. 동일 초기 모델/전체 RNG와 봉인된 초기화 설정 검증 범위로 한정한다. 요청각 기댓값 진단과 혼합하지 않으며 단일 검지 줄3/프렛4·seed17의 독립 재현이지 새 목표 일반화가 아니다. 생산 기본값이나 기존 최고 모델은 자동 교체하지 않는다.
