# 독립 검수

요약 판정: 문제없음. 코드 차이·저장 native/controls·분석·미디어·최종 한국어 문서를 읽기 전용으로 검수했다. simulator, actor, solver, 분석 producer 또는 렌더 재실행은 없다.

- 변경은 source phase 2에서 오른팔 9축 목표를 이전 actuator goal + 0.5×actual-anchored IK delta로 구성하는 우선권이다. local delta±0.15 rad, 누적 목표의 native bounds와 최종 float32 3.2 rad/s cap을 구별한다. 적분은 phase 2에서 동결되고 source의 자연 phase 1 복귀 후 policy+PI로 돌아간다. RH 손가락21은 policy, RThorax3 및 held36은 기존 설정이며 source phase/waypoint/latch/detector/음표 시간/weights를 덮어쓰지 않는다. runner/wrapper/분석 AST3.8도 통과했다.
- 비교 first-hit 실행과 초기 native/PD/81관절·rate/gain이 exact다. 첫 150개 최종 목표와 physics step≤600 native 표본이 exact이며 step<600의 readiness/observation/action/목표/history도 exact다. 모든 300개 목표의 float32 native-bound/rate 조립·held36·source30 history 역변환, 182개 다음 observation history를 독립 재계산했다. phase0/1 PI의 조건부 적분과 antiwindup, phase2의 52개 증분 목표·적분 동결·entry selector/event key 기록이 exact다.
- 실제 1200 physics steps·151 camera frames·16개 계약 검사 통과다. PREPARE49/PLAY182/HOLD69이며 source terminal은 step924/3.85초다. trace에는 terminal 추가 표본 step924가 있어 152개이고 카메라151개와 구별한다. HOLD에서 목표/history/source clock이 동결되지만 물리는 5초까지 이어진다.
- 독립 합산은 target hit/physical hit/accepted release 1/1/1, physical release/miss/wrong 5/7/4다. hit 기록 시각2.483333초·string2·기존 timing45.179844 ms, clearance lifted2.883333초·reached 및 scheduled completion pulse3.266667초(1회)를 대조했다. scheduled pulse를 별도 recovery_complete_pulse나 곡 전체 완료로 바꾸어 해석하지 않는다. phase2의 physical release는0이다. control3.35초의 source step 결과가 phase1로 전이하고 다음 control3.366667초부터 phase1 policy+PI 분기가 재개된다.
- scheduler event3/4 miss2.866667/3.15초, 뒤 교차3.5/3.75/3.833333초의 target/actual string·direction·action phase1·release_phase_violation false를 원자료와 대조했다. event5 창의 115.8 ms는 phase2→1 결과 시점의 source clock 기준이다. 3.75초의 사후 timing 진단과 source 공식 timing_sample=false를 구별한 문서는 정확하다. 목표 완료는 false이며 마지막 running F1 0.153846은 partial이다.
- 거리 최소 PREPARE/PLAY/HOLD 25.211255/1.931564/12.290379 mm, 기타 최대/종료 위치46.353646/40.366381 mm와 회전9.019638/5.485612°, 범위 참229/300·126/182를 raw p/quaternion·controls로 독립 재계산했다. 회복 한 성공 관측은 전체 연주 성공 또는 범위 유지 인증이 아니다.
- native 사전 입력1032개·소스 사본288개 SHA, 종료 unchanged, 현재1030개 exact와 승인 main 두 문서의 사전 prefix를 확인했다. 분석 직접7개 입력도 전후/current exact다. capture151/302 PNG SHA·readonly 기록, 두 actual MP4 SHA와 ffprobe151 frames/30 fps/5.033333초가 일치했다. 실제5초 손 프레임을 확인했고 모든 최종 README/CHANGED_FILES 절대 링크가 존재한다.

최종 README SHA: 3a2c40d06a652c94774cb8a47e87942b841e048a4d673b1650655494f4331e3a. CHANGED_FILES SHA: 3153ca445fee04dcde29f7d9b47cbaef1c9499234845ac5b116e42cc0a369ed3. 소비 runner SHA: e8ab6968f5e6d225f53e94fd2e4b0076252f4741349eaaf5124e5a47b5683d56. wrapper SHA: a0736665e51a12f72c2a25765f4ac6ead1f69bba16b2f27520d045c25e77b282.

미해결 Critical/Warning 없음. 검수 PASS는 이번 진단의 계약·관측·보존·설명의 정합성 판정이며 후속 gain의 실제 응답, 반복 재현성, 정식 actor 자격, cooked clearance 또는 연주 완료를 인증하지 않는다.

최종 판정: PASS
