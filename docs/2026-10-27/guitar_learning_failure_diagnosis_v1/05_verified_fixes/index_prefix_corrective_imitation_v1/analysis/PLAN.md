# 동일 추가 예산의 자료 보강 대조 분석

root가 실행하는 두 fit와 두 NN 평가의 전체 종료 뒤에만 결과를 생성한다. 분석은 CPU 읽기 전용이며 부모 producer, 원 자료, 모델, 준비 봉인을 바꾸지 않는다.

- [x] 완료 guard/합성 자가검증과 기존 분석 helper 연결 준비.
- [ ] launcher 네 child의 원 argv/종료0, 조건별 fit/evaluate 완료, 입력·장면·엄격 모델 읽기 증거 검산.
- [ ] 같은 출발 모델/추가1000×192/6구간, typed reference·NN shadow 출처, 허용 파라미터·critic/std·빈 PPO0·새 조건 metadata 확인.
- [ ] 두 새 NN 조건 각각128시도/384음의 달성·clean·wrong·실패·A 해제와 음악/해제/AND를 별도 비교. 기존 reference와 warmstart NN 결과는 비교 출처로만 제시.
- [ ] 원 9항, 128환경 guard, env0의 60Hz 기하/wrong·목표/실제 각·손목·body 순힘 및 4환경 제어 전 관측/시계/요청 정합을 기존 helper로 재검산.
- [ ] 간단한 표/그림·한국어 결론을 고정한 뒤 분석 source와 실제 수치의 통합 독립 검수 한 번.

`--self-check`는 합성 launcher만 사용한다. `--root-completed`는 실제 네 단계 완료 guard 뒤에 모델과 실행 자료를 읽는다. 실패 조건의 분모를 없애거나, reference 성공을 NN 성과로 상속하지 않는다. 두 조건이 모두 미달이어도 예산·문턱·학습을 자동 확장하지 않는다. 새 NN 자료는 이번 fit 자료로 재사용하지 않는다.

상세 힘/각도는 env0 60Hz, 제어 전 관측은 env0..3에 한정한다. body resultant는 접촉쌍 압력/피부 전체 분리가 아니며 offline 요청 오차와 실제 도달을 구분한다. 같은 장면 env3 검산은 독립 seed 일반화가 아니다. CPU 모델 비교는 native strict load/CUDA RNG 복원을 대체하지 않는다. 100PPO 유지·자유 기타/J33/전곡 적용은 이번 범위 밖이다.
