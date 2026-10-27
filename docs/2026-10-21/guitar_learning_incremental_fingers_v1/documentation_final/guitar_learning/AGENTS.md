# 자유 기타 학습 코드 작업 기준

- 이 디렉토리가 현재 신규 환경·측정·학습 연결 코드의 개발 기준이다. 과거 `archive/legacy_guitar_20261019/stability_adapter_2/free_guitar_learning_v1`와 이 패키지 `archive/` 안의 보관본은 실험 재현용 원본이므로 수정하지 않는다.
- 먼저 이 디렉토리 README와 프로젝트 사용자 지침을 읽는다. 변경 범위를 작게 유지하고 관련 CPU 검사를 실행한다. 변경 검수는 별도 change-reviewer가 맡는다.
- Root 고정·하체 유한 제어, 105/97/8, 자유 기타·중력 ON·스트랩 OFF를 유지한다. 기타 직접 보조 힘·강제 부착·지속 상태 덮어쓰기로 대체하지 않는다.
- native 장면·제어·접촉·렌더는 내부 `native/`, 자산·설정은 `assets/`, 악보 compiler는 `score/`를 사용한다. 최상위 `tab2body`·`stability_adapter_2`를 import하거나 실행 입력으로 읽지 않는다. 새 native 변경은 `assets/native_provenance.json`의 현재 SHA도 갱신하고 원본 SHA는 유지한다.
- 과거 gate의 원문 SHA는 `historical_inputs.py`와 내부 CAS 자료로 검증한다. 현재 실행 소스와 과거 원문의 pin을 섞지 않으며 archive를 import하지 않는다. 접촉 후보를 실제 현 압력·음향이나 음악 성공으로 확대하지 않는다.
- 실행 입력으로 봉인한 소스와 과거 결과는 보존한다. 이후 변경은 새 버전으로 진행한다. 결과·로그는 프로젝트의 기존 docs 결과 규칙을 따른다.

- 테스트 파일은 tests/에 작성한다. 프로젝트 루트에서 `python -m unittest discover -s guitar_learning/tests -t . -v`로 검사한다.

- 새 손별 학습은 README.md의 기본 실행 `guitar_learning.train`을 따르고 전문 실험·재현은 해당 목적별 진입점을 따른다. 검증 도구는 `tool/validation/`에 두며 루트의 미사용 environment.py facade는 보관했다. native 준비/정착/정책 pre-roll은 경로별 계약을 따르고 과거22초 reset 스케줄은 반복하지 않는다. 상태 복원은 에피소드 경계에서 한 번만 수행한다.

## 곡 단위 손별 학습의 기본 실행

- 기본 진입점은 `python -m guitar_learning.train --hand left/right --song SONG_ID --out NEW`다. 기본 곡은 `05_BN2-131-B_solo`의67음 전체다. 새 SpecialistPolicy와왼손512/오른손500상태 전곡 환경으로 시작하며 비활성 손의 정책 행동은0이다. BC·전문가 모델·과거 성공 평가4회를 새 학습의 선행조건으로 추가하지 않는다.
- 합의한035/v14 준비 상태를 매 에피소드 경계에서 정확히 복원한다. native 대기0초이며 첫 tick부터 정책 행동·접촉·비용을 수집한다. 정책 준비3초+원오디오+말미0.5초를 정책60Hz 경계로 올리며 기본 곡은1969tick·32.8167초다. 물리240Hz를 유지한다. 기존 CPU 경로의 기본 수집 길이는 전곡이며 GPU 기본은 아래 절의32tick이다. 짧은 `--horizon`의 PPO 경계에서도 장면·곡 시계·음별 원장을 이어간다. 곡 종료/물리 실패 때만 reset한다.
- 설정은 출력에 자동 저장하고 현재 자산·소스 SHA와 물리 안전은 내부에서 검증한다. 동일 계약의 `--resume`은 기존 strict load를 따른다. 과거 성공 모델 없이 시작하는 새 기본 실행을 이유로 기존 quality·refinement·전문 song의 Actor 이전·gate·strict 입력 계약을 전역에서 완화하지 않는다. 기존563 단음 checkpoint를 새 전곡 실행에 strict resume하거나 암묵적으로 이전하지 않는다.
- `--song`은 `data/song_bundles`의 안전한 식별자로 제한하며 전체 곡·오디오·타현 계획을 사전 확인한다. 지원하지 않는 동작·열린현·누락 계획을 임의로 생략하지 않는다. 손별 전곡 성공과 양손 협응·strict50/100ms 진단을 분리한다.

