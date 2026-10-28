# 새 schema 3음 정책 native 영상 어댑터

현재 허용범위는 이 폴더의 최소3음 renderer·CPU 검증·영상 준비 봉인이다. producer/원 source·1602 준비·사전대조·학습·분석은 동결하고 다른 작업자의 precheck_analysis/learning_analysis를 변경하지 않는다. 학습8단계 actual 완료 뒤 원 사전순위의 best250/latest300을 사용한다. 두 모델 모두 all3/release0이며 성공 모델이 아니다. 독립 학습 actual PASS에 연결된 selection을 확인한 뒤에만 최종 prepare/영상 준비검수를 진행한다. GPU는 root만 직렬 실행한다.

원 `render_short_finger.py`의 단음 schema/selected_index/count1 metadata를 바꾸어 통과시키지 않는다. 작은 새 render 함수에서 새 `learning.SCHEMA`와 `PrefixPolicy(fresh=False)`를 처음부터 사용하고 원 `DecisionPPOTrainer.load`, `_validate_pins`, 카메라/encoder/`_EnvZeroCapture`/GraphicsGym/finish_video를 재사용한다. producer의 `execution_scope('evaluate')`+원128 cap scope와 같은 Pool/current-goal guard/staged wrist를 사용하며 reference N/target 주입은 없다. 정책 입력·행동은 첫tick부터 동일 deterministic mean 경로다.

저장 범위: env0 첫시도의 q/qd/target/body/합력/action·원 source clock·3음 candidate/wrong/released/release_s/거리·wrist 피드백 vector trace, 원 episode와3음 compact, 실제3음 source indices/target IDs/intervals/selected_target_count3·새 policy/control contract metadata. 전128은 producer의 작은 first-attempt DIP sidecar만 유지하고 전체몸체 시계열을 늘리지 않는다. renderer는 evaluator callback을 호출하지 않으므로 그 callback의 모델/RNG 검증을 수행했다고 표기하지 않는다.

카메라는 원 손/전신 두 개와 기존 short renderer의 head/feet framing만 재사용한다. 물리·rate·범위·cap·보상/실패·reset/step 횟수는 바꾸지 않는다. 정상354control이면 각177frame이 예상되지만 env0 실패로 더 짧아질 수 있으므로 실제 종료시각/프레임을 그대로 기록한다. frame n은 control endpoint2(n+1), t0와 홀수 마지막endpoint에는 영상frame이 없다.

합성 CPU 확인은 synthetic header/새schema 거부, 실제 원 capture+CPU pool의3음vector/원시계/frame mapping, BrokenPipe 뒤 보강된 부분raw/원오류 보존, 비env0 종료reset과 env0 first-attempt 종료만 확인한다. 기존 policy/init/128cap/strict 수학은 producer PASS SHA를 재사용한다. 픽셀/codec/native재현성·모델성과를 미리 통과라고 표시하지 않는다.

추가 CPU 검사는 실제250/300 checkpoint의 settings/source/identity/73tensor를 확인하고 단음·다른schema·guard를 거부한다. CPU에서 원본 load는 CUDA RNG topology 복원 지점에서 거부되는 것을 보존한다. 원본은 수정하지 않고 /tmp 사본의 cuda_rng만 None으로 한 CPU projection에서 원 full loader/model/optimizer를 검사한다. 이는 native CUDA RNG 복원 검증이 아니며 실제 renderer는 원본 trainer.load를 그대로 호출한다.

독립 actual 분석 PASS 뒤에만 model/선정review/입력 source를 고정하고 출력·symlink 거부/stdlib gate·독립 준비검수/최종seal을 완성한다. 기존 best 순위와 latest300을 보존하며 best=latest면1모델, 다르면2모델에만 같은128장면 env0 손/전신을 렌더한다. 실제 종료 뒤 원7평가/env0trace/sidecar와 비교하고 전체decode·대표PNG·직접시각/독립actualQA를 수행한다. 영상은 조건부3음F4 학습의 진단이며 자연스러움·해제·전체128영상·자유기타/J33 성공을 인증하지 않는다.

준비 순서와 검증:

- [x] 최소3음 renderer/원 capture 합성 검사 및 실제250/300 CPU identity/model 검사
- [x] 독립 학습 actual PASS 확인: review `59295b114d5fbc0f9992d5857ea71e3aa5601e96a46fbcbd60050ce7a0d5b2a6`, selection `7341023a20d315e86250cf3901766014a5b2385d9105fa9dc925c16ca02d4f59`
- `--prepare`는 selection/model/input SHA와 `commands.json`의 render argv2·video_updates `[250,300]`를 고정한다. 준비 산출물로 실행 완료를 확인한다.
- [ ] 별도 영상 준비검수 PASS, review2 SHA 추가·최종seal·fresh stdlib reviewed gate 후 root 인계

봉인 후 이 PLAN은 수정하지 않는다. 실행·actualQA 진행은 root status 또는 별도 qa/에 남긴다. 준비는 native pixels/codec/실제3음 정합 PASS가 아니며 실제 종료 뒤 별도 QA가 필요하다.
