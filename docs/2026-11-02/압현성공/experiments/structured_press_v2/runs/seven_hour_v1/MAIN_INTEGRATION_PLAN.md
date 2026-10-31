# 현행557상태 경로의 요청각 기댓값 추론 연결 검토

현재 production 기본은 유지한다. 이번 작업은 코드 읽기와 CPU 수치 확인만 수행했으며 production·연구 봉인 helper를 수정하지 않았다. 연구 결과는 선택 기능 후보의 근거이고, 기본 추론을 자동 교체할 근거로 사용하지 않는다.

## 현재 경로와 계약

`guitar_learning/AGENTS.md`와 README는 기본 J33·557상태·GPU 왼손·직접 위치 제어를 우선하고, 보관/봉인 연구 소스를 활성 코드에서 import하지 않도록 한다. 작은 보조 파일로 다시 분할하거나 파일 이동을 이유로 입력 SHA 검증을 완화하지 않는 것도 명시되어 있다. AGENTS 일부 과거 절의 resume.v3보다 현재 README와 실제 코드의 resume.v4가 현행이다.

- [policy.py](/home/ajou/yigyu/3/guitar_learning/training/policy.py:401)의 `FingerSkillPolicy`는557상태·24event·8priority를 요구한다. `forward`는39축 latent Gaussian의 mean/log_std와 두 critic을 반환한다. 활성33축만 표본화·logp·KL에 포함하며, 비활성 오른손6축은 그대로 둔다.
- 같은 파일549행의 `act(deterministic=True)`는 현재 `tanh(mean)`을 실행한다. 학습 수집은 원래 확률 정책의 act를 사용한다.
- [finger_skill_runner.py](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:445)의 `_DeterministicPolicy`가 공통 평가 wrapper다.456행의 `evaluate_checkpoint`는 metadata/입력 SHA를 먼저 검증하고, 실제 pool로 만든 trainer의 strict identity/load도 수행한 뒤506행에서 이 wrapper를 쓴다.
- [evaluate_finger_skill.py](/home/ajou/yigyu/3/guitar_learning/tool/evaluation/evaluate_finger_skill.py:7)는 평가 CLI다. 현재는 추론 규칙 옵션이 없다.
- [render_finger_skill.py](/home/ajou/yigyu/3/guitar_learning/tool/demonstration/render_finger_skill.py:83)는 함수 내부에서 동일 `_DeterministicPolicy`를 import하고141행에서 사용한다. 따라서 평가·영상을 같은 wrapper로 연결할 수 있다.
- 연구601상태는557상태에44열 구조화 상태와 별도 StructuredPolicy/active mask/계약을 붙였다. **수학 함수의39축 입출력은 재사용할 수 있지만601 checkpoint를 main557 모델로 그대로 읽을 수는 없다.** default `_policy`도557 정책만 구성하고 trainer는 schema/architecture/input/control/config 전체를 정확 비교한다.

## 가장 작은 활성 연결안: 기존3파일, 새 helper 파일 없음

새로운 정책 클래스·601호환 분기나 학습 옵션을 만들지 않고 기존 `_DeterministicPolicy`를 확장하는 것이 구현 파일 수가 가장 적다.

1. `training/finger_skill_runner.py`: `_DeterministicPolicy(policy, inference_rule='latent_mean', control_contract=...)`에 선택 규칙과 GH 수학을 함께 둔다. 새 수학 private 함수도 같은 기존 파일에 둔다. `evaluate_checkpoint(..., inference_rule='latent_mean')`가 이를 전달한다. 기본 분기는 원래 `policy.act(..., deterministic=True)`를 그대로 호출해 행동·latent·logp·난수 소비가 bitwise 동일해야 한다.
2. `tool/evaluation/evaluate_finger_skill.py`: `--inference-rule {latent_mean,requested_angle_mean}`만 전달한다. 연구용 다른 mode까지 늘리는 것은 이번 최소 통합 범위에서 제외한다.
3. `tool/demonstration/render_finger_skill.py`: render 함수와 CLI가 같은 옵션을 공통 wrapper에 전달한다. 별도의 렌더 전용 수학 구현을 만들지 않는다.

