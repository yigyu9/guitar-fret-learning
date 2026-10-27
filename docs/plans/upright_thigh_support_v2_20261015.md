# 오른허벅지 받침 높이 후속 한 조건 비교

이전upright_thigh_support 계획/소스/결과는보존한다. 정지V5(source7)는5초와각도·유한제어·금지API/입력보존을통과했으나Chest접촉0이었다. 종료sourceChest간격은이전9.276mm에서4.137mm로줄어기하학적받침높이의효과가관측됐다. 오른Hip_x수정만−.04→−.08rad(−4.584°)로높이고,오른발source최저점soft목표를5mm로두며무릎/발목/발가락최적화범위를±.45rad까지허용해바닥겹침을피한다. 발지면강제고정이아니며발이지면에서조금뜰수있다. Root/왼다리/형상/물성/zero8/원105와같은finitecontroller6·gain·supportcap은변경하지않는다.

발목/발끝의평면화가아닌실제최저점과bottom span을최종float32/native에서측정한다. hard source선정: 원범위/zero8exact,모든발min≥.5mm/오른발bottomspan≤3mm,원PelvisBOX/기타body·chair·ground비관통및capsuleaudit·양손도달. 몸통·Chesttotal≤5°/옆≤3°와실제Chest/R_Shoulder양의접촉을정지5초에서먼저확인한뒤해제15초를실행한다. 실패시기록/보존하고PPO하지않는다.
