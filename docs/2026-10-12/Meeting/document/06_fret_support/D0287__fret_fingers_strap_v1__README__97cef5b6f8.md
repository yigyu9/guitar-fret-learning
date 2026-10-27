# 준비 팔 목표 유지 + Fret 손가락·고정 길이 스트랩 결과

## 결과

직전 팔 목표 유지 시험과 같은 시작 상태, 2초 준비, Fret 손가락 21축, 준비 때 제출한 왼팔 9축 목표 유지를 사용하고, 기존 BASE에서 가져온 수동 스트랩을 첫 물리 step부터 켰다. 기타 pose는 고정하지 않았다. 스트랩 포함 native v2는 892 physics step, 103 actor 제어, 3.716667초에 원본 `index finger_back` 조건으로 끝났다. 목표 완료는 false, press 성공률은 0%, sustain은 0/4였다.

| 시각 | 스트랩 OFF: G 이동 / 회전 변화 | 스트랩 ON: G 이동 / 회전 변화 |
|---:|---:|---:|
| 2.000000 s | 51.094033 mm / 6.495028° | 51.602588 mm / 6.557605° |
| 2.766667 s | 72.742681 mm / 9.854978° | 66.212062 mm / 8.924387° |
| 3.700000 s | 24.472860 mm / 47.569225° | 51.306036 mm / 49.441034° |

스트랩 실행 전체의 최대 G 이동/회전 변화는 69.082173 mm / 51.500005°, 종료값은 68.455837 mm / 51.500005°였다. 공통 시각 2.766667초에는 위치와 회전이 조금 개선됐지만, 3.7초에는 두 지표가 스트랩 OFF보다 나빴다. 스트랩 OFF 실행은 12.916667초까지 계속되어 실행 전체 최대값은 같은 길이 조건의 비교가 아니다. 현재 기록은 일관된 기타 안정화나 연주 성공을 보이지 않는다.

## 스트랩 경로와 힘

물리 법칙은 기존 수동 cable law를 그대로 사용했다. rest length는 상속한 **1.1018469719600776 m**이며, 길이·관절각·gain은 조정하지 않았다. Native 초기 13점 경로 길이는 1.073577334 m로 rest length보다 짧았다. 이 법칙은 당기는 힘만 내므로 초기 케이블 장력은 0 N이다. 첫 양의 힘은 0.170833초, 마지막 양의 힘은 0.195833초에 계산됐고 총 7 step이었다. 계산된 최대 cable tension은 32.365446 N이다. 준비가 끝난 뒤부터 종료까지 양의 힘은 없었고 마지막 제출값은 0 N이었다. 최종 물리 step 바로 전 측정 경로 길이는 0.967968522 m였다.

이 숫자는 저장된 native body 위치·속도에서 수동 cable 법칙으로 계산해 제출한 tension/force이며 force sensor 측정치나 접촉 측정치가 아니다. 화면의 주황색 경로는 13개의 route 점을 잇는 실제 경로 계산 결과를 겹쳐 그린 선이다. 선은 힘이 0 N일 때도 보이며, 곧게 보인다고 팽팽하거나 지속 지지 중이라는 뜻은 아니다. 이는 cloth/strap 변형 시뮬레이션이 아니다. 이번 고정 rest length가 지속 지지를 제공하지 못했다는 결과를 모든 strap 구성의 불가능성으로 일반화하지 않으며, 길이 최적화도 수행하지 않았다.

## 실행 범위와 한계

체크포인트 `fret_035000.pt` (관측/행동/value 420/30/6), 기타·인체 초기 상태, 왼팔 9축 제출 목표 유지, 손가락 제어, 하체/root 고정, 다른 관절의 기존 hold, 원본 실패 종료를 직전 [팔 목표 유지 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md:1)와 맞췄다. 초기 native 상태는 strap OFF 기준과 exact 일치했다. 바뀐 물리 변수는 상속된 수동 스트랩 활성화다. 별도로 native camera의 실제 body pose로 계산한 13점 경로를 영상 위에 표시했다. 기타 목표 pose 추적, 기타 고정, 손 부착, 종료 후 hold, 학습 갱신은 없다. 체크포인트 자산·구현 차이와 source profile 목표 범위/native XML 물리 한계의 적용 범위는 이전 [Fret native 전이 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/README.md:1)과 같으며, 이번 결과는 원본 학습환경 평가가 아니다.

