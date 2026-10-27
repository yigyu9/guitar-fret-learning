# 기타 접촉 사이클: 가슴 접촉 감사

## 핵심 관측

실제 native replay는 16초, 3,840 physics step, 960 control step을 완료했다. 우선 분석은 [analysis_v2.json](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/analysis_v2.json>)이다. Scoped audit은 전체 기타 trace가 이전 left-cycle 실행과 정확히 같고, 범위 내 입력이 보존됐음을 확인한다.

Chest–기타 본체(`human/Chest`–`guitar/G:body`) 접촉은 1,514/3,840 step, 양의 raw contact lambda는 1,473/3,840 step이다. 첫 접촉은 9.6292초, 마지막은 16초다. lambda는 raw solver 값이며 보정된 힘(N)이 아니다.

| body | 접촉 step | 양의 lambda step |
|---|---:|---:|
| Chest | 1,514 / 3,840 | 1,473 / 3,840 |
| Torso / Spine / R_Thorax | 0 | 0 |
| R_Shoulder (오른쪽 위팔) | 3,825 / 3,840 | 3,825 / 3,840 |
| R_Hip (오른쪽 허벅지) | 3,827 / 3,840 | 3,827 / 3,840 |

A 유지(3–4.5초)에는 Chest 접촉이 없다. B 유지(10–11.5초)에는 Chest 양의 lambda가 360/360 표본, 마지막 왼팔·왼손 기타 접촉 없음 구간(13–16초)에는 720/720 표본에서 관측됐다. 따라서 마지막 3초의 기타 상태를 오른쪽 위팔과 허벅지 지지만으로 설명할 수 없다. 손 접촉 표본만으로 grasp force나 force closure를 주장하지 않는다.

## 두 시점의 native 전신 프레임

캡션의 접촉은 이미지에서 추정하지 않고 scoped 물리 표본으로 판정했다. native Isaac Gym 카메라 캡처에는 실제 줄 끝점 사이 비물리적 6개 선 표시가 포함된다. 복사본은 이미지 처리를 거치지 않았다.

**3.5초 — 분석상 Chest 접촉 전** (첫 Chest 접촉 9.6292초)

![3.5초 native 전신 프레임, scoped 분석상 Chest 접촉 전](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/artifacts_v1/figures_v1/whole_body_00105.png)

**14초 — 분석상 Chest 접촉 중** (왼팔·왼손 기타 접촉 없음 구간)

![14초 native 전신 프레임, scoped 분석상 Chest 접촉 중](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/artifacts_v1/figures_v1/whole_body_00420.png)

## 16초 영상

- [전신](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_contact_cycle_v1/whole_body.mp4>) · [손](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_contact_cycle_v1/hands.mp4>) · [엄지 뒤쪽](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_contact_cycle_v1/thumb_back.mp4>)

각 30 fps, 481 frames, 16.033초 길이이며 물리 시뮬레이션 길이는 16초다. 조건은 휴머노이드 root·하체 고정, 기타 자유 동역학, strap OFF, right strike OFF, 오른쪽 위팔 제어 유지였다.

## 실행 범위 한계

원본 [native report](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/native_v1/report.json>)는 `completed=false`, `inputs_unchanged=false`다. 이를 global guard 성공으로 표현하지 않는다. Broad wildcard guard는 동시에 변경된 무관한 `fresh_music_v1` 네 파일과 main PLAN의 후속 append 때문에 실패했다. 이 원본 report와 앞선 [analysis_v1](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/analysis_v1.json>)은 보존돼 있다.

[analysis_v2 scoped audit](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/analysis_v2.json>)는 네 파일을 정확한 범위 제외로 식별하고, native before SHA와 일치하는 main PLAN 원문 prefix, 나머지 actual/shared source·asset·config 보존, 전체 trace exact 일치를 확인한다. 이는 제외된 네 파일의 보존을 인증하지 않으며 global guard 실패를 뒤집지 않는다.

- [복사 SHA manifest](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/artifacts_v1/copy_manifest_v1.json>) · [복사 전 입력 SHA](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/artifacts_v1/artifact_before_v1.json>)
- [main PLAN prefix 증거](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/main_PLAN_append_proof_v1.json>) · [원본 capture record](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_contact_cycle_v1/native_v1/media/capture.json>)
