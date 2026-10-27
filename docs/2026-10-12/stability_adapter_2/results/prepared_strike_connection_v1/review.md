# 준비 배치 Strike 연결 독립 검수

검수 소유권은 이 review.md뿐이다. 새 계획/helper·테스트·native runner·import 전 보존 wrapper를 읽고 기존 v4와 변경 부분을 대조했다. Python3.8 AST·저장 CPU11pass 로그·작은 순수 회전/진단조건 수치만 확인했으며 테스트/solver/actor/native/분석/그림/봉인 본체를 실행하지 않았다. 다른 담당자 파일이나 이전 동결 review/원자료는 수정하지 않았다. 현재 사전 코드 검수이며 실제 연결 결과와 최종 문서는 후속 범위다.

## 요약 판정: 문제없음 — 사전 실행 blocker 없음

새 [계획:5](/home/ajou/yigyu/3/stability_adapter_2/PREPARED_STRIKE_CONNECTION_PLAN.md:5)은 사용자 요청에 따라 엄격한 준비 gate를 유지한 기존 runner와 별도로 느슨한 정책 연결 진단을 만든다. 2초는 이번 비교의 준비 구간이며 필수 연주 과정이 아니다. LH palm 접촉·50mm/6연속 strict readiness가 없어도 진단을 시작할 수 있음을 명시하고, 그 부족을 계속 기록한다. 연주 성공·실제 양손 지지 인증과 actor 연결/기록 성공을 구분한다.

- [회전 helper:6](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_start.py:6)는 actor-root 위치 상자 및 초기 실제 Chest Z 상한을 검사한다. extrinsic xyz의 두 Euler 표현을 고려하고 +90°에서 x−z의 가능 범위[-135,-45]°를 사용하며 q와−q를 동일하게 취급한다. 허용 Euler 상자 내부200개 독립 순수 표본, +90°의9개 x/z 조합, 현재 수평q 및 밖의 특이점 반례를 대조했다. source 영역/허용 회전 집합의 수치 판정이지 기타 전체 형상·관통·손 도달 인증이 아니다.
- [진단 시작 helper:25](/home/ajou/yigyu/3/stability_adapter_2/prepared_strike_start.py:25)는 time≥2s·region·ready distance≤80mm·finite/LHfinger/palm-up/RHfront/grip/모든 RH contact행 차단을 요구한다. palm-underneck 및 strict50mm/6연속은 의도적으로 시작 조건에서 제외한다. [runner:122](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:122)는 원 strict predicate와 영역 여부를 별도로 기록하고 strict_contact_gate_used=false/diagnostic_only=true를 저장한다. 기존 strict v4 소스는 변경하지 않았다. 이전 v4 저장 자료의 step480에서 진단 시작 조건이 성립함을 순수 함수로 확인했으나 실제 native 연결의 성립을 예측으로 인증하지 않는다.
- [handoff:126](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:126)는 이미 준비한 event/lane/geometry를 보존하는 history helper를 사용하고 실제 native state readonly를 추가 대조한다. 이후 준비 IK 대신 frozen303/30 정책을 사용하며 LH12 PI·RH30·RThorax3·other36을 하나의81 목표로 제출한다. 최종 native limit/.8rad/s 및 실제 float32 목표의 source history 회신은 기존 검수된 경로를 유지한다. 정책 중 준비 IK·추가 RH PI와 경쟁하지 않는다.
- [PLAY/HOLD:133](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:133)는 LH 접촉을 측정만 하고 body rearplane crossing 또는 source done에서 마지막 목표 HOLD로 전환한다. [HOLD:160](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:160)는 actor/source step/PI를 호출하지 않고 목표·song/progress/history exact 불변을 검사한다. 물리 tick의 fullstate finite 및 dof 속도 guard, root/하체 유지·PD 불변·no-forbidden/render-readonly를 보존한다. 종료 원인/info/정확한 step 및 terminal native snapshot을 기록한다. HOLD의 수동 물리 구간은 타현 평가로 해석하지 않는다.
- 새 preserved wrapper는 기존 검수된 사전 conservative input SHA/source 사본·종료 after 경로에서 호출 모듈을 새 runner로 바꾼다. 기존 checkpoint/asset/source 기록의 변경이나 physics 전 source import로 보존 시점을 늦추는 변경은 없다.

## Warning — terminal 추가 표본과 후속 분석의 시점 대응

[runner:158](/home/ajou/yigyu/3/stability_adapter_2/run_prepared_strike_connection.py:158)는 source terminal에서 sample()을 추가 호출한다. terminal step이8의 배수이면 동일 step의 두 trace 행, 아니면 off-grid 추가 행이 생길 수 있다. terminal state를 보존하는 동작은 적절하지만 후속 analyzer가 이전 `trace[step//8]` 인덱스를 재사용하면 이후 시점이 어긋난다. 실제 physics_step으로 대응하고 trace 표본 수와151 camera frames를 별도로 검증해야 한다. 이 사전 경고는 actual 자료 오류가 발견됐다는 의미가 아니다.

## 사전 source 식별

