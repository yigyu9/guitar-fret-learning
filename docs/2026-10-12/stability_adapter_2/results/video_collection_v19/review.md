# 영상 모음 v19 독립 검수

요약 판정: **수정 권장 — 영상 보존·복사는 문제없음, HOLD metadata 두 행에 알려진 오류 있음.** 검수 중 native 초기화·물리 실행·수집기 재실행·원자료 수정은 없었다.

- Critical: 없음.
- Warning: [collect_videos.py:125](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/video_collection_v19/collect_videos.py:125)는 terminal 시각 필드가 없으면 `continued_in_hold=false`로 만든다. timed-ENTRY retry는 `completed_5s=true`, `phase_end=HOLD`, `stop_reason=source_terminal`인데 [색인:107](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v19.md:107)과 108행의 두 영상이 “아니오”로 표시됐다. 현재 v19를 그대로 보존하고 별도 v20 metadata에서 실제 controls/trace 근거로 정정하는 방안을 root가 선택했다. v20 완료 여부는 이 검수에 포함하지 않는다.
- Suggestion: 없음.

직접 대조한 범위:

- 스냅샷은 2026-10-10 07:22:14 KST. 검사 대상 284경로는 기존 SHA 매핑 158, 신규 복사 94, 신규 SHA alias 18, partial/실패 제외 14로 분해된다. 보존 사본 제외 672와 스냅샷 뒤 lateral-staging 영상 두 경로를 분리한 목록은 정합하다.
- manifest의 기존 172개 전후 SHA/크기와 현재 archive 266개 SHA를 대조했다. 신규 94개는 원본·사본·기록된 복사 전후 SHA가 모두 같고, 대상 284개 source의 현재 SHA도 일치한다. 새 영상의 추가 인코딩은 없다.
- 신규 94개에 실제 ffprobe를 실행하여 codec/크기/frame count/fps/stream duration을 전부 대조했다. stream 5.033333초와 MP4 container 5.034초는 서로 다른 metadata이며 불일치 오류로 세지 않았다. 색인의 절대 링크와 신규 94개 copy 연결도 확인했다.
- terminal-retract의 적시 hit 4회는 부분 결과이며, source terminal 뒤 5초까지 HOLD한 영상 길이는 완성 연주나 평형 인증이 아니다. `complete_video`는 파일의 검사·복사 분류이지 모든 역사적 trial의 5초 성공 인증이 아니다.

검수한 SHA256:

| 파일 | SHA256 |
|---|---|
| collect_videos.py | `938b045891e3f85c3fcee966d767bfd1b4bce902575ffbedd9ca1893f10bddf6` |
| video_manifest_v19.json | `b7d1bb0fb2abb1be1dbb391a90f6b974fc62c4f89567b67856e9c8e37e35b275` |
| VIDEO_INDEX_v19.md | `1e94450053bf77abda126a1057d42a309ae1fd38a8e81c526f67bdea9aaf34dd` |

영상 내용의 전체 물리·음악 성능을 다시 인증하지 않았으며, 알려진 두 HOLD 표기를 제외한 현재 복사·SHA·영상 metadata 대조에는 남은 문제가 없다.
