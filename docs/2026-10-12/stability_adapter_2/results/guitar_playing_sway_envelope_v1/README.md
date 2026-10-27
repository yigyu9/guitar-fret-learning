# 기타 연주 흔들림을 고려한 시각적 끝점 제안

실제 Isaac Gym의 정적 native 캡처 13개를 검토해, 기존의 좁은 초기 배치 단계를 넘어 팔과 손이 따라 움직이는 상황의 시각적 여유 범위를 제안한다. 이는 물리적으로 자세를 유지한 결과나 연주 중 기타 움직임의 실측값이 아니다. 모든 캡처는 물리 스텝 0에서 생성됐다.

## 제안 범위: 최소 · 선호 중심 · 최대

| 항목 | 최소 | 선호 중심 | 최대 | 뜻 |
|---|---:|---:|---:|---|
| 바디 중심 world X | −50 mm | 0 mm | +50 mm | +X는 사람 오른쪽 |
| 바디 중심 world Y | −50 mm | 0 mm | +50 mm | +Y는 관객 쪽 |
| 바디 중심 world Z | −50 mm | 0 mm | +50 mm | +Z는 위쪽 |
| 넥 상승각 | 10° | 22° | 40° | 절대 semantic 각도 |
| 관객쪽 방위 | −10° | 5° | 20° | 절대 semantic 각도, world −X에서 +Y 방향 |
| 앞판 눕힘 | −5° | +3° | +15° | 원래 기준 자세 대비 correction |

이동 기준은 기타 바디 중심 world `[169.6, 65.0, 676.0] mm`다. 앞판 correction의 −5°/＋3°/＋15°는 선호 중심 +3°를 기준으로 −8°/+0°/+12° 변화다. 넥 22°에서 앞판 법선 상승각은 각각 약 0.56°/7.97°/19.04°다. 회전은 바디 중심 pivot으로 적용했으며 이 값은 절대 Euler XYZ 각이 아니다.

각 축을 한 번에 하나씩 끝점까지 바꾸고 나머지 성분은 선호 중심에 유지했다. 따라서 최소·중심·최대 시트는 각 축의 단독 끝점 비교이며, 여섯 축을 동시에 끝값으로 적용한 복합 자세를 보여주지 않는다.

모든 캡처에서 원 기타·humanoid 모델 형상과 humanoid 상태를 유지했으며, 기타 p/q만 case별로 바꿨다. 팔·손은 현재 상태로 고정되어 있고 끝점 이후에는 팔·손 재배치가 필요할 수 있다.

## 실제 native 비교 시트

각 시트는 3행×3열이다. translation 행은 X/Y/Z이고 열은 −50 mm/0 mm/+50 mm다. rotation 행은 넥 상승각/관객쪽 방위/앞판 눕힘이다. 넥과 방위 열은 행별 절대각(10°/22°/40°, −10°/5°/20°)이고, 앞판 열은 원래 기준 대비 correction(−5°/+3°/+15°)이다. 행·열 라벨은 셀 바깥 label 영역에 두었다. 원본 native image는 aspect를 유지해 축소했고 crop·기하 변형·이미지 위 선/도형 덧그리기는 하지 않았다.

### Translation — front

정면에서 좌우·높이와 기타/상체의 시각적 배치를 비교한다.

![Native translation endpoints, front view](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_translation_front.png)

### Translation — side

측면에서 몸통과 기타의 앞뒤 관계와 높이를 비교한다.

![Native translation endpoints, side view](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_translation_side.png)

### Translation — hands

위치 끝점에서 고정 손과 기타 사이에 보이는 차이를 살핀다. 손이 떨어져 보인다는 이유만으로 기타 배치를 기각하지 않으며, 후속 손·팔 재배치에서 확인할 차이로 남긴다.

![Native translation endpoints, hands view](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_translation_hands.png)

### Rotation — front

넥 상승각과 관객쪽 방위는 절대각, 앞판 눕힘만 원래 기준 대비 correction이다. 넥 10°는 낮은 외곽이고 40°는 크게 세운 외곽으로 후보에 남겼다.

![Native rotation endpoints, front view](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_front.png)

### Rotation — side

앞판 눕힘의 최소·중심·최대가 측면에서 거의 세운 상태부터 조금 더 눕힌 모양으로 이어지는 것을 비교한다.

![Native rotation endpoints, side view](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_side.png)