## 새 버전 작성과 이전 버전 보관

- 같은 기능의 새 버전을 만들기 전에 이전 파일과 필요한 검사·문서를 `archive/<날짜>_<작업명>/`에 먼저 보관하고 원래 경로·SHA·대체 파일을 기록한다.
- 현행 import와 실행 명령을 새 버전으로 바꾸고 검사한 뒤, 활성 디렉토리에서 더 이상 쓰지 않는 이전 버전을 제거한다. 이전 테스트도 보관 위치로 함께 정리한다.
- 구버전 안에 현행 코드가 필요한 기능이 있으면 공통 모듈로 최소 분리한 뒤 보관한다. 현행 코드에서 archive를 import하지 않는다.
- 보관본과 기존 실행 원자료는 수정하거나 덮어쓰지 않는다. 현재 README에는 권장 버전과 보관 위치를 명확히 구분한다.

## 이전 타이밍 경로의 재현 규칙

- 가슴 접촉 지속·삼중 접촉률은 성공의 필수조건이 아니다. 기타 이탈/과도한 회전/접지 등 현 물리 안전과 실제 목표 수행을 기준으로 삼고 접촉 분담은 진단으로 기록한다. 가슴 접촉 저하만으로 다음 실험을 막지 않는다.
- 사용자가 준비시간 증가를 허용했다. 타이밍 경로는 기존 native 정착2초 뒤 정책이 움직일 수 있는 pre-roll1초를 추가한다. 기존 환경의1~2초 제한은 native 정착시간이며 이 정책 준비 구간과 구분한다.
- 고정 단계별 넓은 시간창에서 시작해 반복 평가 후 좁힌다. 완화된 손별 성공과 원래50/100ms 음악 판정은 반드시 별도 기록한다. 실행 중 보이지 않는 기준 변경이나 기존 결과 재분류를 하지 않는다.

## 정책 준비 경로의 재현 규칙

- actionable536의 실행은 `tool.training.train_actionable_preparation`/`tool.evaluation.evaluate_actionable_preparation`이다. native정착0초+policy7초/pre-roll3초이며, 이전1~2초 정착 제한은 legacy 환경의 재현 규칙이다. 사용자가 앞2초의 정책 준비 전환을 명시적으로 지시했다.
- 첫120개 전이를 버리거나 별도 무행동 wait로 돌리지 않는다. 목표는 reset 관측부터 제공하고 실제240Hz 비용/종료와 기존 유한 유지 제어를 처음부터 유지한다.
- LH준비보상은 원candidate의연속접촉시간*.2/s(첫2초),RH는기존guide다. 손끝원점거리proxy를다시성공기준으로사용하지않는다.
- 기존505/536 모델의 성공을 상속하지 않는다. 새 계약의 명시적 Actor 이전과 native 검증을 수행하며 strict resume를 완화하지 않는다. 세부사항은 [docs/ACTIONABLE_PREPARATION.md](docs/ACTIONABLE_PREPARATION.md)를 따른다.

## 기존 손별 음악 품질 기반

- 기존563상태 손별 실행은 `tool.training.train_musical_quality`/`tool.evaluation.evaluate_musical_quality`이며 상세는 [docs/MUSICAL_QUALITY.md](docs/MUSICAL_QUALITY.md)다. 새 기본 손별 학습과 전문 전환/회복 경로를 구분한다. 기존 actionable536은 공유 기반/이전 결과, 해당 경로의 상태는563(기존536+품질이력27)·행동39·native0/policy7이다.
- 원positive와clean 후보를 분리하며 새MusicLedger/timing/preparation eligibility는clean이다. 옛 원판정이 그대로라고 설명하지 않는다. 타현 준비 gate도 새 계약이다.
- 비목표현/기타 지지/불명확한 경계 feature를 일괄 오압현으로 감점하지 않는다. 목표현 higher·할당 오류·missing과release를명시규칙대로구분한다.
- LH postnote 유지 보상은상쇄하고 timing-only성공보너스를audibleclean달성으로대체한다. 실패tick양성억제/비용은보존한다. 타현blocked ID는unprepared/extra와중복감점하지않는다.
- 새563 Actor이전은자체actionable536만명시적으로허용하며새열0/선택Actor/std만이전한다. 원물리·안전·행동·목표/시간·입력536과추가history차원/scale을검사한다. strictresume와성공상속을완화하지않는다.

