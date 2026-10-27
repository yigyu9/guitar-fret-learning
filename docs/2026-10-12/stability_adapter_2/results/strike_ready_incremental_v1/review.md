# READY 증분 제어 — 독립 최종검수

요약 판정: **문제없음(PASS), 연주 성공 미달**. 현재 남은 Critical / Warning / Suggestion 없음. 사전검수 이후 저장 원자료·목표·출처·문서·native 영상을 검수했으며 새 native 초기화·physics 실행은 하지 않았다.

- 실제 1,200 physics steps, 300 controls, 151 camera frames와 23개 실행 계약을 확인했다. Trace는 8-step 표본 151개 외에 step844/3.516667초 terminal HOLD 표본을 더한 152행이다. PREPARE/PLAY/HOLD=49/162/89이며 source phase0 READY 8행·phase2 RECOVER 154행이다. APPROACH가 없으므로 해당 분기의 실행 성공을 인증하지 않는다. Phase1이 없었던 실제 PD switch count는 0이다.
- [run_strike_ready_incremental.py:187](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:187)의 이전 목표+2δ와 162행 적분 보존을 원자료에서 독립 재계산했다. Float32 requested 목표가 정확히 일치했고 반올림 전 식과의 최대 차이는 5.9315476e−8rad였다. 최종 81목표의 기존 rate clip/native bounds도 정확히 재현했다. Free4·손가락·source clock/감지기/PD 소유권은 사전 diff와 기록 범위에서 그대로다.
- Free4 기준 PREPARE 49 controls의 지정 목표·history·readiness·시각 필드, native prefix 25상태 및 첫 actor observation/action은 exact였다. 전체 trajectory 동일성이나 정보 필드 전체 비교를 뜻하지 않는다. [goal_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/goal_audit.json)의 6개 SHA 및 별도 분석 입력 7개 SHA를 확인했다.
- Timely hit 0, physical/accepted hit 1이다. 0.933333초 control의 event0/string2 DOWN은 −382.090790ms premature이며 target_hit=false, prepared_target_hit=false, unprepared_target_hit=false다. Source는 wrong crossing4로 3.516667초 종료했고 HOLD physics는 5초까지 계속됐다. Release5/miss6, ordinary recovery pulse1/scheduled recovery pulse0이므로 연주·정상 회복 성공으로 해석하지 않는다.
- [README:9](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/README.md:9)의 시점을 독립 확인했다: 0.8초 trace pick Gz=39.17999mm, 첫 PLAY control 0.816667초=39.015344mm, 0.933333초=11.332559mm, nominal READY≈20.3mm다. Control의 hit pulse는 해당 control 뒤 physics 결과이고 camera/trace는 표본 시각의 저장 상태다. 최대/종료 기타 p=46.353646/40.855469mm, q=7.095455/5.607060deg, region 전체283/300·PLAY148/162가 기록과 맞는다.
- Native 1,097개 입력은 현재 1,095개와 실행 당시 main 문서 사본 2개로 exact 해결했다. 302 PNG SHA·시점 및 두 MP4의 실제 SHA/ffprobe(1280×720, 151프레임, 30fps, 5.033333s)를 확인했다. 대표 0.933333초 손·5초 전신 이미지를 직접 보았고 README/CHANGED 링크·caption의 저장 자료 범위를 확인했다.
- 문서 Suggestion 해소: [README:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_ready_incremental_v1/README.md:7)의 crossing 설명을 raw unprepared flag와 구분했고 trace152/camera151도 명시했다. 수정 전 README 사본 SHA `098178d9224a7ec5d70e91e49639b787de21455c5bf5be2070608f8deb86592c`를 확인했다. 코드·원자료는 변경하지 않았다.

검수 SHA256: runner `dbcb5923e0ba3740f81ceb7c359a3e8320eb3e3233ad2f02a46eff873ab46bd6`; wrapper `a0d438094c94ed5176d22ffd2969f1ddf9052c7d6a2ac10bef0fb9a89b1e6726`; analysis summary `0d63d57c036e6946ea6c2208ccd4e7f57dc08a2f3a49084ba3d1bbaffa107958`.

완료 범위는 이 저장 실행의 제어·수치·출처·미디어·문서다. Native/source 구동 동등성, 접촉 인과효과, 기타 안정성·전체 연주 성공, 이후 velocity 실험 또는 root의 별도 최종 보존 감사 완료는 인증하지 않는다.
