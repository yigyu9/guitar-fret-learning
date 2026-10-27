# 사전 검수 보완 — OM appearance 카메라

요약 판정: **문제없음.** 추가 Critical 0 / Warning 1 / Suggestion 0. 새runner2의 녹화 키 보완에 실행 차단은 없다. 기존 물리·제어·checkpoint 연결 범위는 [사전 검수1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/review_preflight_v1.md:1)과 같다.

- [원실패 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v1/report.json:1)는 첫capture의 `KeyError: OM_appearance`,0 physics/0 controls/0 right effort, inputs_unchanged true, completed false다. 두view/model 초기화·초기state 검사를 통과한 뒤 녹화 키에서 중단했으며 정상 연주 또는 완료 실행으로 집계할 수 없다. control loop 진입 전이므로 actor 추론도 없었다.
- [runner2:81](/home/ajou/yigyu/3/stability_adapter_2/run_dual_checkpoint_shoulder_v2.py:81)의 diff는 scene 생성/initial 저장 뒤 recorder 전1280×960 OM_appearance 카메라를 생성하고, 초기G pose 기반 기존OM camera target/eye를 설정해 키를 등록하는 부분뿐이다. 카메라 실패도 명시적으로 거절한다. 인간/기타 pose·q/속도·물성·모드·controller·clock·actor/done 경로는 바꾸지 않았다. helper1/scene1/원runner1을 보존하고 새출력native2를 사용한다.
- 기존 FocusedRecording은 해당 키의 카메라 시점만 갱신하고 capture 전후 native state 불변 검사를 수행한다. 기존 camera/physics/control owner를 중복 생성하지 않는다. 새runner AST 통과. [보완계획:5](/home/ajou/yigyu/3/stability_adapter_2/DUAL_CHECKPOINT_SHOULDER_PLAN_V2.md:5)은 실제 녹화 실패와 후속 연주 결과를 구분하며 broad A 입력 closure가 새 계획을 포함한다.

Warning 1 — 첫 사전 리뷰는 transitive FocusedRecording의 OM_appearance 키 요구까지 확인하지 못했다. 실제0-step 실패를 보존한 새버전 보완으로 기록해야 하며, 새카메라 추가만으로 native 연결·PREP exact·음악 성공을 인증하지 않는다. 기존 checkpoint 성능 동등성/학습ready 미인증 scope도 그대로다.

읽기 전용 diff·실패 원자료·syntax에 한정한 보완 검수다. 추가 native/학습/정책추론/기존파일 수정0. root가 진행하는 재시도의 실제결과와 영상·SHA 검증은 후속 범위다.

검수 SHA256:

- 새runner2: `0420cd7f2caac78203da217584fefaa4610ef1c36d5c49c9498270fa02566a4b`
- 보완계획V2: `827df13afbf2510991e660760879f367d09e7fcfd3f01a4cce44bcc412d0ce64`
