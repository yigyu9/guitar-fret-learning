# Body9 goal-space .12mm 증분 실행 component

Root가 선정한 `diagnose_spine_bounded_ramp_v1/result_v1/result.json` index0의 정밀9증분만 새Scene8에 연결한다. 원strict sweep 실패False와actual_dynamic_tracking_validated=False를 보존하며, 이 부품이LH grip 실패나 실제동역학을 해결했다고 말하지 않는다. source/gain/force/asset/모델/PPO/원자료 변경은0이다.

- oldScene7의 MODE/JOINTS/DELTA 및10..10.5 ramp, 부모Scene3의Chest_x+.005는 그대로다. Scene8는 runtime3.Scene을 직접상속하고 oldScene7의짧은command계산만복사한다.
- 순서는 원Controller request → oldBody9 → newIncrement×16..16.5 smoothstep → 부모Chest last → 원Motion/foot/rate/f32다. Scene7에super로새증분을먼저넣는구현은하지않는다.
- 새cfg는 ready_spine_target_increment_mode/delta_rad/joints/ramp_s 네필드다. MODE는 `finite_static_Body9_goalChest_preserve_Spine_away0p12mm_v1`,ramp는[16,16.5]이며9값은선정JSON과exact한다. 기존body9cfg는유지한다.
- Root확정: steps<=3840까지원Scene7 row literal을보존하고새metadata는없다.3844부터 `ready_spine_target_increment`가추가된다. old ready_body9_pose는원input→afterold, newmetadata는afterold→afternew, parentChest original은afternew와exact다. post16 oldscope는old단계만설명하며단일body실행과동일하다고소급주장하지않는다.
- body9외96축/zero8와state/base_target은변경0이다. cfg오염은부모호출전에거부한다. export Controller는기존runtime6alias이며새Motion·Controller연결은이부품범위밖이다.

CPU는closed baseline8/repeat8 실제targetmetadata·initial105names/zero8/props만사용한다. 실제Scene7/Scene8/Scene3의command본문과원rate/f32부분을AST로실행하고원Motion/foot은기존기록을adapter로유지한다.0/2400/2520/3840/3844/3900/3960/6716경계,원hold16까지literal,추가순서B/f32/다른96/금지축/원binding·state·base/cfg오염을검사한다. 원IK/FK/전체기하/native를재실행하지않고새실제추종을인증하지않는다. 동결/독립review/RootACK전actual사용0이다.
