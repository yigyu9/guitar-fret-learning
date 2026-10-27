# 정적 기타 자연스러운 배치 비교 — 시각 제안

Root의 시각적 제안은 기타 바디 중심 world `[169.6, 65.0, 676.0] mm`, 넥 상승각 `22°`, 관객쪽 방위각 `5°`, 기준 대비 앞판 눕힘 `+3°`를 첫 후보로 두는 것이다. 실제 native 측정은 preferred_recline3에서 앞판 법선 상승각 `7.97°`다. 이는 기존 `soundboard_tilt=8°` 값을 그대로 읽은 결과가 아니다. 이 후보는 [combined/scene/candidate_000/pose.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/combined/scene/candidate_000/pose.json:1)에 있으며 기존 기본 시작값을 바꾸지 않는다.

![추천 preferred_recline3 native 정면 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/combined/scene/candidate_000/front.png)

추천 조합의 실제 native 정면 캡처다. 이미지 자체는 정적 배치의 모양을 보여주며 접촉·관통·지지를 인증하지 않는다.

## 시각적 탐색 시작 범위

| 항목 | 제안 범위 | 방향·기준 |
|---|---:|---|
| 바디 중심 좌우 X | −20~+20 mm | +X는 사람 오른쪽 |
| 바디 중심 앞뒤 Y | −10~+20 mm | +Y는 몸통에서 관객 쪽 |
| 바디 중심 높이 Z | −10~+20 mm | +Z는 위 |
| 넥 상승각 | 17~27° | 절대각, 중심 22° |
| 관객쪽 방위각 | 0~10° | 절대각, world −X에서 +Y 방향, 중심 5° |
| 앞판 눕힘 | 기준 대비 0~+5° | 바뀐 넥축 주위, 중심 +3° |

바디 중심의 절대 구간은 X `149.6~189.6 mm`, Y `55.0~85.0 mm`, Z `666.0~696.0 mm`다. 이 범위는 표본 사이 값을 포함한 시각적 제안이다. 범위 안의 모든 자세나 축 조합을 촬영·승인·인증한 것은 아니다. 앞판 법선 상승각 `5.19~9.82°`는 넥 상승각 22°에서만 해당하며 다른 넥 각과 조합하면 다시 계산해야 한다.

회전 비교는 기타 바디 중심 local `[0, -0.4, -0.0217] m`를 유지하도록 actor root 위치를 함께 계산했다. 이는 기존 editor의 actor-root 회전 pivot과 다르므로 같은 각도 입력이어도 위치 결과가 달라질 수 있다. 추천 pose를 재현할 때는 저장 후보를 여는 편이 정확하다. 의미 각도 정의는 넥 상승각 `asin((R·localY)z)`, 관객 방위각 `atan2(neckY, -neckX)`이며, 기준 대비 semantic 보정이지 Euler XYZ 절대각이 아니다.

## 현재 손 자세를 고정했을 때의 작은 단계

현재 양손을 고정한 상태에서 확인할 작은 단계는 위치 축별 ±5 mm, 넥 상승/방위 기준 ±1°, 앞판 눕힘 0~+3°다. 이 작은 단계도 손 접촉이나 관통이 없음을 보증하지 않는다. 기타 배치를 먼저 정한 뒤 손·팔을 맞추는 단계에서는 위의 넓은 제안 구간을 참고한다. 19°/25° 조합에서도 고정 손과의 차이가 보이고 손 재배치가 필요하다. 손과 기타의 정렬은 기타 자체의 시각적 배치 판단과 구분한다.

넥 12°/32°는 고정된 왼손보다 낮거나 높아지고, 17°/27°도 팔·손 재배치가 필요하다. 관객 방위각 −5°/15°는 손과 넥의 앞뒤 관계를 크게 바꿔 우선순위가 낮다. 앞판 눕힘 0~+5°는 측면에서 거의 세운 상태에서 조금 눕힌 상태로 이어진다. +3°는 넥 방향과 바디 중심을 유지하며 작은 시각적 기울기를 준다. −10°는 위쪽이 관객 쪽으로 나오는 느낌, +10°는 더 눕혀지는 느낌이 커 첫 중심 후보에서 제외했다. ±4 cm 이동은 현재 팔·손과 기타 관계를 눈에 띄게 바꾼다.

## 실제 native 비교 시트

아래 contact sheets는 저장된 Isaac Gym native PNG를 aspect-preserving 축소해 셀에 배치했다. 원본 프레임은 자르거나 기하를 변형하지 않았고 이미지 위에 선·도형을 덧그리지 않았다. 별도 label 영역에 축·열 이름을 두었다. 정면/측면/손 시점은 정적 렌더이며 물리 접촉이나 관통을 판정하지 않는다.

### Rotation — front

단일 회전 축 비교를 정면 시점에서 본 시트다. 행은 넥 상승각, 관객쪽 방위각, 앞판 눕힘이다. 열 라벨 −10°, −5°, +5°, +10°는 baseline 대비 semantic 보정값이며 절대각이 아니고, baseline 열은 0° 보정이다. 추천 조합의 실제 장면은 아래 5-case sheet에서 확인한다.

![Native rotation front contact sheet: elevation, yaw, and board recline](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_rotation_front.png)

### Rotation — hands

같은 단일 회전 조건의 손 확대 시점이다. 이 이미지는 고정된 양손 주변의 시각적 정렬을 보여주며 접촉 여부를 검증하지 않는다.

![Native rotation hands contact sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_rotation_hands.png)

### Combined candidates — front, side, hands

열은 저장 입력 순서다. 첫 열 `preferred_recline3`가 시각 제안 중심 `(22°, 5°, +3°)`이고, 나머지는 넥 상승각 변화 2개와 앞/위 이동 및 오른쪽 이동 조합이다.

![Five combined native static candidates in front, side, and hands views](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts_combined/contact_sheet_combined_front_side_hands.png)

기본 25개 native sheet와 원본별 SHA·case 위치는 [case_mapping.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/case_mapping.json:1), [기본 artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/artifact_manifest.json:1)에 있다. 5개 조합 sheet의 행·열·원본 파일과 SHA는 [combined case_mapping.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts_combined/case_mapping.json:1), [combined artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts_combined/artifact_manifest.json:1)에 기록했다. 나머지 기본 시트는 아래와 같다.

- Translation: [front](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_translation_front.png), [side](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_translation_side.png), [hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_translation_hands.png).
- Rotation: [side](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/artifacts/contact_sheet_rotation_side.png).

## 범위와 제한

25개 단일 변화와 5개 작은 조합, 총 30개 native capture를 확인했다. 모두 물리 steps 0이며 비교는 저장 상태와 native 이미지의 정적 시각화다. 참고 strap은 숨겼고 기존 길이는 변경하지 않았다. 실제 접촉, 관통, 정지 안정성, 지지 가능성, 인체공학, 정책 실행 또는 연주 가능성은 확인하지 않았다. 이 제안은 다음 물리 실험의 성공 gate·보상·기타 목표 p/q가 아니다.

모든 capture에서 원 기타·humanoid 모델 형상을 유지하고 humanoid의 root/하체/상체/양팔/양손 상태를 유지했다. 기타 p/q만 후보별로 변경했다. 최종 추천값은 자동으로 기본 시작값에 반영되지 않았다. [25개 native 비교 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/native/comparison.json:1), [5개 combined 비교 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/combined/comparison.json:1), [확정 시각 제안 brief](/home/ajou/yigyu/3/stability_adapter_2/STATIC_GUITAR_NATURAL_RANGE_PROPOSAL.md:1)을 출처로 한다.
