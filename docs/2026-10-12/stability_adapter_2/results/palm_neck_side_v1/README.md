# Palm–neck side target: 저장 native camera 오버레이

2026-10-07. 이 문서는 파란 기타 neck의 아래 측면에 왼손 palm이 닿도록 한 배치 진단과 저장 결과를 정리한다. 그림 생성만을 위해 새 native 실행, 상태 변경, MuJoCo 렌더링은 하지 않았다. 그림은 저장된 Isaac Gym camera PNG에 `target_polygon_W_m`을 설명용으로 투영한 결과다.

## 관측 요약

| 항목 | 저장 관측 | 범위 |
|---|---:|---|
| 이전 source palm hull–blue target 간격 | 77.049519 mm | source palm hull과 지정된 blue target polygon 사이의 직접 거리; neck vertex 선택과 별도 |
| 기존 palmar ray에서 target 중심까지 이동 | 약 136.66 mm | ray 기반 위치는 새 facet search와 별도 |
| palm convex hull의 palmar facet 면적 | 772.75 mm² | 손바닥 hull에서 선택된 실제 palmar facet |
| 새 손바닥 target gap | 0.049807 mm | 50 µm 목표를 둔 source query; cooked clearance가 아님 |
| 새 native initial FK position / rotation 오차 | 0.000151 mm / 4.113×10⁻⁷ rad | 기타·나머지 pose, PD, 고정 strap 길이, root/lower 조건 검사 통과 |
| 첫 완료 physics step | LH:palm–guitar contact 4점, raw lambda 4개 모두 0 | 힘 단위로 환산하지 않음 |
| 0.1초 종료 기타 오차 | 5.107730 mm / 0.969008° | 고정 목표만으로 palm 지지 지속 실패; 안정성 성공 아님 |

새 target은 772.75 mm² palmar facet의 wrist 반대쪽 vertex 방향으로 40% 이동한 내부점을 사용하고, 파란 neck target 중심에서 50 µm source gap을 둔다. 처음의 ray 중심은 136.66 mm 이동이 필요해 직접 target 방식과 구분했다. 최종 관절 설정은 [facet_50um_twist_0mrad_distal_40.json](/home/ajou/yigyu/3/stability_adapter_2/trials/palm_neck_side_v1/facet_distal/facet_50um_twist_0mrad_distal_40.json)에 있다. 오른팔, 손가락, 몸통 9개 PD 목표, root/lower 고정, 기타 초기 위치·회전 목표와 절대 strap rest length 1.1018469719600776 m는 유지됐다. 초기 기타의 +5 mm Z 보정도 기존 조건이다.

기존 palmar ray 중앙 목표 간격 1/3/6/10 mm source fit 중 1 mm와 3 mm 조건은 face-used 검사에서 거절됐고, 6 mm와 10 mm 조건은 재검사 통과 후 fresh native 초기화 확인(2 initialization / 0 step)과 별도의 각 1-step 진단(2 initialization / 2 physics steps, LH:palm contact 0)을 받았다. 이후 200/50/10 µm facet 조건 3개와 −300/−150/+150/+300 mrad twist 조건 4개는 wrist 교차로 거절됐다. 마지막 distal 40% facet 조건은 source filter를 통과해 fresh native 확인 대상으로 사용됐다. 이 source filter는 cooked collider clearance 인증이 아니다.

첫 완료 step에서 네 개의 native contact row가 기록됐지만 raw lambda는 모두 0이며 힘 단위 환산도 없다. 그 시점의 기타 목표 오차는 0.016300 mm / 0.003208°였다. 24 step 실행에서는 step 2–24에 palm contact row가 없고, 기타 목표 오차는 5.107730 mm / 0.969008°까지 커졌다. 이는 초기 접촉 관측이지 지속 지지나 연주 안정화 성공이 아니다. 전체 단계 집계는 11 native initialization / 27 physics steps이며, source-only 도구 실패와 보존 로그는 원래 phase 폴더에 남아 있다.

## 카메라 이미지

### 그림 72. 기타 neck 측면 target과 native 접촉 위치 비교

![저장된 native front camera의 baseline 0, 새 배치 0, 첫 완료 step, 0.1초 비교. 청록색 target 영역과 첫 step의 네 접촉점은 카메라 이미지 위 설명용 투영이다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/comparison_front.png)

### 그림 73. 같은 프레임의 side camera 비교

![저장된 native side camera의 baseline 0, 새 배치 0, 첫 완료 step, 0.1초 비교와 설명용 투영.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/comparison_side.png)

개별 front 이미지: [baseline step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/baseline_front.png), [새 배치 step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/facet_initial_front.png), [step 1 접촉 4점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/facet_step1_front.png), [step 24 / 0.1초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/facet_step24_front.png). Side 이미지: [baseline step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/baseline_side.png), [새 배치 step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/facet_initial_side.png), [step 1 접촉 4점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/facet_step1_side.png), [step 24 / 0.1초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/facet_step24_side.png).

청록색 다각형은 각 probe가 저장한 world-space target vertex를 camera spec의 eye/target, 45° horizontal FOV, 1280×720 비율로 perspective project한 것이다. 투영은 look-at forward/right/up basis를 사용하고, world 좌표 입력은 meter, 결과는 pixel이다. 다각형은 가려진 면도 표시하는 설명 overlay로 native 렌더 geometry가 아니다. 빨간 십자 네 개는 첫 step raw contact의 `localPos0`를 step 1 저장 기타 body-0 pose로 world에 옮긴 뒤 투영한 관측점이다. 색/overlay 자체가 접촉을 판정하지 않으며 접촉 증거는 별도의 raw contact 기록이다.

캡처는 Isaac Gym native camera, CPU PhysX, `graphics_device_id=0`에서 생성됐다. GPU pipeline은 비활성화됐고 graphics backend identity는 확인하지 않았다. strap은 native render shape가 없어 이미지에 나타나지 않는다. 설치된 공개 SDK 조사에서는 rigid convex cooked vertex 조회 API를 확인하지 못했으므로 source OBJ 결과를 cooked clearance로 승격하지 않는다. 초기 `minDist`/`initialOverlap`을 penetration depth로 해석하지 않는다. 기록한 contact lambda는 모두 0이므로 force 또는 지지력의 증거가 아니다.

## 입력과 재현

새 overlay producer [render_target_overlay.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/render_target_overlay.py:1)는 저장 PNG와 JSON만 읽는다. 입력/output hash와 투영법은 [overlay_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/overlay_manifest.json), 실제 실행과 PNG SHA는 [plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/plot_execution.json)에 기록했다. 이전 시도 및 원자료는 phase 디렉터리에서 그대로 보존한다.

```bash
python /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/render_target_overlay.py \
  --out-dir /tmp/palm_neck_side_overlay_reproduction
```

[변경 파일 및 source line 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/CHANGED_FILES.md:1)에는 원자료, settings, source producer와 검증 제한을 정리했다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/review.md:30)는 완료됐으며 미해결 지적사항은 없다. Root의 [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/verification.json)은 13개 검사 모두 통과, 보존 87개 원본 파일·Aug19 자료 49개·이전 artifact 613개 및 합계 11 native initialization / 27 physics steps를 기록한다.
