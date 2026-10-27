# 왼손 완전 이탈과 목 재접촉의 측정 기준

최초 새 source/물리 실행 전에 전체 계획과 재접촉 보완의 측정 좌표를 고정한다.

- 손목60mm 이탈은 `norm(currentG의 실제 L_Wrist 위치 − 실제10초 L_Wrist의 G-relative 참조위치) >= .060m`로 정의한다. world10초 위치 대비 이동은 별도 진단이며 합격을 대체하지 않는다. 현재G의 pose는 실제 native 정규화quaternion으로 매표본 변환한다. 손목을 G와 함께 이동시키는 상태주입은 하지 않는다.
- 완전 이탈15초의 왼팔·손 raw 접촉0에는 L_Thorax/L_Shoulder/L_Elbow/L_Wrist와 LH: 전체를 포함한다. source geometry2mm는 LH:전체+L_Wrist/L_Elbow를 실제60Hz에만 판정하고, 근위2부위의 source간격도 별도 공개한다. cooked 접촉/전체시간 연속간격 인증으로 표현하지 않는다.
- 원기타의 root body `guitar`에는 guitar_neck1/guitar_neck2와 headstock이 있고, 별도 G:nut와 G:fret1..22가 있다. 물리 목 접촉의 사전 후보 body는 이들로 한정하며 실제 shape/filter를 대조한다. G:body/프록시/현/표식/타현영역은 제외한다. root body에는 headstock도 있음을 공개하고, 같은 초기 neck 잡기 위치의 재접촉은 실제 wrist G-reference2cm와 실제 finger close 판정을 동시에 요구해 확인한다.
- 재접촉 후 같은 고정 active finger축의 닫힘량/닫힌목표오차 기준은 별도 regrasp 계획의 .10rad cap·예상량.5·목표오차.10rad를 따른다. 5초 dwell의 모든240Hz 표본에서 그 축이 만족하고 neck-finger 양의접촉비율95%를 별도로 요구한다.
