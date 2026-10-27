# PALM_RATE와 기존 승인된 1/2N 초기 스트랩 길이 조합

2026-10-07. 현재 초기 자세의 1/2N 길이는 LEFT_WRIST_STRAP_COMPARE.md에서 PI로
비교했지만, 승인된 PALM_RATE 제어와의 조합은 미측정이다. 기존 0–5N 탐색 범위의
개별 길이 비교이며 새로운 PD·제어권 변경이 아니다. 어깨 PD 제안은 확인 대기로 둔다.

| 초기 법칙 장력 표기 | 절대 rest length LA (m) |
|---|---:|
|0N 기준|1.1010801317960974|
|1N|1.1009134651294308|
|2N|1.1007467984627641|

LA=L0−T0/6000이며 initial velocity=0이다. Runtime LA는 고정되고 실제 장력은
기존 케이블 법칙으로 변한다. 일정한 기타 복원력이나 동적 스트랩 제어가 아니다.

- [x] 1. 기존 세 입력의 byte copy와 기존 초기 auditor를 사용한다. Full humanoid
  q/body·guitar p/q·PD·route·주요66·zero velocity·no steps·길이만 변경을 검증하고,
  source 음수 pair0·왼손 위쪽 반구·국소 넥 아래 조건을 검사한다.
- [ ] 2. 통과한1/2N만 기존 PALM_RATE 0.1초 runner로 각각 실행한다. 기존 0N의
  native_target_readback_v1/native 기록을 기준으로 재사용한다. 새 어깨 접촉이 없는
  조건만 원래0.5초 runner로 연장한다. 최대4새 rollout이며 1초를 추가하지 않는다.
- [ ] 3. LA만 다른 초기 상태·PD/제어·정확한 sample/update coverage, 같은 길이의
  short prefix와 source SHA를 검증한다. 기타 초기 p/q·손 이탈·실제 scalar 한계·접촉·
  장력을 비교하고 Luna 이미지/설명·변경 파일 실제 줄 번호와 독립 검수를 남긴다.

0.5초 기준은 dof_force_observation_v1/attempt_v2/native를 재사용한다. 센서 추가
전후의 기존7배열 exact가 이미 확인됐으며, 새 rollout에는 추가 센서를 넣지 않는다.
초기 source 감사가 실패하거나 code/finite/설정·제어 계약이 깨지면 해당 조건을 중단하고
실패·부분 자료를 보존한다. 짧은 성능 순위로 0.5초 성능을 추정하지 않는다.

초기각·고정 root·기타 Z+5mm와 기존 회전·몸통9·손가락42·C02하체 목표·주요66,
PALM_RATE 계산·±0.15rad 보정·C02±0.3rad∩모델 box·0.02rad/update·PD/solver는 같다.
기타 고정·강제 손 부착·runtime pose 덮어쓰기·새 gain/gate/학습을 추가하지 않는다.
Source 형상 조건은 cooked clearance나 지지력 인증이 아니며 접촉행은 힘·인과가 아니다.
이번0.5초에서 두 기타 오차가 작아져도 안정·연주 성공으로 선언하지 않는다.

원래 runner를 보존하기 위해 필요한 reference/report.json은 측정 결과를 복제하지 않고
runner가 요구하는 초기/제어 기대값만 담는다. 초기 auditor가 확인한 LA만 달라지며
역할을 ‘expected invariants, not rollout results’로 표시한다. Raw5 symlink는 기존
quiescent 기준의 원본을 읽기만 하며 실제 경로·SHA를 기록한다. PI rollout을 가장하지 않는다.

입력·기대값은 stability_adapter_2/trials/palm_preload_v1, 결과·로그·이미지·설명은
docs/2026-10-12/stability_adapter_2/results/palm_preload_v1에 저장한다.
