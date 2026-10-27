# 직립 몸통에 맞춘 기타 목 상향 배치

source11/12는frontnormal .65soft/.45hard와손도달을함께만족하지못해native미사용이다. source12의실제normalGZ.315/palm18.73mm·3.4°로개선은있지만hardnormal.45미달이다. 원래의정밀연주위치를지킨다고부르지않는다.

source13은source9몸통/Head/lower24/zero8/Root/의자/물성/형상을유지하고기타initial world-Y 회전추가+.25~+.55rad(약14~32°)를허용해목을올린다. Gbody중심높이를맞추도록guitarroot초기Z는+.05~+.20m범위에서함께계산한다. 이는자유강체의초기배치이지동적고정이나매step보정이아니다. 기존자세에서가슴은GlocalY−.246m의좁은상부/윗모서리에닿으려하고초기후G가내려앉으며Spine이먼저지지했다. 목각도를올려가슴높이에넓은몸통구간을놓는새기하다.

Chestgap.4mm/RHip.4mm/Spineclear2mm/PelvisBOXclear2mm를최적화하고양팔은기존guitar-localpalm위치·방향을다시맞춘다. RShoulder근접/앞방향성분·RElbowclearance도검사한다. 원범위/zero8/lower24/head/body보존/손5mm·2°/전체sourceaudit후기존유한controller10/scene8/preload−.08/Chestnormal20/RShoulder3D20으로정지5초를검증한다. 실제기울기total5/right3·Chest/RShoulder양의접촉>95%(1초후)·모든안전gate통과후15초해제. 원자료보존/PPO없음.
