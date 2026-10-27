# 누적 손가락 제어 — GPU 전 독립 검수

요약 판정: **문제없음**. 활성 제어/진단 변경에 GPU 실행을 막는 정적 결함을 찾지 못했다. 실제 물리 응답, 손가락 압현, 학습 향상 및 장시간 안정성은 아직 이 검수의 증거가 아니다.

검수 범위는 `archive/20261021_before_incremental_fingers_v1/guitar_learning` 대비 변경4개와 신설 진단 테스트1개다. 활성 소스는 수정하지 않았다. 새로운 probe/evaluator/renderer/비교 도구는 이 판정에 포함하지 않으며 별도 검수한다.

- `gpu/control.py:379`: 왼손21축만 이전 clamp된 목표에 행동×4/60을 더한다. 목표만 누적하므로 포화 중 숨겨진 적분 상태가 없고, 0명령은 목표 유지, 반대명령은 다음 제어tick에 반영된다. 최종 native clamp·속도한계·zero축 보호가 유지된다. 실제 q의 즉시 정지/반전은 뜻하지 않는다.
- `gpu/control.py:194`: 왼손만 v3/누적 action codec을 계약에 포함한다. `GpuPool`이 이를 정책 architecture의 native backend 계약으로 전달하므로 동일 차원의 구계약 checkpoint도 strict 비교 대상이다. 실제 구모델 거부/새모델 복원은 후속 native 검증 사항이다.
- `gpu/environment.py:471`: 진단13×N×21 double 배열은 크기가 고정이다. q/target 범위는 t0+60Hz endpoint, 추종오차/행동은 n tick, 변화/반대부호는 n−1 pair로 분모가 분리되어 있다. 240Hz 극값이나 실제 접촉한계로 과장하지 않는다. partial reset은 해당 row만 초기화하며 H32 보상창 reset은 누적을 지우지 않는다.
- 기존 reward/observation/안전 판정 변경 없음. 오른손 분기는 새 진단/경계 요구를 사용하지 않으며 controller의 기존 v2 계산을 유지한다. CPU 경로 파일 변경 없음.

독립 실행: CUDA_VISIBLE_DEVICES를 비우고 rl38 Python3.8에서 `test_gpu_control` 11개와 `test_gpu_finger_motion_diagnostics` 7개, 총18개 PASS(3.695초). 64tick 누적·0명령 상태외란·비대칭 포화 반전·partial reset·왼손 다른축/오른손 기존식 정확 비교·진단 분모/학습출력 불변을 포함한다. GPU/native/GL은 실행하지 않았다.

검수 당시 SHA256:

| 파일 | SHA256 |
|---|---|
| gpu/control.py | c7df2924a05ab205530f66fe8c8a1a4cea268bf02e0e14757c03289e68f60281 |
| gpu/environment.py | 75149b953ae2affcae21b9fb19c9bd1535b575da011c3cd3faa9c039bdca4b07 |
| tests/test_gpu_control.py | 6b39d931ad1aae6aa28a6c0e4f1c82bd0b8585e07e2e80bb36a1731be3e1ac1d |
| tests/test_gpu_environment.py | 65bbb938c40bb294cc032f4cca3230dae3a419241e96bde9b4c31f8ac3766ec2 |
| tests/test_gpu_finger_motion_diagnostics.py | fff6fd0b21e6c05a4563d67fa238f7b63aabdff7b05652ea8e346ae7f6ef6676 |

Critical/Warning: 없음. 위 범위에 한해 native 검증 진행 가능하며, native 성공으로 간주하는 판정은 아니다.

## 별도 도구 준비 검수

이후 `evaluate_checkpoints.py`, `render_video.py`, `compare_evaluations.py`, `test_video_workflow.py`도 정적으로 읽었다. fresh 초기0/최종 회수 strict 복원, 저장된 curriculum 유지, 환경별 첫 종료 원장과 reset 이전 자세 캡처, 마지막 불필요 reset 생략, close 전 동기화, 원래106 body의 실제 world pose 재생, all/safe/matched-safe 분모 구분에서 blocker를 찾지 못했다. 이 라운드에서는 해당 도구 실행·영상 생성·GPU/GL을 수행하지 않았다.

소유한 `probe_fingers.py`와 `test_probe_fingers.py`는 새 진단 도구로 작성했다. 기본 N4에서21축×4부호/크기=84 trial, 각30push+10zero+30reverse, 물리종료가 없다면 총1470 control tick/5880 physics step이다. 시작 pose를 포함한 실제 q105/qd/target/action39/body106×13/로컬 및 누적 물리시계를 저장한다. 물리종료는 해당 batch에서 보존 후 중단하고 다음 batch는 명시적 새 시험으로 reset한다. no-windup은 실제 bound에서2개 이상 push endpoint를 관측하고 다음 반전을 관측한 trial만 기록한다. 미도달 한계는 인증하지 않는다.

probe의 `passed`는 제어식·전체 명령일정·물리종료 없음·입력/종료 무결성 범위다. 실제 q의 방향별 push/reverse/hold 변화·range·추종오차는 별도 실측 필드이며 range 하나로 명령방향이나 해부학적 굽힘을 인증하지 않는다. 실제 물리 정지/반전은 관성과 접촉을 받으므로 즉시 목표 변경과 동일시하지 않는다.

독립 CPU5검사 PASS(0.018초): N1..8 네 명령 커버리지, 양쪽 clamp/hold/반전, partial/미포화 미인증, 구 absolute 복귀/숨겨진 windup 회귀 거부, 잘못된 mapping/clock/nonfinite/비명령축 이동 거부. Python3.8 AST와 별도 프로세스 도구 import 후 NumPy/Torch/Isaac 미로딩도 PASS. 실제 probe는 root가 단독 GPU에서 실행해야 한다.

- probe SHA256: `01b2fb23a1c0918b8c58855883c742cf1a9de1c24816106f8414e292378292f6`
- probe test SHA256: `8fde0482f586747cfc7fa6d04c0098a36ff3b11ba440a150c74ec4777109228d`
