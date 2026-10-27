# Strike EFFORT geometry PI 최종 독립 검수

요약 판정: **문제없음 / 검수 PASS**. 실험 결과는 **미채택**이다. 남은 Critical·Warning·Suggestion 없음.

- 실제 저장 자료는 1,200 physics steps·300 controls·151 native trace/camera 표본이며 native 24개 계약이 모두 true다. PREPARE/PLAY/HOLD는 49/251/0이고 5초까지 source terminal은 없다. 사전 Critical이었던 preview/final PI 목표 소유권 불일치는 두 곳 모두 actual R9 기준으로 수정되었으며, 이전 소스와 3-case 회귀 기록은 보존되어 있다.
- `run_strike_effort_geometry_pi.py:103`의 매 physics 요청 1,004개(시작 step196부터1199)를 독립 재계산했다. float32 `clip(original_kp*(logical_goal−actual_q), ±effort_limit)`과 exact이고 R9 외 72개 요소는 0이다. 네 PD 전환(step196/372/908/948, phase0/1/2/1)의 full81 requested/native properties exact 및 state 보존 기록을 확인했다. R9 EFFORT/stiffness0, phase1 native damping quarter이며 다른 72축은 POSITION이다. 이것은 요청 torque 검증이며 측정 drive torque가 아니다.
- 기존 `effort_audit.json`의 49개 PREPARE 선택 control 필드·25개 전체 native-state prefix·첫 actor observation/action exact 근거와 입력 11 SHA를 확인했다. 전체 1,200-step trajectory 또는 모든 control key의 동등성을 주장하지 않는다. 열린 phase0/1의 팔 목표는 geometry PI, fingers21은 policy, closed1은 actual-angle IK, RECOVER는 이전 목표+2δ라는 소스·문서 범위가 일치한다.
- raw hit는 3.766667초 event7→8, string index2, +29.438972 ms의 target/physical/accepted 각1이다. Release2·miss9·wrong1, running F1 0.166666657은 부분 결과다. 기타 위치 max/end 46.353646/33.588116 mm 및 SO(3) 회전 max/end 44.868319/44.009573°를 독립 재계산했고 playable region 49/300 control·3/251 policy 표본과 일치한다.
- Native closure 1,082개는 현재 파일 1,080개와 exact `native/source_before` 사본 2개로 해소된다. 별도 분석 입력7·effort audit11·contact diagnosis11 SHA도 일치한다. 접촉 진단의 5개 저장 pose에서 기타 상대 RHpick 위치·회전 및 handoff(실제 trace0.8초) 대비 회전을 재계산했다. 첫 양의 RH–Gbody 기록은 1.2초 G:body–RH:ring3, raw lambda12.854830741882324다. 5초 pose와 마지막4.983333초 control/contact의 시점 차이도 명시되어 있다.
- 두 native MP4의 실제 SHA와 ffprobe 1280×720·151 frames·30fps·5.033333초, 151×2 frame SHA/step coverage를 확인하고 종료 손 PNG를 직접 검토했다. README·CHANGED_FILES·progress의 결과·원자료 링크·요청 torque/접촉 해석 한계가 맞으며 Python 3.8 AST도 통과한다.

확인 SHA256: runner `ba248c3f1a366c97aef4338f2aff549838e0aaf4c6ec1ff31ee293aff0bd740d`, wrapper `0493041c89296333a4ff72eb90de29432833a3578900880df7c2e12fff6ad16c`, 분석 summary `358583a280c3f245ad73e370636fa8c3a931bb588f0613cdd073131e606b1842`.

검수 중 추가 native 초기화·물리 실행은 0회다. Lambda의 물리 힘 변환·접촉의 인과·면별 지속 지지·전곡 연주 성공·원래 source/native CPU/GPU 동등성은 인증하지 않는다. 후속 POSITION/soft-orientation 단계와 root 최종 보존 감사의 완료를 이 기록으로 대신하지 않는다.
