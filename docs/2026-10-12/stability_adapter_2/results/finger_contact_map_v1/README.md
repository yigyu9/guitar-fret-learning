# 기타-local 손가락 body 원점과 SDK feature 지도

아래 그림은 기존 고정 LA·어깨 +0.008 rad native 실행의 저장 snapshot 0, 32, 56, 1200을 같은 G-local 축 범위로 표시한다. 색 선과 원은 엄지/검지/중지/약지/소지 각 `1→2→3→_top` body origin 연결이며 빈 삼각형은 `*_top` body origin이다. 이 원점들은 해부학적 손끝 패드가 아니다. 색 원점선과 별도로 검정 테두리가 있는 색 점은 해당 snapshot 시점에 저장된 current positive-λ SDK 기타 feature만 표시한다. 각 패널의 점 수는 `0 / 2 / 0 / 1`이다. Step 56에는 현재 양의 λ feature가 없으므로 과거 점을 현재 접촉점처럼 표시하지 않는다.

![기타-local G 좌표에서 네 snapshot의 손가락 body-origin chain과 시점별 current SDK feature를 비교한 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/finger_contact_map_snapshots.png)

반투명 유한 guide는 기존 전면 `Z_G=9.3 mm`, 외곽 전면 `Z_G=11.230006 mm`, 엄지 뒤쪽 `Z_G=−8 mm`, 손바닥 옆면 참조다. 이는 표시용 영역이지 native collision shape, cooked 면, 힘 또는 새 제약이 아니다. 네 패널은 모든 chain과 guide가 들어가는 동일 축 한계를 쓴다. 이 CPU 데이터 그림은 native 프레임을 수정한 이미지가 아니다.

## 기존 native 화면과 좌표 해석

다음 이미지는 동일한 +0.008 rad 실제 native 실행에서 저장해 둔 hands frame이다. 각 프레임은 대응 physics step을 native capture 간격 8 step/frame으로 변환한 actual render이며 기존 스트랩 경로 표시는 유지하고 이번 접촉점 overlay는 추가하지 않았다.

| step 0 · frame 00000 | step 32 · frame 00004 |
|---|---|
| ![실제 native frame 00000, step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00000.png) | ![실제 native frame 00004, step 32](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00004.png) |
| step 56 · frame 00007 | step 1200 · frame 00150 |
| ![실제 native frame 00007, step 56](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00007.png) | ![실제 native frame 00150, step 1200](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png) |

기타 G-local 좌표의 post-feature body-origin 변환에서 분석된 feature 쌍 최대 차는 `0.0000820329349 mm`; 이전 step pose를 쓰면 `0.639182476 mm`였다. G↔world 왕복 오차 최대는 `6.2e−17 m`, guitar/human offsets는 각각 0이다. 이는 좌표 변환 일치 결과이며 cooked 침투 깊이·접촉력·패드 인증은 아니다. 이 기록에서 중지 1→2→3→top model body-origin 선 길이 합은 약 `99.6404 mm`, 검지는 `88.4734 mm`지만 해부학적 손가락 길이/표면 길이가 아니며 약 60° 중지 굽힘의 필요 원인을 증명하지 않는다.

step 1200에서 검지 `_top` body origin은 G 좌표 약 `[-16.302, 97.519, 15.081] mm`이고, SDK가 저장한 기타 feature 점은 `[-16.187, 97.110, 9.295] mm`다. 서로 다른 점이므로 body origin을 실제 패드로 보고 넥 면에 투영하는 목표로 쓰지 않는다.

## 구성 readback 한계와 후속 방향

초기 analyzer의 `single_substep` check는 저장된 physics parameter 키가 없는 상황에서 기본값을 사용했다. 별도의 [configuration clarification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/configuration_clarification.json:1)이 이를 supersede한다. 보존된 source에서 configured substeps 1과 관련 SHA를 확인했지만 native SimParams runtime readback은 수행되지 않았고 저장 physics parameter에도 해당 키가 없다. 따라서 이를 실제 runtime parameter readback으로 설명하지 않는다.

다음 contact-region 설계는 기타 local 전면/후면/옆면의 finite patch와 손가락 안쪽 후보 patch 및 실제 feature 점을 분리해 그리는 관측용 시각화다. 간격·법선·자세를 포함한 soft natural-pose/joint-distribution 선호와 실제 면 접촉 평가가 필요하다. 모든 손가락을 동시에 넥에 닿게 하는 조건은 두지 않으며 연주 중 활성 손가락 목표는 유지한다. LA는 고정하고 최종 66 관절 제어권을 보존한다. 이번 그림은 영역을 제어나 reward에 연결하지 않는다. [Root 결정 및 다음 미실행 조건](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_DECISION.md:1).

[원본 요약 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/analysis.json:1), [1198행 raw feature 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/features.jsonl:1), [후속 접촉 영역 계획](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_PLAN.md:13).
