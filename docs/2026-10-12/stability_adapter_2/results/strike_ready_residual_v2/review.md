# READY 실제 pick 기반 잔차 진단 검수

요약 판정: 문제없음. Critical 없음. 검수는 소스·저장 결과 읽기, 독립 목표/좌표/수치/SHA 대조와 영상 확인에 한정했다. native·actor·IK solver·분석기·그림 producer를 재실행하거나 타담당 파일을 수정하지 않았다.

- [runner](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_residual_v2.py:123)는 현재 native `RH:pick` world 점에 `currentChestDelta*(FK(v)-FK(actual))` 변위만 더한다. 실제 점을 읽어 anchor로 쓰며 state/기타 외력을 제출하지 않는다. source READY0에서 Shoulder/Elbow/Wrist 9축만 actual±.15/native 교집합에서 fit하고, 정책 목표에 제한된 잔차를 더한다. Thorax 3축 및 PREPARE의 12축 IK와 구분된다. 원본 source phase·READY·검출기·정책 weights/RMS는 변경하지 않는다.
- 자동 시작 기준과 초기 native 상태, 81 초기각, PD 속성·native limits, right rate 3.2 및 gain 1이 exact다. 최초 49개 PREPARE 최종 목표도 기준과 exact다. 실제 1200 steps/151 frames/300 controls, 16 runtime checks true, actor 251, PLAY 진입 0.8166666666666667 s, 종료 PLAY/실패 없음이다. 접촉 소실을 지속 중단 조건으로 바꾸지 않았다.
- 300개 요청 목표를 float32 rate/native clip으로 재조립해 최종 81 목표와 exact를 확인했다. other36 유지 및 native bounds도 확인했다. native mids/halfs·source action scale 1로 모든 최종30 목표의 history를 독립 역변환해 오차 0이다. 이후 251개 actor observation history는 직전 최종 history와 exact이며 progress는 1…251이다. source motor phase는 모두 0이다.
- 251개 잔차에서 9축 인덱스·actual 각·policy+correction→요청 목표가 일치한다. 최대 절대 보정은 0.13892755024755815 rad로 .15 경계에 닿지 않는다. 저장 native 시점과 맞는 125개 control에서 actual81·native pick anchor·Chest 회전 변환 및 current-G READY world 변환을 독립 대조했다. source FK 변위 모델을 actual cooked 접촉 또는 동적 전달함수 인증으로 확대하지 않는다.
- raw world p/q에서 기타 오차를 독립 재계산했다. 최소 정책 READY 거리 10.439381133 mm, 범위 안 전체/정책 표본 119/300 및 73/251, 최대 위치/회전 변화 46.353645732 mm/46.014401355°, 종료 25.494145982 mm/44.083733732°다. pulse 합계는 target hit 0/physical target hit 0/release 2/miss 10/wrong crossing 3, accepted release 0이다. source READY 획득·타현·완전 song 성공으로 표시하지 않는 표와 결론은 타당하다.
- native before 1016 inputs/272 source copies를 대조했다. 종료 변경 0/task error 없음이며 현재 입력은 승인된 main README/PLAN append 두 개 외 1014개 SHA exact다. main_before_progress→native source_before→현재 main의 원문 prefix도 각각 exact다. 분석 7개 직접 입력의 현재 SHA 및 before/after 변경 0을 확인했다. consumed runner/wrapper/leaf는 보존 사본과 현행 SHA가 일치한다.
- capture 302 native PNG의 실제 SHA/151 readonly 표본 및 시각을 확인했다. frame 0/60/150이 0/2/5초다. 두 MP4의 실제 SHA 및 독립 ffprobe는 각각 151 frames/30 fps/5.033333 s다. 실제 5초 손 PNG도 확인했다. 이번 단계에 새 과학 그림 생성은 없으며 native 자료를 재사용한 문서다.
- [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_residual_v2/README.md:5)의 9축 정정 및 정정 전 문서 사본, 표·범위·영상 embed·실존 링크와 main [PLAN:263](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:263)/[README:1568](/home/ajou/yigyu/3/stability_adapter_2/README.md:1568)을 확인했다. 보정 후 미세 거리 개선과 여전히 인정 타현 0을 분리했다. 원 v1은 미실행 보존이며 이번 v2와 혼동하지 않는다.
- 후속 PI 사전 delta도 읽기 검수했다. [preview](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_integral.py:149)는 raw goal float32→native bounds→float32 rate/60→최종 float32로 실제 submit 순서와 일치한다. 이전 float64 preview Warning은 해결됐다. P±.15/I±.3/합성±.3 및 READY0 갱신·이후 I 유지 범위는 계획과 정합하며 실제 실행에는 `--right-rate 3.2`를 명시한다. 이는 PI 물리 결과의 인증이 아니다.

검수한 SHA-256:

- residual runner: `b628ad4eaa7a3570c5a64be8326d22eafc6fad8ab2f30fd9652c690754b0a95a`
- residual wrapper: `a4eba74b4869c734ac8ead4ed1f5a8568781bd76836c0d15d49c95c488b9c95d`
- residual leaf: `c75b3b097cc737c4f47758a1ac5cc1bd56aca5a7c86aacc12d5d104964bb3c5f`
- analyzer: `9f0e9facc6dcb099f7808bd5ca959c61e7dc0c670c673ce40c223beeda38e264`
- analysis summary: `855b285d7c345726f0afbd882dc4883cf62cb9492ef0f5dc6ed0fed04f3babd1`
- README: `6625d48951ef5276301924326b0946f55e5f29cdf5436a6a4734db7cb66de3fb`
- CHANGED_FILES: `427877500154396b2419b25296224922e52ccd49c3073283d4c67b46b84e82bf`
- PI runner 사전본: `eefb3a102b826986b02c52ec6b085267da05eac15089ed5ee3726d92172ff6f2`

최종 판정: PASS
