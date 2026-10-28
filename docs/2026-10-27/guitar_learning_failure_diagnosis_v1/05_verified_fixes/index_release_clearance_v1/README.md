# 원 distal128 해제 여유 측정 준비

원128 noNN reference/noisy-reference와 물리·목표각·잡음·guard·원9항/음원장을 유지한다. 새 observer만 원 GoalPool `super().step()` 뒤, 원 imitation.after 앞에 붙인다. 모델 생성/load/fit/PPO는0이다. root만 native를 실행한다.

상세 저장은 env0..3 첫시도의 clock692..920 inclusive(58끝점/환경 최대232행)다. A 원press2.88초부터 B7 sharedpress3.832초를 처음 넘는60Hz 끝점까지다. precontrol first mask로 실패끝점도 보존하며 retry는 제외한다. 전체128 음악/해제 분모는 원 evaluator 그대로다.

`release_clearance4.npz`에는 원 index3/distal128의 point/normal(기타좌표), 원 pose7, 현재 strings/frets 입력, 표본별 finite-cell distance·signed plane height·cos·lateral·in-cell/position/facing/positive와 원 P128 aggregate/nearest·cached 원판정이 저장된다. `surface_static.npz`는 원 index3 local128 point/normal·원4x128 valid·plane, `surface_metadata.json`은 source triangle/barycentric provenance·변환·시간창을 기록한다. index3 body net force/loaded는 모든 표본이 공유하는 body 신호이며 표본별 힘이나 접촉쌍이 아니다. invalid reset snapshot은 명시하며 기하를 native로 해석하지 않는다.

원 손등제외 engineering patch의 이산128표본이며 전체 손가락/피부가 아니다. finite-cell3D 거리와 signed plane height·방향은 별개다. nearest 표본과 any same-sample witness는 다를 수 있다. 새 clearance pass/문턱을 만들지 않으며60Hz 저장으로240Hz 연속 이격·침투·현 압력·인과를 판정하지 않는다. 기존 body1/2 mask나 기하를 확장하지 않는다.

명령은 `cpu_inputs/commands.json`의 reference/noisy_reference 두 argv, 출력은 runs/<mode>이며 새 경로만 허용한다. 준비 독립PASS/최종봉인 후 root가 한 번씩 실행하고 원자료/준비를 동결한다. 분석은 별도 analysis/ 소유다. 현재 native성과/새 표본 측정은 미실행이다.
