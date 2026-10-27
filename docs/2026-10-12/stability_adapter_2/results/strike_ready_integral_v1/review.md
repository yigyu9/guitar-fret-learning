# READY PI 독립 검수

요약 판정: 문제없음. Critical/미해결 Warning 없음. 저장 자료·소스·문서의 읽기 및 독립 산술/SHA/영상 검수만 수행했다. native, actor, solver, 분석기, producer를 재실행하지 않았고 이 review 외 파일을 수정하지 않았다.

- [PI 구현](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_integral.py:146)은 오른쪽 Shoulder/Elbow/Wrist 9축에만 actual pick anchor 기반 P 및 I를 합성한다. P±.15, I±.3, 합성±.3과 실제 float32 rate/native bounds를 사용하는 anti-windup이 계획과 일치한다. 기타 상태/외력, source phase·READY·검출기·weights/RMS를 직접 설정하지 않는다. 다른 관절의 기존 제어 구성은 유지한다.
- P-only 기준과 초기 native 상태, 81 초기각, PD 속성, native limits, right rate 3.2/gain 1이 exact다. 최초 49 PREPARE 최종 목표도 exact다. 이번 실제 실행은 1200 steps/151 frames/300 controls, 251 actor, 16 검사 true/실패 없음, PLAY 진입 0.8166666666666667 s다.
- 모든 300개 최종81 목표를 float32 rate/native clip으로 재조립해 exact를 확인했다. other36 유지와 native bounds도 확인했다. native mid/half 및 source scale 1로 최종30 history를 독립 역변환해 오차 0이며, 251개 후속 actor observation history는 직전 최종 history와 exact다.
- source READY0에서 P/I 갱신 27회, 이후 phase1에서 I 유지 224회를 실제 controls로 확인했다. 제안 I, raw float32 goal, rate/model preview, `P*(rawGoal-finalPreview)>1e-12` 차단 mask, conditional I 및 최종 합성까지 독립 재계산해 기록과 exact다. 최대 |P|/|I|/|P+I|는 0.06532322236113769/0.1073220597878278/0.12173542971436813 rad다. 유지 224회 모두 동일한 마지막 I이며 cap을 넓혔다고 해석할 근거는 없다. 저장 native 시점과 일치하는 13개 갱신 control에서 actual81·pick anchor·Chest/G world 변환도 대조했다.
- 마지막 I는 `[-0.049489556408549205, 0.08750505248475458, -0.1066225078691333, -0.01022751045323782, -0.06251585397350484, 0.1073220597878278, 0.008286432896875393, -0.09042514300727669, 0.08873856758972788]` rad다. I 증분의 .2는 제어 표본당 계수이며 .2초 간격이 아니다.
- raw p/q와 controls로 [summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/analysis/summary.json:1)를 독립 대조했다. 최소 정책 READY 거리 3.240488132 mm, 범위 안 전체/정책 표본 251/300 및 205/251, 최대 기타 위치/회전 변화 46.353645732 mm/8.991360351°, 종료 39.285218736 mm/5.300883246°다. source phase `[0,1]`, READY success 1 및 첫 APPROACH 1.2666666666666666 s를 확인했다. target/physical target hit/accepted release는 모두 0, release 1/miss 10/wrong crossing 1이다. release는 1.0333333333333334 s의 phase0/string3/target2/phase violation true다. READY 획득을 인정 타현·전체 song·지속 범위 성공으로 확대하지 않은 문서는 타당하다.
- native 입력 1019개/사전 source 사본 275개를 대조했다. 종료 변경 0/task error 없음이며 현행 입력은 승인된 main README/PLAN append 외 1017개 SHA exact다. 두 main은 native 사전 원문 prefix를 보존한다. 분석기의 7개 직접 입력 현재 SHA 및 before/after 변경 0도 확인했다. consumed runner/wrapper/leaf 원문은 현행 및 사본과 일치하며 Python 3.8 AST를 통과한다.
- 302 native PNG의 실제 capture SHA/151 readonly 표본 및 시각, 0/2/5초 frame 0/60/150을 확인했다. 두 MP4 실제 SHA와 독립 ffprobe는 각각 151 frames/30 fps/5.033333 s다. 실제 5초 손 PNG도 확인했다. 접촉·관통·PD 힘 또는 source FK 전달함수의 일반 인증으로 확대하지 않는다.
- 최종 [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_integral_v1/README.md:3)·CHANGED_FILES의 9축/12축 구분, 수치·tradeoff·영상 embed·실존 링크는 정합한다. main [PLAN:275](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:275)/[README:1580](/home/ajou/yigyu/3/stability_adapter_2/README.md:1580)의 후속 phase-target 목표선택과 source 판정 불변 설명도 계획과 일치한다. 해당 후속 실험의 성능은 이번 검수에 포함하지 않는다.

최종 SHA-256:

- runner: `eefb3a102b826986b02c52ec6b085267da05eac15089ed5ee3726d92172ff6f2`
- wrapper: `ca648adaf1b0e4e9e4e7ed5b9a15d80e08e8faa65d8198c94127320c639654c8`
- leaf: `36c56fdce5bde18738547392b475a6817d63dd848afc2b38a4f82b8138d39bf1`
- summary: `677af4750236b0e5c3096c667e61aaa017862055a9fa356620317c74a4936989`
- README: `f0eb2dafd10fd72441a943ff3620f9020b6dac9c0bbf98c1e16a7cdfb348cecf`
- CHANGED_FILES: `062584c8fc24b02f7a173ae5a4d68db3f57d5c59dd5223a08dfd7c91527321d1`

최종 판정: PASS
