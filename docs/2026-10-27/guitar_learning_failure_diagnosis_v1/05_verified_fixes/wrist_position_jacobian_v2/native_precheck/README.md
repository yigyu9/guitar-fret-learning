# 검지 qpos-J v2 native precheck

상태: 활성 구현 동결 후 최종 CPU 검사를 통과했고 독립 prep 검수 중이다. 독립검수 PASS 전에는 실행할 수 없다. root가 GPU를 소유하며 여기서는 실행하지 않는다.

기존 `other_finger_precheck_v3`의 첫4 jobs/validate와 `run_short_comparison.run_child`를 재사용한다. 현재 source의 fresh bootstrap1update로 own initial.pt를 생성하고 그것만 reference/zero/random 각4첫시도에 사용한다. teacher/reference JSON은 기존 원본 경로/bytes다. .5°cap/2초ramp/3초onset,PD/범위/보상/원래clock은 그대로다. 원래 checkpoint/config strict load는 유지하며 old checkpoint를 평가에 넣지 않는다. 모델 초기73tensor 비교는 값 비교일 뿐 old full-load 성공이나 학습성과를 뜻하지 않는다.

`child.py`는 원래 runner/pool/판정/제어를 그대로 호출하며 입력pin과 평가 전후 모델/RNG/업데이트0을 새 `precheck_audit.json`에 기록한다. bootstrap1update는 모델·RNG 불변 검사의 대상이 아니다. random 평가 역시 원래 stochastic sampling이 RNG를 소비하므로 전후 hash를 그대로 기록하고 deterministic reference/zero에서만 RNG 불변을 요구한다. wrapper 자체는 추가 sampling을 하지 않는다. 모든평가4환경은 실패도 분모에 포함한다. 기존 report는 덮어쓰지 않고 before/after source·scene closed를 검사한다. 추가 native capture 없이 원래 env0/60Hz trace만 남기므로 다른환경240Hz 힘이나 접촉쌍 압력으로 확대하지 않는다.

출력은 native import 전에 existing directory/깨진symlink 모두 거부한다. base runner가 exclusive 생성한 출력의 dev/inode 소유권 안에서만 추가 보고서를 쓴다. 이전 실행/seal/raw는 변경하지 않는다. old 결과의 source핀은 현재변경으로 stale인 것이 정상이며 old.validate를 현재 source에서 재실행하지 않는다. 역사 비교는 기존검증과 `archive/20261027_before_wrist_position_jacobian_v2`의 명시mapping을 따른다.

현재 CPU 안전검사:

```bash
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/wrist_position_jacobian_v2/native_precheck/safety_check.py
```

`run_probe.py`는 기본 dry plan이다. 최종 준비/독립PASS 인계 후 root가 한GPU로 직렬 실행할 명령:

```bash
/home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/wrist_position_jacobian_v2/native_precheck/run_probe.py --execute
```

아직 native 결과는 없고 회귀/개선 결과를 주장하지 않는다.

최종 CPU: prepare.py --active-complete를 CUDA_VISIBLE_DEVICES 빈 값으로 실행하여18개 수학/short-learning 검사가 통과했다. 원래 settings와의 차이는 wrist_control뿐이며 teacher/reference는 현재 source에서도 유효하다. old checkpoint의 현재source strict검증은 거부됐고, seed7 CPU 초기73개 model tensor/key집합만 동일함을 확인했다. GPU 전체 trainer.load를 CPU에서 실행했다고 주장하지 않는다.

17KB compact fixture `guitar_learning/tests/fixtures/wrist_position_jacobian_native_v1.npz`는 수학 CPU 근거로 명시 pin했다(실행 시 helper가 fixture를 읽지는 않음). root의 별도 결과 비교 analysis는 실행 입력에 넣지 않는다. actual native fresh initial이 old73model과 다르면 비교 보고서를 먼저 보존하고 후속평가를 중단한다.