`FingerSkillPolicy.forward/act/evaluate/log_probability/analytic_kl`, PPO loss·표본화·optimizer, 환경·물리·초기 자세·음표 목표는 변경하지 않는다. 새 추론 규칙은 평가/영상 호출 옵션이며 training settings에 암묵적으로 넣거나 새 checkpoint를 저장하지 않는다. 본래 learned Gaussian의 μ/std와 critic은 그대로 읽는다.

이 안은 기존 공유 wrapper를 재사용하므로 새 Python 파일이나 `policy.py` 변경도 필요 없다. 수학이 커져 runner 가독성을 해치면 기존 `policy.py`에 순수 수학만 모으는4파일 안이 가능하지만, 첫 구현은3파일로 충분하다. tests는 새 분할 없이 기존 정책·평가·렌더 검사 파일에 추가할 수 있다. 연구 helper는 그대로 보존하며 production이 docs/봉인 helper를 import하는 방식은 사용하지 않는다.

##39축 실제 codec은 main에 이미 있다

[rollout.py](/home/ajou/yigyu/3/guitar_learning/training/rollout.py:37)의 실제 `pool.controller`와 `pool.contract['action']['target_contract']`에 다음이 있다.

-39축 `action_order`와105축 `joint_names`
- `reference105_rad`, `action_lower_rad`, `action_upper_rad`
- `action_codec`, smoothing/rate/position 계약

[gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:446)의 실제 식은 `reference + action * (upper-reference)` 또는 음수일 때 `reference + action * (reference-lower)`다. LH21 direct position에서는 control.v4/left_position_fingers.v1이 적용되며 이후 smoothing/4rad/s/native clamp 등 원래 제어 처리는 그대로다.

main에는 연구 catalog가 필요 없다. strict load로 검증한 저장 계약과 현재 `pool.controller.contract`의39축 이름·참조·bounds를 교차 확인해 p=upper−ref, n=ref−lower를 얻는다. 형태/축순서/유한성/양수 span/control.v4·position을 검사한다. 실제 q나 B 권고 자세를 reference로 대신 쓰지 않는다.

적용 수학은 Eδ=(p+n)/2·E[tanh Z]+(p−n)/2·E|tanh Z|, 이후 δ의 부호에 맞는 p/n으로 역정규화한다. GH64와 analytic E|Z| 보정을 사용한다. active33만 변환하고 inactive6은 원래 행동을 보존한다. 포화에서는 active 행동을±(1−dtype epsilon)로 제한→atanh latent→반환action=tanh(latent)로 같은 점을 보장하고, logp는 그 선택 latent의 **원래 정책 밀도**로 계산한다. 결정적 배포 규칙 자체의 확률 밀도라고 표현하지 않는다.

보고서에는 inference rule·수학 버전·node수·원래 Gaussian/weights/physics 보존·실행규칙 변경·포화 보정량을 적는다. 기댓값은 평활화/속도 제한 전 요청각의 기댓값이며 실제 물리 응답의 기댓값이 아니다.

## 중요한 수치 범위 제한

연구에서 검증한 σ≈.049787/.15, μ∈[−8,8]에서는64↔128 node의 E|tanh Z| 최대 차이가 약4.4e−9/1.20e−7이었다. 그러나 main `FingerSkillPolicy`는 log_std를[−5,2]로 clamp할 뿐 연구의 목표 sigma floor.1이나 초기.15 규칙을 쓰지 않는다. 허용 sigma는 약.00674~7.389다.

같은 수학을 CPU로 추가 확인한 결과 σ=1에서는 E|tanh|의64↔128 차이가5.63e−5, σ=e²에서는 E[tanh]0.02519/E|tanh|0.00986까지 커졌다. 이는 두 quadrature 결과의 차이이며 참값 오차 상한은 아니다. 따라서 GH64를 main의 모든 허용 checkpoint에 검증 없이 적용하면 안 된다.

첫 opt-in은 실제 저장 모델의 sigma 범위를 사전 확인하고 검증된 수치 범위만 허용하거나, 실제 입력에서 검증된 수렴 기준을 충족하는 계산으로 제한해야 한다. 범위를 벗어날 때 sigma를 몰래 줄이거나 원래 규칙으로 조용히 fallback하지 않는다. 지원 범위를 넓히려면 실제 μ/std와 worst-case에서 독립 적분/고차 quadrature/MC 수렴 검사를 추가한다. 기본 latent_mean에는 이 비용이나 조건이 적용되지 않는다.