## 학습 로그 기준

- [docs/LOGGING.md](docs/LOGGING.md)를 따른다. 역할·stage·목표·성공 분모와 timing-only/quality/joint를 구분한다. 누적 품질값을 매 행 합산하지 않는다.
- 모든240Hz 표본의 극값/접촉 시간은 safety240으로 기록한다. 기존60Hz끝점 열에서240Hz 최대/접촉률을 주장하지 않는다.
- standard 보고서는 전체episode를 다시 메모리에 읽지 않고 counter/group과 episodes.jsonl 참조를 사용한다. PPO의 기존loss는last이며 평균은diagnostics를 사용한다.
- sampled/logged/durable/committed/discarded를구분한다. prefix복구는원로그를수정하지않고새디렉토리에쓰며PPO반영을추정하지않는다.

## 역할별 코드·문서와 보관 경로

- 루트의 일반 학습 진입점은 `train.py`다. 설정·공용 runner는 `training/start.py`·`training/runner.py`, 환경·측정은 `core/`, native 세션은 `runtime/`, 정책·PPO·수집·기록은 `training/`에 둔다. 손별 기반은 `skills/`, 모방은 `imitation/`, 시간창은 `timing/`, 준비·품질은 `quality/`다. 기본 실행에서 전문 CLI를 import하지 않고 `song/`의 전곡 환경·측정·보상·worker·요약을 사용한다. 기존 단음 전문 경로의 `quality/runtime.py`·`timing/recording.py`도 공용 기능으로 유지한다. 세부 배치는 [docs/CODE_STRUCTURE.md](docs/CODE_STRUCTURE.md)를 따른다.
- 부가 학습·평가·시연은 `tool/training/`·`tool/evaluation/`·`tool/demonstration/`, 검증은 `tool/validation/`, 전문 실험8개는 `tool/experiments/`에 둔다. 이전 경로에 facade를 늘리지 않고 실제 import·명령·설정을 새 경로로 갱신한다.
- `music_task.py`와 `song/task.py`는 checkpoint의 경로·원문 검증 대상이므로 같은 내용으로 보존한다. `song/__init__.py`도 원문을 보존한다. 기본 전곡 실행은 루트 `train.py`, 과거 전문가 이전·양손 전문 전곡 실행은 `tool/experiments/song/`와 `song_reward_v2/`에 유지한다. 환경·측정·음별 판정·보상6개 공용 모듈은 `song/`으로 승격했다. 구버전 환경은 현재 상속·호출·계약 참조를 확인한 뒤 정리하며, 회귀 검사는 제거하지 않는다.

- 곡 등록·압현/타현 데이터·계획·입력 감사·타임라인 보조 도구는 `guitar_learning/tool/`에서 관리한다. 오디오·운지 전처리의 `tab2fingermapping`은 별도 활성 패키지다.
- 구형 여섯 디렉토리는 프로젝트 `archive/legacy_guitar_20261019/`에 보관한다. 현행 코드에서 보관본을 import하거나 입력으로 읽지 않는다. 과거 SHA 식별 경로는 보관 이동에 맞춰 고쳐 쓰지 않는다.

## 전문 전환과 접촉 회복

