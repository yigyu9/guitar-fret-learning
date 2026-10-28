# 실제 프레임 직접 확인

comparison_hand.png·comparison_fullbody.png(각 old250/old300 재사용 + 새 warmstart 4시점), 원해상도 warmstart_hand_176.png·warmstart_fullbody_129.png를 직접 view_image로 확인했다. root도 두 비교 sheet·hand176을 별도로 직접 확인했다.

- 화면은 정상방향이다. 전신 시점의 머리와 양발이 프레임 안에 들어온다.
- 손 시점에서 굽힘 모양의 변화는 보인다. 후반 파란 검지 일부가 기타 넥과 초록 중지 등 다른 손가락에 가려 전체 관절윤곽·실제 표면접촉은 확인할 수 없다. 색은 엄지 빨강, 검지 파랑, 중지 초록, 약지 주황, 소지 보라다.
- 고정0/90/129/176프레임을 사용했다. frame n은 control endpoint2(n+1)이며 t0는 없다. old250/300은 이전 실제 PNG 재사용이고 새 촬영은 warmstart env0 첫시도 두 뷰뿐이다.
- env0는 A만 달성, B7/B8 오압현, A 해제false다. 모델 전체91/128 달성과 구분한다. 실패 예시를 사후 성공환경으로 바꾸거나 재렌더하지 않았다.

두 MP4 모두 H264/1280×720/30fps/177frame, 총354frame CPU decode를 통과했다. 원평가와 env0 원장9항·전128 guard scalar21필드는 exact이고, raw22공통필드는 합력 최대7.62939453125e−6N·시각8.881784197001252e−16s 외 exact다. 차이를 보존했으며 허용오차를 키우거나 수치를 맞추기 위한 재실행은 없었다.

영상의 압력·자연스러움·해제/음악 성공·RL-only·자유기타/J33 도달을 인증하지 않는다. 힘은 60Hz끝점 몸체합력이며 접촉쌍 압력이나240Hz최대가 아니다. 실제 원본 checkpoint full native strict load 및 모델불변은 성공한 원 renderer 경로와 원 report로 검증했고 CPU QA에서 CUDA복원을 재수행하지 않았다. evaluator fingerprint callback은 사용하지 않았다.
