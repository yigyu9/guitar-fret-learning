# 참고 동작으로 초기화한 NN의 세 음 재현 진단

현재는 CPU 준비 단계다. 기존 source·producer·모델·원자료는 수정하지 않으며 실제 수집/GPU fit/NN 평가 실행은 root가 독립 준비 검수 뒤 직렬로 한다. 원 고정 기타/128환경/354control/240Hz·0.25Nm native105 readback·90쌍·손목v3·현재목표 DIP guard·9보상·관측·PrefixPolicy/PPO 계약을 재사용한다. 접촉 기억 guard와 보상 변경을 섞지 않는다.

`probe.py --dry-plan`이 다음 세 명령을 출력한다. 출력은 `runs/collect`, `runs/fit`, `runs/evaluate`로 각각 새로 만들며 기존 경로와 symlink는 import/실행 전에 거부한다.

1. `--execute collect`: 원 noNN reference128을 단 한 번 수행한다. env0..3의 제어 전 원5관측과 요청 선택4열, start/postclock·first/failure·현재목표·6phase·guard 전후DIP목표를 `observations4.npz`에 저장한다. label은 요청 행동이며 guard가 바꾼 목표가 아니다. 원128×3음/9보상/음시계/해제 원장·env0기존trace·128 guard sidecar를 보존한다. 이 reference의 music/release/AND가 통과하지 않으면 fit을 거부한다.
2. `--execute fit`: native 장면 없이 GPU에서 별도로 수행한다. 원 seed7 fresh73 exact를 확인하고 원 trainer의 full strict load를 따른다. env0/1/2만 학습하고 env3은 같은 장면의 미사용 관측 검사로 둔다. 원 요청 endpoint 기준 [ramp2s,Aend,Aend+.10,Bpress−.12,Bpress]로 나눈6구간은 각119/71/6/26/7/125control이며 각32복원추출·배치192, Adam3e−4/1000회/gradnorm.5를 고정한다. 원 `tanh(mean)` 선택4열 MSE만 사용하고 atanh/label clipping/성능별 탐색은 없다.
3. `--execute evaluate`: 새 `runs/fit/initial.pt`를 원 runner strict loader와 원128 evaluator로 읽는다. NN은 첫 tick부터 선택4를 제어하고 reference/N 호출을 거부한다. 원 NN constructor는 fresh=False이므로 fitted 값을 재초기화하지 않는다. 원 acceptance로 음악·A native release·AND를 나누어 보고한다. offline 오차나 reference 성공을 NN 성공으로 대신하지 않는다.

NN-only에서도 같은env0..3의5관측·시계·요청4열·precontrol 선택4 target을 `observations4.npz`에 유한 저장한다. reference label은 `requested_reference_action`, NN 요청은 `requested_NN_action`이고 `source_control` 0/1을 구분한다. fit은 오직 collect 폴더의 reference0만 받아 NN 관측이나 NN 요청이 섞이면 거부한다. 평가 관측 저장에 oracle/reference 계산을 추가하지 않는다.

학습하는 파라미터는 공유 `finger_encoder`와 `finger_heads.index`뿐이다. 다른 head/support·모든 critic·std/buffer 값은 exact로 보존하고 cost2개0을 확인한다. 공유 encoder 때문에 비선택 head 출력까지 exact라는 뜻은 아니다. 실제 비선택 손가락 B/엄지/팔 안내는 원 제어다. 별도 Adam 상태를 checkpoint에 이어 넣지 않고 원 requires_grad 구조를 복원한 뒤 새 PPO optimizer empty/updates0으로 저장한다.100PPO 유지는 이번 코드 범위 밖이다.

새 metadata schema는 `diagnostic.index_prefix_imitation_initialization.v1`이다. 환경/NN architecture identity는 원본과 같고, metadata만 새 자료/절차/초기화를 명시한다. `metadata.settings`의 원 fresh 설명문은 source 설정으로 한정하여 `source_settings_initialization`, `settings_scope`, `actual_initialization`을 기록한다. 원 exact 설정 검사를 우회하거나 새 architecture를 꾸며내지 않는다. 원 metadata runner와 새 runner는 상대 schema를 거부하며 최종 모델 save/load는 원 PPO를 그대로 사용한다.

보상감사 PASS 원문 SHA는 고정한다. 그 검수의 root README/status/masterplan3개만 명시한 정확 allowlist로 당시 문서검수 기록에 한정하고 실행 pin에서 제외한다. 감사4파일·19실제입력·나머지 evidence는 모두 그대로 검증한다. 진행 문서 변경을 허용하기 위한 이 구분은 source/실제 증거 제외나 검증 완화가 아니다.

`--self-test`와 `--prepare`는 CUDA를 숨긴 CPU에서만 실행한다. 합성 구간·시계·첫시도/실패 라벨·label/guard 구분·초기73 exact·허용1step 변화/나머지 불변·empty PPO/strict metadata·오류별칭/기존출력 보호를 검사한다. CPU 검사는 실제128 수집/1000step GPU fit·CUDA RNG·NN 물리성공을 입증하지 않는다. 상세 물리 힘은 원 env0 60Hz뿐이며 body resultant는 접촉쌍 압력이나 피부전체 분리 인증이 아니다. 동일seed128환경/조건부3음이며 독립seed·free/J33/전곡·자연성·RL만의 학습 성공으로 확대하지 않는다.