- 다음은 새 기본 실행과 구분하는 전문 실험·재현 경로다. 전곡은 `tool.experiments.song_reward_v2`, 왼손 정밀화는 `tool.experiments.transition_refinement_runtime_v2.run`, 접촉 회복 평가는 `tool.experiments.contact_recovery.run`을 따른다. 회복 자료 내보내기는 dataset_v2이며 아직 새 회복 BC/PPO 경로로 설명하지 않는다.
- `tool/experiments/`의 song·transition·기존 환경·runner는 전문 경로에서 재사용하는 기반을 포함한다. 구버전 이름만으로 제거하지 않는다. 공통 함수를 과거 CLI에서 분리한 뒤 실제 참조·검사·입력 pin을 갱신한다.
- 학습 중 소스 변경은 입력 무결성을 깨뜨린다. 변경 전 원문·원래 경로·SHA를 보관하고, 과거 증거 CAS와 현재 실행 pin을 각각 검증한다. 기존 gate·checkpoint 검증을 완화하거나 성공을 소급 상속하지 않는다.

## 기본 왼손의 성능 기반 보상

- GPU 왼손은 보상v3/`left_surface_events.v1`의 실제 표면 접근→접촉→유지·전환을 사용한다. 상태512/event24가 같아도 이전 보상v1/v2 checkpoint를 strict resume하지 않고 fresh로 시작한다. CPU 왼손의 기존8곡/27값 단계와 오른손·전문 경로는 유지한다.
- 표면오차는 지정 finger2/3의 유효 샘플만 사용해 유한 현과 프렛 셀±2mm의 교집합 중심선분까지 계산하고, 하중 전에도 제공한다. 속도는 기타 프레임의 실제 선택점 상대속도 음수이며 argmin 샘플 교체의 차분을 쓰지 않는다. 토큰9/10은 순간 candidate/wrong,16~21은 표면오차/속도(scale3cm/0.5m/s)다.
- 접근 potential은 press−2초~end의 모든 음을 포함해 `γΦ(next)−Φ(current)`로 계산하며PPO γ와같은0.99·고정 계수1을 유지한다. true terminal만다음Φ=0이고H32/목표교체에서 항을 생략하거나 초기화하지 않는다.
- 접근 potential과 양성 최초 접촉·유지·누적 달성만 손가락별 `M/(presentF*n_f)`로 균형화한다. 원래40%/최소50ms 성공과 contact_done 판정은 유지한다. 오압현·누락·놓친 음의 기존 공식/legacy 단계 비중과 행동 변화·terminal·안전 비용을 별도로 보존한다.
- GPU 단계는256종료곡·안전90%·모든 존재 손가락별 접근20%(10mm/누적100ms)로0→1, 손가락별접촉20%로1→2를 진행한다. 실패곡은0행으로 포함하고부분 수집으로 진급시키지 않는다. 양성 단계0/1/2 비중은 wrist(.2,.1,.05),contact(.5,1,1),timing(.5,1,2),approach(1,1,1)이다.3331값 이력을 checkpoint에 저장하고 committed PPO 뒤최대0.1만 갱신하며 native시계/장면을 reset하지 않는다.
- 음별 표면/접촉/원인 원장과손가락별 지표·episode reward_components·update reward_component_means를기록한다. 노출0일 때최소거리0, 겹치는원인시간, 후보와실제압력/음향의차이를구분한다. 초기latent std≈.05·학습률·PPO·비용 가중치는유지하며.08 탐색 확대는후속분리실험이다. [표면 압현 개선·검증 현황](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md).

## 기본 왼손의 유연한 손가락 제어

- 사용자 승인으로 기본 왼손만 `guitar_learning.flexible_left_fingers.v1`을 적용한다. LH21 목표 범위는 기존 native 관절 한계 전체, 목표 변화율4rad/s, 평활화0.45, 검지~새끼 K/D12/1.5·엄지 K/D8/1.25다. 나머지 축의 범위·변화율·평활화와 기존 POSITION 모드·effort 상한·물리 안전은 유지한다. 목표 변환과 최종 native 제출의 변화율을 일치시킨다.
- `runtime/finger_session.py`는 원래035/v14 복원 후 step0에서 LH21의 실제 native K/D만 한 번 변경하고 원본의 사본에서 새 PD 예상값을 만든다. 이후 reset은 해당 속성·서명을 엄격히 보존한다. 원본 준비 자료·native 소스·CAS를 바꾸거나 실행 중 속성 변경을 허용하지 않는다. 엄지 B 비교 후보를 초기 자세에 적용하거나 엄지를 별도로 고정하지 않는다.
- 관측은512상태지만 새 제어 계약이므로 이전512 왼손 checkpoint의 strict resume도 거부한다. 오른손500·기존 전문 경로는 새 프로필을 자동 상속하지 않는다. 부드러운 gain·기하 접촉·음악 성공을 구분한다.

