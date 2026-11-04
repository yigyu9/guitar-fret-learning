# PC1에 전달할 야간 실행 프롬프트

현재 PC에서 2026-11-05 오전08:00 KST까지 압현 추가 실험을 진행해줘. 먼저 이 파일과 같은 폴더의 계획.md, 상위 실험설계.md, 프로젝트 AGENTS/README를 읽고 계획에 따라 질문 없이 단계별 준비·검증·실행·분석·영상을 진행해줘. 현재 실험과 공유 원본을 수정하는 권한으로 확대하지 마.

1. 기존 C1을 먼저 마무리해줘.

현재 C1은 docs/2026-11-09/압현_v5_C1_장기학습_v1에서 진행되고 있고, 재부팅 복구 감독은 docs/maintenance/v5_project_cleanup_20261104/tools/resume_c1_after_reboot.py야. 실행 중인 감독·봉인 runtime·입력·모델·원시 로그를 편집하거나 종료하지 마. 2000회 학습뿐 아니라 원래 평가·분석·대표 영상과 프로세스 종료까지 확인한 뒤 새 GPU 작업을 시작해줘. 오류가 나면 기존 실패를 보존하고 원인을 확인해줘. 완료를 가장해 다음 작업으로 넘어가지 마.

2. 독립 준비 접근 비교 환경을 준비해줘.

새 작업의 유일한 출력/도구 소유 경로는 docs/2026-11-09/압현_v5_학습개선실험설계/야간실험_20261105/PC1_준비접근비교야. 다른 PC의 H실험 디렉토리는 읽기만 하고 수정하지 마. 그 연구의 기준봉인.json과 작업자료/source_snapshot을 검증한 뒤 소스·필수 입력·native 패키지를 새 독립 source_snapshot으로 복사하고 사본 SHA·상대 링크·입력 경계를 검사해줘. 원래 사본의 .runtime/cache와 study_outputs는 복제하지 마. source_snapshot은 Git에서 제외되므로 원래 사본과 봉인은 별도 실험 근거로 보존해줘. 각 PC의 Python3.8·native cache는 로컬 것을 써줘.

학습 코드·보상 가중치·제어·네트워크를 수정하지 않고 공식 press_sequence CLI와 기존 corrected/preparation 옵션만 사용해줘. 필요한 감독·검증·분석 코드는 새 작업 경로 안에 두고, 실행 중인 원본 감독은 import 후 전역 상태를 바꾸지 마. CPU 준비는 기존 GPU 학습 중 가능하지만 단일 스레드로 하고 새 GPU 테스트는 기다려줘. 실제 GPU/프로세스 상태가 실행 환경의 격리 때문에 보이지 않으면 호스트 조회로 확인하고, 프로세스가 없다고 추정하지 마.

3. B와 P를 같은 조건에서 각각 새로 학습해줘.

공통 C1·large·num-envs1024·horizon32·updates512·checkpoint-every128·seed7·no-include-pelvis·initial-support-std0.15·initial-finger-std0.35야. B는 --improvement-profile corrected, P는 --improvement-profile preparation만 바꿔. PPO epochs2·minibatch4096·LR·KL·물리·나머지 보상과 종료는 그대로 유지해줘. initial state_dict tensor digest와 실제 전체 settings를 대조하고, 허용 차이는 profile 관련 계약·출력 위치·기록한 벽시계 상한뿐이야.

조건당 planned_transitions16,777,216, full_song_after4,194,304를 확인해줘. 공통 노출 문턱은 새 reset에 적용되는 기존 의미를 유지해줘. 짧은 업데이트 블록을 각각 새 학습으로 만들지 마. 공식 snapshot/scripts/tab2body.py를 통해 -m guitar_learning.tool.experiments.press_sequence train C1을 실행해줘. 경로는 현재 PC의 실제 경로로 만들고 argv 배열을 사용해줘. out은 snapshot/study_outputs/학습/B_seed7/attempt01과 P_seed7/attempt01로 분리해줘.

4. 실행 시간을 먼저 판단하고 감독해줘.

B/P 두 학습이07:00까지, 필요한 평가·분석·영상이08:00까지 들어갈지 실제 처리량과 계획.md의20% 여유 기준으로 판단해줘. 기존 후처리가 늦어 쌍이 안 들어가면 원래 C1 결과 분석을 우선하고 시작 못 한 조건을 시간 부족으로 기록해줘. 무리하게 다른 환경 수·예산·보상으로 축소해 완전한 비교라고 하지 마.

새 학습에는 --max-wall-seconds로07:00까지 남은 시간에서120초를 뺀 상한을 명시하고 기록해줘. native 검사는 rollout 사이에 이뤄진다는 점을 고려해줘. 진행상황.json은 최대60초마다 단계·실제 PID·global update·commit 전이·checkpoint SHA·실제 속도·ETA·다음 작업·오류를 갱신해줘. 터미널이 닫혀도 유지되는 감독으로 순차 실행하고 GPU 경쟁 작업은 피해야 해. 저장공간도 시작 전·실행 중 확인해줘.

실패 복구는 같은 조건으로1회, 공통128회 경계의 SHA가 확인된 모델에서만 허용해줘. 추가 --updates=512−저장 global update이고 기존 계획·RNG·Adam·sampler·노출을 복원해야 해. native 물리 episode가 새로 시작하는 재개 의미와 버린 tail을 기록해줘. 재개 경계가 어긋나면 정확한 평가 시점을 임의 모델로 대체하지 마. NaN·봉인 오류·반복 오류는 중단하고 근거를 보존해줘.

5. 동일 전이 평가와 결과를 정리해줘.

각 조건 initial.pt/global128/256/384/final512의5시점을 원래 C1 full_song·원래 초기 자세·평균 정책·num-envs32로 평가해줘. 매번 저장 manifest SHA, strict 입력·identity·clock, 장면 종료를 확인해줘. 전체20음 분모에 조기 종료로 못 만난 음도 남기고, 실제 노출/발음 창 도달 분모는 별도로 집계해줘. legacy40% 달성을 전체 유지+해제 성공으로 바꾸지 마.

분석/REPORT.md·비교표.csv·전이 및 시간 기준 그래프를 만들어줘. P의 첫 후보/clean이 빨라졌는지, 이전 음 조기 해제·오압현·안전 종료가 나빠지지 않았는지 봐줘. 항목별 보상·LR·KL·가치 진단과 실제 로그에서 읽을 수 있는 std를 비교해줘. 없는 값은 없다고 써줘. 기존 압축 에피소드는 해당 사본의 training_log_io.iter_episode_rows로 읽어줘.

조건당 대표 손확대1개·전신1개만 동영상/에 저장하고 렌더 원문·검증 보고서는 native 출력에 둬줘. 최종 모델을 기본으로 하되 중간 최고 모델을 고르면 전체 유지+해제→안전→clean 순의 선정 근거와 모델 SHA를 남겨줘. 같은 C1 평가로 고른 결과는 독립 테스트 성과가 아니야. 새 seed·LR 스케줄·epochs·탐색 구조 변경은 이번 야간 작업에 추가하지 마.

08:00까지 완료/부분 완료/실패/시간 부족을 구분하고, 실제 결과·대표 영상·분석의 정확한 경로와 다음 단독 실험 추천을 보고해줘. 준비와 실험 구현 검수는 다른 눈으로 확인하되 GPU 작업을 중복 실행하지 마.