기록 완료 native v2(운지 실패)는 CPU PhysX와 Isaac Gym native camera/lavapipe 환경에서 실행했다. GPU 물리와의 동등성은 주장하지 않는다. contact/penetration이나 실제 strap cloth를 인증하는 자료도 아니다.

첫 native 시도는 exit 139로 중단됐다. Fret 실행 전 약 1.9초까지의 58개 frame을 보존했지만, 정확한 fault 시점과 원인은 확인하지 못했다. 보존된 입력 사후 비교에서 변경은 관찰되지 않았다. 같은 물리·source를 사용한 native v2 재시도는 `faulthandler` 옵션만 달리해 종료까지 실행됐다. 이 한 번의 재시도로 최초 crash 원인이 해결됐거나 재현성이 확보됐다고 볼 수는 없다. 두 시도의 자료를 구분해 보존했다.

## 기록 완료 native v2(운지 실패) 영상

전신 영상은 113 frame, 30 fps, 3.766667초다. 양손 영상은 같은 시간 구간을 담는다.

![기록 완료 native v2(운지 실패) 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/whole_body.mp4)

![기록 완료 native v2(운지 실패) 양손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/hands.mp4)

## 실제 화면과 camera 원본

### 시작 — t=0.000초, physics step 0

![native route overlay 시작 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/frames/whole_body/00000.png)

초기 slack에서 route 선은 보여도 힘은 0 N이다. 캡처에는 route의 표시만 더해져 있다.

### PREP 종료·Fret handoff — t=2.000초, physics step 480

![native route overlay handoff 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/frames/whole_body/00060.png)
![같은 시각 native camera 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/raw/frames/whole_body/00060.png)

왼팔 9축 목표 유지 아래 Fret 제어가 시작되는 실제 장면이다. 위 이미지는 13점 경로 표시를 얹은 캡처이고, 아래 이미지는 같은 camera 시각의 원본이다. 경로 선은 실제 케이블 재질 렌더가 아니다.

### 원본 source terminal — t=3.716667초, physics step 892

![native route overlay terminal 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/frames/whole_body/00112.png)
![같은 시각 native 양손 화면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/frames/hands/00112.png)
![같은 시각 native camera 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/raw/frames/whole_body/00112.png)

실패 표식은 검지 `finger_back`이다. 손바닥과 손가락이 아래쪽에 보이지만 그림만으로 프렛 press나 기타 접촉 성공을 판정하지 않는다. 주황색 route가 보여도 terminal last applied tension은 0 N이다.

## 원자료와 검증

- 기록 완료 native v2(운지 실패): [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/report.json:1), [terminal info](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/terminal_info.json:1), [strap force 계산/제출 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/strap_forces.json:1), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/trace.json:1), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/controls.json:1).
- 비교와 독립 재계산: [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/summary.json:1) (26 checks), [공통 시각별 측정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/time_samples.json:1), [analysis 입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/analysis/inputs.json:1).
- Native 및 별도 보존 검사: [native runtime report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/report.json:1) (24 runtime checks), [recording audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/recording_audit.json:1), [source preservation](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/source_preservation.json:1). 실행 입력 1,156개는 native v2 실행 전후 동일하다.
- 첫 실패 시도: [crash audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_crash_audit.json:1), [부분 녹화 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/crash_review.md:1), [retry plan](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/retry_plan.json:1).
- camera 및 route: [overlay capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/capture.json:1), [raw camera manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/native_v2/data/images/raw/capture.json:1), [실제 경로·native 캡처 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/recording_audit.json:1).
- 네 video copy와 SHA 기록: [video index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_fret_strap.md:1), [collection manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_COLLECTION_fret_strap.json:1).

후속 스트랩 길이 비교가 필요하면 현재 native route와 길이 변화를 기준으로 별도 변수를 정해 검토한다. 이번 실행의 한 고정 길이 결과만으로 길이 최적값을 정하지 않는다.
