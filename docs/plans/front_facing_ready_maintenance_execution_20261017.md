# 선정된 몸통·왼손 유지 제어의 실제 검증

2026-10-17 KST. `REQUIREMENTS_v2.md`와 `AGENTS_v4.md`/V3를 따른다. 사용자 기존 실행 위임 범위의 후속 작업이며 이전 코드·입력·실행·실패를 덮어쓰지 않는다. 현재 새로운 유지 제어의 실제 native 실행은0이다.

## 후보와 고정 조건

- Body는old.15 증분/Chest 목표10–10.5초를 유지하고, 선정된새.12 증분을16–16.5초에추가한다. 목표가슴경로와실제반응은분리한다.
- gripped LH arm12는actual16 G상대손목기준/고정e16 유한목표,thumb3는−.1rad 부드러운절대보정이다. 원PD/force cap과Root·큐브·모델·초기105입력은그대로다. source4표본의他손마디여유가약1.273µm인한계가있으므로실제전행검사를반드시통과해야한다.
- Root만고정/하체24중비영16유한/원zero8보존/기타자유·중력ON·strapOFF,기타직접보조힘·부착·매step상태덮어쓰기·새PPO0을유지한다.

## 구현과 경로

- Motion/runtime worker: `motion_v2.py`, `runtime_v9.py` 및 `maintenance_hand_runtime_v1/`만담당한다. Scene은실제runtime_v8.Scene alias다. 계약은자료폴더 `maintenance_hand_contract_v1.md`와 `front_facing_ready_hand_reference_20261017.md`다.
- 분석 worker: `analyze_v9.py` 및 `maintenance_analyzer_v1/` core검증을먼저담당한다. 기존baseline29/action30 gate명을유지하며새목표소유권을실제raw로독립재구성한다. 부모중간요청과새요청·Foot후요청·최종F32제출은분리한다.
- Root: `run_v10.py`, `execute_v10.py`, `inputs_maintenance_v1/`, source감사새버전·추가12 adapter·후속압현준비와전체봉인을담당한다. manual/health의새metadata연결은core검증뒤별도소유권을배정한다.
- 새출력은 `native_<case>_v9`, `analysis_<case>_v9`, `feet_<case>_v9`, `media_audit_<case>_v9`, `planes_<case>_v9`, `remaining_shapes_<case>_v9`, `manual_<case>_v9`, `health_<case>_v9`, `fretting_prepare_<case>_v9`다. baseline추가정지는 `post_increment_hold_baseline_v9`다. 기존v8과이전결과는보존한다.

## 실제 실행 전

- [ ] Body/Thumb선정JSON·Root before/after·검수/ACK·model108·새source/계획/config의expected SHA를충돌거부merge한다. 원 before맵을현재glob로고치지않는다. 새로운source/CPU만별도prospective봉인한다.
- [ ] CPU에서새runner의선정/원config동일성·허용차이,baseline/path/각필수gate/commandCLI와실패거부,정상·예외binding복원,원raw/행schema와생산수학연결을확인한다. source/기하수학의원공통기능을불필요하게반복구현하지않는다.
- [ ] 모든소비코드·필요어댑터를독립change-reviewer가검수하고explicitFINAL/SHA를확인해RootACK·작은CPU원문을보존한다. Root최종실행입력맵은 `execution_inputs_before_v10.json`이다.
- [ ] 기존initial source·발·관절검사를연결한다. 새유지보정은초기snapshot을강제주입하는방식이아니라원초기화→준비→유한목표변화의절차다.

## 순서와 종합 guard

baseline28초 → repeat28초 → release34초 → free_strike34초 → regrasp43초를같은후보로순서대로검증한다. 다음native전에모든선행조건의실제raw/SHA/설정/완료와아래해당범위를명시AND한다.

1. core baseline정확29 gate/action정확30 gate. action명령에는같은후보baseline의 `--baseline`을반드시포함한다. 원execute9누락을전용하지않는다.
2. 발5,영상실제5fps,수동조건19,원전기간건강예산13 및source14와추가12부위9 gate. 전역성공bool만검사하지않고필수이름집합과run/config/SHA·완료범위를확인한다.
3. baseline은17–22초연속5초추가정지14 gate와건강17–19/19–21초480표본·RMS0.001rad를확인한다. 16–16.5초목표보정과겹친구간의분류는maintenance_health_v2계획을따른다.
4. 압현준비는원11–16초와baseline17–22초,repeat16–28초,재접촉38–43초를해당case에서같은3번줄/5프렛기하수치로검사한다. repeat의12초창도실제전구간으로계수하고5초로라벨하지않는다. source60Hz와native240Hz/실제현힘null을구분한다. 선호외관조건을기하/접촉성공의대신으로쓰지않는다.

한필수항목이라도실패하면다음물리실행은중단한다. 실패source가있어도보존범위확인을위한읽기전용추가감사는할수있다. child정상종료와조건통과를구분해기록한다. 기대경로/검수/입력맵/로그/보고누락·SHA충돌·잘못된선행case는거부한다.

## 후속과 한계

단독5단계와미해결최종불채택사유가해결된뒤에만별도77초연속·동일초기새77초를구현·검증한다. 현재77초구현/실행은0이다. 새로운Body/LH유지제어로목표가달라지므로미실행된구59초계획의전체literal동일주장을전용하지않는다.

원actual105 EPS0의미세잔차·zero8실제변화·solver정확원인미확정/원fullfinger FK오류는보존한다. 수치예산이나source조건부PASS가이들을삭제하지않는다. 현통과·압현준비는현재비충돌string표식기하이며실제압현력/현진동/음향이아니다. Root자유전신균형/보행성공을주장하지않는다.
