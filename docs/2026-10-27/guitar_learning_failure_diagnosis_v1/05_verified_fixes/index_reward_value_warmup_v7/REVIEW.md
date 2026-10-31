# V7 준비 코드 독립 검수: PASS

V7 구현 비참여 peer가 계획·새 runtime/learn/experiment/CPU 검사/supervisor와670개 입력 SHA를 검수했다. 이전660개 실제 분석 검수 근거도 정확한 SHA로 확인했다.50/100/300의 자료는 이전 근거 봉인을 위해 해시만 읽고, 실제 가치망 학습은 초기 V6 fit12개 buffer만 읽는다.

실제 rl38 Python3.8.20에서 CUDA_VISIBLE_DEVICES를 비워 CPU 검사를 독립 재실행했다. 원 CPU 보고서 쓰기만 메모리 캡처하여 덮어쓰지 않았으며 독립 결과는 원 보고서와 정확히 같았다.670개 입력 SHA도 전후 일치했다. 실제 NN fit·GPU·Isaac·native 장면·PPO는0이다. 실제 모델은 초기 tensor/출력/기울기 범위 검사에 사용했고1000회 전체 루틴은 작은 toy로 검사했다.

검수 중 두 문제를 찾아 PASS를 보류하고 수정을 확인했다. 첫째 gamma*bool의 float32 승격으로 실제 MC gamma가 달랐다. float64 carry부터 곱하도록 고친 뒤 별도 NumPy 할인 가중 reverse-cumsum과 최대1.55e−15 차이였다. 둘째 warmup 중간 실패의 실제 완료 step/loss가 누락될 수 있었다. 진행 callback으로 parent audit에 보존하며3step 주예외와 flag/gradient 복원 검사가 통과했다. 이전 원문은 preparation_attempt01에 보존되어 있다.

train 환경0..95와 동일장면 holdout96..127의 사전 분할,1000회×512 균등 train행 샘플, value_encoder/reward_critic만 갱신하는 임시 Adam을 확인했다. actor·표준편차·cost head·동일 backend Gaussian 표본·전역 RNG 경계를 보존한다. 별도 holdout 악화 toy에서는 MSE2.25→4.0일 때 accepted=False였고999회 예산도 거부했다. 실제 fit의 holdout 개선이 없으면 저장·PPO 전 중단한다.

V6와 fresh71개 tensor·RNG·출력 동일성, 양의 비용 gradient 학습 가능성, 빈 PPO optimizer, 미완료 warmup 거부를 확인했다. 실제 배우 지도1000회 루프는 원V4를 재사용하며 실행 시 원V6 fresh/fit71개 tensor 동일성을 검사한다. 이 실제1000회 재현은 아직 수행하지 않았다. 새V7 schema/계약/metadata와 기존 full strict GPU load를 유지하고 구형 checkpoint 호환을 추가하지 않았다.

pending gate가 수치/Isaac import 전 거부되는지 확인했다. supervisor도 실제 프로세스 없이 mock으로 단일 실행·중복 lock·허용 환경변수·분리 child·주예외 cleanup을 독립 검사했다. 별도 initial_comparison/compare.py는 읽기 전용 정적 검토만 했으며670개 core 입력에는 포함하지 않았다. 실제 초기 평가 후 원128음원장·9보상·env0 제어/접촉/NN goal 동일성과 force 차이를 별도 검수해야 한다.

미해결 준비 코드 지적은 없다. 상세 SHA와 검증 범위는 review.json에 기록했다. root는 검수 두 파일을 추가해 최종 봉인하고 stdlib gate를 확인할 수 있다. 이 PASS는 실제 NN warmup·holdout 개선·초기 native 수행 동일성·PPO 개선을 입증하지 않는다. 다른 seed·손가락·자유 기타/J33·원곡67음도 미완료다.
