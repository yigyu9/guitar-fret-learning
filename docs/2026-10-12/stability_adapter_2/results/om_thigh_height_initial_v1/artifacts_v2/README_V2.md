# 초기 측면 비교 패널 정정 v2

v1 측면 비교의 하단 follow-camera 설명은 잘려 있었다. v1 그림과 문서는 보존하고, 아래 v2 패널에서만 하단 여백을 늘리고 낮은 두 조건을 `양 Hip 최소 source gap 8/3 mm`로 분명히 표시했다.

![수정된 초기 측면 비교: 이전 높은 기준 및 양 Hip 최소 source gap 8 mm, 3 mm](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v2/initial_side_comparison_v2.png)

높은 기준의 측면 원본은 이전 hold ON native의 초기 화면이다. 그 run의 `initial_values.json`은 이전 high hold OFF 초기값과 byte-identical임을 확인했다. 세 측면 이미지는 각각 기타를 따라가는 native follow-camera 화면이므로 픽셀상의 높이 차이를 실제 world z 변화량으로 읽을 수 없다. source gap의 단위·좌우 Hip 정의, native 결과와 기존 전신 비교는 [v1 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/README.md)에 있다.

v1의 전신·initial strings 패널과 영상 archive는 유효하므로 그대로 사용한다. 기존 여섯 영상과 manifest는 [video index](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/INDEX.md)에서 확인한다. 이번 v2 변경은 캡션 여백과 열 이름뿐이며 native 재실행, 영상 재복사 모두 0회다.

[producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v2/make_side_comparison_v2.py)와 [v1/v2 입력·출력 SHA provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v2/provenance_v2.json)를 함께 둔다.
