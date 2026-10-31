# V2 native camera 실제 산출물 독립검수

2026-10-28 **PASS**. 검수자는 새 GPU/native 실행을 하지 않고 root가 생성한 영상·NPZ·원결과를 읽기전용으로 확인했다. actionable finding은 없다. 이 PASS는 사전에 정한 q/target/body_state/candidate 및128개 episode ledger의 exact gate에 한정한다.

- 준비 seal504개 pin과 독립 review 연결이 현재 바이트와 맞는다. 실제 report는 completed/closed=true,128attempts, failure/cleanup_errors/changed_inputs/unpinned sources 없음이다. inputs_after verified=true이고 NN/checkpoint/PPO/fit은0이다.
- `capture.json`·`video_verification.json`은 완료이며354controls·177frames다. raw capture의 physics_step4..1416, control_tick1..354, time=control_tick/60과 영상 frame_times=2,4,..354 control endpoints가 정확히 맞는다. reset 이후 프레임을 섞지 않았다.
- 실제 replay q/target/body_state/candidate는 원 V2 deterministic trace와 exact이고128개 episode ledger 전체 및 acceptance도 exact다. trace metadata 역시 같다. raw capture q/target/body/action/contact_force/time은 자체 replay trace와 exact다. env0 total reward 합과 episode 누적값의 차이는4.53e-7,9개 보상항 합의 최대차이는3.73e-9다.
- 원trace 총23키 중22키는 exact다. **`net_body_force_n`은112572성분 중59성분이 다르고 최대차7.6293945e-6N**다. 따라서 NPZ 전체 또는 모든 힘성분이 bitexact라고 주장하지 않는다. 이는 사전4필드/ledger exact gate의 위반이 아니며 관측한 차이를 그대로 보존했다.
- 독립 ffprobe decode/count 결과 두 MP4 모두H.264,1280×720,30/1fps,177read frames,5.900000초다. 두 영상의3.5초 native frame을 추출하여 전신이 화면 안에 있고 손 확대가 보이며 위아래가 바르게 표시됨을 확인했다. root의 별도4초 육안확인에만 의존하지 않았다.

이 영상은 원 V2 **noNN deterministic scripted reference**의 사전선택 env0 첫시도다. 훈련된 정책이나 checkpoint의 영상이 아니다. 원128환경 분모와 고정기타·검지3음 범위를 유지하며 자유기타·J33·67음 성과로 확대하지 않는다. 원자료·code·seal·완료 output을 검수자가 다시 쓰지 않았다. 상세 입력/출력 SHA와 ffprobe 결과는 `actual_review.json`에 있다.
