# 동시 음악 actor runtime 진단

## 범위와 실행 집계

이 phase는 정적 preload 진단을 선택한 뒤, 동결된 Fret·Strike actor를 한 native 장면에서 연결해 runtime 경로와 초기 동작을 확인했다. 최종 정책 observation ABI, 음악 성능, 안정성을 인증하거나 학습을 수행한 결과는 아니다.

| 실행 | 조건 | 새 physics step | 결과 |
|---|---|---:|---|
| `run_dual_music_v2` | preload 0.5 | 1200 | 5초 정적 진단 완료 |
| `run_dual_music_v2` | preload 1.0 | 1200 | 5초 정적 진단 완료; pair에 선택 |
| `run_dual_music_v3` | pair 1.0 | 0 | scene 생성 전 active `PATH`에 Ninja가 없어 import 실패 |
| `run_dual_music_v4` | pair 1.0 | 924 | 2초 준비 후 PLAY 1.85초; 첫 source terminal에서 종료 |
| `run_dual_music_v5` | pair 1.0 + Strike goal/grip SHA guard | 924 | guard 검사 후 같은 pair 결과 재현 |

총 네 native 실행(두 preload와 두 pair), 4248 physics step이다. 저장 neutral 기준 run은 재사용했으며 새 실행 수에 포함하지 않았다. v3 import 실패는 별도 0-step 시도다. v4/v5 pair는 각각 111개 동시 actor tick을 기록해 pair tick 합계는 222다. 구 schema의 이전 analyzer 시도도 `human_body_names` 누락으로 physics 전에 실패했고, 수정 결과는 v2 analyzer에 있다. 두 실패는 [early_attempts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/early_attempts.json)에 보존했다. 학습 업데이트는 0회다. 이 단계의 실행 기록은 [execution_summary_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v2.json)이다.

## 정적 preload 비교와 선택

세 preload 조건은 같은 실제 초기 물리 상태를 사용한다. 기타는 자유 상태이고 humanoid root·하체는 고정, self-collision은 켜며 strap은 끈다. factor는 시작 자세를 만들기 위한 정적 목표 보정 크기다. 팔 보정은 ±0.15 rad, 손가락 보정은 ±0.05 rad로 제한하고 몸통·머리 보정은 0이다. PD gain과 rate bound는 동일하다. `median_error_rad`는 정적 preload 목표를 만드는 데 쓰인 실제 오차 통계이며, 각도 state를 바꾸어 재실행한 값이 아니다. 두 preload run의 시작 실제 q와 기타 p/q는 기준 초기값과 exact match한다.

| 초기 조건 | 기타 최대 변위 (mm) | 종료 변위 (mm) | 최대 geodesic 회전 (°) | 종료 회전 (°) | core position-box 최대 초과 (mm) | 초과 표본 |
|---|---:|---:|---:|---:|---:|---:|
| Neutral, factor 0 | 111.790 | 111.787 | 19.486 | 19.485 | 34.335 | 288/301 |
| Preload 0.5 | 75.331 | 75.330 | 13.910 | 12.294 | 11.262 | 273/301 |
| **Preload 1.0 · 선택** | **46.306** | **46.298** | **9.179** | **7.626** | **0.000** | **0/301** |

factor 1.0은 세 조건 중 core actor-root position-box의 최대 초과가 0 mm였고, 중립 기준보다 초기 기타 변위와 회전도 작아서 pair 초기값으로 선택했다. 이 선택은 완전한 SO(3) 허용영역 검사나 지지 접촉 인증이 아니며 안정성 성공도 아니다. 분석 상태는 `stability_success=false`, `training_ready=false`다.

### Preload 그림

![세 조건의 native whole-body 초기 자세 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_comparison_v2.png)

![60 Hz trace에서 측정한 기타 위치 변위와 회전 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_curves_v2.png)

몽타주는 native Isaac Gym camera frame을 사용한다. 곡선의 위치는 초기 actor 위치로부터의 변위, 회전은 초기 quaternion 대비 shortest-path geodesic 각도다. core position-box 통계는 회전 허용영역 검사를 포함하지 않는다. 원자료·조건 설명은 [preload 결과 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_artifact_note_v2.md)에 있다.

