# 3음 prefix 정책 native 영상 준비

실제 새 `diagnostic.index_prefix_learning.v1` 설정과 `PrefixPolicy(fresh=False)`를 사용한다. producer의 staged wrist/current-goal DIP/128cap, 원 strict PPO loader·native 카메라/encoder/capture를 재사용한다. N/reference 주입은 없다. 원 단음 schema나 모델 정체성 검사를 우회하지 않는다.

학습8단계 완료 뒤 사전순위의 best250/latest300을 사용한다. 두 모델 모두 all3/release0인 실패 모델이며 이 영상은 후속 진단용이다. 독립 학습 actual review PASS와 검토된 selection을 stdlib gate로 확인한 뒤 `render.py --prepare`가 준비 입력을 만든다. `cpu_inputs/commands.json`은 `render: [argv250, argv300]`, `video_updates: [250,300]`이다. root만 준비검수 PASS·최종봉인 뒤 `--execute --update 250|300`을 직렬 실행하고 새 `runs/update_XXXXXX/`에 저장한다.

`cpu_verification_stage1.json`은 실제 모델이 없던 초기 단계의 역사적 기록이며 최종 현재 source 검증으로 사용하지 않는다. 최종 `cpu_verification_final.json`의 합성 capture 검사와 실제 모델 CPU 검사를 구분한다. 실제 checkpoint를 CPU에서 원 full loader로 읽으면 CUDA RNG topology 복원이 거부된다. `/tmp` 사본의 cuda_rng만 제외한 projection에서 원 identity/model/optimizer loader를 검산하며 원본 SHA는 불변이다. 실제 native renderer는 원본 checkpoint를 원 loader로 로드한다. CPU projection을 native CUDA RNG 검증으로 부르지 않는다.

metadata의 selected_target_count/source_indices/interval과 candidate/wrong/released/release_s trace를 처음부터3음으로 기록한다. env0 원 episode/3음 compact와 q/qd/target/body/합력/action/wrist를 보존하고 전128은 작은 DIP sidecar만 저장한다. evaluator callback의 검증을 수행했다고 주장하지 않는다. 정상354controls이면 각177frames 예상이나 실제 실패시각·프레임을 그대로 기록한다. frame n은 control endpoint2(n+1)이고 t0와 홀수 마지막끝점에는 frame이 없다.

손·전신은 기존 두 카메라를 재사용한다. 새 native pixels/codec/재현성·압력·자연성·해제 성공·전체128 영상은 CPU 준비로 검증하지 않는다. 실제 종료 뒤 원 평가와 수치/전체decode/대표PNG/직접시각·독립 QA를 별도로 수행한다.
