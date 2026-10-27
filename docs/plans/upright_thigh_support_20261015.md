# 직립 가슴 지지의 오른허벅지 받침 높이 보완

상위 upright_chest_support 계획의 직립각 기준(옆3°/전체5°),Root 고정·기타자유중력ON·스트랩OFF·원105/범위0의8축·유한제어·상태덮어쓰기금지·기존물성/모델보존은그대로다. 기존lower24 초기값보존은앞선단독비교조건이었다. 사용자가초기자세조정을승인한범위안에서새후보만오른Hip_x를−.04rad(−2.292°)바꾸고Knee/Ankle/Toe 유효축으로발bottom을지면위1mm에맞춰받침높이를올린다. pelvis/root/leftleg/기타형상을바꾸지않는다. 원lower24,수정lower24,q_ref105,lower_deltas,예측FK/실제FK/발source/원native물성을각각기록한다.

근거: source6정지V4는몸통·가슴up기울기전체5°/좌우3°를모두통과하고기타root이동22.2mm로안정했지만,가슴양의접촉0/종료sourcegap9.28mm,Spinegap−.244mm였다. 기존고정점3Dtask가거의아래10N에포화된다. normalpress단독비교도실패했다. 힘증가/더큰허리기울기대신받침높이를변경하여가슴접촉높이를맞춘다.

- [ ] source7에서오른knee높이/footmin·span/zero8보존/최종관절범위/원PelvisBOX2mm목표/전체capsule audit 및양손도달검사.
- [ ] 독립검수후기존controller6/scene7같은gain·cap으로정지5초. upper/하체FK·좌표안전gate·발·원조건검증. Chest와R_Shoulder의실제양의contact>95%(1초이후),몸통·Chest전구간right≤3°/total≤5°,기타·하체궤적유한을동시에판정.
- [ ] 정지성공후에만15초왼손해제. 접촉/자세/발·속도·입력SHA와기존실험보존을검수,원자료/실제영상과실패를자료폴더에기록. PPO없음.
