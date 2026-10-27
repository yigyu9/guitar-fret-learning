# GPU 왼손 표면 접근·손가락별 학습 개선

구현과 기능 검증을 완료했다. 전체 CPU823개, 실제large1024의64업데이트와64→65회 재개·음별 원장/보상/커리큘럼 대조를 통과했다. 학습 성능 향상은 아직 검증하지 않았다. 과거2,000회 결과는 guitar_learning_gpu_long_training_v3에 봉인되어 있으며 수정하지 않는다. 이번 보상v3/표면관측v1/손가락별커리큘럼v1은 새 모델로 시작한다. 이전 보상v2의 장기 결과를 이번 코드 성과로 상속하지 않는다.

목표:67음 전곡·035v14·GPU aggregate 물리v3·기존지정손가락/현/프렛/40%최소50ms 성공·안전·remaining5/s 비용을 유지하며 표면접근→접촉→유지·전환을 배운다. CPU/오른손·원native/자산은 유지한다.

변경:지정 finger2/3 실제표면→목표현중심선분(유한현/프렛셀margin2mm) 오차·실상대속도/left24token9,10+16:22, 고정potentialgamma.99(설정PPO와동일)/press−2..end/true terminal0/H32연속, 양성항목손가락균형M/(presentF*n_f), 최초접촉보너스1회/정규화유지/기존누적달성. 원오압현·누락공식과legacy단계계수는분리유지한다.

최근256종료곡(실패0포함),안전90%와존재하는모든finger별접근20%(10mm/100ms)로0→1,각finger접촉20%로1→2. 양성weights wrist(.2,.1,.05),contact(.5,1,1),timing(.5,1,2),approach(1,1,1). 기존CPU의window8/27상태는유지하고GPU만3331상태buffer를저장한다. 모든수치는초기실험설정이며학습성능개선을검증한값은아니다.

탐색확대/비용가중치/학습률 조정은이번기본값변경범위가아니며후속비교실험이다.

## 구현

| 역할 | 현행 파일 |
| --- | --- |
| 실제 메시 표면과 목표 현 선분의 최근접 오차·물리 상대속도 | [gpu/geometry.py](/home/ajou/yigyu/3/guitar_learning/gpu/geometry.py) |
| 표면 관측, 보상, 음별 기록, 손가락별 지표 | [gpu/environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py) |
| 최근256종료곡의 GPU 전용 단계 | [song/gpu_left_curriculum.py](/home/ajou/yigyu/3/guitar_learning/song/gpu_left_curriculum.py) |
| 단계의 저장·복원과 committed PPO 경계 적용 | [song/curriculum_runtime.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py) |
| GPU/CPU 설정 분기와 PPO γ 연결 | [training/start.py](/home/ajou/yigyu/3/guitar_learning/training/start.py) |
| 실제 GPU 수집·학습·업데이트별 보상 분해 | [training/gpu_runner.py](/home/ajou/yigyu/3/guitar_learning/training/gpu_runner.py) |

접근은 접촉 하중이 없어도 계산한다. 지정 손가락의 finger2/3 샘플만 사용하고 최근접 샘플 교체를 속도로 오인하지 않는다. 모든 활성 음의 potential을 현재/다음 상태의 실제 곡 시각에서 각각 계산하므로 음 전환·준비창·PPO 수집 경계의 항을 누락하지 않는다. 표면 거리10mm의 접근 달성과 기존 하중을 포함한 압현 성공은 별도 지표다.

| 양성 항목 | 원시 보상 | 손가락 균형 | 단계0/1/2 계수 |
| --- | --- | --- | --- |
| 표면 접근 | γΦ(next)−Φ(current), 거리 척도3cm | Φ 안에 반영 | 1 / 1 / 1 |
| 최초 접촉 | 원래 contact_done 달성 때0.5 한 번 | 적용 | 0.5 / 1 / 1 |
| 청정 유지 | 2×청정 유지 증가시간÷음 길이 | 적용 | 0.5 / 1 / 2 |
| 음 달성 | 원래40%·최소50ms 누적기준 달성 때0.5 한 번 | 적용 | 0.5 / 1 / 2 |
| 손목 보조 | 기존 위치·방향 보조 | 미적용 | 0.2 / 0.1 / 0.05 |

손가락 균형은 목표 수M, 곡에 존재하는 손가락 수F, 해당 손가락 목표 수n에 대해 M/(F×n)이다. 기본67음의 검지/중지/약지/새끼 비중은 각각0.67/0.930556/1.395833/1.395833이다. 음 달성 뒤에도 실제 청정 유지가 늘면 유지 보상을 받는다. 오압현·누락·놓친 음에는 원래 공식과 기존 단계 계수를 적용하며, 실패 tick 양성 억제·−2 보상·+5 비용·남은 곡 시간×5/s 비용을 유지한다.

