# Tab2Body 이식성 수정·검증 — 2026-10-29

구현과 가능한 검증을 완료했다. GPU 종단 실행 검증은 이 PC의 NVIDIA 드라이버 부재로 완료하지 못했다.
현행 대상은 GPU 왼손 finger-skill v3·J33·LH21 position 직접 제어다. 기존 미커밋 변경과 실험 결과를 보존했다.

## 수정 파일과 이유

전체 파일 목록과 구조화 결과는 [summary.json](summary.json)에 있다.

| 파일 | 수정 내용 |
| --- | --- |
| `guitar_learning/native/paths.py` | 역사 식별자와 현재 경로를 분리하고 외부 링크 해석 전에 내부 입력으로 매핑 |
| `runtime/prepared_reset_v1.py`, `assets/native_provenance.json` | 내부 준비 입력 사용, 현재 manifest 상대 경로, 원 SHA 유지 |
| `historical_inputs.py`, `core/dependency_inputs.py` | 이동한 프로젝트에서도 원 역사 경로 키와 CAS 근거 검증 유지 |
| `gpu/scene.py`, `gpu/contact.py` | compound 기타와 접촉 계약의 옛 docs 참조를 내부 파일로 해석. 기하·물리 계산 변경 없음 |
| `song/finger_phrases.py` | 실제 곡·시간·구간 선택은 유지하고 catalog SHA의 현재 경로만 정규화 |
| `portability.py` | `project://` 식별자, 설정 snapshot/SHA, 역사 필드 보존, 보고서 상대 참조 |
| `training/finger_skill_runner.py`, `training/ppo.py`, `tool/demonstration/render_finger_skill.py` | 이동 가능한 신규 strict checkpoint·재개·평가·영상 경로, 기존 저장본 명확한 거부 |
| `scripts/tab2body.py`, `scripts/probe_isaacgym.py` | PC 로컬 Isaac Gym native·빌드 캐시, 버전/전체 SHA 검증, 실제120step probe |
| `scripts/smoke_portability.py`, `tool/validation/portable_inputs.py` | 다른 루트 복사·다른 CWD 짧은 실행·필수 입력 감사 |
| `scripts/environment.rl38.yml`, `scripts/README.md`, `docs/PORTABILITY.md` | 설치 조건·복사·SSHFS·학습·재개·평가 명령 |
| README·CURRENT_STATUS·PROJECT_CONTEXT·guitar_learning/README | 현행 이식 방법과 실제 검증 한계 반영 |
| `.gitignore`, `.githooks/check-staged-files.py`, `.githooks/README.md` | 새 scripts 디렉토리를 기존 저장소 파일 정책에 포함 |
| 관련 tests | 실제 다른 루트의 환경·정책·catalog·sampler·입력 검증과 캐시 동시 생성·변조 거부 검사 |

## 내부로 포함한 원본 입력

기존 docs의 절대 외부 심볼릭 링크는 역사 기록으로 보존하고 현행 코드만 아래 일반 파일을 사용한다.
새 입력은 원본 바이트를 그대로 복사했으며 정해진 SHA와 비교했다.

| 내부 경로 (`guitar_learning/assets/prepared_reset_v1/`) | 바이트 | SHA256 |
| --- | ---: | --- |
| `initial_values.json` | 111750 | `5b84e68b085ef63133bb1834c65d25c5413584d36a7998b31c9253beaac75e1b` |
| `prepared.json` | 96474 | `49631241132d303e36ae02cc40a3a6e035f68d3dd54982f8a4a2c3b50e0970db` |
| `inputs_before.json` | 219931 | `4cc689037ec0a8bd67b4e2cdca005aee1d479d82f3b957e889bae6e5a40f1588` |

합계428155바이트다. 과거 외부 실험 전체를 복사하지 않았다.
현재 manifest193개 SHA와 준비 입력110개(원시 설정4개·XML/mesh106개)를 검증했다.
기본 곡67음과 compound 자산까지 포함한 [필수 입력207개 검사](input_audit_final.json)는 외부·누락 입력0이다.
모델 XML의 mesh 이외 file 참조가 없는 것도 확인했다.

## 실제 검증 결과