## GPU 왼손 손가락의 누적 이동

- GPU 기본 왼손21축만 `guitar_learning.gpu_left_incremental_fingers.v1`으로 현재 목표에 행동×4rad/s÷60을 더한다. 기존 native 한계로 clamp한 목표만 다음틱에 보관해 windup을 만들지 않는다. 행동0은 목표 유지이며 반전은 다음틱부터다. 손가락의 위치평활화는 우회한다. 실제 관절의 즉각 정지/반전을 보장하는 것으로 설명하지 않는다.
- 위 유연 프로필의 native K/D·POSITION·힘·관절 한계는 유지하고 CPU의 초기자세 비례 위치/평활화0.45, GPU오른손·팔/손목·전문 경로는 유지한다. 새GPU왼손 control v3/action codec을 계약에 묶고 기존위치제어 checkpoint의 strict resume를 거부한다. 초기035/v14·상태512·행동39는 같아도 의미가 다르다.
- 초기화는 에피소드 경계의 선택행만; H32경계에서 목표를 초기화하지 않는다. 손가락 움직임 진단은 t0/60Hzendpoint·행동/인접행동변화의 분모를 명시하고240Hz극값이나음향성공으로 확대하지 않는다. 보상·탐색폭 변화 없이 제어검증과 학습성과를 분리한다. [구현·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

## GPU 기본 실행 (사용자 승인: 접촉 판정도 GPU 방식으로 재설계)

- 기본 `guitar_learning.train`은CUDA 정책과GPU PhysX·GPU tensor pipeline을 사용한다. 기본128환경/H32/medium/100업데이트이며1~1024환경을지원한다. GPU가없으면기본실행을CPU로대체하지않는다. CPU물리재현은`--physics cpu`로명시하고기존16worker제한과전곡수집기본을유지한다.
- `gpu/scene.py`는한simulator·여러env를소유하고경계에서만저장DOF/guitar root를복원한다. 직접기타힘·부착·진행중상태주입은금지한다. GPUtensor좌표는실측한env-local기준이며env origin을임의더하거나빼지않는다. 환경별aggregate는실제asset 합계68몸체/145shape 용량·self_collisions=True이며human→guitar→chair 순서·기존collision group/filter를유지한다.
- 현재GPU v3 물리 계약은환경별aggregate와함께기타를1native자유강체·89collision shapes로표현하고기존39개마커를rigid transform으로복원한다. native68몸체와논리106몸체를구분한다. 논리body_state의선형속도·com은각원래COM기준이며native aggregate COM을섞지않는다. 접촉합력은native인체/의자와기타전체root만기록하고가상마커힘을배분하지않는다. 두비물리proxy의의자/지면포함collision완전제외를새계약에명시한다. 모델·manifest SHA를실행입력과checkpoint계약에묶고구GPU v1/v2 checkpoint를재개하지않는다. 잔여느린이탈이있으므로수치폭발완화와장기안정성을구분한다.
- 새GPU접촉은loaded source-mesh surface후보이며기존CPU pair/witness clean과별도스키마다. 접촉합력으로몸체쌍·압력·음향을인증하지않는다. 새GPU의보상/성공을과거CPU결과에소급상속하지않는다.
- GPU하체기하질량·반복DLS IK·삼각형근접solver차이를계약에기록한다. 제어기의인증/유한값검사를물리진행전에확인하고실패시수집을중단한다. 유한하고인증된최근접점의방향만정의되지않으면해당환경을support_control_invalid물리실패로기록하고이tick말까지마지막유효한유한힘을유지한뒤선택reset한다. 실패tick양성억제·비용은유지한다. native48POSITION/57EFFORT·zero8·힘상한·LH21유연프로필을유지한다.
- 현재GPU 왼손 보상v3도기존 실행 중 비용과종료 실패 비용+5에더해물리 실패의실제tick 뒤남은 곡 시간에초당5의비용을한 번 추가한다. 고정률 absorbing-failure 모델이며단계 비중으로낮추지 않는다. 기존GPU 왼손 보상v1/v2 checkpoint는strict resume을거부한다. CPU/오른손은기존 계약을유지한다.
- PPO horizon은곡종료가아니다.32tick경계에서도곡시계/원장/물리상태를이어가고실제종료환경만reset한다. terminal관측으로bootstrap을계산한뒤reset한다. CPUcheckpoint를GPU에암묵이전하지않는다.
- 과거CPU기본원본은`archive/20261020_before_gpu_batch_v1`에보존한다. 실제GPU연결·1024자원·저장/재개·전곡종료를각각검증하고단기결과를장기수렴으로표현하지않는다.

- GPU 장기 실행에서는 종료 episode 객체를 계속 보관하지 않고 counter와`episodes.jsonl` 참조를 사용한다. PPO 로그 지표 계산이 끝난 rollout buffer를 해제하고 최적화 경계에서 유휴Torch 캐시를 반환해PhysX와경쟁하지않게한다. 반환전후free/current allocated/reserved를기록하고기존1GiB GPU 하한을유지한다. no-grad만으로메모리가제한되지않으므로전체rollout KL/진단forward는최대4096개씩순서대로평가하되전체표본의기존KL/평균/임계값과PPO 학습계산은유지한다.
- 이전aggregate v3/왼손 보상v2·동결 소스의large1024/H32/seed7 실제학습은2000업데이트·65,536,000전이·5시간41분25초를정상완료했고저장본2000→2001 실제GPU 재개도통과했다. post-cache free 최저7.374GiB·최종8.206GiB, 비Torch 추정 증가136MiB 이후plateau는이실행조건의검증이다. [2000업데이트 실행·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md) · [실제2000→2001 재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_verification.json). 이전 결과를현재표면 보상v3의장기검증·연주향상으로상속하지 않는다. 표면구현의초기검증은전체CPU823검사·독립검수·large1024/H32/seed7 GPU64회(2,097,152전이)와64→65실제재개를통과했다. 시간축완주1009·물리종료16건,3331값전체재생과572/573입력SHA를검증했으며그64회실행만으로2000회장기성능을주장하지않는다. 이후장기결과는아래JSON기록절을따른다. 연주 수렴·물리 무실패나모든 설정의SDK 메모리 누수 해결을주장하지 않는다.
- aggregate 적용 전1024환경39업데이트의PhysX 할당실패와512환경후반비Torch 메모리증가/94업데이트 정상중단은 과거 결과로 보존한다. [장기점검](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/README.md)의실패/정상중단/복구범위를덮어쓰지 않는다. 접촉버퍼를줄여충돌누락을허용하거나안전기준을완화해해결로분류하지않는다.

## 장기 실행의 JSON 실수 기록

- `training/json_io.py`의 로컬 Dragon4 기본 인코더로 공용 기록을 저장한다. NumPy는 실수 포맷 시 지연 import하여 Isaac 초기화 순서를 유지한다. 전역 JSON API나 FP 마스크를 바꾸지 않는다.
- 이 환경의 CPython dtoa에서 SIGFPE가 CPU검산과 GPU학습 모두에 발생했다. FE_INEXACT만 가린 첫 보호도 실패했다. 같은 오류를 다시 조사할 때 기존 `tool/experiments/transition_refinement_runtime_v2/serialization.py`와 [현재 장기 실행의 진단·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md)부터 읽는다. Dragon4는 오류 노출을 피하는 우회이며 x87 상태 변경 주체의 해결로 표현하지 않는다.
- 현재 보상v3 모델경로2000회는300+150+350+1200 복구 합계다. 마지막1200회 정상 종료/별도 초기·최종1024평가/전신 실측자세 재생을 검증했다. 3회 중단·미저장63회·물리 상태의 새 곡 reset을 구분한다. 평균3.861→8.301/67음이지만 중지0·전체67음 성공0이고 검지편중이 남는다. 이전CPU/보상v2 성과나 일반적인 곡 연주 숙련으로 확대하지 않는다.
