# GPU 왼손의 목표 접근·손가락 출력·학습 신호 개선

현재 보상은 v8이다. 중지·약지의 목표 접근 부족, 한 방향 출력의 지속, 안전 비용과 보상 신호의 크기 차이, 끝관절 편중을 개선 대상으로 삼았다. 손가락 움직임 비용0을 유지하고 아래 변경을 구현했다. 짧은 실제 GPU 학습과 저장·복원을 검증했으며, 연주 성과나 동작의 자연스러움이 좋아졌다는 결론은 아직 내리지 않는다.

## 구현한 변경

| 항목 | 현재 동작 | 목적 |
| --- | --- | --- |
| 원거리 추종 | `(1+거리/.04)^-2 × (1+candidate)`, 추종v5 | 10cm 이상 떨어져 있어도 접근 신호 제공. 기존 최대4/s 유지 |
| 접근 potential | 공통 tracking slot0만 손가락당1개, 최대4개 | 서로 다른 준비 목표를 동시에 당기는 신호 줄임 |
| 손가락별 출력 | 공유17축(팔12+엄지5)과 손가락별4축×4 | 각 손가락이 자기 목표·관절 상태를 별도 비선형 분기로 처리 |
| 보상·비용 신호 | 각각 표준화 → `reward_norm−cost_weight×cost_norm` → 최종 표준화 | 원래 신호 크기 차이에 따른 상대 비중 변화를 줄임 |
| 시간 연결 | GPU왼손 GAEλ0.95→0.98 | 준비 행동과 뒤의 결과 연결을 늘림. H32·rewardγ0.99/costγ1 유지 |
| 자세 prior | 기존 위반식에 `relu(min(PIP,DIP)−60°)` 추가, 대기PIP[15°,75°] | 두 관절을 함께 과하게 접는 상태와 비사용 손가락의 과도한 폄 구분 |

접근 potential의 거리식은 기존 `exp(-d/.03)`이며, 추종 보상의 새 거리식과 구분한다. 기존 손가락 가중치와 `γΦ(next)−Φ(current)`를 유지하고, true terminal만 다음Φ를0으로 한다. 목표 교체·H32 경계에서 임의로 초기화하지 않는다. 이전의 모든 준비 음 합산을 공통 선택기의 tracking 목표로 바꿨다.

전용 분기는 기존 shared actor context, 자신의 masked tracking/next 토큰2개(각128차원), 자신의 관절·자세20열을 받아 hidden128/Tanh를 거쳐4축을 출력한다. 20열은 q_offset/q_velocity/target_error 각4개, 실제 MCP/PIP/DIP sin/cos6개, valid/idle2개다. 관측 이름과 ACTIVE_NAMES 순서를 계약으로 검사한다. 초기 출력은0이며 모델·optimizer·strict identity에 새 분기를 포함한다. 마지막 선형33층만 네 조각으로 나누는 방식과 다르다.

자세 항은 각각 최대0.05/s인 실험적 soft prior다. 관절 비율·고정 각도를 강제하거나 가동범위를 줄이지 않는다. LH21의 명령 변화 감점과 추종의 명령 크기/속도 감쇠는 계속0이다. 팔·손목의 기존 축당 비용, native 범위·독립 누적제어·PD·원물리·접촉/성공·물리 안전 종료와3331값 curriculum은 유지한다. critic 손실, cost_weight1, KL guard/재시도, 초기 std도 유지한다. CPU·오른손은 기존 joint 정규화·설정·모델 초기화/RNG·checkpoint identity를 보존한다.

## 검증 결과

활성 Python438개의 Python3.8 AST와 메모리 내 컴파일 검사를 통과했다. 관련 CPU 검사는 중복을 제외하면218개 중217개 통과, 기존 실패1개다: reward47, actor/specialist19, PPO/GPU설정23, 추가 회귀129. 추가 회귀의 `test_left512_rejects_legacy500_before_mutation_and_right500_stays_compatible`는 기존GPU 기본544를512로 기대하는 알려진 실패이며 원인을 분리해 기록했다. 이번 변경과 무관한 해당 검사는 수정하지 않았다. fresh process별 검사 결과이며 전체 모듈을 한 process에서 통과했다고 주장하지 않는다.

legacy 모델의 상태·RNG fingerprint와 기존 PPO의 모델/optimizer/RNG 일치를 대조했다. 각 손가락의 local 입력과 token 마스킹/gradient, selected-target potential의 목표교체·terminal 포함 telescoping, 명령/속도 변화에 따른 보상 불변, 각 신호의 상수/0/배율 변화, transactional rollback과 엄격 저장/복원을 검사했다. 구v7 계약 거부는 CPU fixture에서, 실제 구v6 GPU checkpoint 거부는 원본 SHA와 거부 전후 상태 불변을 검사했다.

