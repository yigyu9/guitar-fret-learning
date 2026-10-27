# 현실 비율 기타 그림 정정본

이 폴더는 이미 공유된 v1 자료를 수정하지 않고, 두 그림을 바로잡은 후처리 산출물입니다. 이번 작업에서는 원본 결과를 다시 실행하거나 영상을 복사하지 않았습니다.

![old/new native raw t0와 충돌 형상 시각화의 2×2 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/native_collision_2x2.png)

2×2 그림은 행이 원본/새 비율, 열이 같은 전신 카메라의 native raw t0/충돌 형상 시각화입니다. raw frame은 raw capture SHA에 고정했고, 충돌 그림은 각 native run의 `initial_collision.png`를 사용했습니다.

![동일한 cm 축척으로 나란히 비교한 원본 사각 경계와 새 몸체 profile](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/body_outline_common_cm.png)

윤곽도는 두 패널 모두 cm 단위와 같은 픽셀/cm 축척을 사용합니다. 원본은 확인된 몸체 bounds 34×30cm 사각 경계이고, 새 윤곽은 build 입력 `half_width_profile_t_m` 및 몸체 길이 48.7896cm를 실제 크기로 그렸습니다. 새 최대폭은 37.3039cm입니다. 전체 길이 82.5333cm라는 기존 source bound는 목을 포함한 종방향 값이며 몸체 길이가 아닙니다. 정확한 hardware 치수나 Yamaha 제품 스캔으로 간주하면 안 됩니다.

## 정정 내용과 해석 범위

v1의 t0 시각/충돌 그림은 두 장을 위쪽에만 놓아 비교가 불완전했고, 치수 그림은 세로 크기를 고정해 원본과 새 몸체의 실제 상대 크기를 오해할 수 있었습니다. v1 파일은 보존했습니다. 이 v2는 native에서 캡처한 같은 카메라의 t0 입력 두 쌍과 검증된 geometry profile로 만든 정정 시각화입니다.

v2는 그림 후처리만 포함하며 native 실행, 물리 계산, 영상 복사·재인코딩은 0회입니다. 이미 검증된 native 전신·손 영상은 [기존 artifact 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/README.md)에, 두께 비교 그림은 [v1 두께 도식](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/thickness_comparison.png)에 있습니다.

입력 전후 SHA, 두 이미지 및 README 출력 SHA, NanumGothic font SHA와 producer SHA는 [provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/provenance.json)에 기록했습니다. [그림 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/make_artifacts_v2.py)는 이 디렉터리 안에서만 사용됩니다.
