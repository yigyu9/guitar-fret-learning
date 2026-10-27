# 영상 metadata 정정 기록

기존 `manifest_v2.json`과 `INDEX_V2.md`의 native1 label “기타 4° 좌측 기울임”은 의미가 부정확했습니다. 이 조건은 기타의 초기 위치·회전(q)을 유지하고 몸통 Chest를 player-left 방향으로 4° 회전한 조건입니다. 기존 V1/V2 파일은 보존하고, native1의 label만 정정한 `manifest_v3.json`과 `INDEX_V3.md`를 새 canonical 색인으로 추가했습니다.

Native1 영상 2개의 source/copy 경로, SHA-256, view, ffprobe 정보는 V2와 그대로입니다. 나머지 네 영상의 metadata도 바뀌지 않았습니다. 영상 복사·재인코딩·native 실행은 추가하지 않았습니다.

- [새 영상 색인 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V3.md)
- [새 manifest V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v3.json)
- [보존된 이전 색인 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md) · [보존된 이전 manifest V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v2.json)
