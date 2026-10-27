# 영상 자료 색인 V7

최신 색인입니다. [이전 V6 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V6.md)을 유지하면서 parallel validation 4개와 parallel long initial/cutoff 4개, 이번 phase의 영상 8개를 연결합니다. 이 수는 이번 8개 자료에 한정되며 이전 V1–V6 및 기존 보관본을 모두 합한 수가 아닙니다.

- [V1 전체 실험 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/index_absolute_v1.md)
- [V2 추가 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v2/README.md)
- [V3 추가 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v3/README.md)
- [V4 CP157/CP241/CP242 영상 및 매니페스트](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/README.md)
- [최신 CP241→CP242 비교 설명 및 한글 native 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/README.md)

## 새 장기 평가 초기 영상

실제 Isaac Gym에서 저장한 initial_000000 평가의 전신·손 영상입니다. 물리 구간은 16.366667초이고 영상 재생 시간은 16.4초이며 전체 구간을 마쳤고, 연주 성공은 0/42입니다. 전체 구간 완주는 성공 판정이 아닙니다.

- [초기 평가 영상 설명](/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/initial_000000/README.md)
- [초기 평가 매니페스트](/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/initial_000000/manifest.json)
- [초기 평가 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/initial_000000/whole_body.mp4)
- [초기 평가 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/initial_000000/hands.mp4)

resume 검증은 2026-10-12 01:52:56.056519 UTC에 passed=true였습니다. 첫 복구 저장은 CP257, 65,792 transitions, 2026-10-12 01:52:25.607348 UTC였고, 해당 검증 스냅샷의 마지막 완료 기록은 CP258, 66,048 transitions입니다. 이 결과는 첫 복구 및 유한한 진행 prefix 검증이며 장기 학습 완료나 성능 성공을 뜻하지 않습니다. [복구 검증 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/resume_verification_v1.json)

## parallel collection 영상 8개

각 MP4는 이미 SHA 검증된 저장본이며 여기서는 읽고 연결만 합니다. initial CP316과 cutoff CP320은 각각 별도의 단일 환경 native 평가입니다.

- [CP315 validation 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP315_whole_body.mp4)
- [CP315 validation 손](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP315_hands.mp4)
- [CP316 validation 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP316_whole_body.mp4)
- [CP316 validation 손](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/CP316_hands.mp4)
- [CP316 long initial 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/initial_000000/whole_body.mp4)
- [CP316 long initial 손](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/initial_000000/hands.mp4)
- [CP320 cutoff 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/cutoff_000320/whole_body.mp4)
- [CP320 cutoff 손](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/cutoff_000320/hands.mp4)
- [CP316→CP320 분석 및 한글 캡처 패널](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v2/README.md)
- [parallel validation 보관 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_validation_v1/README.md)
- [parallel long 초기 보관 기록](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/initial_000000/README.md)
- [parallel long cutoff 보관 기록](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/cutoff_000320/README.md)

N4T256 실행은 11:40 KST wall-clock cutoff에서 종료됐습니다. 이 색인은 완료된 초기·cutoff 영상만 담으며 추가 동적 평가 경로를 예상하지 않습니다.

