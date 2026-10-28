# native 영상 observer 준비 독립 검수

요약 판정: **문제없음 / PASS**. 남은 Critical·Warning·Suggestion 없음.

원 repro.execute/cap.execute와 collector를 그대로 호출하며 NN·checkpoint·추가 reset/physics 경로가 없다. 원 _pins를 바꾸지 않고 새 seal 입력을 추가한다. 네 조건은20Nm/0.25Nm×index/middle의 새4환경 첫 시도이며 env0만 촬영한다. 실제 cap105 readback과 원 판정·전체4분모는 기존 경로에 남는다.

최종 CPU self-test를 재실행했다. 원 collector 반환·행동·4step 보존, 실제 _EnvZeroCapture의 첫3끝점/두 RGB stream/2번째끝점30Hz프레임, step binding 및 gym/camera/collect alias·시각색상 복원을 확인했다. 기존·깨진 symlink 출력과 pending seal은 native import 전에 거부된다.834개 핀과 공식 실제 분석 review/verification 연결을 확인했다.

검수 중 인코더 BrokenPipe 이후 마지막 행의 scripted/wrist 필드가 빠져 partial NPZ 저장이 실패하는 경로를 재현했다. 작성자가 보강 코드를 finally로 이동했다. 최종 실제 helper 회귀에서 원 BrokenPipeError를 유지하고2행 전체 필드 stack 및NPZ 저장·읽기(physics[4,8],q(2,105),candidate arm(2,12))가 통과한다. 해결된 finding이며 남은 문제는 없다.

실제 GPU·native scene·encoder 실행은 하지 않았고 runs는 없다. 픽셀 방향/머리·발 여백,8MP4의 실제 codec·프레임·종료, 원자료와의 궤적 차이는 실행 후 별도 QA 대상이다. 성과가 미달한 검지 조건을 성공으로 바꾸거나 힘을 압력·자연스러움으로 확대하지 않는다. 최종 검토 SHA와 입력 fingerprint는 [review.json](review.json)에 기록했다.
