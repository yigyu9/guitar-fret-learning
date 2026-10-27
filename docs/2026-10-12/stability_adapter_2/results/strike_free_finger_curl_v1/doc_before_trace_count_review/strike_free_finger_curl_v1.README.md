# Strike free-finger curl 진단

이 5초 native 진단은 기존 POSITION timed-wait-rebase 조건을 기준으로, PLAY에서 RH:middle2, RH:middle3, RH:ring2, RH:ring3 네 관절의 source policy requested goal에만 +0.2 rad residual을 더했다. 나머지 17개 RH finger 목표, 그중 pinch group 9개는 policy 요청 그대로 유지했다. actor는 frozen 303-observation/30-action checkpoint를 계속 실행했다. 준비 각도, source clock/detector, R9 policy+PI와 source phase 1 damping schedule은 변경하지 않았다. [대상 관절·goal 수정](/home/ajou/yigyu/3/stability_adapter_2/run_strike_free_finger_curl.py:70), [pinch 보존·free4 residual checks](/home/ajou/yigyu/3/stability_adapter_2/run_strike_free_finger_curl.py:148), [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_FREE_FINGER_CURL_PLAN.md:1).

**결과: 연주 성공 미달.** 1,200 physics steps와 151 native camera frames를 기록했고 23/23 contract checks가 통과했다. Native closure 1,094개는 변경 0, 분석기 입력 7개 SHA도 before/after unchanged다. PREPARE/PLAY/HOLD는 49/155/96 control samples였다. Source는 wrong-crossing count로 3.400000초 종료됐지만, native physics와 기록은 HOLD에서 계속되어 5초 전체를 채웠다. actor는 PLAY에서 155 step 실행했고 학습 update는 0이다.

Timely target hit은 0이었다. 첫 physical/accepted hit은 1.366667초 event index 1, string 2 DOWN이었지만 타이밍 −226.674256 ms의 premature release라 timely hit로 인정되지 않았다. 해당 hit의 scheduled recovery completion은 false였다. 1.566667초 ordinary recovery pulse는 있었지만 scheduled recovery pulse는 false였다. 합계 physical target hit 1, accepted release mask 1, physical release 5, miss 5, wrong crossing 4다. 이 결과는 source timing 판정과 physical/geometry crossing을 구분한다.

기타 회전 변화는 최대 9.229756°·종료 4.805715°, 위치 변화는 최대 46.353646 mm·종료 36.271020 mm였다. Playable region 표본은 전체 control 233/300, PLAY policy 91/155다. 최소 PLAY policy pick-to-READY 거리는 1.802802 mm다. 부분 점수와 실제 physical hit 하나를 전체 연주 성공으로 해석하지 않는다.

기준 [POSITION timed-wait-rebase 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_wait_rebase_v1/README.md:1)는 timely hit 1회, 최대 회전 변화 7.095455°, region 표본 164/178 PLAY policy를 기록했다. 이번 curl trajectory는 timely hit 0회이며 region 표본 91/155다. 두 결과의 값은 각 저장 실행의 관측치이고, 차이를 손가락 residual 하나의 인과효과로 확대하지 않는다. 후속 [READY incremental plan](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_INCREMENTAL_PLAN.md:1)은 같은 finger condition에서 팔 goal ownership을 별도로 다루는 계획이며 본 결과의 검수나 완료를 대신하지 않는다.

## 실행 및 분석 자료

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/report.json), [native closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/inputs_after.json): 1,200 steps, 151 frames, 23 checks, 1,094 inputs unchanged, terminal 뒤 HOLD 계속 실행.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/analysis/summary.json), [analysis SHA before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/analysis/inputs_after.json): pulse·phase·region·pose summary와 7개 analysis inputs의 SHA 불변 기록.
- [Initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/initial_audit.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/checkpoint_connection.json): 시작 관절/상태와 frozen policy·free finger 설정.
- [Native controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/trace.json): 300 control rows, 151 native state samples; 각 pulse와 curl requested targets 저장.
- [Native capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/capture.json), [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/videos.json): still/video capture provenance.

## 저장된 native 전신 및 손 이미지·영상

정지 이미지는 Gym native camera의 실제 capture다. 0초는 초기 상태, 1.2초와 3초는 PLAY 중, 5초는 3.4초 source terminal 이후 HOLD에서 physics가 이어진 상태다. 전신·손 영상은 각각 151 frames, 30 fps, 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초, 초기 상태 | ![전신 0초 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/hands/00000.png) |
| 1.2초, PLAY 중·첫 physical hit 전 | ![전신 1.2초 PLAY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/whole_body/00036.png) | ![손 1.2초 PLAY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/hands/00036.png) |
| 3초, PLAY 중·source terminal 전 | ![전신 3초 PLAY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/whole_body/00090.png) | ![손 3초 PLAY](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/hands/00090.png) |
| 5초, HOLD·physics 지속 | ![전신 5초 HOLD](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초 HOLD](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/frames/hands/00150.png) |

![전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/whole_body.mp4)

![손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/native/data/images/hands.mp4)
