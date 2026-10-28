# Goal codec fit/NN-only 분석 범위

선행 reference128의 실제 통합검수 PASS 뒤 root가 수행하는 fit1000회와 NN-only128 평가만 분석한다. 실행 전에는 성과나 결과 파일을 만들지 않는다. 원 source·producer·자료·모델은 바꾸지 않으며 GPU/native는 root만 한다.

- `02_launcher.json`의 fit/evaluate 두 child가 원 argv로 종료0인지 먼저 확인한다.
- 같은 원 fresh73 초기값, 학습 허용 finger_encoder/indexhead 외 critic/std/다른 상태 불변, cost2zero·새 PPO/update0와1000×192/6구간/env3 검산을 확인한다. 실제 모델은 새 layered contract의 genuine `GoalPolicy`로 읽으며 이전 PrefixPolicy identity로 우회하지 않는다.
- `raw_goal_normalized`의 목표 출력 오차, `decoded_goal_rad`, 변환된 `requested_NN_action` 물리 요청, 원 guard 뒤 `final_target_rad`를 분리한다. 정규화 목표 RMS와 증분 action RMS를 같은 단위로 비교하지 않는다.
- 새128시도/384음·실패·원9항과 각음/all3·A release·music/release/AND 원90% 기준을 유지한다. 선행 noNN reference 성공은 NN 성과에 상속하지 않는다.
- reference 분석의 기존 helper를 재사용해 native105/cap.25/90쌍·닫기·관련 입력, 4환경 precontrol 시계/목표·env0 60Hz 각/힘/손목/기하만 검산한다. reference/N 주입0과 NN/RNG frozen은 원 native 보고서 근거와 CPU 모델 재현 범위를 구분한다.
- 기존 최초 incremental1000회 결과는 별도 출처로 비교한다. 동일 수치 std가 같은 물리 탐색은 아니며 deterministic 초기화 검사만 해석한다.

최소 CPU 자가검증→root 전체 종료 guard→실제 계산→짧은 한국어 결과와 source/수치 통합 독립 검수1회 순서다. 과거 전체 수천 핀 재순회나 새 그림·예산/문턱 확장은 추가하지 않는다. NN 기준 미달이면100PPO를 시작하지 않는다.
