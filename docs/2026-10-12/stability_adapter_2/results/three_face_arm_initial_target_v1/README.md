# 초기 팔 목표 일치: 두 조건 결과

## 목적과 실행 범위

저장된 `three_face_support_loss_v1` 비교 상태를 새 native trial로 세지 않고, 왼팔 12축 목표가 실제 초기각과 달랐던 효과를 분리했다. 두 새 조건 모두 팔 12축의 상수 목표를 실제 시작각과 일치시켰다. `arm_initial_saved_fingers`는 손가락 21축에 저장된 절대 목표를 유지했고, `arm_and_fingers_initial`은 손가락 21축도 각 실제 초기각을 목표로 삼았다. 나머지 48축 목표와 초기 실제 전신 81관절각, 기타 위치·회전·속도, PD, solver, 물성과 strap 법칙은 동일하게 유지했다. 자세를 매 step 덮어쓰거나 기타를 고정하지 않았다.

각 새 조건은 native 초기화 1회, physics 1200 step/5.0초를 완료했다. 신규 실행 합계는 2회/2400 step이다. 보고서의 점선 저장 기준은 저장된 분석 trace이며 새 native 실행에 포함되지 않는다. 입력별 실제 초기 상태와 제출 목표 전체는 각 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_initial_saved_fingers/initial_values.json) 및 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_and_fingers_initial/initial_values.json)에 보존했다. 실행에 사용한 초기 설정은 [arm_initial_saved_fingers.json](/home/ajou/yigyu/3/stability_adapter_2/trials/three_face_arm_initial_target_v1/arm_initial_saved_fingers.json)과 [arm_and_fingers_initial.json](/home/ajou/yigyu/3/stability_adapter_2/trials/three_face_arm_initial_target_v1/arm_and_fingers_initial.json)에서 확인한다.

두 조건 공통 시작 설정에는 왼팔과 왼손 시작관절각, `strap_rest_length_m=1.1018469719600776`, `guitar_initial_z_offset_m=0.005`가 있다. 팔 12축은 목표 offset 0으로 실제 초기값에 맞췄고, 손가락 21축은 조건별로 saved 목표 또는 초기값을 사용했다. 기타 초기 생성 위치에 적용한 추가 translation 보정은 `[-0.0004154374643955208, 0.000012260650287418993, -0.001026975665529615] m`이다. 81개 실제 관절각, 기타 world 위치와 xyzw 회전·속도, 초기 PD/목표 및 각 joint의 정확한 값은 위 원자료에 있다.

두 strap 모두 초기 slack은 `15.0137668072902 mm`였고, 수동 strap law의 제출 장력은 1200개 control 전부 `0 N`, 기록된 법칙 재계산 오차는 `0`이었다. 이는 이번 경로에서 장력이 발생하지 않았다는 측정이며 strap을 비활성화했거나 기타 악화의 단독 원인이라는 결론은 아니다.

## 기타 오차와 목표 오차

기타 위치 오차는 공용 목표에 대한 world 위치 거리(mm), 회전 오차는 world 회전의 SO(3) 각도(degree)다. 목표 좌표 오차는 관절별 scalar 좌표 오차를 묶은 값이며 SO(3) 회전 오차가 아니다.

| 조건 | 구간 | 최대 위치 (mm) | 종료 위치 (mm) | 최대 회전 (°) | 종료 회전 (°) | 최대 arm12 좌표 오차 (°) | 최대 finger21 좌표 오차 (°) | 최대 torso9 좌표 오차 (°) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 저장 목표 기준 (저장 자료) | 5초 | 25.229274 | 21.912505 | 7.770624 | 7.091529 | — | — | — |
| Arm initial · saved fingers | 5초 | 159.799114 | 159.795174 | 25.272466 | 25.142339 | 18.793557 | 2.686505 | 3.404581 |
| Arm and fingers initial | 5초 | 157.516483 | 157.510653 | 25.623971 | 24.868219 | 18.571721 | 1.991038 | 3.312841 |

두 팔 초기 목표 조건 모두 기타 위치 편차가 저장 기준보다 크게 커졌다. finger 목표도 초기값으로 맞춘 조건의 위치 편차는 약간 작았으나 회전 최대값은 더 컸다. 따라서 두 조건 모두 채택하지 않는다. 초기 source geometry 접근 기준은 둘 다 통과했지만 지속적인 세 면 지지의 증거가 아니다. 제약 위반 기록은 두 run 모두 비어 있다.

초기 source hull gap은 두 조건에서 같았다: thumb3 `2.868915 mm`, index3 `0.949860 mm`, middle3 `0.000036 mm`, palm `2.129621 mm`. source gap은 PhysX cooked clearance를 인증하지 않는다. 양의 raw-lambda body sample은 관측된 body 이름에 대한 기록으로, 넥의 특정 면, 접촉력 N, 해부학적 손가락 접촉 또는 지속 지지를 인증하지 않는다. 선택된 thumb facet의 해부학적 의미도 확인되지 않았다.

