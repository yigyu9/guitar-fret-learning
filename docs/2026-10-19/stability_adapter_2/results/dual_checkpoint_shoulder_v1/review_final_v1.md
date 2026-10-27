# 최종 검수 — 두 checkpoint 직접 연결

요약 판정: **문제없음.** 현재 Critical 0 / Warning 2 / Suggestion 1. 원봉인1의 영상 프레임 검사 Critical은 미실행 원본을 보존한 새봉인2에서 해결됐다. 연결·자료 정리의 완료를 확인하며 실제 연주는 조기 안전종료로 실패했다.

- [native 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/review_native_v1.md:1)의 전체initial/PD/mass·PREP120control/480명령 exact,123목표/492torque 수식·한 owner·afterphysics/music hook 검수와 canonicalv3 결과가 일치한다. native1은0-step 카메라 셋업 실패, native2는492steps/123controls/2.05초 실행 완료지만 PLAY3회 뒤 원Fret wristZ/finger_back done으로 종료했다. Strike_done/두 goal_finished는 false다. 연주 완주·42곡 전체성공률로 확대하지 않는다.
- [정식 artifactV3:20](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V3.md:20)의 물리492step·PREP480physics/120control·PLAY3tick과 [artifactV3:22](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V3.md:22)의 공동 음악 이벤트0/현 crossing0 설명이 맞다. 과거 ‘관절 event/crossing’ 오역은 새V3로 정정하고 V1/V2를 보존했다. 준비 중 왼손 READY/wrist/finger 안전 및 오른pick READY 전환은 아직 구현되지 않았다. 마지막Strike entry_ready false/tip 거리 .082541637m도 raw와 일치한다.
- 실제 PNG를 열어0/480/492step의 전신·왼손/넥 카메라0/2/2.05초 패널과 terminal·캡션·배치를 확인했다. 손근접 패널은 오른손 접촉 증거가 아니다. provenance1/2/3의 실제 flat producer·입력 before/after·출력 SHA가 일치했다. 영상4개는 신규2개63frames/30fps/2.1초와 기준2개151frames/30fps/5.033333초의 byte-exact 사본이며 실제ffprobe도 대조했다. 기준 영상을 이번 물리 실행 수에 합치지 않는다.
- [root README:34](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/README.md:34)는 분석v1 raw quaternion 표현 실패와 v2 body.pos 미포함 OBJ 중심 오류를 구분한다. canonicalv3의XML body.pos 포함63조각 중심 `[0,−.4,−.055937985]m`와 최종BB9.617284mm/SO3 2.983343°·최대10.455249mm/3.343712°를 native 검수에서 재계산했다. 과거25.609mm는 보존된 잘못된 중간수치이며 활성 결론에 사용하지 않는다.
- navigation1→2의 main3 exactprefix·before/after SHA chain과 rootREADME canonical append snapshot을 확인했다. 최초추가 PLAN1171/A README2263/D README96 및 후속추가 heading을 기록한 최신map과 정식routing이 맞다. 첫 문서검수65개·최신45개 절대링크/줄을 대조했다.
- [봉인2:71](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/seal_outputs_v2.py:71)의 영상 검사는 실제4 unique 목적지와 case별2개 whole_body/hands·63/151frame·30fps·2.1/5.033333초를 구분한다. 원봉인1의 모든행63frame 오류가 해결됐다. generic flat producer·before/after schema와 원자료 map SHA,0-step 셋업 실패1/실행 완료1/음악 완료0 집계·review gate·exclusive final 출력·syntax를 읽기 검토했다. 잘못된 분석v2를 SHA 보존 검사하는 것은 수치의 승인과 다르다. 봉인은 실행하지 않았다.

Warning 1 — [root README:21](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/README.md:21)의2→2.05초 .037970mm/.012452° 변화는 짧고 검열된 관찰이다. 정책효과의 인과·장기 안정·이전정지5초/팔꿈치동작 인증 또는 음악성능으로 확대하지 않는다. 이벤트 미정산0을 전체곡0/42 성공률로 바꾸면 안 된다.

Warning 2 — [root README:34](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/README.md:34)의 source profile/정규화·history inverse clip·COM ABI·보수적 crossing 범위와 native XML/model 한계를 구분해야 한다. 실제원본 wrist/finger 안전종료와 별개로 source joint_limit_usage를 native hard-limit 위반 인증으로 부르지 않는다. 요청 point힘/접촉 raw lambda는 측정지지력·힘분담이 아니다. 원고정기타 checkpoint 성능 동등성/학습ready detector 인증도 아니다.

Suggestion 1 — rootREADME 끝의 변경색인 링크 label에 일본어가 남아 있다. 목적지와 데이터는 맞고 실행·결론에 영향이 없지만, 사용자안내는 한국어인 canonical README_V3/CHANGED_FILES_v2를 직접 사용하는 것이 적절하다. 소비된 원문을 이번 검수에서 수정하지 않았다.

추가 native/학습/정책추론/기존소스·산출물 수정0. 이전 전체 inventory/입력버전 전수 보존 감사와 source_final/inventory/final_verification 생성은 root 후속 봉인 범위다. 아직 실행되지 않은 최종 감사를 완료로 주장하지 않는다.

검수 SHA256:

- root README: `c417baafbb50df7a8d116e86cced075c53514c18e4dea76c47afeb00d9fee33b`
- canonical artifact README_V3: `de9d03966b01dab7b6d52187be72e94e0534dbf720a43a2262e8c5ce19d87621`
- 새 변경색인: `1ea7e21ff8fa9cc5abe4cf4265701d9e619e510b5bf7bffd2dd91920908f10f0`
- 새봉인2: `a23088102033542089c9e3b920f760b112ebd6258195699eeec7e2fc309a9471`
- 새provenance3: `9de7a23d467ab8ca0e5d188f40f9bf59070d30f2bbc2b3de9b839cdcc674d5c2`
- 실제캡처 PNG: `497541157a2cb8d37d0689d28817ff11db9328ff668cca8c4ad88ab822f64a4c`
- 영상 manifest1: `8de0beb311bea513614a92b520f169888ba97b74dc6884ed78d94da8b2a2e218`
