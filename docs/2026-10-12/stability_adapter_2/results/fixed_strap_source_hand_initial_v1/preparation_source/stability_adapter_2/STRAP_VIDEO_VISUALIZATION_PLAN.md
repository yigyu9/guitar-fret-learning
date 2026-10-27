# 실제 스트랩 경로를 결과 영상에 표시

사용자 요청: 이후 Isaac Gym 결과 동영상에 스트랩도 함께 표현한다. 현재 수동 스트랩은 기타 버튼→몸통/어깨 guide11개→다른 기타 버튼의13지점/12구간과 tension-only법칙이며, camera에보이는mesh는없다. 기존 Lines API는viewer만표시되고camera sensor영상에는안보인다고설치된Gymgraphics매뉴얼에명시돼있다.

새 녹화 helper는 매프레임 실제 env.route()의world지점을조회해 camera view/projection으로project하고 nativeRGBA에주황경로를표시한다. Native depth를이용해보이는구간은실선,가려진구간은옅은점선으로표시하고범례를둔다. 숨겨진경로를표면접촉으로오해하지않도록구별한다. LA는고정절대길이를표시한다. 질량/천mesh/처짐을새로모델링하는변경은아니다.

1. frozen gym_trial_recording/camera/기존runner/영상은수정하지않고새 StrapTrialRecording helper와별도runner를작성한다. native rawPNG와route/camera행렬/표시PNG를모두보존한다. humanoid/기타상태·목표·gain·strap force법칙에대한write는추가하지않는다.
2. 직전기존목표근접진단과같은입력으로한actual5초/1200step/151frame·두카메라를기록한다. 기존5배열(states/trace/tasks/contacts/controls)exact일치는관측으로보고하며성공gate로삼지않는다. root하체/물리불변성·raw/표시영상coverage·route와trace일치/투영방향·실제PNG를검사한다.
3. docs새strap_video_v1에raw/표시PNG·영상/로그/초기값·한국어설명·변경파일 실제줄·원본보존검증을저장한다. 이후새trial/feedback runner의기본녹화에새helper를사용하도록 main workflow에기록한다. 과거재현runner는그대로보존한다.

- [ ] 실제route→카메라투영/깊이가림 표시 구현·수치/문법 검사
- [ ] 동일입력actual5초/원자료·녹화·그림 검증
- [ ] 이후녹화 기본규칙·설명·보존/검수 상태

사용자의 자율진행 지침에 따라 별도승인질문없이진행한다. 신규 actor/충돌shape/힘/pose overwrite 없이 영상표시만변경한다. source기하/실제카메라/영상overlay를분명히구별한다.
