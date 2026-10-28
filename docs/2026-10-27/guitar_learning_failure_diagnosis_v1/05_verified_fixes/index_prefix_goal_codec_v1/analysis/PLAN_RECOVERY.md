# 원 fit 실패와 회복 평가의 출처 분리

원 `PLAN.md`와 `analyze.py`의 두 성공 단계 가정은 보존한다. root가 원 fit 종료1·평가 미실행을 통보했으므로 기존 actual main을 실행하거나 원 report를 정상 완료로 바꾸지 않는다. producer2023/source·실패 launcher·모델·원자료는 불변이다.

- 회복 담당자의 fit 산출물 감사와 중복하지 않는다. 회복 수용의 명시적 새 문서/독립검수 SHA를 참조하며 새 fit·추가1000회는 없다.
- 새 완료 guard는 원 `02_launcher.json`의 completed=False/종료1/fit child1·evaluate 없음과 새 회복 evaluate 종료0을 별도로 검증한다. 회복 담당자가 확정한 출력·metadata·계약 인터페이스를 사용한다.
- 원 실패·수용 근거·평가 성공을 결과에서 별도 표기한다. 기존 두 성공 단계 guard를 무력화하거나 원 report에 completed=True를 덧씌우지 않는다.
- 실제 회복 평가 종료 통보 전 모델/실행 raw 읽기·결과 생성0. 이후에는 기존 범위의128원장·384음·9항, genuine GoalPolicy/goal 출력·물리 요청·guard·env0 기하/손목/힘을 최소 재사용해 검산한다.
- 회복 감사의 모델/1000loss/metadata 검산 결과는 출처를 명시해 재사용한다. 새 평가 자체에서 원 identity/모델 불변·NN-only를 확인하고 reference 성공을 NN에 상속하지 않는다.

현재는 계획/완료 guard 준비만 한다. 새 학습·보상/범위/문턱·GPU/native 실행은 하지 않는다. 회복 평가 후 source+actual 통합 독립 검수1회로 마무리한다.
