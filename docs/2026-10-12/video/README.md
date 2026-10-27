# 2026-10-12 실험 영상 보관소

이 보관소는 `docs/2026-10-12` 아래 기존 `.mp4`, `.webm`, `.mov`, `.avi`, `.mkv` 원본을 상대 경로 그대로 바이트 복사해 모았습니다. 원본 1,362개, 총 373,017,061 bytes(약 373 MB)를 복사했고, 전부 원본 전후 SHA-256·크기·수정시각과 복사본 SHA-256이 일치했습니다. 내용이 중복되는 파일도 제거하지 않고 보존했습니다. 1,362개 파일은 1,362개의 독립 실험을 뜻하지 않습니다.

- 전체 실험별 영상 색인: [archive_v1/index.md](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/index.md)
- 파일별 출처·SHA-256·bytes·ffprobe 정보와 입력 문서: [metadata/manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/metadata/manifest.json)
- 보관 계획: [ARCHIVE_PLAN_V1.md](/home/ajou/yigyu/3/docs/2026-10-12/video/ARCHIVE_PLAN_V1.md)

## 폴더별 개수

| 원래 폴더 분류 | 파일 수 |
|---|---:|
| 중앙 `stability_adapter_2/videos` 모음 | 278 |
| `quiet_wrist_z_support_authority_v1` | 176 |
| `quiet_index_support_authority_v1` | 172 |
| `quiet_wrist_support_authority_v1` | 172 |
| `interactive_guitar_pose_v1` | 154 |
| `strap_fallback_training_v1` | 36 |
| 그 밖의 날짜 폴더 영상 | 374 |

분류는 기존 결과 경로의 폴더 이름을 사용했습니다. 세부 전체 목록은 색인에서 확인할 수 있습니다. 중앙 videos 모음과 이름에 `backup`, `copy`, `collection`, `snapshot`이 포함된 경로는 기존 실험 폴더 복사본과 구분해 별도 분류합니다. 같은 영상 내용의 복제본은 각각 유지합니다.

## 최근 학습 결과 대표 영상

`stability_priority_training_v1`의 OFF/ON 장기 학습 첫 평가 영상을 나란히 확인할 수 있습니다. 각 쌍의 길이와 프레임 수는 색인과 manifest에 있습니다.

- OFF: [whole_body.mp4 보관본](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/stability_priority_training_v1/long_off_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)
- ON: [whole_body.mp4 보관본](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

![stability_priority_training_v1 OFF 첫 평가 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/stability_priority_training_v1/long_off_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

`strap_fallback_training_v1`의 초기 비교 영상입니다. 제목과 해석은 원본 실험 문서에서 확인하세요.

- [전신 비교 영상 보관본](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_whole_body.mp4)
- [손 비교 영상 보관본](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_hands.mp4)

`deadline_training_v1`은 smoke 검증 및 장기 실행 결과를 각각 보존합니다. 원본 보고서는 장기 v3 실행이 9회 갱신 후 중단되었다고 기록하므로 이를 완료된 학습으로 부르지 않습니다.

- [smoke v2 update 1 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/deadline_training_v1/smoke_v2/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)
- [장기 v3 update 1 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v1/stability_adapter_2/results/deadline_training_v1/long_run_v3/evaluations/update_000001/native/episode_0001/media/whole_body.mp4)

## 검증 범위

ffprobe는 복사본 1,362개 모두에서 영상 스트림을 찾았고 실패는 0개였습니다. manifest에는 파일별 재생 시간, 프레임률과 확인 가능한 프레임 수를 기록했습니다. 재생 정보는 컨테이너 분석 결과이며 실험의 성공 여부를 판정하지 않습니다. 이번 수집은 실행을 추가하지 않았고, 날짜 폴더 내 새 파일을 자동으로 수집하는 기능도 만들지 않았습니다.
