# Video collection v19 수집 기록

이 collection은 2026-10-10 07:22:14 KST 스냅샷의 `results/**/*.mp4`를 기존 `videos/`와 SHA-256으로 대조한다. `source_before*`, `source_final`, `source_snapshot`, `collection_source`, `analysis_source` 아래의 보존 사본과 결과 수집기 자신의 디렉터리는 신규 영상으로 세지 않는다. 스냅샷 시각 뒤 수정된 파일은 실행 중 output일 수 있어 이번 모음에서 제외하고 manifest에 남긴다. 수집 직후 시작된 `strike_lateral_staging_v1` native PTY 58332의 whole-body/hands MP4는 v19 snapshot 밖이며 후속 collection에서 처리한다.

완료한 결과 영상은 원본 바이트를 그대로 복사한다. source가 기존 v18 파일과 같은 SHA면 기존 파일에 매핑하고, source 간 SHA가 같으면 하나만 복사해 나머지를 alias로 표시한다. 기존 파일명과 충돌하면서 SHA가 다르면 기존 파일을 덮어쓰지 않고 source 이름에 SHA 앞 8자리를 추가한다. 각 source와 archive copy의 SHA, 실제 ffprobe frame count/duration/framerate, full decode 여부를 manifest에 보관한다. Partial path, probe/decode error, 실패한 native report의 영상은 copy하지 않고 manifest와 v19 index의 오류 목록에만 기록하며 원본은 그대로 둔다.

수집 코드는 [collect_videos.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/video_collection_v19/collect_videos.py)이고 결과 인덱스는 [VIDEO_INDEX_v19.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v19.md:1), complete source/copy 기록은 [video_manifest_v19.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_manifest_v19.json)이다. 기존 [v18 index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v18.md:1)와 archive files는 수정하지 않는다.
