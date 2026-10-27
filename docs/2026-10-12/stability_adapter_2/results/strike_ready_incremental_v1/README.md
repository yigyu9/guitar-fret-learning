# Strike READY incremental 목표 진단

이 5초 native 진단은 free-finger-curl 조건을 유지하면서 source READY(phase 0)와 RECOVER(phase 2)에서 오른팔 R9 목표를 `이전 제출 목표 + 2 × bounded local IK correction`으로 계산했다. 열린 APPROACH(phase 1)에서만 source policy+PI arm 목표를 쓰도록 했고, 적분 상태는 READY·닫힌 APPROACH·RECOVER 동안 보존했다. 원본 READY·타현·timing·clearance 조건을 변경하거나 완화하지 않았다. Source geometry 5는 원래 RECOVER의 release lift/next-entry lift/next-READY clearance target을 포함한다. [goal 계산 및 phase 분기](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:183), [phase geometry와 time gate](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:157), [실험 계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_READY_INCREMENTAL_PLAN.md:1).

**결과: 연주 성공 미달.** Native 실행은 1,200 physics steps, 151 camera frames, 23/23 checks 완료다. Native input closure 1,097개는 변경 0, analysis 입력 7개와 goal audit 입력 6개도 각각 unchanged였다. PREPARE/PLAY/HOLD는 49/162/89 control samples다. 저장 source motor phases는 `[0, 2]`: phase 0 READY에서 phase 2 RECOVER로 넘어갔고 APPROACH phase 1은 관측되지 않았다. 따라서 open/closed APPROACH control samples는 0이다. Source는 wrong-crossing count로 3.516667초 종료했지만 physics와 camera 기록은 HOLD에서 5초까지 계속됐다. READY success 0, 학습 update 0이다.

첫 physical/accepted hit은 0.933333초 event 0, string 2 DOWN이었다. 그러나 source phase 0 READY에서 발생한 crossing이었고 timing −382.090790 ms의 premature release라 timely target hit는 0이다. 이후 wrong crossing이 누적돼 terminal 됐다. 집계는 physical target hit 1, accepted release mask 1, physical release 5, miss 6, wrong crossing 4다. 이 hit을 성공 연주로 해석하지 않는다.

처음 READY 접근에서 target의 Guitar-local z는 20.3 mm였다. 저장 native state의 pick z는 0.8초 39.180 mm에서 0.933333초 11.333 mm로 이동했고, 같은 시점에 위의 이른 physical crossing이 기록됐다. 이는 관측된 trajectory 관계이지 목표 ownership만의 원인 판정은 아니다. max/end 기타 회전 변화는 7.095455°/5.607060°, 위치 변화는 46.353646/40.855469 mm다. Playable region 표본은 전체 control 283/300, PLAY policy 148/162이고 minimum PLAY policy pick-to-READY 거리는 3.501140 mm다.

`goal_audit.json`은 free-finger-curl 실행과 비교해 PREPARE controls 49개, sampled native trace prefix 25개, 첫 actor observation/action exact를 확인했다. 또한 READY goal 8행과 RECOVER goal 154행, 닫힌/열린 APPROACH 각 0행에서 `previous_goal + 2δ` 공식 최대 오차 5.93e−8 rad 및 적분 보존을 확인했다. 이는 시작 prefix와 저장된 requested/final goals audit이며 전체 trajectory 동일성, 접촉 인과성, 연주 성공 인증이 아니다. 이전 [free-finger-curl 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_free_finger_curl_v1/README.md:1)도 timely hit 0·physical hit 1의 조기 crossing이었다. 이번 phase 역시 적시 타현을 얻지 못했다.

## 실행·분석 자료

- [Native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/report.json), [native closure](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/inputs_after.json): 1,200 steps, 151 camera frames, 23 checks, closure 1,097개 unchanged와 source terminal 뒤 HOLD.
- [Analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/analysis/summary.json), [analysis inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/analysis/inputs_before.json), [after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/analysis/inputs_after.json): pulse·phase·region·pose 요약과 analysis SHA 불변.
- [Goal audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/goal_audit.json): 6개 입력 SHA 불변, prefix 및 READY/RECOVER requested/final goal 검증.
- [Initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/initial_values.json), [initial audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/initial_audit.json), [checkpoint connection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/checkpoint_connection.json): native 시작 상태와 frozen policy/goal ownership metadata.
- [Native controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/controls.json), [native trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/trace.json): 300 control rows와 152 trace rows. 8-step grid의 151개 sample 뒤 physics step 844/3.516667초에 HOLD terminal sample 1개가 추가된다. Camera 기록은 별도로 151 frames다. [Camera capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/capture.json)와 [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/videos.json)는 camera/frame provenance를 담는다.
- [Runner goal logic](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:183), [policy/finger ownership and recorded goals](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:147), [post-terminal HOLD loop](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:278).

## 저장된 native 전신·손 capture

정지 이미지는 native camera frame이다. 0초는 초기 상태, 0.933333초는 첫 physical/accepted crossing sample에 대응하는 capture 시점, 2초는 PLAY, 5초는 3.516667초 source terminal 뒤 HOLD에서 이어진 physics 상태다. 두 영상은 각각 151 frames, 30 fps, 5.033333초다.

| 시점 | 전신 | 손 |
|---|---|---|
| 0초, 초기 상태 | ![전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/whole_body/00000.png) | ![손 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/hands/00000.png) |
| 0.933333초, 첫 조기 physical/accepted crossing | ![전신 0.933333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/whole_body/00028.png) | ![손 0.933333초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/hands/00028.png) |
| 2초, PLAY | ![전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/whole_body/00060.png) | ![손 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/hands/00060.png) |
| 5초, HOLD·physics 지속 | ![전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/whole_body/00150.png) | ![손 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/frames/hands/00150.png) |

![전신 native video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/whole_body.mp4)

![손 native video](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/native/data/images/hands.mp4)
