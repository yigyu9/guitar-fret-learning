# 상체 공동 학습 구조 최종 독립 검수

## 요약 판정

**문제없음 — 구조 구현·CPU optimizer 검사·실제 native 추론의 설명과 원자료가 일치한다.** 739D 관측, 상체81 Actor와 scalar Critic, PPO/GAE 및 체크포인트 계약은 이번 범위에 맞다. 실제 기타 연주 학습과 공동 음악 성공은 아직 확인되지 않았다.

검수자는 소스·원 로그·저장 데이터를 읽고 CPU에서 산술·SHA를 대조했다. 추가 native 실행·정책 학습·신경망 추론을 하지 않았고 이 검수 파일만 작성했다. 최종 봉인·inventory는 root 소유다.

## Critical — 반드시 고칠 것

현재 범위의 실행을 막는 미해결 코드 오류는 발견하지 못했다. 앞선 관측 재무장 메모리 누락, rollout마다 reset하는 문제와 불완전한 의존 소스 계약은 CPU 소비 전에 정정됐다. 소비된 runner v1은 유지했고 native 실행은 체크포인트 자가참조를 제외하고 부분 음악 로그를 보존하는 v2를 사용했다.

## Warning — 실환경 학습 전에 해소할 것

- [joint_learning_observation_v1.py:117](/home/ajou/yigyu/3/stability_adapter_2/joint_learning_observation_v1.py:117), [run_joint_policy_v2.py:24](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:24): SO(3) 허용집합, 연속 유지/dropout ledger, fatal 일정 정산/할인, distal press pad, reward 측정/mask가 미인증이다. `--train`을 장면·출력 생성 전에 차단하는 현재 계약을 유지하고 실제 scalar reward·terminated/truncated 환경 API를 검증한 뒤 학습을 열어야 한다.
- [joint_learning_observation_v1.py:41](/home/ajou/yigyu/3/stability_adapter_2/joint_learning_observation_v1.py:41): 739D는 이번 버전의 관측 ABI다. 현재 기하 압현 셀·최고 sounding fret·보수적 crossing bracket이 실제 pad 접촉이나 음표 유지·해제 성공을 대신하지 않는다. ledger/보상 판정 상태를 추가하면 관측과 체크포인트 계약을 새 버전으로 갱신해야 한다.
- [joint_policy_v1.py:45](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py:45): anchor가 한계에 놓인 채널은 한쪽 행동 방향의 목표 변화가 0이다. manifest가 이 채널을 공개하므로 숨겨진 구현 오류는 아니다. 후속 학습에서 이 비대칭과 목표 rate 제한을 고려하고 표본 action을 실제 목표 변화로 오해하지 않아야 한다.
- [README.md:27](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/README.md:27): 평균·탐색 각각 공동 이벤트 정산 9건 중 성공 0건, crossing 0건이다. 평균 정책의 이전 preload 재현과 작은 탐색은 제어 경로 검증이며 음악 성능·지지 안정성 인증이 아니다. 실제 body 관절각 변화도 목표 ±5° 제한과 별도로 해석해야 한다.

## Suggestion — 선택

후속 reward 구현에서는 유지·해제·dropout·물리 실패의 경계를 실제 판정 코드 반례로 추가하고, 기존 22개 구조 검사와 분리해 보고하면 학습 준비 근거를 명확히 유지할 수 있다.

## 독립 대조