| 실제 GPU 실행 | large/1024/H32/seed7 | raw 행 | wall | 물리 종료 |
| --- | --- | --- | --- | --- |
| 새 모델8회 | 262,144전이, optimizer8 | 256 | 102.36초 | 기타 이탈25건 |
| 동일 계약 재개1회 | 32,768전이, optimizer9 | 32 | 19.94초 | 0건 |

두 실행 모두 GDB에서 정상 종료했고 장면 close·입력 SHA·journal sampled/logged/durable/committed가 일치했다. 전체288행/9gzip member의 CRC·EOF·순서·1024개 환경 배열·보상/비용 평균과 종료 에피소드 대응을 확인했다. 입력 SHA는 새 실행583개/재개584개를 검사했다. 실제 네 손가락 출력 가중치 모두 갱신됐고, 표준화한 reward/cost/mixed 신호의 평균0·표준편차1과 유한값을 확인했다.

새 모델의 마지막 저장본과 재개 초기의 모델·두Adam·난수 상태·3331 curriculum은 metadata를 제외하고 정확히 같았다. 재개 후 모델과 두Adam이 다시 갱신됐고 유한값을 유지했다. 새 모델8회는 환경당 약4.27초의 수집일 뿐 전곡 완료 평가가 아니다. 위 물리 종료를 전체 곡의 안전 성공률로 변환하지 않으며, 기존v6의 장기 성과나 영상을 v8에 상속하지 않는다.

[실제 GPU 검산](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_targeted_finger_learning_v1/training_verification.json) · [추가 CPU 회귀](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_targeted_finger_learning_v1/ppo_related_regression.json) · [현재 실행 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)

## 보관과 재현

이전17개 파일에 통합용 runner/test logging 및 .gitignore 원본3개를 추가 보관했다. 원문은 [archive](/home/ajou/yigyu/3/guitar_learning/archive/20261022_before_targeted_finger_learning_v1/manifest.json)와 이 디렉토리의 additional_before_manifest.json에 기록했다. v7과v6 기존 결과의 정규파일33개/1511개 SHA를 모두 다시 대조했으며 변경은 없었다. 현재 소스438개와 변경15개 overlay는 tested_source_manifest.json에 고정했다. 이전v7 이하 GPU왼손 모델은 새 정책·보상·PPO 계약과 strict resume할 수 없어 fresh로 시작한다.

디스크 여유가 약319MiB여서 실행 출력은 별도 임시 메모리 공간에서 만들었다. 완료 후 원본340,093,062바이트/41파일을 gpu_runs.tar.xz의184,217,340바이트로 무손실 보관하고, 모든 archive member의 원본 SHA/크기를 스트림으로 대조했다. 모델 외 로그·설정·원자료는 아래 gpu_smoke8/gpu_resume1에도 복사했다. 모델4개는 압축파일 안에 있으며 원래 SHA는 gpu_runs_manifest.json에 있다. 압축파일 SHA는 `be11682d56c7158500dcfdbeca1f40a3d8a20b3dd3829768cf5dd863c475d48e`다. Git 자동 snapshot에 큰 중복 객체가 추가되지 않도록 이 생성 압축파일 하나만 .gitignore에 추가했다. 기존 Git pack/임시 pack/결과는 변경하지 않았다.

재검산하려면 충분한 공간의 새 디렉토리에 압축을 풀고 `verify_training.py --runs <추출한 디렉토리>`를 실행한다. 원래 `/dev/shm/...`로 고정된 입력 경로는 해당 추출 위치로만 대응시켜 SHA를 검사하며, 다른 프로젝트 입력은 실제 경로의 SHA를 검사한다. 프로젝트 root를 PYTHONPATH에 포함하고 rl38 Python을 사용한다. 검산은 CPU만 사용한다. 소스를 이후 버전으로 바꾸면 현재 source freeze 검사는 당연히 실패한다.

현재 디스크 여유는 약132MiB이므로 새 장기 학습은 공간을 확보한 뒤 진행해야 한다. 이번 요청에서는 짧은 구현 검증만 실행했다. 후속 성능 평가는 새v8의 고정 조건에서 초기/중간/최종 모델의 손가락별 접근·접촉·달성음, 안전 종료, 실제 전체 관절 움직임을 함께 비교해야 한다.