종료 로그 `left_note_ledger`는 각67음의 접근 노출·10mm 체류·최소 표면거리·기하 후보·하중 동반 후보·원인별 시간·접촉·청정 유지·달성을 기록한다. `body_load_time`은 최근접으로 선택된 표면 샘플의 몸체 하중이며, 임의의 손가락 몸체 하중이 아니다. 원인 시간은 서로 겹칠 수 있고 노출0의 최소거리0은 미측정 표기다. 접촉 합력과 기하 후보로 실제 현 압력·음향을 인증하지 않는다.

`episode.reward_components`는 종료곡 보상 합계, `update.reward_component_means`는 실제 H×N 전이당 평균이다. 부분 수집은 완주로 세지 않고 음별 원장과 물리 시계를 이어간다. 물리 상태의 곡 중간 저장·복원은 추가하지 않았다.

## 검증 결과

전체CPU823개를523.272초에 통과했다. 동결본의 추가통합9개도 별도로 재검사했다. 표면 기하7개·새 단계11개·통합9개는 전체823개에 포함되므로 더하지 않는다. [전체 검사 로그](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/full_cpu_tests.log)·[통합 검사 로그](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/integration_tests.log). 독립 검수에서 새 관측·potential·일회 보너스·유지 보상·3331값 저장 경로와 기존 오른손의6tick/물리종료 대조를 통과했다.

실행 입력427개 Python을 [동결 목록](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/training_source_manifest.json)과 `source_training/`에 보관했다. 변경 전13파일과 보호 대상3파일의 SHA는 [원문 보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261021_before_surface_fretting_v1/manifest.json)로 확인했다. 과거 봉인 실행은 수정하지 않았다.

| 실제 GPU 검증 | 결과 |
| --- | --- |
| 본 실행 | fresh large1024/H32/seed7,64업데이트·2,097,152전이·708.603초 |
| 종료 기록 | 1025건=시간축 완주1009+물리 종료16,67음 전곡 과제 성공0 |
| 장면/입력 | GPU PhysX·CUDA pipeline·1024환경·8192 batched physics steps·정상 close,572입력 SHA·427소스 일치 |
| 원본 전이 | 2048행·gzip CRC/EOF·episode/update/metrics 대응,폐기0 |
| 보상/성공 | 보상15항 합계·기존40%/50ms와접촉 문턱·실패 남은시간 비용 대조 통과 |
| 합산 최대 오차 | episode0.000236,update mean1.05e-8; 허용오차는 verification.json에 명시 |
| 단계 이력 | 매 update summary 및 최종3331값 전체 재생오차0 |
| 저장/재개 | 64→65 실제GPU,32,768추가전이,573입력 SHA,모든 nonmetadata 정확 복원 |
| 재개 갱신 | 두 optimizer·왼손 actor 갱신,비활성 오른손 actor 불변,167개 model/optimizer tensor 유한 |
| 과거 모델 | 실제 이전v2의2000회 모델을 현재 strict loader에 넣어 계약 불일치 거부 확인 |
| 자원 | post-cache GPU free 최저6.909GiB,본 실행 수집평균8.622초/PPO평균2.278초 |

[기계 대조 결과](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/verification.json)·[본 실행 보고서](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/train1024_large_64/report.json)·[재개 보고서](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/resume_1/report.json)를 따른다. 재개는 모델/optimizer/난수/단계 이력을 복원하고 초기 자세의 새 물리 에피소드를 시작한다. 곡 중간 물리 상태를 복원하지 않는다.

짧은 학습 수집에서 마지막256곡의 손가락별 접근률은 검지37.33%·중지43.88%·약지53.42%·새끼6.41%였다. 새끼가20%를 채우지 못해진행도0/표면 접근단계에 머물렀다. 손목 보조 성과만으로 다음 단계에 넘어가지 않는 것을 실제 실행에서 확인했다. 중지/약지/새끼의 접촉·음 달성은 이짧은실행에서0이었다. 안전 완주1009곡의 평균 달성음3.013/67은 학습 중 계속 갱신한 정책의 수집 결과이며,이전 고정정책 평가4.232/67과 직접 비교하지 않는다. 새 장기 학습·최종 고정정책 평가는 수행하지 않았다. [수집 분석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/collection_analysis.json).

새 음별 원장을 포함한 본 실행 전체는274,585,608bytes(3checkpoint포함),측정로그/JSON은104,908,544bytes였다. 로그만단순비례하면2000회약3.05GiB지만 실제 종료빈도·수집결과에따라 달라지므로 디스크 상한으로 쓰지 않는다. 주기 checkpoint는 별도다.

실행 명령과 저장 흐름은 [학습 안내](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)를 따른다. 새 장기 실행은 새로운 출력 경로와 fresh 모델을 사용하거나,현재 표면 계약의 저장본만 strict resume한다. 이전2,000회 모델의 자동 이전은 추가하지 않았다.

최종 독립 검수는 코드·검사·실제 원장 재집계·입력 SHA·문서 수치 대조를 통과했다. [검수 기록](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/review.json)과 [최종 파일 SHA 목록](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/result_manifest.json)을 보존하며 이후 변경은 새 결과 경로를 사용한다.
