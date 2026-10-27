# 4.2° 전경 목표의 유한 상체 제어 비교

정지V9(source9/preload−.08/normalChest20)은5초/모든초기·안전·각도기준을통과했으나Chest접촉0,종료sourcegap2.987mm다. 끝법선요청norm12.0N으로20Ncap에도달하지않으므로cap증가만의근거가없다. source9초기상체는Torso3.298/Spine3.586/Chest3.502°전경이고현재동적Chest전체최대4.147°다.

다음은초기source9와모든gain/cap/하체/preload/normal task/물성/제약을보존하고상체의유한관절목표만조정한다. Torso/Spine/Chest의worldup을옆기울기0/전경4.2°로계산하고양손palm의기존world위치·방향과Head방향을IK로유지한다. 목표q105는원범위안이고lower24/zero8는초기와exact같다. q_target은초기state가아니며,접촉을누르는목표형상의sourceChest음수gap은강제상태설정/실제관통주장이아니다. native초기는여전히source9의안전배치이며s.command의기존body.1rad/s·팔3rad/s등rate로유한effort/nativeposition48에만제출한다. 별도target파일·생성입력/코드도pin한다.

정지5초:Torso/Chest전구간total≤5/right≤3,Chest/RShoulder양의응답>95%(1초후),모든안전gate와발/zero8/Root·의자/실제기타자유/해시보존을동시판정한다. 통과후같은조건으로왼손15초,새PPO없음.
