# guard native 영상 준비

root 승인 범위: 기존 guard 평가와 동일한 B300 strict/fresh=False·128cap 장면에서 guard 조건만 손/전신 두 MP4로 기록한다. 기존 B300 원본 두 영상은 출처를 명시해 대조로 재사용한다. GPU는 root만 실행하고 기존 source/1420 준비핀/평가·분석·원자료를 변경하지 않는다.

1. 원 `B.execution_scope('render')`와 `B.base.launch('render')` 및 동결된 `guard.observer_scope`를 얇게 연결한다. output만 새 `native_video_v1/runs/guard/`로 바꾸고 pins는 새 입력의 superset을 전달한다. 원 renderer의 runtime ShortPool import가 같은 hook을 받도록 한다.
2. 원 evaluator/trainer callback은 렌더에서 호출되지 않는다. 이를 호출했다고 기록하지 않고, 원 renderer의 strict load·모델/체크포인트 불변·updates300·scene/encoder 종료검사를 사용한다. full128 scalar DIP sidecar는 원 필터와 같은 first-attempt mask/실패 endpoint/retry 제외 규칙으로 저장한다.
3. CPU 검사: 출력/symlink 조기거부, render phase/checkpoint/output 전달, runtime/runner/두 pins alias·B 태그 scope와 예외복원, 미호출 평가 callback 정직한 표기, 부분 sidecar 저장과 원오류 보존. 기존 필터 수학/strict128cap CPU 검수 SHA는 재사용한다.
4. 독립 준비검수 PASS 뒤 review2 SHA를 추가해 최종 봉인하고 fresh stdlib gate를 확인한다. 실제 pixels/codec/재현은 아직 미검증이며 root native 완료 통보 전 새 raw를 읽지 않는다.
5. 실제 QA는 별도 `qa/`: 원 guard 평가와 env0 221끝점 q/target/body/gate/action/wrist·전128 sidecar를 대조하고 차이를 보존한다. 새2MP4 30fps/110프레임씩 총220프레임 디코딩·8PNG 직접시각검사·기존 B300 두 영상 출처/비교이미지·손목/넥 가림과 전신 머리/발/정방향을 확인한다. native frame n은 control endpoint 2(n+1)에 해당하며 마지막 홀수 endpoint에는 영상frame이 없다.

영상은 frozen B300에 실행한 closed-loop DIP guard의 env0 첫시도다. 무개입 정책성과·새 학습·전체128 영상·해제 성공·자연스러움/압력 인증으로 확대하지 않는다. 기존 renderer의 policy_performance 필드는 원문으로 보존하고 별도 execution override에서 의미를 선언한다.
