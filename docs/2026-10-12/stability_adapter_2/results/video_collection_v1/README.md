# 영상 모음 완료

[영상만 모은 폴더](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos)에 기존120개를 원본과 같은 바이트로 복사했다. 원본은 results의 실험별 경로에 보존한다. [전체 목록과 최근 스트랩 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX.md:1)을 이용한다.

- [x] 전체120개 이름 충돌 없이 복사
- [x] 모든 원본/복사본 SHA·크기 일치, ffprobe 성공
- [x] 실제 영상/source 재구성·물리시각과 파일길이·이전 제작본 표시
- [ ] 독립검수: 도구 thread 한도로 미완료. Root 자체 확인과 구분한다.

새 native/physics0이다. 구현은 stability_adapter_2/collect_experiment_videos.py, 입력계획·실행 소스·로그·metadata를 같은 phase에 보존했다.
