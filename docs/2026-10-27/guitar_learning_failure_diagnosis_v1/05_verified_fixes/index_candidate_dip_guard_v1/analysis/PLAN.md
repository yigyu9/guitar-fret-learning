# 두 조건 실제 분석

현재는 분석 준비 단계다. root의 실제 두 child 종료 통보와 `01_launcher.json`의 completed/returncode/children 두 조건·argv·returncode를 확인한 뒤에만 원자료를 읽고 결과를 생성한다. GPU/native 실행과 기존 준비·입력·원자료 변경은 하지 않는다.

- [ ] 전체 입력 SHA, 두 scene의 원 strict B300/fresh=False·128 cap/readback·90 collision pairs·설정/시계/종료·alias 복원과 NN/RNG/updates 불변을 확인한다.
- [ ] 원 evaluator의 전체 2×128 첫 시도 원장을 실패 포함하여 집계하고 원 9항 보상을 공개한다. 완료 뒤 retry는 제외하며 실패 endpoint는 포함한다. 새 passthrough를 기존 B300의 128 원장 및 env0 trace와 비교하고 모든 차이를 보존한다.
- [ ] 전128 `dip_control60.npz`의 first-attempt mask/clock과 candidate·wrong·reset·failure·finite로 eligibility를 재계산한다. guard는 유효 candidate & ~wrong이고 raw DIP>old인 경우 final=old, 그 외 final=raw여야 한다. 음의 증분과 다른104열·메모리/scene/관측의 저장 검증잔차를 확인한다. 실제 로그 없이 무개입/개입 효과를 가정하지 않는다.
- [ ] 개입 횟수·지속시간·gate 상실 뒤 원제어 복귀와 negative/opening 통과를 구분한다. 개입이 없거나 negative 명령이 관측되지 않으면 그 한계를 명시한다.
- [ ] 기존 검수된 trace/arm helper를 재사용하여 env0의 음전/음중/음후 선택4 actual/target, DIP/PIP 추종, 손목, 움직임, 세 마디 몸체합력을 비교한다. 힘은 60Hz env0 표본이며 쌍별 압력이나 나머지127·240Hz 최대값으로 확대하지 않는다.
- [ ] 작은 표/그림과 한국어 RESULTS·verification/input SHA를 저장한 뒤 기존 reviewer에게 코드와 실제 수치의 통합 독립 검수를 요청한다.

이는 동일 B300 모델을 읽는 closed-loop 실행개입이다. 관측과 이후 NN 행동도 달라질 수 있으며 fixed-tape 인과분해, 원 정책의 무개입 성과, 자연스러움 또는 학습 개선을 인증하지 않는다. 억제 이전에 존재하는 target−actual 차이는 남고 actual 관절을 고정하지 않는다. old 중지 normal-projection 시험과 같은 조건으로 해석하지 않는다.
