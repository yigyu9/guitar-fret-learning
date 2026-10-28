# 직접 시각 QA

comparison_hand.png·comparison_fullbody.png 두sheet와 goal_hand_176.png·goal_fullbody_129.png 원해상도를 직접 확인했다. 영상은 정방향이며 전신뷰는 머리와 양발이 프레임 안에 포함된다. 손뷰에서 파란 검지의 자세 변화 일부가 보이지만 후반에는 초록 중지와 넥이 겹쳐 선택 검지의 전체 관절 윤곽·실제 접촉을 시각만으로 확정할 수 없다.

old250/old300 두 행은 검수된 기존 PNG를 재사용한 비교이며 새GPU촬영은 없었다. 아래 goal NEW행만 원70e40d/PPO0/지도1000 모델의 사전지정env0 첫시도다. 색은 엄지 빨강/검지 파랑/중지 초록/약지 주황/소지 보라다. root도 두sheet와 손176 원해상도를 확인해 방향·전신포함·가림 한계에 동의했다.

영상env0는 세음 달성·A해제False이고 원128평가 원장과 exact다. 모델전체 all3 126/128·A release73/128과 구분한다. F4/비선택B고정·고정기타/finite wrist/currentgoal guard 조건의 NN초기화 사례이며 자연스러움·전곡/J33·압력·RL성과나 해제성공을 인증하지 않는다. 60Hz 합력은240Hz최대나 접촉쌍압력이 아니다.

두 MP4 각177/총354프레임을 전체 CPU decode했고 대표8PNG/두sheet를 저장했다. frame n은control끝점2(n+1), t0없음. 원9항은env0 episode합계이며 tick별9항과 qd는 원평가trace미저장으로 동일성을 주장하지 않는다. 원renderer는 evaluator fingerprint callback을 쓰지 않았고 원본 native full strict load 성공·model/checkpoint불변/scene·encoder0을 검증근거로 사용했다.
