# 낮은 구동 상한에서 학습 전 기준 대조와 네 손가락 회귀

고정 목표 명령의 검지112 새4/4·중지114 기존4/4를 확인한 조건에서, 실제 손가락 명령의 기여를 구분한다. 약지·소지는 손목v3/낮은상한으로 아직 재검사하지 않았으므로 네 손가락 학습으로 일반화하지 않는다. NN/기존checkpoint/새보상 없이 동일 원음·실패·범위를 유지하는 유한 진단이다.

1. [ ] CPU최소구현: 원ShortPool/runner._evaluate·make_settings/read_reference·compact_episode·원기하/보상/종료를 재사용한다. 검지row1·중지row8 zero/random 각4시도, 약지row16·소지row23 reference/zero/random 각4시도, 총10새scene/40첫시도다. reference검지112/중지114는검수된원4시도를재사용한다. 같은seed7의4환경이며4seed가 아니다.
2. [ ] 제어정의: zero는선택4행동0(팔안내/비선택B/엄지035는유지), random은선택4만mean0·std0.1711710544767014독립Gaussian→tanh의사전seed7명령이다. 새로운정책성능/기존untrainedNN과exact로부르지않는다. reference는기존_evaluate의ramp/trajectory_actions와원ring/pinkyreference를그대로쓴다. 전경우private16effort0.25/나머지89축·thumb5·PD·90충돌·범위·4rad/s·wristv3·음시계불변이다.
3. [ ] 별도CPU검수: 원cap.effort_loader/verify_native4를재사용해105속성/private사본/loader복원/controllercap동일/생성오류cleanup을검사한다. 새입력전후SHA/strict source봉인·기존출력/symlink거부·원평가4분모/장면닫기/실제exit를지킨다. native전gate는stdlib만사용하고실제freshprocess로Torch/NumPy/Isaac미import회귀검사한다. 원source/archive/기존raw/봉인은변경하지않는다.
4. [ ] 검지freshv2 actual독립PASS·입력불변후최종준비봉인/별도검수, root만GPU10scene직렬실행한다. 새정책/학습/소스변경을끼워넣지않는다. 전60Hz끝점/각env첫시도실패포함원장과env0상세q/body/force/wrist기록,scope는고정기타의고정/0/무작위명령대조다.
5. [ ] 실제분석/독립검수: 네손가락의reference/zero/random 원판정·전체분모·원load/position/facing/positive/candidate/wrong·실제각/하중/손목을대조한다. 팔만으로음이달성되는finger는손가락학습증거로세지않는다. 하중/자세와단음달성은별도다. 통과가능성/무명령대조를확인한finger부터짧은학습·재현/해제·음전환을검사하며자유기타/전곡성과는미확인으로유지한다.

최소코드로기존함수를재사용하고일반화프레임워크나cap/gain/음목표범위탐색을추가하지않는다. 자료정리중지·진단/원기준결과제외는유지한다. root가GPU스케줄을전담한다.
