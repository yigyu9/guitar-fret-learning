# 2초 준비·에피소드 종료 녹화 독립 최종 검수

판정: **PASS — 문제없음**. 현재 Critical / Warning / Suggestion 없음. 완료된 것은 준비 시간·가변 길이 녹화 기능이며 음악 완주·연주 문제 해결은 아니다.

| 실행 | 저장 원자료에서 확인한 결과 |
|---|---|
| v1 | 2400 physics steps / 10초 / actor 0 / `preparation_timeout`, 301 frames / 영상 10.033333초 |
| v2 | 2.00초 handoff / actor 93 / 852 steps / 3.55초 `source_failed_terminal`, 108 frames / 영상 3.600초 |

v2 마지막 actor 행의 `done=True`, `wrong_crossing_count_termination=True`, `goal_finished=False`를 확인했다. 완료 info에서 다시 합산한 적시 타현 1 / physical 타현 1 / release 4 / miss 1 / wrong 4가 분석과 일치한다. source physical 타현은 가상 피크 교차 판정이며 강체 접촉 횟수가 아니다. 저장된 오른손–기타 접촉은 2.85초 RH:pinky3–G:body 한 행/raw lambda 0이며, 표본 사이 접촉이나 연속 clearance를 인증하지 않는다.

확인한 검증 범위:

- v1/v2 준비 native trace 61개와 전환 전 controls 120개는 동일하다(control의 새 `entry_region` 관측 필드만 제외). 61회×두 시야 camera prefix SHA도 동일하다. PREP에서 actor는 없고 곡 시계는 초기 값에 고정된다.
- 두 실행의 초기값 파일은 동일하며 실행 checks는 모두 true다. 입력 closure **1122 / 1127개**를 현재 파일 또는 각 실행 `source_before`의 정확한 보존본으로 대조했다. 실행 뒤 main 문서 3개가 각각 보존본으로 해소됐으며 미해소 입력은 없다. 두 분석의 직접 입력은 **각 8개**로 시작·종료 및 현재 SHA가 일치한다.
- v2의 0~848 step/8 간격에 **852 step 최종 frame**이 추가돼 native trace/report/capture 끝이 일치한다. 종료 뒤 추가 actor/물리를 진행하지 않는다. 모든 v2 frame SHA와 실제 영상 네 개의 ffprobe(1280×720, 30fps, frame 수·stream duration), 원본·복사본 SHA가 일치한다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_two_second.md:1)은 물리 시간과 재생 길이를 구분한다.
- [2초 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/images/frames/whole_body/00060.png)과 [3.55초 frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/native/data/images/frames/whole_body/00107.png)을 직접 확인했다. 카메라 step480/852와 준비·원본 실패 종료 캡션이 맞으며, 이미지를 물리 평형·성공 증거로 설명하지 않는다.
- [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md:31), v1 설명, [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/CHANGED_FILES.md:1), [PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:505), [main README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1801), [workflow](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:135)의 경로·실제 줄 위치를 확인했다. 진입 0.1°는 bounds 확장으로 표시하고 원래 strict 결과/음악 성공 기준을 보존한다. step480은 strict false / entry true이고 허용 reference와의 거리 0.028954°이며 전역 최근접 증거가 아니다.
- 이전 분석기 Warning은 별도 v2에서 actor 요청 행과 info 있는 완료 행을 구분해 해소했다. 이전 코드·검수 기록은 보존된다. 초기 raw 자체가 없는 실패까지 처리하는 분석기로 범위를 넓혀 주장하지 않는다.

검수 시작·끝에 코드/문서/metadata **14개**, 직접 raw·분석·실행 metadata **22개** SHA를 대조해 변경 없음을 확인했다. 실행에 소비된 primary 코드도 실행 입력 SHA와 일치했다. [recording_audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/recording_audit.json:1)의 21개 검사와 원자료를 대조했다. 이후 최종 보존 감사·봉인은 root의 별도 작업이다.

| 검수 소스·기록 | SHA256 |
|---|---|
| v2 runner | `d727a9ddb61b09424b59c9e1d2ccefecfec0a76acf158bf30fe0a6aba2d79383` |
| 회전 helper | `3dd77ecc5f71c920dd5f8f7fd5ef4f4ffbdd8baa05cce5adebf5de30654d7f20` |
| v2 분석기 | `980e22c6be9ed666d2cf808fa2eb2b6499ff557818a33629201a38fe8206f2da` |
| recording audit | `d28da6b150fda0d5ece9a731404f540176078122caac1c199dbbb0fbc1d9ea25` |

검수의 native 초기화·물리 재실행·다른 파일 변경은 0이다. 전체 곡 성공, GPU 동등성, 연속 접촉·mesh clearance는 미검증이며 실제 v2는 wrong 4에 의한 실패 종료다.
