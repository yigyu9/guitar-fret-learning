# 모방 초기화 실제 결과 분석 범위

소유는 이 analysis/뿐이다. producer/1882준비/기존source·모델·raw는 동결하며 GPU/native 실행은 root만 한다. 사전코드검수는 추가하지 않는다. CPU selfcheck와 완료guard 이후 실제분석·소스+수치 통합 독립검수1회로 마친다.

1. root의 collect→기본검산→fit→evaluate 전체 종료 통보와01/02/03_launcher 각각 completed/exit0를 먼저 확인한다. 그전 실제 결과파일은 생성하지 않는다. 각단계 report·입력후·source SHA·별칭/장면종료·native128×105/0.25/90쌍을 원증거로 대조한다.
2. 새 reference128과 NN-only128의 원9항/모든 실패·3음/384음 기회·all3/A release/music/release/AND를 각각 집계한다. 원 precheck reference 및 기존 fresh0000평가는 출처를 구분해 재사용하고 GPU반복하지 않는다. reference성공을 NN성과로 합치지 않는다.
3. collect/NN의 env0..3 제어전5관측·clock4·first/즉시실패라벨·pretarget·요청4열을 대조한다. reference label과 NN 요청/guard목표를 분리하고 NN자료가 fit에 들어가지 않았음을 검사한다. 상세힘/실제각/손목은 원env0 60Hz에 한정한다.
4. CPU model-only로 초기73원본 exact, fit 허용모듈 외 state/critics/std/buffer exact·cost2zero·PPOoptimizer empty/updates0·새metadata와 원environment/NNidentity·NNfreshFalse/fullstrict native보고를 확인한다. CUDA RNG나CPU fullnative load를 대신 증명하지 않는다.
5. offline6구간 RMS/최대/환경별누적 요청차와 env0 NNphase별 실제4각·목표·guard·힘·손목·wrong을 기존 precheck/learning 분석helper로 최소 재사용한다. 공유encoder의 비선택 head출력 불변이나 open-loop오차의 물리성공을 주장하지 않는다.

NN-only가 미달이면 닫힌 루프 재현 실패로 기록하며100PPO/예산확장/보상·제어 변경을 자동실행하지 않는다. 통과하더라도 deterministic재현과 원std의 stochasticPPO유지는 별개다. fixed/조건부3음/동일seed128환경이며 free/J33/전곡/자연성/모방없는RL 성과로 확대하지 않는다.
