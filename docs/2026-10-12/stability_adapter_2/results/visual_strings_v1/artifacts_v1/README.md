# 여섯 현 영상 오버레이

완료된 native_v1 카메라 녹화 위에 기타의 실제 `string1`–`string6` 양 끝점 쌍을 프레임별 투영한 화면 자료다. 선은 밝은 회색 2 px 표시이고, native depth tolerance 2 mm에서 가려진 구간은 숨긴다. overlay는 물리 현을 추가하지 않으며 실물 현의 gauge(굵기), 진동, 장력 또는 접촉을 표현하지 않는다.

## 같은 시점의 화면

![native 전신, 0·2·5초의 여섯 현 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/whole_body_strings_0_2_5s.png)

![native 손 카메라, 0·2·5초의 여섯 현 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/hands_strings_0_2_5s.png)

![초기 native 화면의 선 오버레이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/initial_strings_captioned.png)

![동일 초기 손 프레임: 원본과 여섯 선 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/hands_sameframe_raw_vs_sixline.png)

동일 프레임 비교의 왼쪽은 `media/strap/raw/frames/hands/00000.png`이며 native camera와 strap만 포함한다. 오른쪽 `media/frames/hands/00000.png`에는 여섯 선 overlay와 strap이 있다. 원본 native camera, strap 중간 overlay, 최종 strings overlay frame은 원본 위치에서 각각 보존했다. 비교는 두 표시 단계의 차이를 보여주며 물리 장면의 변화를 뜻하지 않는다.

## 보관 영상과 범위

아래 MP4 두 개는 원본 `media/whole_body.mp4`, `media/hands.mp4`의 bytes를 그대로 복사했다. 세부 해시·크기·ffprobe 결과는 [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/visual_strings_v1/manifest_v1.json)에 있다.

![전신 native 영상, 여섯 현 표시](/home/ajou/yigyu/3/docs/2026-10-12/video/visual_strings_v1/whole_body_sixline.mp4)

![손 native 영상, 여섯 현 표시](/home/ajou/yigyu/3/docs/2026-10-12/video/visual_strings_v1/hands_sixline.mp4)

검증 자료는 한 번의 native 녹화, 1,200 physics step, 300 control, view당 151 frame을 기록하며 선 표시는 물리 geometry를 추가하지 않았다. 초기→5초 actor-root 이동 113.199839 mm 및 회전 4.857745°는 native 조건에서 관측한 변화일 뿐, 현 overlay의 효과나 자세 유지·연주 성공을 나타내지 않는다. 모든 원본 질량·접촉·초기값·trajectory가 직전 OM native 기준과 exact 일치했다는 검증은 [root verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/verification_v1.json)에 따른다.

[재생성 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/make_visual_strings_archive_v1.py)와 [SHA-256 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/provenance_v1.json)를 함께 둔다. native 재실행이나 source·physics 변경은 수행하지 않았다.
