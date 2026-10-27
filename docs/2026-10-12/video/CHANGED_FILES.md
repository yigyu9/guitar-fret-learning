# 변경 파일 기록

| 파일 | 실제 줄 | 내용 |
|---|---:|---|
| `docs/2026-10-12/video/README.md` | 1 | 보관 개요, 폴더별 파일 수, 대표 실험 영상 링크 및 검증 범위 |
| `docs/2026-10-12/video/archive_v1/archive_videos.py` | 1 | 재현 가능한 최대 8 worker 복사·해시 검증·ffprobe producer |
| `docs/2026-10-12/video/archive_v1/index.md` | 1 | 원본별 절대 view/source 링크, duration/fps/frames 및 해당 폴더 보고서 링크 |
| `docs/2026-10-12/video/archive_v1/metadata/manifest.json` | 1 | 보관 manifest의 스키마·요약·producer 및 입력 참조 문서 기록 시작 |
| `docs/2026-10-12/video/archive_v1/metadata/manifest.json` | 69 | 개별 파일 출처·해시·bytes·probe 항목 배열 시작 |

검증 결과: 원본 1,362개(373,017,061 bytes) 전부 복사본과 SHA-256이 일치했고, 원본 확인 중 변경 0개, 보관 제외 0개, ffprobe 실패 0개였습니다. 실제 스크립트 SHA-256은 manifest의 `producer.sha256` 값입니다.
