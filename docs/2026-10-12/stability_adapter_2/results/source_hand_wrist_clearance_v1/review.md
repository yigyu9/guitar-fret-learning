# 손목13조건 source 검색 사전 검수

요약 판정: **문제없음(PASS)**. 검토한 최종 코드에서 실행을 막는 Critical/Warning은 없다. 소유 파일은 이 review.md뿐이며 이전 봉인 review/소비 파일·타인 소스를 수정하지 않았다. 검수 시점 search/native 출력은 없었고 geometry/FK/search/native/producer main은 실행하지 않았다.

- [기준 상태:36](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:36)는 변형하지 않은 source-hand5 실제 초기 상태를 사용하고 해당sealed SHA와 기존조건부모델 checks를 확인한다. 새 finger1변경이나 실패한thumb1/2 delta를 승계하지 않는다. CoupledSnapshot에는 같은 실제state를 기준/현재로 전달하고 zero pose identity를 강제한다. 조건부source 모델이며 actualnative 응답 인증은 아니다.
- [이동 범위:75](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:75)는 L_Wrist 전체XML subtree를 사용한다. XML 직접검산상23 body에 thumb_pad/top까지 포함되며 활성collision geom17개가 대상이다. build_probe에서 제외하는thumb_pad geom과 따라가는pad pose를 구분한다. [identity 검사:121](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:121)는 상위팔 pose/비이동mesh 및 wrist아래전체 parent-relative 변환을 보존한다. 이전thumb2 코드의자식body 누락은 재발하지 않는다.
- [수치 계약:85](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:85)은 기존 left33offset 전체를 유지해 원전체target을 먼저재현하고 zero1+각wristx/y/z±.05/±.1의13조건을 float32초기각으로 조립한다. 검수자가 원raw/범위/offset으로 float64조립→float32를 별도재계산해 다른80초기·held exact, 전체81effective범위·손목sinusoid±.005양끝을 통과했다. x/y/z를initial=held/offset0으로 바꾸지 않는다. 일부axis의held_delta는 float32반올림으로initial actual_delta와1ULP수준 차이가 나며 코드가 별도필드로 기록해 올바르게 구분한다.
- [형상 검사:111](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:111)는 전체human–G/cross/self1188과palmarup>0을 필수조건으로 삼고,palm/허용patch·thumb3/후면patch의source거리upper/lower를 기록한다. 평면법선은world polygon으로 만들며proxy와의절대내적은필수gate가아니다. [선택:147](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:147)은 actual|delta|→두patchupper제곱합→alignment큰순→고정order이며 계획과 일치한다. LP/source witness 거리를 cooked침투깊이·실제접촉·힘·지지 성공으로 확대하지 않는다.
- [후보:149](/home/ajou/yigyu/3/stability_adapter_2/search_wrist_clearance.py:149)는 새phase전용trial에한초기axis만변경하고 offset전체동일성을assert한다. 다른80초기/target은위검사를통해보존하며원proposal의source_state를제거한다. source_prediction.json은별도예측기록이고runtime에서state로재생하지않는다. Clear후보없으면proposal/native없음,한후보만freshdirectnative gate/통과시같은init5초로이어진다. 미래실제source결과/선택/actualgate/PD응답은아직검수범위가아니다.
- [wrapper:25](/home/ajou/yigyu/3/stability_adapter_2/run_wrist_clearance_phase.py:25)는 직접원자료·모델·XML/mesh·canonicalhelper를사전SHA/사본보존하고nativeonly로frozenrunner가실제읽는기존closure와source_prediction을추가한다. Frozenruntime/innerSHA를강제하며전후SHA·로그·exit를기록하고0step+directgatefalse만예상거절terminal로구분한다. [entryadapter:10](/home/ajou/yigyu/3/stability_adapter_2/run_wrist_clearance_candidate.py:10)는원audit_initial을재사용하고원scope/failure출처를남기며finally에서후킹을복구한다. 별도FK gate나추가외력/자세고정·상태덮어쓰기 경로는없다.

Python3.8 AST 통과 및 사전 확인 SHA-256:

- search_wrist_clearance.py: `bac9f7c7e63f15a73d1d6da2b6c4eac8b22f98ad3908bfa19fa2cbb3eaec0b47`
- run_wrist_clearance_phase.py: `f312230d35c6d1064e6c1545ff45cc74be5692255de4e99f4d566534cb006a91`
- run_wrist_clearance_candidate.py: `3eac48f4e385f9f561f6301619c38aeffc87829f3a461779dabab16731575c2f`

검수는 소스읽기·AST·XML계층·작은독립수치계약에한정된다. LA/G/PD/root하체/몸통9·최종66권한을 유지한다는 [미실행계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:7)과정합하며,13source통과나임시자연구역을안정화/연주/학습완료로선언하지않는다.


## 실제 source13조건·최종 그림/문서·다음 계획 검수: PASS

요약 판정: **문제없음(PASS)**. 추가 Critical/Warning은 없다. Source-clear후보는0개이며 이번phase의 새native/physics/actor/학습과5초측정은없다. 사전 검수와 마찬가지로검수자는geometry/FK/search/producer/native/감사 main을실행하지않았다.

