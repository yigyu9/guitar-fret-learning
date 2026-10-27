# 5초 baseline 기록과 카메라 contact sheet

baseline은 요청된 초기값으로 새 native 환경을 만들어 240 Hz에서 1200 physics steps(5.0초)를 완료했다. 초기 81개 관절각, 기타 world 위치·xyzw 회전·속도, PD와 절대 strap 길이는 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/initial_values.json)에 저장되어 있다. 실행 설정은 [attempt.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/attempt.json), 완료 보고서는 [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/report.json)이다.

아래 contact sheet는 실제 Isaac Gym native camera로 저장된 frame 6장을 결합했다. 위 행은 전신, 아래 행은 손 근접 장면이며 열은 t=0, 2.5, 5.0초(physics step 0, 600, 1200)다. 실행은 CPU PhysX와 graphics device 0을 사용했고 이미지는 Isaac Gym native camera에서 기록했다. 그래픽 backend identity는 별도 확인하지 않았다. 장면은 MuJoCo replay나 사후 자세 렌더가 아니다. 합성 과정은 저장 이미지에만 적용했고 물리 실행을 추가하지 않았다.

![실제 Gym 카메라 baseline의 전신 및 손 장면: 0, 2.5, 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts/recorded_trial_5s_contact_sheet.png)

전신과 손 영상은 각각 [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/whole_body.mp4), [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/hands.mp4)다. 두 파일 모두 1280×720, 30fps, 151 frame이며 컨테이너 재생시간은 5.033333초다. 151번째 frame은 실제 시뮬레이션 t=5.0초 endpoint다. 이는 5.033초 물리 실행을 뜻하지 않는다. 기록된 전신/손 frame은 [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/capture.json)의 frame별 시각·physics step 및 이미지 SHA와 대조했다.

| 저장 관측 | 값 |
|---|---:|
| native 실행 | 정상 완료 1회, 1200 physics steps |
| 최대 기타 위치 오차 | 82.047438 mm |
| 최대 기타 회전 오차 | 10.831454° |
| 종료 기타 위치 오차 | 80.435305 mm |
| 종료 기타 회전 오차 | 10.563577° |
| 종료 손 추적점 오차 | 100.687667 mm |

5초 기록은 자세·기타 안정화 성공을 뜻하지 않으며 실제 오차가 남았다. `palm_up_proxy_violations=0`도 다른 제약이나 접촉 지지 성공을 인증하지 않는다. 별도의 [controlled-stop 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/stop_execution.json)은 1 init/28 steps에서 의도한 KeyboardInterrupt와 exit 1, partial frame을 확인했으며 위 1200-step baseline과 합치지 않는다. `native_initialization_attempts`는 생성 시도 횟수이고 `native_initializations`는 constructor 완료 횟수다. 실패한 시도에서 실제 `create_sim` 호출 여부는 이 횟수만으로 단정할 수 없다. [8개 검증 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/verification.json)을 참조한다. 이후 controls/contact 시각 순서 검사를 보완했으며 기존 checks·counts·summary·video 메타데이터는 그대로다([보완 이력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/verification_refinement.json)).

초기 입력 외 원자료는 [states.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/states.jsonl), [trace.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/trace.jsonl), [contacts.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/contacts.jsonl), [controls.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/controls.jsonl), [tasks.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/tasks.jsonl)다. 처음 24 physics steps는 이전 PD v2 1× 조건의 다섯 저장 배열과 exact다. 영상 생성 및 contact sheet는 별도 재생 단계가 아니다.

이후 상수 목표 trial의 기본 진입점은 [`run_recorded_trial`](/home/ajou/yigyu/3/stability_adapter_2/run_recorded_trial.py:18)이며 같은 실제 카메라 기록 helper인 [`GymTrialRecording`](/home/ajou/yigyu/3/stability_adapter_2/gym_trial_recording.py:11)을 재사용해 후속 feedback 실행도 기록할 수 있다. 이번 contact sheet 생성은 그 helper를 호출하지 않고 저장된 PNG만 사용했다.

재생성 명령은 출력 경로가 비어 있어야 한다: `python /home/ajou/yigyu/3/stability_adapter_2/make_recorded_trial_contact_sheet.py --out-dir /tmp/recorded_trial_5s_sheet_reproduction`. [실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/contact_sheet_execution.json)는 명령, 종료 코드 및 입력/출력 SHA를 기록한다. [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts/contact_sheet_manifest.json)은 producer와 여섯 프레임을 포함한 입력/출력 SHA를 기록한다.


레이아웃 초안 producer 보존 기록도 구분한다. `producer_before_layout_fix/`의 기존 파일은 수정 후 작업본( SHA `5f490b…`)이며 초안 manifest가 요구한 원 producer는 아니다. 초기 producer 내용을 복원한 [정확 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/producer_before_layout_fix_exact/make_recorded_trial_contact_sheet.py)은 초안 manifest의 기대 SHA `d7408a1c13be55133e4ec95333b2f6f48cbf2d662dc3cff9670d2918a8bff4f2`와 일치한다. 기존 작업본, manifest, 이미지 모두 그대로 보존했다.
