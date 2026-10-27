# 고정LA에서 source 범위에 들어가는 손5관절 초기 배치

현재 초기middle3정렬후보는 임시자연구역안의actual5초를완료했지만 source/native/normalized 범위CPU34검사에서 왼손5관절이범위밖이다. 원본checkpoint/자격/환경을바꾸지않고 초기손자세를새후보로검증한다. 이계획은다음물리단위이며현재미실행이다.

1. fixed_strap_source_compatibility_v1/joint_ranges.jsonl의initial_aligned 실제초기/held행을사용해 LH:thumb1_x,thumb1_y,thumb3,index1_x,ring1_x만 각각가장가까운교집합경계의float32 1ULP안쪽값으로선택한다. 초기q와유지목표를따로검산하고offset도새q에맞춰기록한다. 다른76초기q/유지목표와1200손목명령·G초기p/q/LA1.1018469719600776m/PD·몸통목표/root하체고정은보존한다. 현재0.66rad크기의엄지변경을이전±.3rad팔탐색과혼동하지않는다. 사용자의필요결정자율진행범위에서근거를남기고단계검증한다.
2. 기존조건부18좌표FK/이전proposal의FK_pose_matches 검사를사용하지않는새진입점을작성한다. Fresh native실제초기상태에서전체81q/heldtarget·nativefilter/PD/root하체/G를입력과대조하고source human–G/cross-hands/정책self1188쌍·palm상향proxy를검사한다. Source형상은PhysX cooked관통인증과구별한다. 직접형상검사에FK검사를통과했다고붙이지않는다. 초기구조검사는0step/read-only이어야한다.
3. Gate실패면실제초기값/이미지·겹침pair/이유/0step을보존한다. 통과면그한초기화로actual1200step5초/두151frame30fps스트랩영상을저장한다. 새각/목표가source범위에들어가는지와실제각이실행중벗어나는지분리해기록한다. 기존초기52.09°및quiet후보의기타초기이탈·후기1초/2초기준/접촉·자세와비교한다. 손모든손가락의동시접촉이나특정palm접촉을새필수조건으로추가하지않는다.
4. Sol이원자료를판단하고Luna가확정brief의결과/영상/그림설명을정리한다. 별도change-reviewer와보존감사뒤다음후보/연주무학습연결방향을결정한다. 실패trial도보존하며본계획을기타/손고정·상태덮어쓰기·actorloader자격우회로대체하지않는다.

- [ ] 5관절후보와float32목표/범위보존 준비
- [ ] Fresh native직접초기gate 구현·검수
- [ ] 0step실패또는같은초기화5초/두영상·원자료비교
- [ ] 결과·검토·다음결정

메인계획·구현은 /home/ajou/yigyu/3/stability_adapter_2, 예정결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1 이다. 신규actor추론/학습·제어보상변경은이단위에포함하지않는다. 최종Thorax이하66권한·몸통9목표·고정root하체·자유기타/수동스트랩·기존결과/공용자산보존을유지한다. 임시30mm/5°와후기1초5mm/1°는관찰기준이며자연성/연주성공의확정판정이아니다.
