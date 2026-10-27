# 동일 절대 목표에서의 세 면 초기 자세 비교

세 조건(baseline repeat, quarter, half)은 기존 관측을 바탕으로 초기 왼쪽 33개 좌표만 바꾸어 각각 새 Isaac Gym 실행으로 5초 측정했다. endpoint 보간 실행이 아니라 정적 초기 자세 refinement다. 절대 81축 PD 목표, 나머지 48개 초기 관절각, 기타 목표, root/하체 고정, 절대 strap rest length는 유지했다. 절대 strap rest length는 세 조건 모두 1.1018469719600776 m지만, 초기 자세가 달라 strap route 길이는 baseline 1.0866096862 m, quarter 1.0867203139 m, half 1.0868332052 m였다. 따라서 route geometry나 실제 strap tension까지 고정된 비교는 아니다. 동일 손 내부 importer 제외와 비활성 thumb pad 조건은 그대로였다.

| 조건 | 첫 0.1초 최대 p/q | 5초 최대 p/q | 5초 종료 p/q | 마지막 1초 최대 p/q |
|---|---:|---:|---:|---:|
| Baseline repeat | 5.108 mm / 0.969° | 25.281 mm / 7.753° | 21.989 mm / 7.097° | 21.991 mm / 7.098° |
| Quarter | 5.108 mm / 0.969° | 25.487 mm / 7.821° | 22.176 mm / 7.142° | 22.177 mm / 7.143° |
| Half | 4.719 mm / 0.936° | 25.229 mm / 7.771° | 21.913 mm / 7.092° | 21.915 mm / 7.093° |

p는 기타 목표 대비 world 위치 오차 norm(mm), q는 world orientation의 SO(3) geodesic 오차(도)다. Half는 baseline보다 최대 위치 오차가 0.052 mm 작았지만 최대 회전 오차는 0.017° 컸다. 이 작은 차이만으로 개선이나 안정화를 선언하지 않는다. Half의 초기 source-hull gap 여섯 값은 모두 3 mm 이내였지만 CPU source 형상 거리이며 PhysX cooked 형상 clearance나 실제 면 접촉 판정이 아니다.

세 trial 모두 분석 check를 통과했다(3 native initialization, 3600 physics steps, 7개 분석 계약). 초기 자세 변경으로 strap 경로가 변하는 점도 함께 고려한다. Half 실행에서 thumb3와 middle3의 positive raw-lambda 기록은 step 1200에도 있었지만 index는 step 81, palm은 step 123에서 마지막 positive 기록을 남겼다. 마지막 접촉 row는 index step 83, palm step 132다. 접촉 row 수, positive-lambda를 기록한 서로 다른 step 수, source gap은 다른 관측량이다. 이 자료는 기타 면, 지속 지지, 뉴턴 단위 힘 또는 안정성을 인증하지 않는다.

Baseline repeat에서 저장 states/trace/tasks/contacts는 이전 기준과 exact 일치했고 controls는 로그 스키마 변경 때문에 달랐다(새 로그는 81개 목표를 기록하고 feedback 진단 필드를 포함하지 않음). hands 및 whole-body 영상은 둘 다 exact 일치했다. Exact 재현은 관측값이며 결과 통과 gate가 아니다. 세 조건 모두 안정성 성공이나 채택 후보로 선언하지 않았다.

## 산출 그림

![저장 trace의 기타 위치·회전 오차와 세 trial의 6개 초기 source-hull gap](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/three_face_same_target_curves.png)

곡선은 저장된 실제 240 Hz trace의 0–5초 위치 오차(mm)와 회전 오차(도)다. 그룹 막대는 thumb3, index3, middle3, ring3, pinky3, palm의 초기 source-hull gap(mm)이며 세 trial을 구분한다. 작은 양수도 지수 표기 등으로 표시해 0으로 반올림하지 않았다.

![세 실제 Isaac Gym hands 카메라의 t=0 및 t=5초 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/three_face_same_target_hands.png)

각 열은 baseline repeat, quarter, half 순이고 위/아래 행은 실제 native hands 카메라의 step 0/t=0초와 step 1200/t=5초다. 그림 생성에는 저장 자료만 사용했고 native 호출은 없었다.

## 초기값 및 5초 영상

| 조건 | Hands 영상 | 전신 영상 | 초기값·기타 상태 |
|---|---|---|---|
| Baseline repeat | [hands.mp4](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/baseline_repeat/hands.mp4>) | [whole_body.mp4](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/baseline_repeat/whole_body.mp4>) | [initial_values.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/baseline_repeat/initial_values.json>) |
| Quarter | [hands.mp4](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/three_face_quarter/hands.mp4>) | [whole_body.mp4](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/three_face_quarter/whole_body.mp4>) | [initial_values.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/three_face_quarter/initial_values.json>) |
| Half | [hands.mp4](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/three_face_half/hands.mp4>) | [whole_body.mp4](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/three_face_half/whole_body.mp4>) | [initial_values.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/native/three_face_half/initial_values.json>) |

각 영상은 151 frames, 30 fps, 인코딩 길이 5.033초이며 physics 구간은 step 0–1200의 5초다.

## 산출 이력과 입력 출처

저장 분석은 [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/analysis.json>), 승인 brief는 [artifact_brief.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifact_brief.json>), 그래프 입력·출력 해시는 [artifact manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/artifact_manifest.json>)에 있다. 성공 재생성은 Python 3.8 환경에서 완료됐다(exit code 0, 약 0.866초, manifest에 기록된 입력 19개 전후 SHA 동일, native_calls 0). 출력은 이 README의 두 PNG이며 각 출력 SHA는 manifest를 참조한다.

첫 후처리 시도는 Python 3.8에서 `str.removeprefix`를 호출해 실패했다(exit code 1, native_calls 0). 당시 producer 원문, 실행 로그, 실패 execution metadata 및 보존된 빈 output directory 기록은 [artifact_attempt_v1](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifact_attempt_v1>)에 보존했다. producer를 Python 3.8 호환 문자열 slicing으로 보완한 후 저장 데이터에서 다시 생성했다. 이는 후처리 재시도이며 native 실험 재실행이 아니다.

이전 source-only 거절 분기들은 native initialization 0회로 기록돼 있다. source 거리로 cooked 접촉을 추정하지 않았고 세 admitted 조건만 fresh native run을 수행했다. [현재 source 계획](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_INITIAL_SAME_TARGET_PLAN.md:1>)과 [다음 미실행 finger-target hold 계획](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FINGER_TARGET_HOLD_PLAN.md:1>)을 구분한다.

검수 및 보존 대조 결과는 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/review.md>)와 [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/final_verification.json>)에 기록한다.
