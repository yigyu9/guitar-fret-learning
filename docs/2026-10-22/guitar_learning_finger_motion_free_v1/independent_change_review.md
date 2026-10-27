# 독립 변경 검수

**요약 판정: 문제없음.** 사용자 요청에 해당하는 GPU 왼손의 손가락 움직임 비용 제거에서 새 결함이나 계약 회귀를 발견하지 않았다.

- **Critical:** 없음.
- **Warning:** 이번 변경에 대한 지적 없음.
- **Suggestion:** 없음.

보관된 변경 전9파일과 현재의 구현3개·테스트2개·현재 문서4개를 직접 비교했다. 프로젝트 전체의 누적 git diff를 이번 변경으로 취급하지 않았다. 구현이나 테스트는 수정하지 않았으며 이 검수 기록만 작성했다.

## 코드 근거

- `guitar_learning/gpu/finger_reward.py:84`: 추종 품질은 `exp(-distance/.02)*(1+candidate)`다. 명령 크기·실제 표면속도·요청속도·속도 오차 항이 모두 제거됐다. 기존 선택기와 준비창·유효성·손가락 분모 및 적분률은 유지된다. `velocity`와 `actions`는 호출 형태 검사에만 남는다.
- `guitar_learning/gpu/environment.py:800`: 새 뺄셈 텐서의 LH21 채널만0으로 만들어 엄지를 포함한 손가락 명령 변화를 감점에서 제외한다. 원래39축 분모와 나머지 축당 계수 `.01/60`은 유지된다. 입력 행동을 덮어쓰지 않는다. 오른손은 마스킹 분기를 지나지 않아 원식과 같다.
- `guitar_learning/gpu/environment.py:179`: GPU 왼손 보상v7 및 비용 제외 범위를 계약에 명시한다. `guitar_learning/song/curriculum_runtime.py:15`가 v7을 기존 GPU 표면 단계 경로로 인식하므로3331값 상태가 유지된다. `guitar_learning/training/ppo.py:235`의 기존 identity 검사가 모델·optimizer·RNG 변경 전에 구계약을 거부한다.
- `guitar_learning/gpu/environment.py:727`: 거리 추종과 별도로 자세 보상을 유지한다. `:768`의 관절속도50rad/s 초과 안전종료 및 기타 이탈·지지 안전 비용도 유지된다. 이는 일반적인 손가락 움직임 억제 항과 다르다. 제어/PD/범위/PPO 및 CPU 경로에는 이번 변경이 없다.
- `guitar_learning/tests/test_gpu_press_learning.py:124`: 명령 변경·반전에도 동일한 기하에서 손가락 감점이0임을 검사한다. `:136`은 팔·손목/오른손의 원래39분모를, `:259`는 같은v7 복원과 실제 봉인v6의 보상 의미를 사용한 구계약 거부 및 거부 전후 불변성을 검사한다.

## 직접 실행 및 기록 확인

- 별도 CPU 프로세스로 변경된 두 모듈을 직접 실행했다. `test_gpu_finger_reward`23개, `test_gpu_press_learning`11개 모두 통과했다. CUDA는 숨겼으며 native/GPU/GL/학습을 실행하지 않았다.
- 독립 수학 fixture에서도 네 손가락의 서로 다른 거리·후보 상태와 양음 명령/표면속도를 조합해 추종률이 해석값 `1.5726401368693024`와 일치하고 움직임 입력에 불변임을 확인했다.
- `tested_source_manifest.json`의 현재436개 SHA와 AST를 직접 확인했다. 변경 Python은 정확히5개이며 각 `source_overlay` 사본이 현재 원문과 일치한다. 보관9개 원문의 SHA도 모두 직접 확인했다.
- root의 회귀 로그/`cpu_regression.json`/`validation_summary.json`은 추가107개 중106개 통과, 합계141개 중140개 통과를 정확히 보고한다. 전체 검사 통과라고 주장하지 않는다.
- 남은 실패는 수정하지 않은 `guitar_learning/tests/test_left_curriculum_runtime.py:218`의 기본 왼손 차원512 가정이다. 실제 기본값544이며 coordinator 호출 전 첫 assert에서 실패한다. `existing_failure.json`의 이전v6와 동일한 test/start.py SHA 및 변경 전 coordinator 대조 로그에서 같은 실패를 확인했다. 이번 변경이 새로 만든 실패로 분류하지 않는다.
- 이전v6 결과 manifest SHA `d80cb90248e0a7ce80d694879229a69dd5f946dc06e0cdaa67e156624c65757c`를 직접 확인했다. `preservation.json`은 root가 이전 정규1511파일·3,379,865,794bytes 전체를 재검산한 증거다. 검수자가 이 전체 대용량 검산을 반복 실행한 것은 아니다.
- 현재 문서4개와 새 README가 보상v7·이전v6 strict resume 거부·자세/안전 유지·실제GPU 미실행을 구분한다. 새 학습의 성능이나 자연스러움 개선을 검증한 것으로 표현하지 않는다.

## 검수 대상 SHA

| 파일 | SHA256 |
|---|---|
| `guitar_learning/gpu/finger_reward.py` | `0d00ad8968e0448d63d03739a58a7c697a0ea85a0cc30ee9088c6a627f01a5eb` |
| `guitar_learning/gpu/environment.py` | `34746ed4847bd703141b9f7ef422a4348dd6faf503f1c1ba6faf89a64f67fe78` |
| `guitar_learning/song/curriculum_runtime.py` | `1cb446a78184a202c50cec8d90c4050b77abf22c5ff69da83b9643e6345a1a44` |
| `guitar_learning/tests/test_gpu_finger_reward.py` | `98c9481119704b0c1c8d28e2d586312b1e14a992febe178eb0ef7c386e82bba5` |
| `guitar_learning/tests/test_gpu_press_learning.py` | `76f0e934662b9dd30716d6cf4f1a8a286154aae5521abd8bda510d4c4fd31738` |
| `guitar_learning/README.md` | `53f0f3af4cf8dcf312e6a6baf1918958392c29876f77ee08340c30e19fe39c4b` |
| `guitar_learning/AGENTS.md` | `0ecba43d9abae262bea7ecab35f1b2616b8cf9be5df3b315cdb059cd31e3afd1` |
| `CURRENT_STATUS.md` | `c214fedec7a59b3d8607cf2c67b7b458fd1373e67900a12c28de50810c790a9e` |
| `docs/2026-10-26/learning_flow/README.md` | `45b98548f8bde8a0831e919cbd13b454de33e84fd07db8cf0b66efcab76ba5c4` |
| 새 phase `README.md` | `da8e7088a86d20d241dc9e03f74ee27749e90bd1acada496db65e65fd36e58f9` |

검수 기록 작성 이후 모든 쓰기를 종료한다. 최종 새 phase 봉인 생성은 root가 수행한다.
