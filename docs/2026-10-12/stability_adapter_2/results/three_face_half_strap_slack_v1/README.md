# 세 면 half 자세의 스트랩 여유 비교

2026-10-08. 새 native 실행 2회가 각 5.0초/1200 physics step 완료했다(신규 초기화 2회, 총 2400 step). 두 조건은 저장된 half 자세의 실제 초기 81관절각과 기존 절대 81관절 PD 목표가 같다. trial 입력에서 바뀐 값은 고정 스트랩 rest length뿐이다. 기준 곡선은 이전 `three_face_support_loss_v1`의 저장 자료이며 새 실행으로 세지 않는다.

Humanoid root와 하체는 고정하고, 몸통 9개 PD 목표를 유지했으며, 양팔·손의 최종 66제어 관절을 유지했다. 기타는 자유롭게 두었다. 기타 고정, 손 부착, pose 덮어쓰기, 기타 목표 방향의 인위적 힘은 사용하지 않았다. 두 조건은 fresh 초기 source/FK admission을 통과했지만, 이 검사는 cooked PhysX 간극이나 기타 면 접촉을 인증하지 않는다.

## 초기값과 공통 목표

| 조건 | 절대 LA rest length | 초기 route length | 초기 slack |
|---|---:|---:|---:|
| Half slack | 1.0943400885564325 m | 1.0868332051527874 m | 7.506883 mm |
| Zero slack | 1.0868332051527874 m | 1.0868332051527874 m | 0 mm |

두 실행은 실제 초기 81관절각, 절대 81관절 목표, 기타 초기 위치와 속도가 같다. 공통 기타 목표는 world 위치 `[-0.1972053649442413, 0.11878119221286644, 0.8277786273204872] m`, xyzw 회전 `[-0.3412600918621295, 0.5816458777723966, 0.5857788413284049, 0.44954729631550555]`다. [half_slack 초기값](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/initial_values.json>)과 [zero_slack 초기값](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/initial_values.json>)에는 81개 실제 각도, 81개 PD 목표, 기타 pose/속도와 적용 strap 길이가 저장돼 있다.

## 측정 비교

| 조건 | 첫 0.1초 최대 위치 / 회전 오차 | 5초 최대 위치 / 회전 오차 | 종료 위치 / 회전 오차 |
|---|---:|---:|---:|
| 저장된 support-loss 기준 | 4.718710 mm / 0.936405° | 25.229274 mm / 7.770624° | 21.912505 mm / 7.091529° |
| Half slack | 4.718710 mm / 0.936405° | 30.696048 mm / 7.727219° | 30.695007 mm / 7.622948° |
| Zero slack | 3.567710 mm / 0.511048° | 32.861798 mm / 7.103582° | 32.860232 mm / 7.103303° |

위치 오차는 `analysis.json`의 `curves.*.guitar_position_error_mm`, 회전 오차는 `curves.*.guitar_rotation_error_deg`다. 회전은 world SO(3) 오차다. 실선은 새 두 조건, 회색 점선은 기존 저장 기준이다. 두 조건 모두 기준보다 최대 회전 오차는 작지만, 최대/종료 위치 오차와 종료 회전 오차가 크다. 어느 길이도 안정 자세 또는 복원 자세로 채택하지 않았다.

Passive strap law 그래프는 `curves.*.strap_submitted_time_s` 및 `strap_submitted_tension_n`의 1200개 구간 시작 시각 `step/240 s`를 표시한다. 이 값은 제출된 법칙으로 계산한 N이며 native force sensor 값이 아니다. Half slack 최대/종료는 12.894182/1.063010 N, zero slack은 5.119047/2.677263 N이다. 법칙 재구성 오차는 0이며 300 N cap에 도달한 step은 없다.

