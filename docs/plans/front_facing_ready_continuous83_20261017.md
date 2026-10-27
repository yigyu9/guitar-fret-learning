# 최종 같은 실행 검증의83초 설계 — 미구현·미실행

개별 baseline/repeat/release/free_strike/regrasp가 모두필수감사를통과한뒤에만이계획을구현·검수·실행한다. 기존77초구상/59초proposal은실제성공자료가아니고소비기록을수정하지않는다. 새Body/손16..16.5보정은그대로두고,실제정지17..22를검증한뒤동작을시작하려고행동시각만6초늦춘다. 실제step/physics clock를재배치하지않는다.

## 실제절대시각의예정일정

- 0..16.5: 기존동일초기화/준비/Body·손보정/e16latch16.
- 17..22: 보정완료후연속정지5초. LH유지IK는유한하게목표를갱신할수있으며2396목표literal고정조건을이구간에잘못이식하지않는다.
- 22/26/30: 각4초R여섯줄왕복,손가락21/피크상대고정·R근위제한미세변화기록.
- episode1: release34..37(open34..35,withdraw35..37),접촉완전해제37..52연속15초,off타현39/43/47.
- approach52..54,close54..55,settle55..56,dwell56..61: 기존동일한한선언축의재접촉5초조건과압현준비기하.
- post-regrasp 타현61..65.
- episode2: release65..68(open65..66,withdraw66..68),완전해제68..83연속15초,off타현70/74/78,마지막82..83정지.
- 총83초/19920outer;state/contact19921행,target60Hz4980행+별도finalendpoint. 두개free창은각raw3601/source901을별도로검사한다. 시간을합쳐연속30초라고설명하지않는다.

## 최소구현범위와주의

새protocol에두episode를명시하고얇은Motion에서현재episode의기존단일일정view만부모에전달한다. 새open actual손목/q26,withdraw heldcommandpose,close actual14 latch·경계held26은원로직을재사용한다. started/actual10/FK/reference16/e16/RH첫orientation은재초기화하지않는다. Motion3gripped bounded유지와regrasp_hold상속의의미를임의변경하지않는다. metadata에episode ID/각release actual시작참조를구분한다.

analyzer의stage선택/anchor/left_evidence·source_and_target는episode별필수판정으로확장한다. 빈목록all()나두창합산평균으로통과시키지않는다. support/feet/health·소스/압현준비/미세제한진단은모든창을닫는다. 같은실행이후별도fresh재초기화83초도동일전체기준으로검사한다. 기존59/77실제prefix가없으므로literal비교성공이라고주장하지않는다.

Source의단일free=[case.free]가정과grip_steps를새버전에서다룬다. support/RH/Spine/Torso는5..83전기간,grip1mm는두free내부합집합만제외하고모든경계를포함,free2mm는각901별도필수다. 전체누락12/모델108/Nativefilter·왼팔전체nonfinger부정접촉도유지한다. sourcepair방향상한을cooked침투로해석하지않는다.

두번째LHoff15초·off타현/마지막정지통과는재접촉후다시왼손없이유지됐다는직접근거다. LH가접촉중전달한하중까지알아낸것은아니다. 실제현힘·진동/음향도별도미검증이다.

## 보존용량

현재reference native28초가약0.945GiB다. 남은개별34/34/43초와83초2회를같은평문raw/중복overlay로저장하면현재여유에부족할수있다. 기존소비자료를삭제·변환하지않는다. 저장형식보완은새83버전에서만손실없는gzip 및필수native3view/5fps의중복파생overlay저장분리로설계한다. 압축과압축해제원byteSHA·row/step/time/끝점·잘린gzip/JSON거부·평문과정확재생동등성을검증하고독립FINAL/RootACK후사용한다. gzip은디스크만줄이며기존동시배열메모리부하는별도다. prefix압축ratio는추정치이고83실측크기로설명하지않는다.

## 진행

- [x] 기존코드의단일episode가정/재사용범위읽기전용점검.
- [ ] 현재개별4action의모든실제필수감사PASS.
- [ ] 새protocol/Motion·83분석/소스·저장/소비경로의작은실제schemaCPU·독립검수/RootACK.
- [ ] 같은실행83초전체AND.
- [ ] 같은조건fresh83초전체AND및재현대조.

현재이계획의새코드/새83native/새최적화/새source실행은0이다. 원strictEPS0/좌표잔차전체원인False/최종채택False를계속보존한다. 새PPO금지.
