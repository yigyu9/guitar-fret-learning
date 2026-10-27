# 선택적 Body9 유지자세 후보

## 실패와 선정 근거

Chest_x+.005 후보의 native_free_strike_v4는28초/6720step 정상완료했지만 삼중양성지지가 세왕복82.7263/20.8117/8.0125%로95%에 실패했다. 발 전행/세왕복6→1·1→6/근위1도/왼손완전해제15초/제어수학은 통과했다. 기타가 떨어지지 않았다는 사실을 가슴 지지 성공으로 바꾸지 않는다. 재접촉과52초 연속실험은 아직 실행하지 않았다.

독립 비교 diagnose_free_strike_v4_v1/summary_v1.json(SHA5201099181b815ace037af121d89b83acc0388a8ffe8d8b68e836f95f7889fbd)에서 Chest_x 실제 변화는약+.0046rad였지만 고정Chest피부점 world법선 이동차는 수µm뿐이었다. 고정G/다른관절불변 FK의 .1495mm 예측이 실제 전체자세에서 실현되지 않았다. 기타가 똑같이 따라가 상쇄했다고 단정하지 않는다. R_Shoulder는 보정된 고정WORLD vector spring이고 Spine 직접 support spring은 없다. 실제 Chest/R상완/Spine 접촉·source형상·가상힘을 구분한다.

새 source 진단은 원initial FK를 유지하고 실제10초에서 Chest source피부점 G쪽+.4mm, Spine source피부점 법선이동0, R_Shoulder 원support_reference.local_m의 world xyz이동0, Chest up_W.z변화0을 만족하는 한 상수 Body9 추가벡터를 구했다. 관절suffix는 world축이 아니다. R상완 전체나 Spine 전체를 고정한다는 뜻이 아니고, 한점/투영 제약이다. 마지막 FD행은 up_z/rad이고 다른행은m/rad라 condition을 물리 안정성 지표로 해석하지 않는다. SLSQP local해이며 전역최적 증명은 아니다.

선정 자료: /home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/diagnose_selective_posture_v1/selected_v5/selected_vector.json SHA da6a3f530da9821de2213cdbd6606c583e86d9c5baf4a31d7f9380bb29a098a9, pointer /additional_delta9_rad. 순서는 Torso_xyz,Spine_xyz,Chest_xyz(105인덱스24..32)이며 추가 rad는 [-0.0024914193053158524,0.0012502098265553363,0.0009860719371486124,0.01266242285746553,0.00028587694834892127,-0.0015162127764489063,-0.00991982325421395,-0.002496360525058921,0.002195595180496408]다.

selected_v5/result.json SHA1734b453d9e1f94cbaa5055b3e0f42bbfa514e67af2b8029026b6d2b2326643b에서 실제10..28초4321상태+추가벡터 source예측 maxTorso3.487797/Spine4.836059/Chest4.717510도,right1.198113도였다. 원전체105제출목표/float32/변경Body9 bounds/zero8 변경 위반0. Rmaterial world잔차≤6.865µm, Spine normal−3.131..+4.674µm다. 원목표조건 Spine−13.101..−9.375µm를0이라고 설명하지 않는다. .5mm해의Spine4.97938도는 여유가 작아 기각했다. 고정G/저장q에 얹은 예측은 새로운 실제 다점접촉/하중/미래기울기 성공이 아니다.

## 구현과 검증

- [ ] runtime_v4.Scene는 runtime_v3.Scene를 상속한다. 2400step 전에는 부모 반환값 그대로이며 새metadata가 없다. 이후 원named사본에 위 추가9×smoothstep(10..10.5초)을 먼저 더하고 부모를 한번 호출한다. 기존 Chest_x+.005는 부모에서 나중에 더한다. 두 가산을 총벡터로 묶어 부동소수점 결합순서를 바꾸지 않는다. 정상상태 원base 대비 Chest_x 총가산은−.00491982325421395rad지만 추가항은−.00991982325421395rad다. 기타/실제상태/base_target를 변경하지 않는다.
- [ ] 추가4cfg는 ready_body9_pose_mode=finite_static_Body9_selective0p4mm_tilt0_v1, ready_body9_pose_joints, ready_body9_pose_delta_rad, ready_body9_pose_ramp_s=[10,10.5]다. ready_body9_pose metadata는 원105/추가후105/9축·bias/시각·step/다른96동일/상태와base보존을 기록한다. 기존 ready_chest_pose metadata는 추가Body9가 반영된 요청을 original로 갖는다. 기존Chest preload10mm/K2000/D30/cap20·모든원gain/cap/일정/initialsource9/큐브/하체/충돌정책 불변이다. 타현주기/접촉을 추종해 Body9를 흔들지 않는다.
- [ ] analyze_v5는 원base/lower/2396R12로 Body9 추가전105를 독립구성하고 새metadata와 추가후105를 검사한다. 추가후105를 기존 Chest helper expected_original로 전달하고 최종other 기대값도 Body9 먼저→기존Chest scalar 나중으로 만든다. 원28/29gate, 전N 제어수학, first10 actual4raw exact, 발 전행, 근위목표/실제1도, 실제6줄/양측준비, 원LH15초 raw0/형상2mm/재접촉5초를 유지한다. 누락/부호·시각·벡터·순서 변조를 CPU에서 거부한다.
- [ ] run_v6는 runtime_v4.Scene/원runtime_v2.Controller를 명시하고 같은 새후보 baseline_v5의 core/발/입력·원자료 SHA를 확인한다. Root는 새 inputs_body9_pose_v1 6cfg/execute_v5.py/prepare_body9_pose_v1.py/execution_inputs_v7.py를 생성한다. 원v4 cfg에 새4필드와 baseline_summary 경로만 추가·변경한다. 이전코드/설정/실패/CPU원문과선정진단·원XML2/mesh104/manifest2를 사전·사후 SHA로 보존한다.
- [ ] 문법/CPU/독립코드검수 명시완료와 동결review SHA를 Root가 ACK한 뒤 closure와config를 실행한다. CPU가 실제부모 footIK/native를 실행하지 않은 범위는 명시한다. 실제출력 native_<case>_v5, analysis_<case>_v5/feet_<case>_v5/media_audit_<case>_v5로 분리한다. baseline28→repeat22→release28→free_strike28→regrasp36→continuous52 순서로 각 core+발 통과 전 다음실험 금지다. 실패 시 원95%/5도 등 gate를 완화하지 않고 보존·진단한다.
- [ ] 최종 자료는 같은 phase에 한국어로 근거/실제관측/실패/남은과제/자세값과영상경로를 기록한다. 실제기타free·중력ON·strapOFF·Root만고정·하체16유한/원zero8보존,기타힘0/부착0/매step상태주입0/PPO0를 유지한다. 현통과는 기하학적 타현이며 접촉력/진동/음향 검증이 아니다.

소유권: 구현담당 runtime_v4.py/run_v6.py와 자기CPU, 분석담당 analyze_v5.py와 자기CPU, Root leaf/설정/외부wrapper/closure/main문서/최종보존, 독립reviewer 검수파일. 서로 혼자 작업하는 것이 아니므로 타담당/소비 파일을 되돌리지 않는다. 사용자2026-10-07 자율실험 및 현재초기자세 범위로 진행한다.