| 조건 | LH palm 양의 raw-lambda sample 마지막 step | LH index3 마지막 step | LH thumb3 마지막 step | 오른쪽 허벅지 쪽 body group 양의 unique sample / 1200 |
|---|---:|---:|---:|---:|
| Arm initial · saved fingers | 90 | 11 | 38 | 1191 |
| Arm and fingers initial | 99 | 11 | 1200 | 1190 |

오른쪽 허벅지 쪽 body group (raw key `human/R_Hip`)은 각각 1191/1190 unique positive steps를 기록했다. 이는 모든 1200 step의 연속 접촉을 뜻하지 않으며 LH 손 접촉이나 기타 지지, 특정 기타 면을 인증하지 않는다. 각 body 그룹의 positive sample 시점과 전체 측정은 [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/analysis.json)에 있다.

## 초기값과 실제 native 영상

각 native run에서 초기값과 Isaac Gym camera의 실제 경과를 저장했다. 아래 파일은 전신 및 양손 camera에서 각각 캡처한 원본 영상이다. 각 영상은 30 fps, 151 frame이며 step 0과 step 1200을 포함하고 encoded duration은 `5.033333 s`다.

| 조건 | 손 camera | 전신 camera |
|---|---|---|
| Arm initial · saved fingers | [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_initial_saved_fingers/hands.mp4) | [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_initial_saved_fingers/whole_body.mp4) |
| Arm and fingers initial | [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_and_fingers_initial/hands.mp4) | [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_and_fingers_initial/whole_body.mp4) |

![Arm and fingers initial 조건의 실제 native hands camera 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_and_fingers_initial/hands.mp4)

## 그림과 산출물

### 그림 116 — 기타 오차와 양의 raw-lambda body sample 시간

![두 새 조건의 기타 위치·회전 오차와 손 body 양의 raw-lambda 시점, 저장 reference 포함](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifacts/three_face_arm_initial_target_curves.png)

실선 두 개는 각 새 native 실행의 저장 trace다. 회색 점선은 저장 reference 곡선으로 새 실행이 아니다. 첫 두 패널은 240 Hz 샘플의 기타 위치 오차(mm)와 world SO(3) 회전 오차(°)를 0–5초에 표시한다. 아래 타임라인은 LH thumb3, index3, middle3, palm의 positive raw-lambda row가 포함된 physics step을 `step/240 s`에 표기한다. 표식은 lambda 크기, 접촉력, 연속 접촉 구간 또는 넥 면을 뜻하지 않는다.

### 그림 117 — 실제 손 camera 시작·종료 장면

![두 native 조건 hands camera의 step 0 및 step 1200 frame 2×2 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifacts/three_face_arm_initial_target_hands.png)

네 칸은 native Isaac Gym hands camera의 실제 PNG frame이다. 윗줄은 step 0 (`t=0.0 s`), 아랫줄은 step 1200 (`t=5.0 s`)이며 왼쪽 열은 saved fingers, 오른쪽 열은 arm and fingers initial 조건이다. 합성 접촉점이나 source geometry overlay는 추가하지 않았다. 이 영상 프레임만으로 접촉 면·힘·clearance를 판정하지 않는다.

산출물 producer는 저장 자료만 읽었고 native 호출/physics step은 0이다. 실행은 [artifact_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifact_execution.json)에, 입력·출력 SHA256은 [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifacts/artifact_manifest.json)에 기록했다. producer 실행 시간은 `0.7822753069922328 s`, exit code는 0이다. 점선 reference를 포함한 실제 source와 원본 template provenance는 `producer_template_snapshot/` 아래 보존했다.

독립 검수와 최종 입력 보존 대조는 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/review.md) 및 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/final_verification.json)에 기록한다.

## 다음 단계와 남은 한계

계획에 따라 다음에는 기존 saved-reference initial 81-q와 기존 absolute 81-joint PD 목표를 복원하고 strap 초기 slack만 `7.5068834036451 mm` 및 `0 mm`로 비교한다. 해당 계획은 [THREE_FACE_HALF_STRAP_SLACK_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_HALF_STRAP_SLACK_PLAN.md)이며 이 README 작성 시점에 미실행이다. 최종 기타 p/q 복원·유지, 양손의 지속 지지, cooked clearance·접촉력 인증과 연주 중 안정화는 완료되지 않았다.

## 입력 SHA와 provenance

분석 결과 파일 `analysis.json`의 SHA256은 `7a481c7061935999b9e85aacc52b6f174bf51463888a84b387347b376b059811`이다. 원자료·분석 입력의 provenance는 phase 파일들과 각 `native/<condition>/report.json`, `capture.json`, `initial_values.json`에 있다. figure producer는 SHA `b534d707478f2cb02101fb320ba441fd0d05934edd0057b5cfca2ec51e0fb50f`다. 실행 전후 입력 SHA는 manifest에 기록되어 있다.