Body positive raw-lambda 표본에서 palm은 두 조건 모두 step 1200까지 기록됐다. Thumb3의 양의 raw-lambda 기록은 half slack에서 step 35, zero slack에서 step 96에서 끝났다. 이는 body 단위의 표본이며 기타 넥 면 접촉, N 단위 힘, substep 연속 접촉 또는 지속적인 세 면 지지를 인증하지 않는다. 전체 자세 복원 및 연주 안정화는 미완료다.

## 그림과 실제 영상

### 그림 118 — 기타 오차, 제출 strap law, body raw-lambda 기록 시각

![Half-slack과 zero-slack 기타 위치·회전 오차, 계산된 strap-law 출력, 양의 body raw-lambda 표본 시각](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/three_face_half_strap_slack_curves.png)

위쪽 두 패널은 240 Hz 저장 표본의 위치 오차(mm)와 world SO(3) 회전 오차(degree)를 보여준다. 왼쪽 아래는 1200개 interval-start 시점의 제출 passive strap law다. 오른쪽 아래는 LH thumb3, index3, middle3, palm의 양의 raw-lambda 표본을 post-step 시각 `step/240 s`에 표시한다. 표식은 표본이며 힘 크기나 연속 접촉 구간이 아니다. 기존 점선 기준은 기타 오차 패널에만 있다.

### 그림 119 — 실제 native hands 카메라의 시작과 종료 장면

![Half-slack과 zero-slack의 실제 hands 카메라 step 0 및 step 1200 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/three_face_half_strap_slack_hands.png)

2×2 montage의 열은 half slack / zero slack, 행은 t=0.0초·step 0 / t=5.0초·step 1200이다. 실제 Isaac Gym 카메라 이미지이며 합성 접촉 표식은 없다.

각 실제 native 영상은 30 fps·151 frame으로, 0–5초를 담고 5.033333초로 인코딩됐다.

- [Half-slack 손 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/hands.mp4>)
- [Half-slack 전신 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/whole_body.mp4>)
- [Zero-slack 손 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/hands.mp4>)
- [Zero-slack 전신 영상](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/whole_body.mp4>)

Half-slack 손 영상:

![실제 native hands 카메라 영상, half slack](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/hands.mp4)

## 산출물 출처와 다음 진단

Canonical PNG는 위 v2 산출물이다. v1 producer도 성공(exit 0, 0.8542346449103206초, native 0)했으며 결과와 실행 기록을 [artifact_layout_v1](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_layout_v1/>)에 보존했다. 시각 검토에서 v1 timeline legend가 후기 palm 표식과 겹쳐, v2에서 legend를 오른쪽 아래로 옮기고 새 출력 경로에 저장했다. v2는 exit 0, 0.8706656479043886초, native 0으로 완료했다. 물리 실행을 반복하지 않았다.

분석 결과 파일 `analysis.json` SHA-256은 `35e2054f93c863d299437842a79addcadafa40b6ec24f9dfceeaa232c87746e8`이다. 별도로 분석기는 입력 11321개의 SHA와 7개 분석 계약을 기록했고, 각 계약과 입력 closure는 확인됐다. 그림 생성은 producer·폰트·brief·analysis·선택 native 입력으로 이루어진 별도 14개 입력 SHA closure를 기록하며 PNG 2개를 만든다. [v2 실행 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_execution_v2.json>)과 [v2 14-input/2-output manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/artifact_manifest.json>)를 참조한다.

다음 미실행 진단은 [native contact-feature 위치 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_NATIVE_FEATURE_MAP_PLAN.md:1)이다. 저장 접촉 feature와 요청 기타 영역을 대조하고 frame/time 불확실성을 기록한 뒤, 후속 손 위치 또는 목표 보정 근거를 정한다. 이 계획은 controller, gain 또는 관절각을 미리 추가하지 않는다. 기존 runner인 [run_seed2_support_warmstart.py:18](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_support_warmstart.py:18)는 수정하지 않았다.

[변경 파일 색인](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/CHANGED_FILES.md>) · [독립 검수 상태](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/review.md>) · [검증 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/final_verification.json>)
