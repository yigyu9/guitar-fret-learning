# 현행 약지 마지막300 저장본 영상

실행 전 사전지정: 성과와 관계없이 마지막300회 checkpoint의 평균행동을 원128환경·env0 첫시도에서 렌더한다. 현재 학습이 완료되지 않았으므로 이 문서는 영상 성과나 완료를 뜻하지 않는다.

- 원 current_ring_learning_v1의 strict checkpoint·557/Jv3·동일128 native 제어/힘 상한/teacher 계약과 설정을 유지한다. 실제 학습/NN 파라미터 갱신은0이다.
- 원 `_evaluate`를 그대로 실행하고 기존 GraphicsGym·native camera/encoder/EnvZeroCapture로 손 확대·전신을 저장한다. 장면/정책tick을 중복 실행하거나 물리상태를 영상용으로 덮어쓰지 않는다. 카메라 변경은 영상만 바꾼다.
- 실제 마지막300 고정평가의128첫시도 compact 요약과 env0 trace를 대조한다. 순힘의 수치오차는 별도로 기록한다. 동일하지 않으면 같은 재현이라고 주장하지 않는다.
- CPU 검사 및 비참여 준비검수 후 GPU를 단독 실행한다. 출력·해시·실제 종료0·FFmpeg decode/프레임 크기·정방향 QA와 독립 검수를 남긴다.

계획과 소스는 준비 봉인 후 동결하며, 원 학습 소스·checkpoint·평가는 수정하지 않는다.
