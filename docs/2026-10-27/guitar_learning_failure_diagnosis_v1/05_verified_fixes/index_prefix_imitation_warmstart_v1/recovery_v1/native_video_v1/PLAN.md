# 회복된 지도 초기화 모델 영상 — CPU 준비

소유는 이 새폴더만이다. recovery producer1912·원집계/학습/평가·checkpoint·기존 영상과 다른 worker의 analysis를 수정하지 않는다. GPU는 root만 실행하며 실제 분석 PASS/준비검수/최종봉인 전에는 native 실행을 거부한다.

모델은 recovery runs/fit/initial.pt SHA162c617a28e548757bea8b0721c13c740d452fc430ae1601f01ed8411e2e480a 하나다. 원 metadata `diagnostic.index_prefix_imitation_initialization.recovery.v1`·supervised1000·원 PPO optimizer empty/updates0·원 PrefixPolicy/environment identity를 그대로 보존한다. 옛250/300/single schema로 payload를 바꾸지 않는다. 수집 exit1은 독립검수된 단일 후처리오류 회복 이력이며 성공수집 exit0으로 표기하지 않는다.

원3음 renderer의 render_native/capture/save_raw와 카메라/encoder/GraphicsGym/원 strict full loader/128cap를 재사용한다. 얇은 scope가 새 header를 검증하고 새 출력 metadata에만 초기화 provenance와 올바른 selection 설명을 추가한다. 원 원장/물리/목표/step/reset/guard는 그대로이며 reference/N 호출을 금지한다. fresh=False·선택4 첫tick NN·current-goal guard/stagedwrist/035/비선택B/전체범위/rate/9보상 유지. 원 evaluator fingerprint callback 사용을 주장하지 않는다.

CPU 검사: 새 header의 실제schema/PPO0/metadata 불변, 잘못된 schema/update/초기화 거부, 실제73tensor/identity·빈 PPO optimizer·원 strict CPU projection, alias/메타데이터/예외복원·원 합성capture/BrokenPipe/출력보호의 기존 PASS 재사용. 실제 CUDA RNG topology는 CPU에서 복원하지 않으며 원본 load의 해당 거부를 보존한다. /tmp에서 cuda_rng만 제외한 projection을 검사하고 실제 native는 원본 checkpoint를 원 loader로 로드한다.

- [x] 최소 adapter/CPU검사(Python3.8 AST·실제73tensor/identity/빈PPO0·새header 거부·alias/reference 금지·fresh stdlib 거부 통과)
- [x] recovery 실제분석 PASS 연결: review2c7445ce886db063a39d08e4fb88a0f4953af9e3a5df9dcebb616a6008c837c6, verification6c1ccddf9900f1fa7fc46034e4940bb6142ebbb9dfd951e7fe0ce6bbc9b47972
- prepare/독립 영상준비검수·최종seal/freshgate는 별도 산출물로 확인한다.
- [ ] root 직렬 native1scene/env0firstepisode 손·전신2MP4

기존250/300 영상은 나중 QA 비교에서 출처를 표시해 재사용하며 다시 렌더하지 않는다. 범위는 조건부 고정기타/F4·finite wrist·지도초기화의 NN-only 수행이다. RL-only/fullJ33/자연성/압력·원90%기준통과라고 부르지 않는다. native 종료 뒤 별도qa/에서 수치·전체decode/대표PNG·직접시각·통합독립검수를 수행한다. 준비 이후 PLAN 체크는 수정하지 않는다.
