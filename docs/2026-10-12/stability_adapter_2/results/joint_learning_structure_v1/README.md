# 상체 공동 학습 구조 1차 구현 결과

739D 관측에서 상체81관절을 제어하는 공동 Actor/Critic과 PPO 학습기를 구현했다. CPU22검사, 실제 Isaac Gym5초 평균 정책 실행, 같은 체크포인트를 불러온5초 탐색 실행을 확인했다. **실환경 보상·학습은 아직 비활성이다.** CPU 합성 보상의 parameter 갱신을 기타 연주 학습으로 해석하지 않는다. 기존 stability_adapter와 공용 파일을 보존했다.

## 구현한 구조

![공동 정책 구조 — native 학습 비활성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/artifacts/joint_learning_architecture_v4.png)

- Actor: 739→512(ELU)→256(ELU)→mean81. 관측과 독립인 학습 가능한 log_std81과 tanh Gaussian을 사용한다. Critic은 별도739→512→256→value1이다.
- 제어: body9/head6/arms24/fingers42 전부 정책 출력이다. body 목표는 기준±5°와 모델 범위의 교집합이다. 목표 변화율은 body0.1/head0.5/arm1.0/finger1.5rad/s이며 실제 관절 상태를 덮어쓰지 않는다. PD/하체·root 고정/자유 기타/스트랩OFF는 기존 검증 장면을 유지한다.
- 초기 평균: preload1.0 절대 목표. tanh 행동0이 이 지지 목표, ±1이 각 관절 범위 끝에 대응한다. 누적 보정이 아니다. 경계 anchor에서 한쪽 목표가 평평해지는 채널을 manifest에 공개한다.
- PPO: tanh 이전 표본 latent와 원 action/logprob/value를 보존한다. 실행 목표를 역변환해 likelihood를 바꾸지 않는다. scalar GAE는 terminated bootstrap0, truncated 실제 마지막 관측 bootstrap, 양쪽 경계 trace 차단을 적용한다. 미종료 곡은 다음 rollout으로 이어진다.
- 할인: 60Hz에서 gamma=2^(-1/600), lambda=2^(-1/60). 할인 half-life10초, trace half-life1초인 시작 설정이며 최적값 인증이 아니다. clipping0.2, Adam3e-4, 4epoch, minibatch128, value weight0.5, entropy weight0.001(관절 평균), gradient norm1, target KL0.02다.
- RMS는 rollout/PPO 중 고정하고 update 끝에 갱신한다. 체크포인트는 model/RMS/Adam/RNG/설정/ABI를 저장하며 기존 파일을 덮어쓰지 않는다. 복원은 새 물리 episode에서 시작한다. v1 학습·RNG backend는 CPU이며 GPU vector 환경은 구현하지 않았다.

관측739은 물리548+공동 음악28+현재 event의 crossing timing6/required6+방향2/시작·끝까지 시간2+실제 압현 셀132+pick detector 상태6/재무장 진행6+직전 G-local pick tip3이다. 현재 기타에 대한 손 위치/속도와 실제 압현·타현 측정을 사용하며 기존 정책 행동이나 미래 실제 성공 결과를 입력하지 않는다. 이번 ABI는 detector/보상 최종 인증 전 버전이며 reward ledger 관측을 추가하면 새 계약이 필요하다.

Fret035000/Strike010000 checkpoint는 측정 view 설정과 원본 계약 검증에 사용했다. 두 기존 Actor의 추론 호출은0이며, 새739→81 Actor에 가중치를 이식하지 않았다. 기존 source skill의 평가 done도 새 정책 진단을 중단시키지 않는다. 원본 기하 압현 셀과 보수적240Hz crossing bracket이 최종 distal pad/연속 압현 인증을 대체하지 않는다.

## 실제 환경 결과

![평균 정책의 실제 Isaac Gym 0·2·5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/artifacts/mean_policy_native_montage_v2.png)

윗줄은 전신, 아랫줄은 양손이다. 초록색이 왼손, 분홍색이 오른손, 파란색이 기타다. 저장된 실제 Isaac Gym camera frame을 사용했다. 손과 기타가 약간 움직이며, 초기 지지 목표를 재현하는 정책의 진단이다. 접촉 인증이나 압현·타현 성공을 이미지로 판정하지 않는다.

| 조건 | 최대 초기 대비 이동 | 최대 회전 | 실제 body 관절각 최대 변화 | 완료 event / 공동 성공 |
|---|---:|---:|---:|---:|
| 새 정책 평균 행동 | 46.306mm | 9.179° | 2.164° | 9 / 0 |
| 같은 checkpoint 복원 + 작은 탐색 | 57.114mm | 9.960° | 2.398° | 9 / 0 |

