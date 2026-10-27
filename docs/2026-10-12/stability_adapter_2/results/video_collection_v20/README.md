# Video collection v20 metadata correction

v20은 v19 영상 모음을 바꾸지 않고 메타데이터만 교정한다. v19가 두 `strike_timed_entry_v1/native_retry_v1` 영상에 `continued_in_hold=false`를 기록했지만, 원본 report는 `phase_end=HOLD`, `stop_reason=source_terminal`이고 raw controls에는 79개 HOLD 제어행이 연속 기록되어 있다. 첫 HOLD 시각은 3.683333초이며 raw trace에도 41개 HOLD 표본이 기록되어 마지막 5.0초까지 이어진다. 이에 v20은 두 영상의 HOLD 여부를 true, 시각을 3.683333초로 고친다.

기존 v19 index/manifest, report, controls, trace, collector와 이 producer의 SHA-256을 실행 전후 기록·대조했다. 기존 266개 archive 파일의 SHA도 inventory 값과 각각 비교했으며, 새 MP4 복사는 0개다. v19 원본은 변경하지 않는다.

- [v19 index 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v19.md)
- [v19 manifest 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_manifest_v19.json)
- [v20 index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v20.md)
- [v20 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_manifest_v20.json)
- [수정 대상 native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/report.json), [controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/controls.json), [trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/trace.json)
