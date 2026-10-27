# 근접 후면 엄지 anchor의 초기각 검색

Catalog367면에서선택한303/1462centroid는최대면적323의필요이동17.136178mm보다작은11.677485/11.698917mm였다. 두anchor모두initialrear-facing이며간격2mm이상이다. Linearfit잔차가작아도fullFK/겹침/물리유지인증은아니다.

- 같은half q81/G/LA1.1018469719600776m/oldT81/gain/native/Aug19/C02와팔±.05·엄지±.20의17좌표bounds를유지한다. 나머지64 초기각은유지한다. 두anchor각각.3/.7mmclearance의네source후보를준비한다.
- 각thumb목표XY는catalog의최근2mm insetpatchgoal에서왼쪽edge의inwardnormal방향으로0.5mm reserve를두고GZ는rear−8mm에서clearance만큼바깥이다. Palm기존관측anchor및목표(Y45mm,Z4.5mm)를유지한다. 새로운G world목표/외력은아니다. Thumb source면normals+GZ/palm−sideX는soft선호다.
- 기존source각도한계/목표81 exact/상향proxy·전체human–guitar/양손/비인접왼손교차/point2·3mm여유/거리interval.3~1mm/rearwitness방향gate를완화하지않는다.
- 이전실제source교차자료의index3–guitar/fret3 및middle3–guitar/fret4에만SAT face-plane분리soft항을추가한다. 최소source간격.1mm를선호한다(최종LP로검사, actual접촉인증아님). 네다른손가락초기각과기존front높이선호는유지한다.
- 선택된각centroid/normal/area/index는freshsourcemesh에서catalog값과대조한다. 원최대면적/관측anchor는수정하지않고보존한다. 최종source통과후보가있으면anchor중복을줄여최대2개실제5초/freshnativeFK/초기값·전신/손151frame을기록한다. 실패후보는물리실행하지않는다.

최종양쪽Thorax→손가락66권한/몸통9 PD목표/root하체물리고정/자유G·중력·수동strap/selfcollisionON은같다. 기타고정/손부착/pose덮어쓰기/G목표힘은없다. 다음제어·학습구조는actual지지자료를읽고정한다.