### Rotation — hands

회전 끝점과 현재 고정 손의 차이를 보는 시점이다. 넥 40°에서는 헤드 끝이 손 시점 카메라 범위를 벗어나므로 전체 기타 형상은 front 시트를 기준으로 본다.

![Native rotation endpoints, hands view](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_hands.png)

## 개별 끝점 원본 열기

표의 각 셀은 실제 native case ID와 폴더를 표시하고 해당 pose JSON, front PNG, side PNG에 직접 연결한다. 중심 case `center`는 모든 단일축 비교에서 공통이다.

| 축 | 최소 | 선호 중심 | 최대 |
|---|---|---|---|
| X 이동 | −50 mm · [x_min, candidate_001](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_001/pose.json) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_001/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_001/side.png>) | 0 mm · [center, candidate_000](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/side.png>) | +50 mm · [x_max, candidate_002](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_002/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_002/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_002/side.png>) |
| Y 이동 | −50 mm · [y_min, candidate_003](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_003/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_003/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_003/side.png>) | 0 mm · [center, candidate_000](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/side.png>) | +50 mm · [y_max, candidate_004](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_004/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_004/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_004/side.png>) |
| Z 이동 | −50 mm · [z_min, candidate_005](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_005/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_005/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_005/side.png>) | 0 mm · [center, candidate_000](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/side.png>) | +50 mm · [z_max, candidate_006](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_006/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_006/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_006/side.png>) |
| 넥 상승각 절대각 | 10° · [elevation_min, candidate_007](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_007/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_007/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_007/side.png>) | 22° · [center, candidate_000](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/side.png>) | 40° · [elevation_max, candidate_008](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_008/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_008/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_008/side.png>) |
| 관객 방위 절대각 | −10° · [audience_yaw_min, candidate_009](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_009/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_009/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_009/side.png>) | 5° · [center, candidate_000](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/side.png>) | 20° · [audience_yaw_max, candidate_010](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_010/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_010/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_010/side.png>) |
| 앞판 눕힘 기존기준 대비 correction | −5° · [board_recline_min, candidate_011](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_011/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_011/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_011/side.png>) | +3° · [center, candidate_000](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_000/side.png>) | +15° · [board_recline_max, candidate_012](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_012/pose.json>) · [front](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_012/front.png>) · [side](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/scene/candidate_012/side.png>) |

## 해석 범위와 한계

이번에는 현재 손 위치를 고정한 상태에서 13개 끝점을 비교했다. Y±50 mm는 몸통과 오른팔과의 관계를 크게 바꾸며, Z±50 mm도 양손 높이를 다시 맞춰야 한다. 손이 떨어진다는 이유만으로 기타 배치를 기각하지 말고, 기타 배치 후 팔과 손을 재배치할 차이로 본다. 넥 10°는 낮은 외곽, 40°는 크게 세운 외곽이다. 큰 끝점들을 일상적인 미세 흔들림의 권장값으로 보지 않는다.

이는 13개 단독 끝점의 물리 없는 시각 비교다. fret/strike 도중의 움직임 진폭이나 동적 연주를 측정하지 않았으며, 접촉·관통·스트랩 지지·관절 범위 안 도달 가능성, 64개 복합 모서리 또는 연속 경로도 검증하지 않았다. controller, gate, reward, 학습, 기본 시작 pose는 바꾸지 않았다. 참고 스트랩 표시는 OFF이며 길이 변경도 없다.

## 보존 이력

최초 contact sheet 생성 뒤 label 여백을 고치며 최초 producer 버전과 첫 산출물은 별도 경로에 보존되지 않았다. 그 버전은 복구하거나 재구성했다고 주장하지 않는다. 원본 13개 native 캡처는 보존되어 있고, 현재 `artifacts` 결과는 변경하지 않은 채 root가 producer/manifest/mapping을 별도 보존한 뒤 새 `artifacts_v2` producer로 다시 생성했다. 두 현재 산출 경로의 6개 PNG SHA-256이 모두 일치한다. 기록은 [artifact preservation note](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifact_preservation_before_v2.json:1)에 있다.

## 출처

[13개 native 비교 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/native/comparison.json:1), [v2 artifact mapping](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/case_mapping.json:1), [v2 artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/artifact_manifest.json:1), [확정 시각 제안](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_PLAYING_SWAY_ENVELOPE_DECISION.md:1)을 참조한다.
