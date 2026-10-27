# 절대 경로 변경 파일 색인

이번 URI 보완에서 새로 추가한 문서와 검증 근거입니다. 기존 README·index·manifest·영상은 변경하지 않았습니다.

| 항목 | 실제 줄 | 설명 |
|---|---:|---|
| [README 절대 링크 보완본](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V1.md:1) | 1 | 원본 README 내용과 보완 색인 링크, 변경 범위 설명 |
| [보완된 영상 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/index_absolute_v1.md:1) | 1 | 기존 1,362개 항목의 `file://` 목적지를 절대 경로 Markdown 링크로 변환 |
| [원본 입력 해시 기록](/home/ajou/yigyu/3/docs/2026-10-12/video/link_fix_inputs_v1.json:1) | 1 | 보완 전후 기존 README·index·manifest SHA-256과 bytes |
| [원본 보관 producer](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/archive_videos.py:1) | 1 | 원본 보관 스크립트; 수정하지 않음 |
| [보관 manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/metadata/manifest.json:69) | 69 | `files` 원본별 기록 배열 시작; 수정하지 않음 |
| [독립 검증 스크립트](/home/ajou/yigyu/3/docs/2026-10-12/video/root_verify_archive_v1.py:1) | 1 | root 소유 보관 검증 도구; 수정하지 않음 |
| [최종 검증 결과](/home/ajou/yigyu/3/docs/2026-10-12/video/root_final_verification_v1.json:1) | 1 | root 소유 최종 원본·복사본 검사 결과; 수정하지 않음 |
| [시작 전 원본 목록](/home/ajou/yigyu/3/docs/2026-10-12/video/root_source_inventory_before_v1.json:1) | 1 | root 소유 시작 전 inventory; 수정하지 않음 |

검수 시 색인의 2,440개 view/report 링크를 모두 실제 경로로 확인했고 `file://` 링크는 0개입니다. 기존 세 입력 파일의 SHA-256과 크기는 보완 전후 동일합니다. 영상 bytes, 카테고리, 파일 수, 재생 정보와 실험 성공 판정은 바뀌지 않았습니다.
