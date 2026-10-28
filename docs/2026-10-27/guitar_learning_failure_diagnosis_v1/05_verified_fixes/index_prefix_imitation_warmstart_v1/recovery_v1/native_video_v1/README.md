# 지도 초기화 모델의 native 영상 준비

원 recovery `runs/fit/initial.pt` 한 모델만 촬영한다. metadata는 실제 `diagnostic.index_prefix_imitation_initialization.recovery.v1`, 지도학습1000회/PPO 업데이트0이며 원 PrefixPolicy·환경 정체성을 유지한다. checkpoint를250/300/단음 모델처럼 다시 쓰지 않는다. original collect exit1의 회복 이력도 descriptor에 남긴다.

새 renderer는 원3음 render_native·카메라·capture·encoder·128cap/guard/stagedwrist·원 strict full loader를 그대로 호출한다. 작은 scope가 실제 새 header를 검사하고 새 출력 metadata만 지도 초기화 문구로 보강한다. NN은 첫 tick부터 선택4를 제어하고 reference/N을 호출하면 실행을 거부한다. evaluator fingerprint callback을 수행했다고 표기하지 않는다.

CPU `--self-test`는 실제 모델73tensor/원 identity/빈PPO optimizer/updates0·metadata 불변·잘못된 schema/초기화/updates 거부·예외/alias/reference 금지·새 출력 metadata를 확인한다. 원본 CPU full load가 CUDA RNG topology에서 거부되는 사실을 보존하고 /tmp 사본의 cuda_rng만 제외한 projection을 사용한다. 실제 native는 원본 파일을 원 loader로 로드한다. 기존 합성capture/BrokenPipe/픽셀 QA는 동결된 source SHA와 PASS 근거로 재사용한다.

회복 actual 분석 PASS 뒤에만 `--prepare`가 입력·commands·검증·pending seal을 만든다. 별도 준비검수 PASS와 최종 stdlib gate 뒤 root만 `--execute`를 직렬 실행해 새 `runs/initial/{hand,fullbody}.mp4`를 기록한다. 기존 출력/symlink를 거부하며 원 영상/원 결과를 덮지 않는다. 기존250/300 영상은 QA에서 출처를 표시해 재사용하며 다시 촬영하지 않는다.

이 영상은 조건부 고정기타/F4·유한 손목 안내하의 지도초기화 NN-only 첫시도다. 원90% 음악/해제 기준 미달 여부를 그대로 보존하며, RL-only/fullJ33·압력·자연성 해결로 확대하지 않는다. 실제 native/CUDA 복원·픽셀·코덱·수치 재현성은 CPU 준비와 별개로 후속 actual QA에서 검증한다.