| 검증 | 결과·근거 |
| --- | --- |
| 관련 CPU 검사 | **125개 통과**, [최종 로그](cpu_tests_final.log) |
| 원래 프로젝트 접근을 막은 복사본 | 준비 자세·모델·mesh·CAS·pin 검증 통과. 원래 `/home/ajou/yigyu/3`와 `/media/ajou` 열기를 audit hook으로 거부 |
| 실제 환경·정책의 경로 이동 | CPU에서 실제 기본 곡·FingerSkillEnvironment·FingerSkillPolicy·catalog·sampler로 구성하여 다른 루트 strict 복원 통과 |
| 독립 CPU checkpoint 검사 | 임시 원본 루트·설정 파일·부모 저장본 삭제 후 model/Adam 복원 통과. 소스·자산·설정·제어 변조 및 구형 계약 거부 |
| 다른 CWD·공백 경로 | `/tmp/Tab2Body portability final/project with spaces`의 최소 실행 복사본에서 로컬 runtime 준비와207입력 감사 통과. [단계 보고서](relocated_smoke_final/report.json) |
| Isaac Gym native | 로컬 ext4 캐시의 `gym_38.so` 실제 import 통과 |
| GymTorch 빌드 | 로컬 Torch extension C++ 빌드·import 통과. [명령·출력](runtime_validation.json) |
| 로컬 캐시 | 실제 파일 SHA·vendor 버전 변경·변조·동시 생성·링크 검사 통과. 원격 mount 거부는 `fuse.sshfs` 모의 검사 |
| GPU PhysX·CUDA tensor120step | **미완료**. probe가 실제 native import 후 `CUDA is unavailable`로 종료 |
| 최소 GPU 학습 | **시도 후 실패**. 소수2환경/H2/1update가 CUDA 요구 검사에서 중단. [명령](gpu_train_attempt.json), [실제 오류](gpu_train_attempt.log) |
| GPU 저장 후 strict resume·별도 평가·영상 | GPU 저장본이 생성되지 않아 **미실행**. CPU strict 복원 검증과 구분 |
| 실제 SSHFS 마운트 종단 실행 | 사용 가능한 마운트가 없어 **미검증** |

`nvidia-smi`는 종료코드9, `torch.cuda.is_available()`는False였고 `/dev/nvidia*`가 없었다.
드라이버를 임의로 변경하거나 CPU 실행을 GPU 검증으로 대체하지 않았다.
환경 파일을 새 Conda 환경으로 설치하는 검사는 수행하지 않았으며 기존 rl38의 실제 버전을 기록했다.
기존 역사 전체 gate 검사1개는 현행 입력과 무관한 과거 `left_bc_v1/actor_initialization.pt` 부재로 실패한다.
이 결과를 복원·재생성하거나 검증을 완화하지 않았다.

## 연구 조건·기존 자료 보존

[작업 시작 SHA](research_conditions_before.json)와 [완료 SHA](research_conditions_after.json)를 비교했다.
control·환경 보상/종료·policy·rollout은 시작 바이트와 동일하다.
scene/contact의 변경은 파일 resolver 연결뿐이며, 구간 목록의 숫자·표본 선택·시간 계산도 바꾸지 않았다.
PPO 변경은 저장·로드 identity 정규화에 한정하고 기존 작업 트리의 PPO 변경을 보존했다.
역사 원본 SHA·source manifest·곡 번들의 출처 기록은 유지한다.

수정 전 바이트·SHA는 `guitar_learning/archive/20261029_before_portable_inputs_v1/`,
`20261029_before_portable_checkpoints_v1/`, `20261029_before_portability_scene_v1/`,
`20261029_before_portability_docs_v1/`에 보존했다. 이 디렉토리는 기존 archive 제외 정책대로 로컬 보관이다.

## 재현·남은 조건

[명령 전체](../../PORTABILITY.md)와 [실행기 안내](../../../scripts/README.md)를 따른다.
새 checkpoint는 resume.v4이며, 이전 v3 절대 경로·누적 제어 저장본을 자동 이전하지 않는다.
GPU가 정상인 PC에서 `scripts/smoke_portability.py --out NEW --cache-root LOCAL --relocate-to NEW_COPY --render`로
남은 GPU 학습·재개·평가·영상 구동을 확인해야 한다. 출력은 항상 새 디렉토리를 사용한다.
원본과 복사본이 모두 남아 있어도 복사본 검증은 원본 입력 접근 없이 수행했다.
실제 두 PC는 각자 로컬 Python·cache·가시 GPU 구성을 사용하고 서로 다른 출력에 기록한다.
학습 중 공유 소스·자산을 수정하지 않는다. SSHFS가 hard link 저장을 지원하지 않으면 출력을 로컬에 둔다.
