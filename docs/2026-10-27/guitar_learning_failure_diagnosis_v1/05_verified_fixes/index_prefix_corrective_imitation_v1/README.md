# 같은 추가 예산의 참고 자료 대조와 교정 label 보강

현재는 CPU 준비만 수행한다. 원 warmstart1882/recovery1912/actual14파일·실패collect·모델·raw는 보존하며 새로운 수집 명령은 없다. actual PASS를 고정한 뒤 원 starting checkpoint SHA162c617a…에서 두 조건을 시작한다. GPU fit/evaluate는 준비독립PASS와 root의 직렬인계 이후뿐이다.

`cpu_inputs/commands.json`은 조건별 fit/evaluate의4개 명령이다. CLI는 `probe.py --execute fit|evaluate --condition reference_only|corrective_mixed`, 출력은 `runs/{condition}_{fit|evaluate}/`다. 기존경로를 native/모델import보다 먼저 거부한다. root실행순서는 두fit 뒤 두evaluate이며 같은출발점·추가1000회/배치192·원std/.25cap/90쌍/guard/reward/codec/rate를 유지한다.

CPU labels.npz에는 원 native reference request와 저장NN관측의 **offline shadow reference request**, 원 NN실제requested/executed를 각각 다른 이름으로 저장한다. label_manifest는 원관측파일SHA·생성함수·원분석 근거를 구분한다. 원 reference_action으로 원1416요청4열 bit-exact를 요구한다. NN은reference로 위장하지 않으며 counterfactual을 실제실행/성공자료로 부르지 않는다. 일부양DIP교정은 원guard에 막힐 수 있어 label을임의0으로 바꾸지 않는다.

학습은 env0/1/2만, env3은 동일장면 heldout 관측 검사다. 원6구간119/71/6/26/7/125를 사용하고 각구간 두번16행 복원추출한다. reference_only는 ref16+ref16, corrective_mixed는 ref16+shadow16이다. 두자료의같은clock/phase/행수라같은seed7의1000×두16추출 난수소비가 같다. 이를CUDA 전체결정성/독립seed일반화로 확대하지 않는다.

원PrefixPolicy와 trainable/invariants·PPO save/load를 재사용하고 작은 추가fit루프만 둔다. finger_encoder/indexhead 외 state/critic/std/buffer는 출발모델과 exact, cost2개0이다. 공유encoder 때문에다른head출력exact는아니다. 원requires_grad를복원한새PPOoptimizer empty/updates0으로각조건최종checkpoint한개만 저장한다. 새 metadata/schema에condition·원1000+추가1000=2000회·원source설정과실제초기화·자료출처를 명시하며 originalarchitecture/environment identity는꾸며바꾸지않는다.

NN평가는원source gate/output/SCHEMA/descriptor의scoped연결과원fullstrictload를재사용한다. 작은Trainer.load검사는원load를그대로호출한뒤condition/procedure와고정경로를검증하며 finally복원한다. 잘못된condition/path/checkpoint/schema를거부한다. 원128cap/evaluator/4환경preobs·guard·9보상·모델RNG동결/NN첫tick/noN은그대로다. 이번CPU검사는actualGPUfit/NN성과나CUDA RNG를대신증명하지않으며100PPO·추가예산자동확장은구현하지않는다.
