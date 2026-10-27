# 실제 quiet 자세에서 기타 보정 제어권을 확인하는 다음 소단계

연속 팔 탐색은두seed각400회·총800source평가상한으로종료됐다. 두optimizer는수렴성공이아닌평가수상한종료다. Clear후보는없으며가장작은최대HG반경은row798의0.783417117mm다. Palm–G0.427649599mm,thumb2–G0.688060578mm,middle3–G0.783417117mm가남는다. 이는가동범위전체의불가능성증명이아니다. 예정대로같은source범위를더탐색하지않고실제5초를확보한quiet기준으로돌아간다.

## 기준을 고르는 근거

initial_middle3_alignment_v1/native는자유기타·고정LA1.1018469719600776m·몸통9PDhold·root/하체고정에서실제1200step/5초를완료했다. 최대기타초기오차14.608483mm/2.918412°,후기완전1초창변화0.648625mm/0.115306°다. Native양의raw lambda관측step은LH:index3 1156,LH:thumb3 587,LH:middle3 91,LH:ring3 38,R_Hip1200이었다. Palm접촉은확인되지않았다. Rawlambda를지지력·forceclosure·관통깊이인증으로취급하지않는다.

이자세의일부손관절은기존checkpoint출력통계범위밖이다. Source호환5관절을먼저강제하면thumb2겹침이생겼고지금까지해결하지못했다. 따라서초기자세를checkpoint출력통계범위안에넣는것을현재모든물리PD진단의필수조건으로두지않는다. 모델native관절한계·초기source형상/양손/self검사·palm위쪽반구는유지한다. 통계범위를해부학적한계와동일시하지않으며정책호환미해결을숨기지않는다. 기존actorqualification/로더gate를우회하거나정책추론·학습을시작하는변경이아니다. 다음연주전환설계에서는안정hold목표와pretrained연주목표를어떻게연결할지명시적으로다룬다.

## 다음 두 실제 입력

원quiet초기81각/heldoffset/PD/기타fullstate/고정LA·몸통9/root하체/최종66권한을유지한다. 원기록과같은L_Wrist_x ±.005rad·1Hz명령도t0부터유지한다. LH:index3는native접촉이관측된scalarfinger축이므로첫물리제어권진단대상으로고른다.

두조건은LH:index3 PD목표에만각각+.005/−.005rad를더한다. t<2초에는0,2≤t<2.5초에는선형증가,2.5초부터5초까지는각각상수보정을유지한다. 변경은60Hz최종목표합성뿐이며source/native관절목표를clip하지않는다. 다른80목표와초기81각은원quiet기록과exact로검산한다. 2초는causal비교를위한진단시점이며연주전의WAIT/GRIP단계를필수화하지않는다. 새feedbackgain·새기타힘은아직넣지않는다.

각조건에서fresh actualnative직접초기HG/cross/self1188·palmup·81초기각/PD/기타fullstate/LA/root하체를검사하고통과한같은초기화로1200step5초전신/손스트랩영상을기록한다. 최대두초기화·두완료5초다. 초기검사거절은0step partial로보존한다. 원quiet와0~2초state/trace/명령prefix의동일성을확인하고이후차이를보정입력에의한응답으로분리한다. 이전rawsource/q/목표/영상은수정하지않는다.

## 측정과 이후 판단

두조건과원quiet의초기p/q최대/종료오차,2~5초완전1초창변화,PD추종,실제접촉과palm방향을비교한다. t5에서각조건과baseline의기타world위치차이및world회전log차이를구하고±.005rad입력사이의중앙차분으로6×1응답을기록한다. 이것은마찰·접촉상태가있는한자세/한시간구간의유한응답이며전역Jacobian이나안정한feedbackgain의인증이아니다.

초기목표로되돌리는방향의관절입력이있는지실제자료로판단한뒤다른접촉축/팔목표·제한된feedback또는연주목표연결의다음실험을정한다. 출력이작으면'이축의이번입력에대한응답이작다'고기록하고전체66권한이없다고확대하지않는다. 기타고정/강제손부착/지속pose덮어쓰기/인위적기타복원힘은금지한다. 정식자연스러움/성공기준·fret/strike전환은아직미검증이다.

- [ ] Quiet초기입력/두scalar목표명령과fresh직접gate entry 구현·독립검수
- [ ] 두조건actual5초/각초기값·두카메라·모든원자료보존
- [ ] Prefixexact·6×1응답·기타오차/접촉/제약분석
- [ ] 그림/영상·독립검수·다음물리보정/연주전환결정

아직미실행이다. 예정결과경로는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1 이다. 사용자자율진행지침에따라필요한진단방향을파일에먼저기록한다.
