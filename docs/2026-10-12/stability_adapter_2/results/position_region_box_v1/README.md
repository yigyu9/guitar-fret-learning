# 기타 위치 허용영역 박스와 기준점

기타를 여러 위치로 이동한 비교 이미지가 아니라, 기타 한 대를 기준 포즈에 둔 채 root 위치 허용영역을 박스로 표시했습니다. 박스와 표식은 native Isaac Gym camera view/projection에 맞춰 깊이 검사를 적용해 이미지 위에 그렸습니다.

현재 저장된 사람 자세의 `Chest` rigid-body 원점은 월드 `0.884m`입니다. 이를 요청하신 “가슴 높이 정도”의 Z 상한으로 사용했습니다. 이는 링크 원점으로 정한 근사 높이이며 가슴 표면이나 충돌 경계가 아닙니다.

허용영역은 X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,0.884]m`입니다. 기타 actor-root 기준점 `(-0.325,0.000,0.800)m`는 노란 표식입니다. 박스는 root 위치를 제한하는 영역이며 기타 전체 형상이 박스 안에 들어간다는 뜻은 아닙니다. Chest 원점은 분홍 표식입니다.

![위치 허용영역 박스와 기타 root 기준점 — isometric](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/position_region_box_v1/images/position_region_isometric.png)

![위치 허용영역 박스와 기타 root 기준점 — whole body](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/position_region_box_v1/images/position_region_whole_body.png)

장면 초기화 후 물리 step은 0입니다. 휴머노이드 및 기타 상태가 렌더 전후 동일하고 strap은 표시하지 않았습니다. 이미지는 영역의 공간적 의미를 설명하며 접촉·겹침·안정성을 검증하지 않습니다.