### Preload native 영상

![Preload 0.5 whole-body native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload050_v2/media/whole_body.mp4)

![Preload 1.0 whole-body native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload100_v2/media/whole_body.mp4)

## 동결 actor pair와 runtime 결과

Pair는 Fret checkpoint `fret_035000.pt`와 Strike checkpoint `strike_010000.pt`를 연결했다. 두 checkpoint는 곡 `02_Jazz1-200-B_solo`의 canonical 42-event 자료를 사용하고 score clock은 60 Hz다. 각 control 주기에서 단일 physical owner가 81-joint action/target을 한 번 제출하고 physics를 4 step 진행했다. 2초 준비 뒤 동결 actor 둘이 111 tick을 함께 수행했다. Fret/Strike 각 30개 action channel을 사용하고 나머지 21개 joint target은 선택된 preload로 유지했다. 기록된 1299차원 값은 후보 관측 로그이며 최종 Actor observation ABI가 아니다. 81-action을 받는 최종 관측 정의와 512→256 정책은 구현·학습되지 않았다.

| Pair 측정 | v4와 SHA guard v5 결과 |
|---|---:|
| Physics / control step | 924 / 231 |
| 준비 / PLAY | 2.00 s / 1.85 s |
| 동시 동결 actor tick | 111 per run |
| 기타 최대 초기 변위 | 403.605 mm |
| 기타 최대 초기 회전 | 63.992° |
| Core position-box 최대 초과 norm | 261.953 mm |
| 해결된 joint event / 성공 | 4 / 0 |
| Joint crossing | 1회, `wrong_string` |
| Strike source target hit / miss | 0 / 4회 |

첫 terminal은 Fret의 기타 G-local 손목 X safety 경계였다. 물리시간 3.85초, score PLAY 1.85초에 기록된 값은 `0.34882652759552 m`다. 이는 위치 기반 safety bound이며 손목 각도 제한이 아니다. Fret은 종료했고 Strike는 완료되지 않았으며 곡도 완주되지 않았다. Pair에서 기타 최대 이동은 403.605 mm, 최대 회전 차이는 63.992°였고 position-box 최대 초과 norm은 261.953 mm다. 회전 수치는 전체 SO(3) 허용영역 판정을 의미하지 않는다. 정적 preload 개선은 이 동결 source PLAY에서 유지되지 않았다.

### 이벤트 측정 범위

음악 이벤트 진단은 240 Hz 기하학적 fret press, 가장 높은 fret, 240 Hz 표본의 진단 pickup-zone, 8 physics-frame 재arm, 0.1초 dwell, 보수적 endpoint bracket을 사용했다. subframe pressure 측정, 실제 물리 접촉 증명 또는 인증된 detector가 아니다. Strike source per-control 기록은 target hit 0회와 miss 4회다. 별도 joint-event 진단은 crossing 1회(`wrong_string`), 성공 0회다. 두 통계를 섞어 해석하지 않는다.

Fret source history 재구성 최대 오차는 `0.66246 rad`이고 PLAY 중에는 `0.63746 rad`였으며 146 control sample을 clip했다. Strike 최대 오차는 `8.94e-8 rad`이고 clipped sample은 없었다. 상속한 source ABI는 native COM linear velocity를 복사하고 물리 adapter는 해당 속도를 body-origin 기준으로 변환한다. 따라서 Fret의 clipped reconstruction과 Strike의 작은 오차는 source ABI 동등성을 입증하지 않는다.

### Pair native frame 몽타주

![Pair v4의 native whole-body 및 hands camera 시작·2초·종료 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_montage_v2.png)

여섯 패널은 pair100_v4 실행에서 저장한 실제 Isaac Gym camera PNG다. 행은 capture frame 00000/00060/00116, physics step 0/480/924 및 물리시간 0/2/3.85초이고, 열은 전신과 손 camera다. 몽타주에는 한글 label과 여백만 추가했으며 접촉·프렛·press 표시를 그리지 않았다. v5도 924 step에서 같은 source wrist terminal을 재현했고 v4와 controls, trace, initial values, music physics samples, joint crossing/events, observation manifest가 exact 일치한다. 그림은 원본 보존을 위해 v4 frame을 사용한다. 이 비교는 별도의 학습 결과가 아니다.

