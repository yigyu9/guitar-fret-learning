# 엄지 기저부의 작은 초기각 변경을 직접 native로 검증

엄지2의7source조건(0/±0.05/±0.10/±0.20rad)은모두thumb2–guitar 겹침을남겼다. 음수방향으로LP공통내접반경은4.288365→3.054824mm로줄었으나clear는아니다. Thumb3후면패치source거리도약8.375~9.295mm여서원래의넥후면지지가회복됐다고볼수없다. 이결과는시험한±.2범위에한하며thumb2전체가동범위의불가능성증명은아니다. LP반경은PhysX침투깊이가아니다.

다음에는겹친thumb2의상위관절인thumb1기저부를조정해thumb2와distal pad의위치자체를옮긴다. Thumb3만움직이면상위thumb2형상은바뀌지않는다. Finger1다축importer의FK를검증하지않았으므로CPU예측으로초기형상통과를선언하지않고실제native초기pose를읽는다.

1. fixed_strap_source_hand_initial_v1의실제초기/유지목표를기준으로4개숫자후보를준비한다. 순서는thumb1_x−0.05rad,thumb1_y+0.05rad,thumb1_x−0.10rad,thumb1_y+0.10rad다. 각각한축만변경하고초기각=유지목표(offset0)를유지한다. Baseline x0.530243992805481rad/y−0.9044572114944458rad에서source교집합안쪽으로만움직이며thumb2는0.3384127914905548rad초기/0.3474094569683075rad기존held를유지한다. 다른80초기각/목표와기타초기p/q·LA1.1018469719600776m·PD·몸통9목표·root하체고정·손목파형을보존한다.
2. 각후보의全81native/source/normalized box필요조건·목표float32재조립을검산한뒤순서대로fresh native직접source HG/cross/self1188·palmup·G/root하체/PD/qreadback을검사한다. 이전run_source_hand_initial.py의직접gate를그대로사용하고 source_state/FK_pose_matches는추가하지않는다. Gate거절은0step실제초기이미지/partial영상과겹침pair를보존한다.
3. 처음으로gate를통과한한후보만그같은초기화에서actual1200step5초/두151frame30fps스트랩영상을기록하고이소단계의추가후보실행을끝낸다. 이는batch상한이며전체안정화/연주목표완료판정이아니다. 통과할경우초기기타goal이탈/후기변화·finger실제각source이탈/접촉과엄지후면패치접근을원래quietbaseline과비교한다. Pose·기타·손강제고정/상태반복덮어쓰기·새외력·학습은사용하지않는다.
4. 네후보가모두초기gate거절이면그결과를보존하고손목등으로손전체위치를바꾸는다음단계를새계획으로정한다. 각도범위를벗어나거나gate를삭제해실행시키지않는다. Clear의접촉없는기하필요조건과자유기타의실제안정성은분리해해석한다.

- [ ] 한축4후보숫자준비/범위·다른80보존·사전검수
- [ ] 순서별native직접gate·처음통과한조건의같은초기화5초(최대4초기화/1개5초)
- [ ] 실제변화·초기접촉/손자세·영상/독립검수와다음결정

아직미실행계획이며예정결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1 이다. 조건·기준을임의의최종성공선언으로바꾸지않는다. 기존원본/실험/공용자산을보존하고최종Thorax부터손가락66권한을유지한다.
