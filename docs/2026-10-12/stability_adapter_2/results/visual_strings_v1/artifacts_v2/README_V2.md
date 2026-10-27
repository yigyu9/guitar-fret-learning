# 같은 native 손 프레임 비교 — v2

v1의 `hands_sameframe_raw_vs_sixline.png`는 왼쪽이 native raw frame인데 상단에 strap이 표시된 것처럼 잘못 캡션되어 있었다. 기존 v1 파일은 보존한다. v2에서는 좌우 모두 strap overlay가 포함된 같은 초기 hands camera frame을 비교한다.

![현 표시 OFF: native와 strap / 현 표시 ON: native와 strap 및 여섯 선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v2/hands_sameframe_strap_vs_sixline_v2.png)

왼쪽은 `native_v1/media/strap/frames/hands/00000.png`, 오른쪽은 `native_v1/media/frames/hands/00000.png`다. 오른쪽의 밝은 회색 선은 native camera에 투영된 2 px 시각 표시이며 물리 현이 아니다. 캡션 정정만 수행했으며 물리/native 재실행과 영상 재복사는 모두 0회다.

[재생성 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v2/make_comparison_v2.py)와 [입력 전후 및 출력 해시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v2/provenance_v2.json)를 확인할 수 있다.
