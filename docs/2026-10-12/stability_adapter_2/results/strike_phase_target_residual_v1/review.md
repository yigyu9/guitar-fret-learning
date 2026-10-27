# Phase-target 첫 인정 타현 진단 검수

요약 판정: 문제없음. Critical/미해결 Warning 없음. 소스·저장 결과 읽기, 독립 수치/SHA·미디어 대조만 수행했다. native/actor/solver/분석기/producer를 재실행하지 않았고 이 review 외 파일을 수정하지 않았다.

- [selector](/home/ajou/yigyu/3/stability_adapter_2/run_strike_phase_target_residual.py:133)는 원본 geometry의 READY=3/ENTRY=4/EXIT=5를 사용한다. source phase0/1/2, event/string/direction key, 실제 entry 거리와 threshold로 모든 111개 actor control의 flag와 geometry index를 독립 재계산해 일치함을 확인했다. adapter flag는 목표 선택용이며 원본 FSM/entry 판정/검출기/시간/weights를 직접 설정하지 않는다. source 회복 함수는 clearance가 활성일 때 이미 geometry5를 release-lift/후속 clearance 점으로 교체한다. source에 lift가 없었다고 해석하지 않는다.
- READY PI 기준과 초기 native 상태, 81 초기각, PD 속성, native limits, right rate 3.2/gain 1 및 최초 49 PREPARE 목표가 exact다. 16 runtime checks true, native 입력 1025개 종료 변경 0/task error 없음이다. 실제 1200 physics steps/151 camera frames를 완료했지만 actor는 111회다. PREPARE 49/PLAY 111/HOLD 140이며 source wrong-crossing-count terminal은 step640/2.6666666666666665 s다. 이후 HOLD에서는 actor·목표·history·source clock이 유지된다.
- PREPARE/PLAY 목표의 float32 rate/native clip과 HOLD 목표 동결을 독립 대조했다. 전체 300개 최종81 목표, other36 유지, native bounds 및 최종30 history 역변환은 exact다. 111개 actor observation history는 직전 최종 history와 exact이며 progress는 1…111이다. 111개 P/I 제안·raw float32 goal·rate/model preview·anti-windup mask·conditional I·합성 보정과 저장 요청 목표도 독립 재계산해 일치한다. P±.15/I±.3/합성±.3을 유지한다. 저장 native 시점과 맞는 actor control에서는 actual81/pick anchor/Chest/current-G 변환도 대조했고 ENTRY 선택 시 실제 거리식도 확인했다.
- [교정 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_phase_target_residual_v1/analysis_phase_corrected/summary.json:1)의 pulse를 raw info에서 재집계했다. target hit 1/physical target hit 1/accepted release 1, release 5/miss 2/wrong crossing 4다. hit control의 시작시각 필드는 2.4833333333333334 s이며 string2/phase1/phase violation false, `info.timing_error_ms=45.17984390258789`이다. 이는 해당 control에서 반환된 event 기록이며 별도의 연속 접촉 timestamp 측정으로 확대하지 않는다. 마지막 running F1 .25는 source 실패 종료/goal_finished false의 부분 값으로 완전 song 성공이 아니다.
- source phase2의 10개 보정 control은 geometry5를 선택하며 clearance_required true/lifted false/reached false다. 원본 높이를 변경하지 않았고 실제 회복 실패를 숨기지 않았다. raw quaternion/world p에서 독립 재계산한 최대 위치/회전 변화는 46.353645732 mm/44.171367854°, 5초 종료는 28.357006493 mm/43.983680557°다. 범위 안 전체/정책 표본은 143/300 및 66/111이다. 인정 타현 한 건을 지속 범위·회복·연주 성공으로 확대하지 않은 설명이 타당하다.
- legacy 분석은 `not actor_used`로 HOLD까지 준비 최소거리로 포함했다. 원 분석기/summary를 보존하고 신규 [v2 분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials_v2.py:44)가 phase별 집계를 분리했다. 실제 PREPARE/PLAY/HOLD 최소 READY 거리는 25.211254562/3.240488132/13.844196414 mm다. 두 분석의 7개 직접 입력은 현재 SHA exact이며 각각 before/after 변경 0이다. 분석 변경은 원자료·physics·검출 판정을 바꾸지 않는다.
- trace는 152행이며 step640의 종료 추가 표본이 중복된다. 고유 시점 151개와 camera151 frames를 구분했다. 302개 native PNG capture SHA/readonly/시각, frame0/60/150의 0/2/5초를 확인했다. 두 MP4 실제 SHA와 독립 ffprobe는 각각 151 frames/30 fps/5.033333 s다. 실제 5초 손 PNG도 확인했다. 종료 뒤 영상은 HOLD 물리이며 5초 actor 연주로 표시하지 않는다.
- 사전 source 사본 281개와 native 입력 SHA를 대조했다. 현재 입력은 승인된 main README/PLAN append 외 1023개 SHA exact이며 두 main의 native 사전 원문 prefix가 보존됐다. consumed runner/wrapper/leaf는 현행 SHA·실제 사본과 일치한다. old/new analyzer의 현행 SHA는 각 분석의 입력 metadata와 일치하며, 신규 분석기의 별도 phase 내 소스 사본은 아직 없다. Python 3.8 AST도 통과한다. 최종 README/CHANGED_FILES의 값·부분 성공/회복 실패 범위·실존 링크·영상 embed와 timing 정정 전 문서 사본을 확인했다. 후속 orientation 시험 결과는 이번 판정에 포함하지 않는다.

검수 SHA-256:

- runner: `a9b829ccce34c09014015c0579f73a21824fcea15496e711e5754d7730e91a80`
- wrapper: `cae3cf41f2c13a9bd36a6822ee8a7c3a11cc9d8609ce7798d3a15c3f26fda7fe`
- leaf: `06aec5a17a1b4f5c2e1d6e0b73e25ceecb93f109e2fadd5006270e93bf342884`
- corrected analyzer: `8e6feb45a03eea77dffd979f80178101bad0b5bb2a3feb8ea83e664457b39594`
- legacy summary: `70d4302ed9541073e7bf8ccbeca4c29956eef3cd02af24c3c32f968c47a396cc`
- corrected summary: `7f351a17cb29157b2bfa94d21c928053b124b3c0fb13b0878de78ca884628941`
- README: `086886029c2937e2af86aa0d605a05d5ecd9b2c3118f16ecdb9cd389b9c26d19`
- CHANGED_FILES: `967a91575f3cc07f5ee2f036ab87a7879f6ac36875e4da53387c4b1c655b11c3`

최종 판정: PASS
