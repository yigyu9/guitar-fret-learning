# 기존 영상 보관 독립 검수

요약 판정: **문제없음 — 절대 링크 보완본까지 확인 완료.** 검수 범위는 수집 당시 날짜 폴더에 존재한 encoded 영상의 바이트 보관·출처·색인이다. 영상 전체 재생/디코딩 품질, 물리 실행 성공, 연주·학습 성공은 판정하지 않았다. 검수자는 읽기 전용 파일·SHA 대조만 수행했고 이 새 보고서 외 파일을 변경하지 않았다.

## Critical

없음.

## 확인 사항

- [복사 producer](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/archive_videos.py:65)는 날짜 폴더의 상대 경로를 유지하고 원본은 읽기만 한다. 임시 복사본을 만든 뒤 원본 전후 크기·mtime·SHA와 복사본 SHA를 대조하며 기존 목적지 존재 시 오류로 중단한다. 새 보관 폴더는 발견 대상에서 제외한다. 현재 snapshot/manifest에서 목적지1,362개가 모두 고유하고 실제 보관 영상 집합과 정확히 일치해 누락·이름 충돌·추가 encoded 사본은 없었다.
- [독립 원본 snapshot](/home/ajou/yigyu/3/docs/2026-10-12/video/root_source_inventory_before_v1.json)·[manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/metadata/manifest.json:69)·현재 원본·현재 복사본의 SHA를 검수자가1,362개 전부 직접 대조했다. 오류0, 합계373,017,061bytes, 고유 내용333개였다. 원본별 상대 경로·bytes·전후 stat도 일치하고 변경/불일치 제외 목록은0개다. 중복 내용은 제거하지 않았다. 중앙 videos278개 및 과거 backup/copy 경로도 포함하므로1,362개의 독립 실험이라는 뜻은 아니다.
- [root 검사](/home/ajou/yigyu/3/docs/2026-10-12/video/root_verify_archive_v1.py:22)는 producer manifest와 별도의 사전 snapshot을 기준으로 검사한다. [최종 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/video/root_final_verification_v1.json)의 count/bytes/고유 내용/실패0이 독립 대조와 일치한다. inventory 및 root 검증 스크립트의 현재 SHA도 기록과 같다.
- producer SHA는 `f1fcbb902f500628d072242f1c4267ab6cbdf303547ac6eb97315a0c1238e05e`로 manifest 및 현재 스크립트와 같다. 직접 참조 문서7개의 현재 SHA도 manifest와 일치했다. manifest의1,362개 probe 상태는 모두 ok다. [README 보완본](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V1.md:44)은 이를 영상 스트림·재생 정보 확인으로 제한하고 실험 성공 인증으로 설명하지 않는다. 검수자는 ffprobe 재실행이나 새 영상 생성·재인코딩을 하지 않았다.
- 최초 [색인](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/index.md:7)의 `file://` 목적지와 최초 변경 기록의 일반 상대 경로 표기를 지적했다. 원본을 수정하지 않고 [새 절대 경로 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/index_absolute_v1.md:7)·[새 안내](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V1.md:5)·[새 변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/CHANGED_FILES_ABSOLUTE_V1.md:7)을 생성해 해결했다. 새 색인은 기존2,440개 view/report 링크의 URI 목적지만 직접 경로로 변환했다. 내용·분류·개수·재생 정보는 동일하다. 세 보완 문서의 총2,459개 링크는 모두 절대 경로로 존재하고 명시된 줄 번호도 실제 위치와 맞으며 `file://` 목적지는0개다.
- [링크 보완 입력 기록](/home/ajou/yigyu/3/docs/2026-10-12/video/link_fix_inputs_v1.json)의 원래 README/index/manifest3개 before/after SHA·bytes를 현재 파일과 직접 대조해 동일함을 확인했다. 기존 소비본과 보관 영상을 덮어쓰지 않았다는 보완 범위가 기록과 일치한다.

## Warning

새 수정 요구 없음. 사용자 안내는 **README_ABSOLUTE_V1.md와 index_absolute_v1.md**를 사용해야 한다. 보존된 최초 index에는 기존 URI 형식이 그대로 남아 있다. 이번 보관은 사전 snapshot의 기존 encoded 파일 범위이며 이후 진행 중 학습이 생성하는 미래 영상의 자동 수집이나 원본 실험 전체 보존 감사를 대신하지 않는다.

## Suggestion

없음. 기존 소스·A/main·native 학습은 이 보관 검수에서 변경하지 않았다.
