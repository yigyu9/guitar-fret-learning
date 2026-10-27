# 독립 사전 검수

판정: **PASS — 문제없음**. Critical / Warning / Suggestion: 현재 남은 항목 없음. 이 기록은 실행 전 코드 검수이며 native 실행·영상·연주 결과를 인증하지 않는다.

- [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_two_second_episode.py:37), [wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_two_second_episode_preserved_run.py:1), [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TWO_SECOND_EPISODE_PLAN.md:5) 및 메인 PLAN/README 마지막 추가 절을 기준 staging-damping 코드와 비교했다. Python 3.8 AST 문법을 확인했다.
- [시간 전환](/home/ajou/yigyu/3/stability_adapter_2/run_strike_two_second_episode.py:282)은 기존 준비 조건과 물리 시간 2초를 함께 요구한다. 준비 미충족 상태의 10초 경계는 별도 실패 종료다. 실제 분기 AST를 추출한 12개 경계 사례가 통과했다. 초기값·PREP 제어와 `advance` / `integrate` / `sample` / `left_target`의 제어 내용은 기준과 동일하다.
- 5초 녹화 cap을 제거하고 원본 full-song episode horizon에 준비 최대 시간만 더한 보호 한도를 둔다. 원본 done 뒤 actor/물리를 추가 진행하지 않고 goal-finished·실패·준비 timeout·어댑터 안전 중단·watchdog를 구분한다. [최종 상태 저장](/home/ajou/yigyu/3/stability_adapter_2/run_strike_two_second_episode.py:328)은 카메라 격자 밖 종료 frame도 포함한다. 원본 goal-finished는 실패 종료를 제외한 원본 정의이며 전체 음표 정확도 인증과 구분된다.
- 해소된 Warning: 정리 과정에서 close/encode 실패가 raw 저장을 막던 순서를 [raw 선저장과 개별 예외 기록](/home/ajou/yigyu/3/stability_adapter_2/run_strike_two_second_episode.py:345)으로 보완했다. 실제 finally AST의 모의 동시 실패에서 controls/trace/report가 저장되고 완료 표시는 false이며 기존 실패 원인도 유지됨을 독립 확인했다. 물리/API 실행은 하지 않았다.

최종 검수 시작·종료에 기준/신규 코드와 계획·메인 문서 7개 SHA를 대조해 변경 없음 확인. 초기 초안 이후 수정된 파일은 위 정리 보완 runner 하나이며 최종본을 별도 봉인 기준으로 검수했다. [transition_preflight_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v1/transition_preflight_v2.json)의 입력 SHA도 현재 코드와 일치한다.

| 파일 | 검수 SHA256 |
|---|---|
| 기준 runner | `9daeed8eb4a5f41b3532fa1fd938f49358fb6d6b4d20f1bce19cc813b199338e` |
| 신규 runner | `d7271e8a1a91cbf85ba1ce8b17ebb1c88a3238f50c2ec9037f81e5c3ebb51c78` |
| 신규 wrapper | `a0e8ac83ae3cc21755e9070769acdb0e78bc526d65b118aa9f328669d1751458` |
| 신규 계획 | `2d59498986149231e0819b43cc9187aaf71c4757027aba373930be330d00822f` |

실제 준비 유지·handoff·원본 종료·가변 길이 raw/영상·마지막 frame와 입력 closure는 후속 native 결과 검수 대상이다. 이번 검수의 native 초기화/물리 실행은 0이며, 별도 가변 길이 분석기는 후속 검수 대상으로 남긴다.