- [원 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/search_execution.json:1)의 exit0/terminal completed,69입력/69사본의현재·전후SHA와로그SHA를직접대조했다. [Search](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/search.json:1)는8검사true/13조건/23movingbody·17collisionbody이며selected=null이다. Proposal/source_prediction/native디렉터리/native_execution이없다. 각조건actualfloat32초기각/초기delta/offset유지compose후held角·helddelta를원baseline에서독립재조립해일치했다. 저장source_clear식을재계산하고다른80/upperarm/nonmovingmesh/handrelative identity·self1188/cross clear·up>0과patch거리upper/lower/gap/feasible witness오차의정합성을확인했다. Solver/FK미재호출이므로형상수치는저장결과·코드·기준재현검사의정합성검수다.
- 모든13조건에thumb2–G교차가남았다. Wrist_y−.10의thumb2 LP0.815475676mm만보고clear로판단하면안되며palm–G2.076522306mm와finger/fret등총HG6쌍이남는다. Wrist_x+.10은평면정렬proxy0.999391469지만thumb2/palm의HG2쌍이남았다. 원기준thumb2 LP4.288364821mm와조건별전체HG쌍이원search·문서/그림과맞는다. LP반경은cooked침투깊이/접촉력/지지인증이아니며13표본을전체손목범위불가능성으로일반화하지않는다.
- [실제PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/artifacts/wrist_source_clearance_radii.png)를직접열어13조건의파란thumb2반경/주황나머지보고HG최대반경·각값·rad/mm·두범례·세줄caption의표시와잘림/겹침없음을확인했다. `none`은다른pair가1e−7m LP보고임계값을넘지않았음을뜻하며거리0으로표현하지않는다. 최종README13행의HG쌍수·두반경·up proxy를원search에서6자리format으로재계산해전부일치했다. 재사용Gym초기이미지는직전source-hand5실제0step거절장면이며이번조건의새native렌더로설명하지않는다.
- Artifact ONE실행exit0/직접6입력/producer·wrapper포함8사전사본의현재·전후SHA·로그·PNG출력SHA가exact다. Producer AST3.8통과/SHA `2d030f3a5409c9c07a20504b50e917fa440489a2b5a13060febb9eed52590378`, wrapper SHA `65981ca5e47dc7be4d64f61ba6334f69ee94f105cd8c20dd5721b6e6b91d0e78`. 저장검색69입력closure와그림직접6입력은구분했다. Artifact/README/ROOTnotes는새물리0·기존영상152개유지·5초미측정으로일치한다. 영상/이전inventory의최종전체보존감사는root담당이다.
- [다음팔계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:7)은원baseline과Wrist_y−.10가설의두seed에서각seed자체1+Thorax/Shoulder/Elbow9축×4delta=37조건씩총74조건인 **미실행 계획**이다. 두번째seed는채택된자세가아니며최대두초기축변경·originalbaseline대비실제delta L2norm우선/동률patchupper제곱합→soft정렬→고정order로범위를명시한다. [offset보존:8](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:8),다른79/80·전체81범위/손목sin양끝·Torso/Spine/Chest/body9/root하체/Gfullstate/LA/PD·최종66권한과자유기타를유지한다. 측정finger1계층을사용하며재현성검사후한후보만freshactualgate/통과시같은init5초,별도prediction대조/state미재생으로계획돼있다. Source검사를물리유지·자연성·fret/strike연주목표완료로대체하지않는다. 향후구현/실제허용판정은이번검수범위가아니다.
- 최종README/CHANGED·[ROOTnotes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/ROOT_VERIFICATION_NOTES.md:3)와main [README:1184](/home/ajou/yigyu/3/stability_adapter_2/README.md:1184)·[PLAN:2005](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2005)·[VISUAL§115:2080](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2080)이결과와일치한다. 문서파일/줄링크및main사전prefix보존을확인했고CHANGED마지막main결과refs1184/2005정정도확인했다.
- [root감사코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/root_final_audit_producer.py:20)는source69입력/사본·8checks/13rows/no-candidate·그림·기존6inventory/152영상·인덱스·mainprefix를검산후source_final/inventory를작성하고그직후현재SHA를재확인한다. Append가능maincanonical3개는사본을남기고inventory에서제외한다. AST3.8통과/SHA `204416c64d2ea7f255c639cc14df645fbd1fd364480720f8f98f41c447a4c97c`. 감사코드는읽기만검토했으며현재실행완료를인증하지않는다. Root의결과폴더stdout파일미개방방침으로직전열린로그inventory오류를반복하지않는다.

최종확인 SHA-256:

- PNG: `2bc07d8268d798510d3ad213b04af48e999f5bd0583c75dbcc8d94b1fb597e24`
- README: `2ca040a20844866bf78e1a291cc0f192d4258c65f159779be4e8b6c5de7759db`
- CHANGED_FILES: `fcdb568916e7357c24413859d76a3e178a704b9f6d7b1bd611fa9fb11bf204c4`
- ROOT_VERIFICATION_NOTES: `1ee4521a8c798b9a3dbfb3b2cf2f4d1d30166f6e276b73803890bc469a7ee4bb`

소유파일은이번review.md뿐이다. 최종추가기록을동결하며이후root의별도보존감사결과를따른다.
