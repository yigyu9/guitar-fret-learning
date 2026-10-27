# 세 면 지지 후보의 native contact feature 위치 진단

## 다음 변경을 정할 근거

half 초기81q와 이전 절대81 목표를 유지한 `three_face_half_strap_slack_v1`의 새2회5초는 여유7.506883/0mm에서 종료 이동30.695007/32.860232mm·회전7.622948/7.103303°였다. 저장 기준21.912505mm/7.091529°보다 두 종료 오차가 커 두 길이를 안정 설정으로 채택하지 않는다. 최대 회전은7.727219/7.103582°로 저장 기준7.770624°보다 작지만 전체 복원 성공은 아니다.

두 길이 모두 손바닥 body 양의 raw lambda 기록은 step1200까지 관찰됐으나 thumb3는35/96에서 끝났다. 저장 기준은 반대로 thumb3가1200까지, palm은123까지다. 스트랩 길이가 지지 조합을 바꾸는 관측이므로, 새 gain이나 손가락각을 바로 추정하기 전에 기존 native feature 위치를 넥의 요청된 후면/전면/옆면과 대조한다. 선택 thumb source facet의 해부학적 pad 정체성은 미확인이다.

## 작은 실행 단위

- [ ] 저장 reference와 half_slack/zero_slack의 전체 contacts·states·초기값·source 자산·형상·SDK 물성 readback의 예상 SHA를 검증하고 명시 입력을 봉인한다. 이 단계는 저장3조건/3600개 contact records의 offline 분석이며 신규 native 초기화/physics step은0이다. 기존 영상은 재사용 출처를 명시한다.
- [ ] Local SDK RigidContact.local_pos0/1, offset0/1, normal 및 contact collection 설정을 확인한다. Feature와 offset을 더한 surface 위치를 구분하고, local body frame을 추측으로 확정하지 않는다. 기록된 native body pose와 source/FK·body 이름/인덱스를 대조하며 guitar child/fret의 G-root 변환을 검사한다. COM/body-origin 및 last internal substep의 정확한 pose 시점이 확인되지 않으면 불확실성을 기록하고 확정 면 분류를 보류한다.
- [ ] 검증 가능한 local feature를 G-root 좌표로 표시하고 요청 polygon의 투영 내부 여부·signed plane 거리·경계 거리 및 접촉 normal 방향을 보고한다. 넥 source hull 및 fret 등 부속 형상의 실제 source 범위를 함께 표시한다. Source polygon 근접은 proxy이며 PhysX cooked 형상이나 해부학적 pad 인증이 아니다. 먼 점/경계/두 면 근접/기타 body 접촉은 미분류로 남긴다. 초기·접촉 소실 전후·후기 표본과 전체 기록 집계를 구별한다.
- [ ] Native 손 프레임과 별도의 source/feature 도표·시간 집계·설명을 결과 디렉토리에 남기고 독립 검수한다. 근거가 확보되면 손바닥과 엄지의 지지를 함께 유지하는 다음 초기 thumb/hand 각도 또는 물리 PD 목표 보정 방향을 별도 새 계획으로 정한다. 이번 진단에서 제어 목표·초기각·gain·스트랩·물성·solver를 변경하지 않는다.

데이터의 raw lambda는 units/calibration을 임의로 Newton 힘으로 환산하지 않으며 양의 표본을 substep 연속 지지로 읽지 않는다. Signed feature 기록을 cooked 관통 판정이나 source 허용 gate의 대체로 사용하지 않는다. Root/하체 물리 고정, 몸통9 PD 목표 유지, 최종 양쪽66 제어권 및 기타 고정/손 부착/지속 pose 덮어쓰기 금지를 유지한다. 자유 기타 초기 p/q 복원·유지와 연주 중 안정화·학습 구조는 미완료다.

계획·구현은 `stability_adapter_2/`, 결과는 `docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/`에 저장한다. 이 계획은 아직 구현·실행하지 않았다.