평균 행동의301개 전체 trace는 이전 preload100_v2와 exact 일치했다. 탐색에서는81개 모든 채널의 표본이0이 아니었고 요청 목표 anchor 대비 RMS는 body0.000594/head0.005257/arm0.030504/finger0.017157rad였다. 이는 탐색 요청의 분포이며 실제 움직임은 위 표처럼 별도로 측정했다. 무학습 Actor가 음악을 잘 수행한다는 결과는 아니다.

두 실행 모두 초기 실제 상태 exact, 고정 root·하체, 60/240Hz 순서,739D 유한 관측,81D 원 표본/목표 변환, 목표 한계/변화율, 금지 API0, 입력 SHA 유지가 확인됐다. 각1200physics/300control/151녹화frame이며 총2400physics와4영상이다. t=0과5초 frame을 포함해 각 MP4 재생 길이는5.033초다. 신경망은2초 준비 때도 작동하지만 음악 평가는 음수 score time에서 비활성이다. 이번 영상은 미학습 정책의5초 진단이며 곡 종료까지 연주 성공을 시험한 영상이 아니다.

평균 정책 전신:

![새 정책 평균 행동 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_mean_v2/media/whole_body.mp4)

체크포인트 복원·작은 탐색 전신:

![체크포인트 복원·탐색 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_sample_resume_v2/media/whole_body.mp4)

양손 영상: [평균 행동](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_mean_v2/media/hands.mp4), [복원·탐색](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_sample_resume_v2/media/hands.mp4).

## 검증과 재현

[CPU22검사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/cpu_verification_v1.json:1) · [원 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/cpu_tests_v1.log:1) · [native 수치·계약 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_verification_v1.json:1). CPU 검사는 초기 평균·끝점/경계 codec, 포화 latent likelihood, 실제 Actor/Critic 갱신, 종료/절단 bootstrap, 원 행동 보존, stale rollout 거절, 저장/복원/덮어쓰기 거절, 재무장0/7frame과 rollout 연속성을 포함한다.

CPU검사: `/home/ajou/miniconda3/envs/rl38/bin/python -m unittest stability_adapter_2.test_joint_learning_v1 -v`. native entry: [run_joint_policy_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:17). 이전 실행과 같은 rl38/Isaac Gym 경로·CPU PhysX·software Vulkan 설정에서 `--out <새 절대 경로>`로 실행한다. `--checkpoint <initial_policy.pt> --stochastic`은 같은 ABI를 확인한 뒤 작은 탐색을 한다. `[각 native 폴더]/attempt.json`의 전체 입력 SHA와 초기값/ABI/controls/trace/music 기록, media/capture.json·report.json을 보존했다. 체크포인트 자체는 ABI 소스 fingerprint에서 제외해 복원의 자가참조를 피하고, 실제 관측/모델/물리 의존 소스·자산은 봉인한다.

## 실환경 학습 전 남은 단계

현재 `--train`은 물리 장면이나 출력 폴더를 만들기 전에 오류로 막는다. SO(3) 허용집합 거리, 연속 유지/dropout ledger, fatal 이후 고정 일정 정산과 할인 연결, distal press pad 계약, reward v5의 실제 측정/mask가 미완료이기 때문이다. 임의 보상0으로 대체하지 않았다. [실제 차단 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_training_gate_v2.log:1).

후속은 음악 이벤트의 유지·release·dropout과 물리 실패를 구분하는 reward v5를 실제 관측에 연결하는 것이다. 검증된 환경은 `require_training_ready()`, `reset()→obs`, `step(action)→final_obs,reward,terminated,truncated,info`를 만족해야 한다. 지금 native Scene의 관측·제어 연결에는 scalar reward/종료 정산이 아직 없으며, 이를 완료한 뒤 이번 `JointPPO.collect→update→save`를 사용한다. 첫 curriculum에서도81관절을 출력하며 Fret/Strike/안정화의 공동 성공을 평가한다.

검수에서 발견한 재무장 메모리와 rollout 연결은 소비 전에 수정했다. runner v1은 syntax 소비 이력으로 보존하고 실제 native entry는 v2다. 이미지 v1의 잘린 몽타주, v2의 분포 표기, v3의 글자 넘침은 보존하며 최종 구조도v4/몽타주v2를 사용한다. 변경 줄 번호는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/CHANGED_FILES.md:1)에 기록한다.