## strict checkpoint의 실질적인 배포 제약

[finger_skill_runner.py](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:130)의 `_pins`는 archive를 제외한 활성 패키지의 Python 파일 전체를 저장한다. [portability.py](/home/ajou/yigyu/3/guitar_learning/portability.py:108)는 저장 settings digest/snapshot과 required 파일별 SHA를 확인한다. trainer.load는 별도로 실제 pool의 policy architecture/control/PPO identity를 확인한다.

따라서 기존 runner나 CLI/렌더 파일을 수정하면 과거 checkpoint는 아키텍처가 같아도 **원래 required source SHA가 달라져 main에서 strict 평가가 거부된다.** “추론 옵션만 추가했으니 옛 checkpoint를 그대로 읽는다”는 약속을 해서는 안 된다. metadata SHA를 바꾸거나 required pin을 빼거나 loader를 우회하지 않는다.

안전한 순서는 다음과 같다.

1. 현재 main 원문과 사용하려는 checkpoint를 원래 소스와 함께 보존한다. 연구601 저장본도 원래 봉인 runtime에 남긴다.
2. 통합은 새 버전/독립 사본에서 수행하고 변경 후 소스로 만든 **현행557** 검증 checkpoint를 사용한다. 처음에는0/짧은 native smoke로 구현을 확인하고 별도 짧은 학습으로 의미 있는 모델을 준비한다.601→557 암묵 전이는 하지 않는다.
3. 옛 main557 checkpoint를 먼저 진단해야 한다면, 그 원문 main을 바꾸지 않는 **외부 진단 wrapper**에서 strict 검증 이후 실행 규칙만 명시적으로 감싸는 별도 경로가 필요하다. 이는 새 외부 파일을 쓰는 연구 방식이며 “기존3파일에 바로 통합하면서 과거 pin도 유지”하는 것과 양립하지 않는다. 현재 보존 규칙 아래에서는 이 차이를 명확히 선택해야 한다.

기존 source pin 계약을 유지할 때 새 shared helper를 기존 파일에 통합하는 안과 과거 checkpoint의 무수정 strict 사용을 동시에 달성하는 shortcut은 없다.

## 필요한 검증 순서

- CPU: 기본 latent_mean의 bitwise 행동/latent/logp/critic/RNG 동등성, 실제 main39 codec 이름·bounds·reference, zeroσ/대칭span/비대칭μ0/64↔고차·독립적분·MC, 포화±10의 action=tanh(latent)/logp, inactive6 exact 보존. 실제 main checkpoint의 sigma 범위도 포함한다.
- strict: 잘못된 inference rule/낡은601 schema/변경 source SHA/codec 불일치/범위 밖 수치를 명확히 거부한다. 새 규칙이 학습 act/분포/Adam/RNG와 strict resume에 개입하지 않는지 확인한다.
- native557: 같은 checkpoint를 고정하고 latent/requested 각각32환경 최초 episode(실패 포함), 명시 reset과 실제 q/hold 대응, native lifecycle/source/state_dict/optimizer0을 확인한다. 연구601 수치로 main557 성공을 대신하지 않는다.
- musical: 단일 진단 목표 다음으로 현재 기본67음에서9항·할인reward/cost·오압현·연속clean·종료를 비교한다. 다른 손가락·프렛·줄에서도 확인하고 기존 최고보다 나쁜 모델을 대체하지 않는다.
- 영상: 같은 선택 규칙을 실제 renderer가 쓰는지, native 프레임·media SHA와 mode 태그가 맞는지 확인한다. 실제 Gaussian 평균 실행이라고 잘못 표시하지 않는다.
- 운영: 평가32환경/영상4환경에서 GPU 메모리·시간 비용을 측정한 뒤 더 큰 환경 수로 확장한다. GH 추가가 물리 실패 조건·clock·초기 자세를 바꾸지 않아야 한다. 변경 검수는 별도 reviewer가 수행한다.

현재 권장은 **production 기본을 유지한 채 새 버전의 명시적 opt-in만 준비**하는 것이다. 수치 범위·557 native·67음 검증과 독립 seed 확인이 끝나기 전에는 기본 교체나 “모든 손가락에 무손상” 주장을 하지 않는다.