계획 SHA `b28c4b96d592ea92a16ab34ef7f022128a7a0a4031904eadef0aaf874b6b5487`.
시작 helper `31cb1047935994e728e329534fef7da5a3d2e8b8787813ac60f8b3ad4a065ef5`.
테스트 `f65752a8caa10d5094a7a8510727c57e0d64315ed824fe8a69f3dd0036d7a9fc`.
native runner `bf52cb9a888d9cb0a91e5928a26aa54911ad90b337105d2672c4bbdfb548e83b`.
preserved wrapper `b41a69fb0d296ebecb5f6da5d3765ba7a3c911b3273de7e58a06814cd0bee916`.

아직 actual 정책 연결/성능과 전체5초 산출물은 검수하지 않았다. 최종 판정 및 review 동결은 실제 자료·분석·산출물/문서 전달 후 별도로 한다.

## 실제 연결 및 저장 분석 추가 검수

요약 판정: 저장 실제 연결/분석은 **문제없음**. 연주 성능과 기타 영역 유지는 성공으로 판정하지 않는다. 아직 문서·산출물 최종 검수 및 review 동결 전이다.

실제 report는1200physics steps/151camera frames/15checks true·failure없음·2.0초 PLAY시작·actor180·PLAY 종료·stop=null이다. 300control은 step0..1196 stride4, policy180은 before480..1196/after484..1200이며 실제 정책 물리 구간은3초다. 실제 source done/HOLD는 없었다. 따라서 hold_goals_clock_history_frozen=true는 이번 실행에서 HOLD 경로를 실행한 근거가 아니다. 이 완료는 전체5초 기록과 정책 연결을 뜻하며 strict contact gate/타현 성공을 뜻하지 않는다.

baseline native initial fullstate/PD와 exact였고 0~2초 native trace61개 및 준비 final goal120명령은 strict v4와 exact였다. 전체300 final81의 native bounds·.8rad/s·other36 유지와 실제 native lower/upper/checkpoint action_scale1.0 기반 final30→sourcehistory 역산 최대차0을 독립 확인했다. 추가로 policy180개의303관측 O_history slice273:303은 각각 직전 제출 최종 목표의 저장 sourcehistory와 float32 exact였다. 초기 preflight만이 아닌 실제 handoff 이후 history 연속성의 저장 대조다. 최대 목표 update.013333380222320557rad였다.

raw trace G p/q에서 독립 계산한 위치 최대59.578528/종료23.034000mm와 회전 최대46.151458/종료46.035929°가 [분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/analysis/summary.json)와 일치했다. current native pose가 있는150개 control의 region 여부를 순수 helper로 재계산해 저장 flag와 일치했다. 정책180표본 중 영역 내부64/외부116(최초 외부3.066667초), strict preparation true0/palm75/finger180이다. loose handoff 당시 palm=false·strict50mm near=false였으나 finger/up/front/grip/noncontact 및 region=true, ready57.003358mm라 명시한80mm 진단 시작 조건을 충족했다. 이후 경계 복귀·연속 지지 유지 성공으로 해석하지 않는다.

[이벤트 분석 summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/event_analysis/summary.json)의 per-control pulse 합계를 controls180개에서 독립 재집계했다. target_hit0/physical_target_hit0/physical_release1/miss8/wrong_crossing_count1, accepted_release_mask true 합계0이 맞다. source motor phase는0만 관찰됐고 마지막 source song clock2.5230984687805176초/event index8, running strike_f1=0이었다. done=false·strike_episode_f1=[]이므로 완결된 episode/전체곡 F1, TP/FP/FN으로 확대하지 않는다. source wrong_count는 [원본:3987](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3987)의 현재 release 위반 합계라 이 분석은 cumulative metric을 다시 합산한 것이 아니다.

두 stdlib/NumPy 저장 analyzer AST와 직접 입력10개/2개 before/after/current SHA를 확인했다. native closure986개는 종료changed0, 검수 current984개 exact였다. 달라진 두 main PLAN/README는 native before SHA exact인 main_before와 current prefix exact로 승인된 결과 append임을 확인했다. 관련 native runner/helper/wrapper의 소비 source 사본도 canonical current와 byte exact다. 이전 준비 phase inventory2476파일은 모두 current SHA exact였다. 두 실제 영상 SHA는 report와 일치하고 저장 ffprobe151frames/30fps와 정합한다.

## 미소비 봉인 코드 사전 대조

[seal_phase.py:13](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/seal_phase.py:13)의 AST·권한/보존 순서를 읽었다. native closure current 중 main2 승인 prefix만 허용, 이전2476 inventory 및 inventory SHA, 종료native after, connection10입력/event2입력 current+after, actor>0/report checks, 준비 prefix/history, 영상SHA/151/30을 검사한다. 새7개 직접 계획/코드/test/main 사본을 보존하고 닫힌 파일 inventory를 재검산한 뒤 최종 verification을 저장한다. 봉인 stdout은 phase 밖이며 review 동결·모든 writer/log 종료 후 root 실행 조건이다. 이번 단계에는 새로운 scientific plot producer가 없다는 root 범위를 적용하며 native 이미지는 최종 문서에서 별도 검수한다. 아직 검수자가 봉인을 실행한 것은 아니다.

