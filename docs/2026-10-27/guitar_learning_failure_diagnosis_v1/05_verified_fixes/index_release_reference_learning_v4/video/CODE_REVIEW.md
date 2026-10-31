# V4 영상 코드 예비 검수

**요약 판정: 문제없음 — 코드 검수 PASS.** 미해결 Critical / Warning / Suggestion 없음. 선택 checkpoint·평가자료의 최종 봉인이나 native 실행 승인은 아니다.

실제 rl38 Python3.8.20 stdlib CPU 검사를 독립 재실행했다. 기존 fit/deterministic 한쌍은 읽기 전용 preflight만 통과시키고 잘못된 checkpoint 거부를 확인했다. Torch·NumPy·Isaac·checkpoint 로딩이나 prepare/seal 쓰기는 없었다. 원 learn.evaluate/NN선택축 금지문맥을 재사용하며 preflight와 source gate가 native import보다 앞에 있다.

원 물리 step 다음·collector reset 전에 capture하고,4물리스텝/제어 검사를 재사용한다. pipe 실패 뒤에도 부분 행에9보상을 보존하고 카메라 생성 실패 시 sceneclose·acquire_gym 복구를 확인했다. 추가 mocked execute에서 평가 원예외와 영상report 쓰기 실패가 함께 발생해도 원예외 유지 및 GoalPool 별칭 복구를 확인했다.

특정 평가의128원장과 q/target/body/candidate·raw/decoded NN목표를 exact 대조하고 합력 차이는 따로 보고한다. 원 env0 첫시도354제어·177프레임·1280×720·30fps,기존 upright 전신카메라 좌표를 사용하며 픽셀 뒤집기는 없다. 이는 코드상 요구이며 실제 결과 증명이 아니다.

현재 선택 checkpoint는 null·execution_ready=false로 유지했다. 선택 완료 뒤 별도입력 봉인·실행 검수와 실제 영상의 메타데이터/첫끝프레임·손/전신 구도 확인이 필요하다. 이검수는 진행 중 PPO나 선택 전 checkpoint를 변경하지 않았다.