- **정책·PPO:** Actor/Critic은 별도 739→512(ELU)→256(ELU) 경로이며 출력은 mean81/value1이다. 관측 독립 log_std81, 저장 latent의 안정적 tanh 로그확률을 사용한다. 목표 rate 적용 후 결과로 likelihood를 역산하지 않는다. GAE는 terminated bootstrap0, truncated 실제 마지막 관측 bootstrap, 양쪽 경계 trace 차단이다. 같은 env의 미종료 rollout은 이어지고 load 후 수집 캐시는 초기화한다. RMS는 collection/PPO 중 고정된다.
- **체크포인트:** 기존 파일을 교체하지 않는 exclusive 저장, 설정·ABI 확인 후 복원, CPU model/RMS/Adam/RNG 저장 범위를 확인했다. 관측·분포·물리 의존 소스와 입력·자산 fingerprint를 포함하며 joint `.pt` 자체는 ABI source 목록에서 제외한다. 두 native ABI가 전체 값까지 동일하고 canonical digest도 각각 맞다. 새 episode 재개이며 물리 중간 상태 복원을 주장하지 않는다. 739/512/256/81 및 scalar Critic의 파라미터 수는 산술로 1,041,571개다.
- **CPU 검사:** 원 로그의 22개 `ok`와 `Ran 22 tests ... OK`, cpu_verification의 목록·로그 SHA가 일치한다. 실제 합성 Actor/Critic optimizer 갱신, 포화 likelihood, 종료/절단, checkpoint/덮어쓰기, 실제 detector wait_frames 0/7 및 두 번 collect의 진행 유지 반례를 확인했다. 이번 검수에서는 optimizer 검사를 재실행하지 않았다.
- **실제 실행:** 평균5초와 같은 ABI checkpoint 복원·탐색5초, 각각1200 physics/300 control/301 trace/151frame×2view다. 전체2400 physics/4영상, source Actor 호출0/native 학습0이다. 실행 manifest와 두 report의 완료·입력 불변·금지 API0이 일치한다. train 차단 원 로그는 미완료 gate 오류를 기록하며 blocked 출력 디렉터리가 없다.
- **600개 제어 재계산:** 모든739D 관측이 유한하고 latent→tanh 표본81→절대 anchor 요청→rate/native 범위 최종 목표가 저장 기록과 일치한다. 초기 mean0·그룹 std를 이용한 로그확률 산술 대조의 최대 차이는3.1e-5 이하다. 평균 행동은0, 탐색은81채널 전체에 표본이 있다. 요청 anchor 대비 RMS와 실제 관절 움직임은 별개다.
- **물리 수치:** 원 trace에서 평균 기타 최대46.306319mm/9.178642°, 탐색57.113690mm/9.959916°를 재계산했다. 실제 body 최대각 변화는 각각2.164068°/2.398120°다. 평균301행 trace는 이전 preload100_v2와 exact 일치하며 두 조건의 실제 초기 상태도 같다. 각1200개 음악 물리 표본의 원 release는0이고 저장 이벤트9건/성공0과 맞다.
- **그림·영상:** 구조도v4와 평균 정책 native 몽타주v2를 실제 열어 코드·관측 block·제어·학습 차단 설명과 대조했다. 몽타주는 전신/양손의0·2·5초, step0/480/1200 native 프레임이다. 두 실행의 전체151frame SHA와 MP44개 SHA가 metadata와 맞으며 영상5.033초와 물리5초를 구분한다. 후처리 metadata v1–v4의 전후 입력·현재 입력/출력 및 producer SHA가 모두 일치하고 이전 그림도 보존돼 있다.
- **보존:** pre-task nonmain764파일, legacy12607파일, 직전 phase inventory1225파일의 현재 SHA가 원 목록과 모두 일치한다. 소비 소스 v1 6개/v2 1개는 현재 원본·보존 사본·manifest가 같다. main4는 검증된 이전 bytes를 prefix로 그대로 유지한다. 이름 충돌로 초기 A README snapshot이 덮인 이력은 공개됐고, 복구한 prefix가 pre-task SHA와 byte-exact임을 독립 확인했다. 이를 당시 별도 snapshot이 보존됐다는 주장으로 확대하지 않는다.
- **native 입력·문서:** 두 실행 입력1106/1107개는 현재 파일 또는 검증된 main append 전 snapshot과 일치한다. native 수치 검증 입력28개 SHA가 맞다. 한국어 README·CHANGED_FILES 및 main4 추가 기록의 범위·수치를 읽어 대조했다. BLOCKS13행/검사 클래스15행 정정과 나머지 실제 정의 링크를 확인했다. 실환경 학습이 비활성이고 이번 결과가 음악 성공이 아니라는 한계가 문서·그림에 일관되게 표시된다.

근거: [설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/README.md:1) · [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/CHANGED_FILES.md:1) · [CPU 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/cpu_verification_v1.json:1) · [native 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/native_verification_v1.json:1) · [보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/preservation_audit_v1.json:1) · [실행 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/execution_manifest_v1.json:1).