connection analyzer SHA `76561e6e9c677ad9c3d685f4d55a3237d42be1c48b464204d1e26d7925ff965c`.
event analyzer SHA `cd94c5d5d95244d010b1e91fd5a12778b2d489f9366d76d658a41e55fcd462d1`.
미소비 sealer SHA `9c41e59c3e4c1b9df6317a8b283f21ca2a8387c39e3262ea0cdb17765cd090c1`.

확정 원자료 검수는 완료했다. 최종 README/변경색인/native 이미지·main/VISUAL append의 정합을 대조한 후 최종 판정과 review 동결을 별도로 기록한다.

## 최종 접촉 집계·문서·미디어 및 봉인 delta 검수

요약 판정: **문제없음**. 최종 판정은 실제 정책 연결 진단·저장 근거·후처리/문서 정합의 판정이다. strict 준비 획득·인정 타현·연주 또는 기타 영역 유지 성공을 인증하지 않는다. 다른 담당자 코드/원자료/문서를 수정하지 않았고 solver/actor/native/분석/그림/봉인 본체를 재실행하지 않았다.

- [접촉 분석기:8](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/analyze_hand_contacts.py:8)의 AST와2입력 before/after/current SHA를 확인했다. 저장 readiness counter를 합산하는 것 외에180policy raw contacts의 body0/body1 라벨로 RH–G행을 독립 재식별했다. handoff0행, 접촉 있는 정책157/180표본·전체419행이 맞다. RH는 모든 raw lambda 행을 세고 LH 지지는 positive finite lambda 영역 증거를 사용한다. LH palm+finger 동시75표본/최장연속75도 독립 재집계해 일치했다. 완전 구간의 지지력·뉴턴 단위 힘 인증으로 확대하지 않는다.
- 수정 전 성공 후처리 문서는 doc_before_contact_correction에 보존됐다. 최종 [README:19](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/README.md:19)는 RH 접촉0을 handoff 순간으로 좁히고 정책 구간157/419 및 LH 동시75/연속75를 정확히 설명한다. 초기 strict gate false·별도2초/80mm 시작·actor180/source READY0·부분 pulse0/0/1/8/1/accepted0·episode 미완료·범위64/180/회전46° 및 actuator/qualification 한계를 확정 원자료와 대조했다. 실제 연결과 성능 부족을 분리하며 후속 성능 개선을 이미 실행했다고 표현하지 않는다.
- 최종 native 전신2초/5초와 손5초 PNG를 실제 열어 카메라 구도·2초 전이 시점과 큰 기타 회전·무스트랩 장면 설명을 확인했다. 문서0/2/5초 프레임 번호00000/00060/00150은30Hz capture와 맞고 두MP4 inline embed·151frames/30fps/5.033333초는 보고서 SHA/저장 metadata와 정합한다. 이번 산출물에 새 scientific plot producer나 이미지 편집은 없다.
- [CHANGED_FILES](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/CHANGED_FILES.md:1)의 계획/helper/tests/runner/wrapper, 종합/event/contact 분석기 및 원자료·미디어/sealer 링크 경로와 line 존재를 확인했다. 마지막 audit 라벨은 보존된 직전 문서에서 ‘handoff 초기’→‘t0 native 초기’ 한 곳만 바뀌었다. initial_audit.json은t0 기하 admission이며2초 handoff geometry 인증과 구분한다.
- [main PLAN:160](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:160), [README:1465](/home/ajou/yigyu/3/stability_adapter_2/README.md:1465), [VISUAL §126:2244](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2244)의 실제 연결 완료와 strict 준비/연주/범위 유지 성능 미완료 표현을 대조했고, 원문 main2 및 VISUAL prefix 보존을 확인했다.
- 마지막 미소비 sealer에는 contact2입력 current+after 검사도 추가됐다. 기존 event2/connection10/native closure·두 main 승인 append·영상/이전2476파일·source_final/inventory 재검산 순서를 유지한다. Python3.8 AST와 추가 몇 줄 논리에 blocker는 없다. 모든 writer/log 종료 후 phase 밖 stdout으로 root가 실행하는 조건이며 검수자는 봉인 실행 결과를 선행 주장하지 않는다.

접촉 analyzer SHA `b851bde4b573afd1aa6f9810e116f888625b906f10d60fef026c69b610eb21bd`.
최종 README SHA `e91ee7b9fa3ce953d451c1055904ea9a207d0caf1b30612f0a3d82caf4b63d95`.
최종 CHANGED_FILES SHA `a38853eadad675e91dd711b3f91a0e69f68447fad6d2567706f759c5fac126a6`.
최종 VISUAL_REPORT SHA `3c4c394a2cd1b0538626b8aefbbe49c1ec057aa4edc6b1dfa1ab324061d780b3`.
최종 미소비 sealer SHA `b4a44c3659e5fb95b61e5aafc583cf167d69ff3036c11e703c237baf3bc703ef`.

남은 material blocker 없음. 이후 이 review.md를 동결한다.

최종 판정: PASS
