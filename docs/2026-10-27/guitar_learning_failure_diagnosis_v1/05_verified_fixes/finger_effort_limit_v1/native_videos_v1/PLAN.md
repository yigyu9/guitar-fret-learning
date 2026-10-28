# 선정 압현 자세의 실제 GPU 손·전신 비교 영상

실제cap비교/별도검수뒤기존20Nm와진단0.25Nm의움직임·자세를눈으로확인한다. 두손가락index115/middle114각두조건의env0첫시도만촬영한다. 학습된정책/최고체크포인트영상이아니며기존4환경전체성과나미추적실패env2영상으로가장하지않는다. 0.25조건의향상은현재미확인이다.

1. [ ] CPU최소연결/검수: 원repro/capprobe의실제collect/목표/4첫시도·EffortPool/native105readback을유지하고별도얇은observer wrapper에서step후기존_EnvZeroCapture를호출한다. 기존활성render_finger_skill의camera/encoder/capture와GraphicsGym을재사용하며NN/oldcheckpoint/과거source import0. source수정0·추가physics step/reset/시계변경0. 카메라생성을위한graphics활성화·시각색상만원위치/finally복원. 원_pins는완화하지않고새observer/사용helper/현재원본seal·actualreviewSHA를superset으로추가한다. 모두새output에서실행한다.
2. [ ] root GPU직렬: baseline20/index,middle 및cap0.25/index,middle각4환경. env0한번의firstattempt에손/전신1280×720·30fps. 기존fullbody y=3.4시야와hand카메라좌표를시작값으로쓰되새장면upright/머리발여백을가정하지않고실제확인. nativecontrol60/physics240·원duration상한을그대로유지한다.
3. [ ] 실제QA/별도검수: encoder2종료0/codec·fps·예상110index·109middle프레임·원control/physics시계/sceneclose/입력불변. recorded nativeq/target/body/candidate/wrong/force와해당원실행을비교하고부동소수/실제변이값을정직하게기록한다. 영상frame과60Hz끝점관계를명시하며t0나미촬영odd끝점이있는것처럼설명하지않는다. 전신은머리/발이보이고손영상에서관절방향을볼수있는지직접view_image로검사한다.

source/준비·기존결과/봉인수정0. root만GPU스케줄. parentcap실제자료와독립검수완료가실행전gate이며CPU최소준비는먼저가능하다. 실제결과가나쁘더라도비교영상그대로보고하며기본cap채택/자연스러움인증은별도다. 진단자료정리중단·제외유지.