### Pair native 영상

![Pair v4 whole-body native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/whole_body.mp4)

![Pair v4 hands native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/hands.mp4)

![Pair v5 whole-body native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v5/media/whole_body.mp4)

![Pair v5 hands native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v5/media/hands.mp4)

두 pair 실행의 영상은 각각 30 fps, 117 frame, encoded 3.9초이며 physics 종료는 3.85초다. Fret safety terminal에서 끝나므로 곡 완주 영상이 아니다.

## Guard 재실행과 남은 작업

v4 runtime은 실행 직전 Strike goal/grip 입력의 기대 SHA를 guard하지 않았다. 저장 입력 파일들은 의도한 checkpoint/source와 일치하므로 v4 측정 자체는 그 파일들에 귀속된다. 추가한 v5는 추론 전에 문서·입력·view contract를 guard하고 CPU counterexample 검사를 통과한 뒤 동일 pair를 다시 실행했다. [contract guard 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json)은 v4/v5의 controls, trace, initial values, music samples, joint events/crossings 및 observation manifest의 exact 일치와 같은 종료를 기록한다. 새 guard는 이 계약 확인을 보완했으며 pair 실패를 개선하거나 학습을 추가하지 않았다.

Reward v4/fatal ledger, 최종 Actor observation ABI, PPO/GPU 학습, 학습 업데이트는 완료되지 않았다. 남은 gate는 source action을 실제 support pose에 표현할 수 있는지 확인하고, 기타 joint control과 전체 SO(3) 허용영역을 검증하고, sustain/dropout/fatal ledger와 reward v4 안전·시간 계약을 확정한 다음 최종 ABI/PPO pilot을 수행하는 것이다. 이번 결과에는 pair 조기 종료, Strike miss 4회, 성공 joint event 0회가 그대로 남는다.

## 재현·보존 기록

첫 pair artifact v1 시도는 렌더 전 검증에서 `videos.json`의 `nb_read_frames`가 문자열 `"117"`인 점과 producer의 정수 비교가 맞지 않아 중단됐다. 이 실패는 image/manifest를 만들지 않았고 native 호출·physics step도 0이었다. 당시 producer snapshot과 실행 SHA seal은 저장하지 않았다. [pair_artifact_attempt_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_artifact_attempt_v1.json)은 tool 원문에서 복원한 [실패 producer 재구성본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/producer_pair_artifact_v1_failed_reconstructed.py)의 SHA를 실행 당시 봉인 SHA로 표시하지 않는다. 이후 정정된 v1 producer 결과는 [v1 montage](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_montage_v1.png) 및 [v1 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_artifact_manifest_v1.json)에 보존되어 있다. 수정 후 별도 v2 source/output을 만들었다.

현재 몽타주용 producer와 manifest는 [producer_pair_artifact_v2.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/producer_pair_artifact_v2.py), [pair_montage_v2.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_montage_v2.png), [pair_artifact_manifest_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_artifact_manifest_v2.json)이다. producer는 저장된 여섯 pair frame만 렌더하고, 명시한 분석·native metadata·선택 frame·preload 그림·기존 v1 artifact·글꼴의 SHA를 실행 전후 대조한다. v2 생성은 native call 0회, physics step 0회였다. 몽타주는 1328×1329 pixel이며 frame 원자료와 시각 대조를 마쳤다.

핵심 원자료는 [execution_summary_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v2.json), [preload_analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_analysis_v2.json), [pair_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_analysis_v1.json), [pair v4 initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/initial_values.json), [pair v4 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/report.json), [v4 source contract](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/source_contract.json), [v5 contract guard verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json)에 보존했다. 영어 초안은 [README_draft_en_v1.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README_draft_en_v1.md)에 보존했다.

독립 검수자는 [final_review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/final_review.md)를 작성할 예정이다. root는 최종 보존 대조 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/final_verification.json), [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/artifact_inventory.json), [source_final/manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/source_final/manifest.json)을 작성할 예정이다. 이 artifact producer는 이들 검수·감사 파일을 작성하지 않는다. Guard 후속 범위는 [PROVENANCE_NOTE_V2.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE_V2.md)에 기록됐다.
