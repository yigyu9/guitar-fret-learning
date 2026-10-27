# 현재 import 관절 구조의 단일 export 진단

목적은 현재 조건의 constructor에서 관절 graph/type/frame/명시 limit을 추가 관찰하는 것이다. export가 compiled PhysX axisMotion이나 유한 step 잔차 원인을 보존한다는 계약은 없다. 결과에 없는 정보를 추정하지 않는다.

- [ ] 원 Scene13/원 baseline11 설정으로 한 번 생성하고 asset/actor index domain을 별도 보존한다.
- [ ] physics export 옵션의 live 지원/readback과 asset/sim USD 원파일·반환값을 저장한다.
- [ ] 초기 q/dq/body 상태·DOF/강체 속성 불변, simulate/fetch 0, cleanup 결과를 확인한다.
- [ ] 새 source/CPU/독립 검수/Root ACK 및 사전 SHA 대조 후에만 실행한다.
- [ ] authored joint 자료가 존재하면 원값을 읽고, 없거나 불충분하면 mapping/axisMotion/cause를 미확인으로 기록한다.

Root만 새 `diagnose_imported_joint_export_v1` 코드·출력을 소유한다. 현재 실제 동작 실험과 기존 소비 파일은 수정하지 않는다. constructor 진단은 동적 성공 횟수에 더하지 않는다. 작은 예산 통과·zero8 실제 운동·원 EPS0 실패·원인 미확정·최종 미채택을 그대로 보존한다. 가동8축 추가, 제어 강도 변경, 적분 step 추가, 기타 보조 힘은 이 진단 범위가 아니다.

선행 근거는 `limit_coordinate_next_probe_v1/SUMMARY_v1.md`와 기존 topology probe2다. 내보낸 자료의 물리 엔진 충실도가 입증되지 않으면 같은 getter/export를 반복하지 않고 미확인 상태로 닫는다. 기존 세션에서 승인된 자율 진단 범위에서 준비하며 최종 실행은 구체 코드·검수 결과에 대한 Root ACK 뒤 진행한다.
