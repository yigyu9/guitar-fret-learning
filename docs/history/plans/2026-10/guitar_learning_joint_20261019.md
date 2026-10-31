# 최신 손별 정책의 공동 실행·학습

요청: 최신 BC 모델을 포함한 joint 모드의 모델 초기화·양손 환경·통합 판정·고정 정책 검증·공동 PPO 연결을 구현한다.

기존 손별 소스·모델·검증·실패 기록은 수정하지 않는다. 새 코드는 guitar_learning/joint, 검사는 guitar_learning/tests에 둔다. Root 고정/하체 유한 제어/105·97·8/자유 기타·중력ON·스트랩OFF/39행동/원관절범위·gain·240Hz 물리·60Hz 정책·native0/policy7초를 유지한다.

공동 관측은 기존 손별563상태를 각각 보존한 두 시점과 공동 판정 이력6개를 연결한1132차원이다. 각 Actor는 자기563+공동6=569차원만 받는다. 기존563 Actor의 새6열은0으로 초기화해 이전 관측에서 출력이 보존되는지 확인한다. 공동 Critic은1132상태를 받으며 새로 시작한다. 출력33+6을 단순 연결하고 별도 출력 합성망은 만들지 않는다.

한 물리 환경에서 양손 Skill/Timing/QualityLedger를 동일240Hz 표본으로 갱신한다. 손별 품질과 타현 순간의 clean 압현을 결합한 공동 판정, 엄격50/100ms 원 MusicLedger, 물리 안전을 각각 기록한다. 음악 성공이 아직 없어도 안전한 전체 preflight가 완료되면 협응 PPO를 시작할 수 있다. 초기부터 joint 성공을 요구해 학습을 막지는 않는다. 새 성공은 손별 결과에서 상속하지 않는다.

- [x] 양손 관측·동일 표본 ledger·공동 보상/판정 구현 및 CPU 검증.
- [x] 두 BC/원4회 평가 증거의 엄격한 이전·569 Actor/1132 Critic·동시 추론과 strict resume 검증.
- [x] 고정 정책 평가·자원보호·joint PPO·로그·실행 설정 연결.
- [x] 별도 검수 후 실제 동일 환경 고정 양손 실행과 짧은 PPO 업데이트 확인.
- [x] 결과·한계·실행법·원 입력 보존 감사를 문서화.

소유권: 환경/판정 담당자는 joint/environment.py·metrics.py 및 해당 검사, 모델 담당자는 joint/policy.py·transfer.py·settings.py 및 해당 검사, root는 joint/spec.py·train.py·evaluate.py·worker.py·문서·실제 실행을 맡는다. 다른 작업자의 변경을 되돌리지 않는다. 기존 모델 성공과 공동 성공/실행 구현의 완료는 구분한다.

실제 검증1차: session_factory가 persistent reset 계약을 만족하지 않아 첫 reset에서중단. 실패원자료 fixed_experts_evaluation_v1 보존. evaluate/worker를 PersistentHeadlessPreparedSession으로 수정하고 이전본은 archive/20261019_before_joint_persistent_session_fix에 보관. 음악·물리성공실행으로세지않는다.

수정본 CPU34검사통과. 실제 fixed_experts_evaluation_v2 1회7초안전완주, LH1/RH0/joint0. ppo_smoke_v1 2환경840전이/1update완료, 2회안전완주/LH2/RH0/joint0, persistent감사통과. 최종 checkpoint native strict평가진행중.

최종: ppo_evaluation_v1 strictload 1회7초안전완주, LH1/RH0/joint0. 신규source20개/과거169·6·15·11개/실제실행1702·1740개등 최종SHA감사변경0. 결과README·재현설정·실패/소스보관완료. 현재장기joint학습은시작하지않음.
