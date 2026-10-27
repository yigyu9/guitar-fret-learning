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

- 기본 진입점은 `python -m guitar_learning.train --hand left/right --song SONG_ID --out NEW`다. 기본 곡은 `05_BN2-131-B_solo`의67음 전체다. 새 SpecialistPolicy와GPU왼손544/CPU왼손512/오른손500상태 전곡 환경으로 시작하며 비활성 손의 정책 행동은0이다. BC·전문가 모델·과거 성공 평가4회를 새 학습의 선행조건으로 추가하지 않는다.
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

- GPU 왼손은 보상v8/`left_surface_events.v2`의 실제 표면 접근→접촉→유지·전환을 사용한다. 현재544상태/8priority 계약은 이전 보상v1/v2/v3/v4/v5/v6/v7 checkpoint를 strict resume하지 않고 fresh로 시작한다. CPU 왼손의 기존8곡/27값 단계와 오른손·전문 경로는 유지한다.
- 표면오차는 지정finger2/3의 유효샘플에서 pin된 넥 압현면으로 투영한 유한목표선과프렛셀안쪽2mm 교집합까지 계산하고,하중 전에도 제공한다. 속도는 기타 프레임의 실제 선택점 상대속도 음수이며 argmin 샘플 교체의 차분을 쓰지 않는다. 토큰9/10은 순간 candidate/wrong,16~21은 표면오차/속도(scale3cm/0.5m/s)다.
- 접근 potential은 공통 선택기의 유효 tracking slot0를 손가락별 하나씩 최대4개 포함해 `γΦ(next)−Φ(current)`로 계산하며PPO γ와같은0.99·고정 계수1을 유지한다. true terminal만다음Φ=0이고H32/목표교체에서 항을 생략하거나 초기화하지 않는다.
- 접근 potential과 양성 최초 접촉·유지·누적 달성만 손가락별 `M/(presentF*n_f)`로 균형화한다. 원래40%/최소50ms 성공과 contact_done 판정은 유지한다. 오압현·누락·놓친 음의 기존 공식/legacy 단계 비중과 손가락 제외 행동 변화·terminal·안전 비용을 별도로 보존한다.
- GPU 단계는256종료곡·안전90%·모든 존재 손가락별 접근20%(10mm/누적100ms)로0→1, 손가락별접촉20%로1→2를 진행한다. 실패곡은0행으로 포함하고부분 수집으로 진급시키지 않는다. 양성 단계0/1/2 비중은 wrist(.2,.1,.05),contact(.5,1,1),timing(.5,1,2),approach(1,1,1)이다.3331값 이력을 checkpoint에 저장하고 committed PPO 뒤최대0.1만 갱신하며 native시계/장면을 reset하지 않는다.
- 음별 표면/접촉/원인 원장과손가락별 지표·episode reward_components·update reward_component_means를기록한다. 노출0일 때최소거리0, 겹치는원인시간, 후보와실제압력/음향의차이를구분한다. 초기latent std≈.05·학습률·PPO·비용 가중치는유지하며.08 탐색 확대는후속분리실험이다. [표면 압현 개선·검증 현황](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md).

## 기본 왼손의 유연한 손가락 제어

- 사용자 승인으로 기본 왼손만 `guitar_learning.flexible_left_fingers.v1`을 적용한다. LH21 목표 범위는 기존 native 관절 한계 전체, 목표 변화율4rad/s, 평활화0.45, 검지~새끼 K/D12/1.5·엄지 K/D8/1.25다. 나머지 축의 범위·변화율·평활화와 기존 POSITION 모드·effort 상한·물리 안전은 유지한다. 목표 변환과 최종 native 제출의 변화율을 일치시킨다.
- `runtime/finger_session.py`는 원래035/v14 복원 후 step0에서 LH21의 실제 native K/D만 한 번 변경하고 원본의 사본에서 새 PD 예상값을 만든다. 이후 reset은 해당 속성·서명을 엄격히 보존한다. 원본 준비 자료·native 소스·CAS를 바꾸거나 실행 중 속성 변경을 허용하지 않는다. 엄지 B 비교 후보를 초기 자세에 적용하거나 엄지를 별도로 고정하지 않는다.
- 유연 제어 도입 당시 관측은512상태였지만 새 제어 계약이므로 이전512 왼손 checkpoint의 strict resume도 거부한다. 오른손500·기존 전문 경로는 새 프로필을 자동 상속하지 않는다. 부드러운 gain·기하 접촉·음악 성공을 구분한다.

## GPU 왼손 손가락의 누적 이동

- GPU 기본 왼손21축만 `guitar_learning.gpu_left_incremental_fingers.v1`으로 현재 목표에 행동×4rad/s÷60을 더한다. 기존 native 한계로 clamp한 목표만 다음틱에 보관해 windup을 만들지 않는다. 행동0은 목표 유지이며 반전은 다음틱부터다. 손가락의 위치평활화는 우회한다. 실제 관절의 즉각 정지/반전을 보장하는 것으로 설명하지 않는다.
- 위 유연 프로필의 native K/D·POSITION·힘·관절 한계는 유지하고 CPU의 초기자세 비례 위치/평활화0.45, GPU오른손·팔/손목·전문 경로는 유지한다. 새GPU왼손 control v3/action codec을 계약에 묶고 기존위치제어 checkpoint의 strict resume를 거부한다. 누적 제어 도입 당시 초기035/v14·상태512·행동39는 같아도 의미가 달랐다.
- 초기화는 에피소드 경계의 선택행만; H32경계에서 목표를 초기화하지 않는다. 손가락 움직임 진단은 t0/60Hzendpoint·행동/인접행동변화의 분모를 명시하고240Hz극값이나음향성공으로 확대하지 않는다. 해당v3실험은 보상·탐색폭 변화 없이 제어를 검증했으며, 이후v4접근·추종 보상 변경은 아래 절을 따른다. 제어검증과 학습성과를 분리한다. [구현·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

## GPU 기본 실행 (사용자 승인: 접촉 판정도 GPU 방식으로 재설계)

- 기본 `guitar_learning.train`은CUDA 정책과GPU PhysX·GPU tensor pipeline을 사용한다. 기본128환경/H32/medium/100업데이트이며1~1024환경을지원한다. GPU가없으면기본실행을CPU로대체하지않는다. CPU물리재현은`--physics cpu`로명시하고기존16worker제한과전곡수집기본을유지한다.
- `gpu/scene.py`는한simulator·여러env를소유하고경계에서만저장DOF/guitar root를복원한다. 직접기타힘·부착·진행중상태주입은금지한다. GPUtensor좌표는실측한env-local기준이며env origin을임의더하거나빼지않는다. 환경별aggregate는실제asset 합계68몸체/145shape 용량·self_collisions=True이며human→guitar→chair 순서·기존collision group/filter를유지한다.
- 현재GPU v3 물리 계약은환경별aggregate와함께기타를1native자유강체·89collision shapes로표현하고기존39개마커를rigid transform으로복원한다. native68몸체와논리106몸체를구분한다. 논리body_state의선형속도·com은각원래COM기준이며native aggregate COM을섞지않는다. 접촉합력은native인체/의자와기타전체root만기록하고가상마커힘을배분하지않는다. 두비물리proxy의의자/지면포함collision완전제외를새계약에명시한다. 모델·manifest SHA를실행입력과checkpoint계약에묶고구GPU v1/v2 checkpoint를재개하지않는다. 잔여느린이탈이있으므로수치폭발완화와장기안정성을구분한다.
- 새GPU접촉은loaded source-mesh surface후보이며기존CPU pair/witness clean과별도스키마다. 접촉합력으로몸체쌍·압력·음향을인증하지않는다. 새GPU의보상/성공을과거CPU결과에소급상속하지않는다.
- GPU하체기하질량·반복DLS IK·삼각형근접solver차이를계약에기록한다. 제어기의인증/유한값검사를물리진행전에확인하고실패시수집을중단한다. 유한하고인증된최근접점의방향만정의되지않으면해당환경을support_control_invalid물리실패로기록하고이tick말까지마지막유효한유한힘을유지한뒤선택reset한다. 실패tick양성억제·비용은유지한다. native48POSITION/57EFFORT·zero8·힘상한·LH21유연프로필을유지한다.
- 현재GPU 왼손 보상v8은v3에서 도입한 기존 실행 중 비용과종료 실패 비용+5에더해물리 실패의실제tick 뒤남은 곡 시간에초당5의비용을한 번 추가한다. 고정률 absorbing-failure 모델이며단계 비중으로낮추지 않는다. 기존GPU 왼손 보상v1/v2 checkpoint는strict resume을거부한다. CPU/오른손은기존 계약을유지한다.
- PPO horizon은곡종료가아니다.32tick경계에서도곡시계/원장/물리상태를이어가고실제종료환경만reset한다. terminal관측으로bootstrap을계산한뒤reset한다. CPUcheckpoint를GPU에암묵이전하지않는다.
- 과거CPU기본원본은`archive/20261020_before_gpu_batch_v1`에보존한다. 실제GPU연결·1024자원·저장/재개·전곡종료를각각검증하고단기결과를장기수렴으로표현하지않는다.

- GPU 장기 실행에서는 종료 episode 객체를 계속 보관하지 않고 counter와`episodes.jsonl` 참조를 사용한다. PPO 로그 지표 계산이 끝난 rollout buffer를 해제하고 최적화 경계에서 유휴Torch 캐시를 반환해PhysX와경쟁하지않게한다. 반환전후free/current allocated/reserved를기록하고기존1GiB GPU 하한을유지한다. no-grad만으로메모리가제한되지않으므로전체rollout KL/진단forward는최대4096개씩순서대로평가하되전체표본의기존KL/평균/임계값과PPO 학습계산은유지한다.
- 이전aggregate v3/왼손 보상v2·동결 소스의large1024/H32/seed7 실제학습은2000업데이트·65,536,000전이·5시간41분25초를정상완료했고저장본2000→2001 실제GPU 재개도통과했다. post-cache free 최저7.374GiB·최종8.206GiB, 비Torch 추정 증가136MiB 이후plateau는이실행조건의검증이다. [2000업데이트 실행·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md) · [실제2000→2001 재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_verification.json). 이전 결과를현재 보상v8의장기검증·연주향상으로상속하지 않는다. 표면구현의초기검증은전체CPU823검사·독립검수·large1024/H32/seed7 GPU64회(2,097,152전이)와64→65실제재개를통과했다. 시간축완주1009·물리종료16건,3331값전체재생과572/573입력SHA를검증했으며그64회실행만으로2000회장기성능을주장하지않는다. 이후장기결과는아래JSON기록절을따른다. 연주 수렴·물리 무실패나모든 설정의SDK 메모리 누수 해결을주장하지 않는다.
- aggregate 적용 전1024환경39업데이트의PhysX 할당실패와512환경후반비Torch 메모리증가/94업데이트 정상중단은 과거 결과로 보존한다. [장기점검](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/README.md)의실패/정상중단/복구범위를덮어쓰지 않는다. 접촉버퍼를줄여충돌누락을허용하거나안전기준을완화해해결로분류하지않는다.

## 장기 실행의 JSON 실수 기록

- `training/json_io.py`의 로컬 Dragon4 기본 인코더로 공용 기록을 저장한다. NumPy는 실수 포맷 시 지연 import하여 Isaac 초기화 순서를 유지한다. 전역 JSON API나 FP 마스크를 바꾸지 않는다.
- 이 환경의 CPython dtoa에서 SIGFPE가 CPU검산과 GPU학습 모두에 발생했다. FE_INEXACT만 가린 첫 보호도 실패했다. 같은 오류를 다시 조사할 때 기존 `tool/experiments/transition_refinement_runtime_v2/serialization.py`와 [현재 장기 실행의 진단·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md)부터 읽는다. Dragon4는 오류 노출을 피하는 우회이며 x87 상태 변경 주체의 해결로 표현하지 않는다.
- 이전 절대위치제어·보상v3 모델경로2000회는300+150+350+1200 복구 합계다. 마지막1200회 정상 종료/별도 초기·최종1024평가/전신 실측자세 재생을 검증했다. 3회 중단·미저장63회·물리 상태의 새 곡 reset을 구분한다. 평균3.861→8.301/67음이지만 중지0·전체67음 성공0이고 검지편중이 남는다. 이전CPU/보상v2 성과나 일반적인 곡 연주 숙련으로 확대하지 않는다.


## 이전v4의 압현면 접근·감속·유지 기록

- 보상v4/표면관측v2는 pin된 compound neck 충돌mesh에서 공통상향평면을 추출해 접근 목표로 쓴다. 현재Gz9.3mm이며 비충돌 현 중심12.3mm와 다르다. 목표선은 현x/y 유지 Gz투영·fret cell 안쪽2mm로 제한한다. 기존 현/프렛/하중 candidate·clean 성공 기준은 바꾸지 않는다. sourceconvex증명을 cooked접촉/압력 인증으로 확대하지 않는다.
- 담당finger별 현재음 우선/다음 준비음의 단일목표에 유한양성 추종rate0..4/s를240Hz마다한번 적분한다. 가까움·실제접근/감속속도·해당손가락4축 요청속도(sum/21)를함께보며, 상수incrementalaction도 움직이라는지속요청임을구분한다. 자동zero/deadzone/손가락고정/범위축소를넣지않는다. 실패tick새양성도0이며H32/부분reset에서다른행을지우지않는다.
- v3→v4는동일512/39와누적actioncodec이어도목표/보상/원장이달라strictresume거부·fresh로시작한다.3331curriculum은명시적으로보존한다. CPU/오른손/PD/PPO/std/원물리를유지하고과거실행성과를상속하지않는다.
- 전모듈단일CPU검사에서legacy JSON실수decode `_PyOS_ascii_strtod` SIGFPE가재발했다. 실패log와FP상태를보존하고,파일별freshprocess전체검사를단일process성공이나FP근본해결로표현하지않는다. 새GPU실행의완료/성과는별도검증한다.

- 이전435소스 보상v4 실제large1024/H32 fresh100·3276800전이·100→101재개는 실행/저장 검증을 통과했지만 고정0/100 평균3.8046875→0음·safe1024→1021로 연주개선을 입증하지 못했다. 당시 단계0/지속 한방향 출력이 남았으며 이후 이전 보상v4의436소스의 명시 요청 장기 실행과 구분한다. source면 추출·보상 단위검사 통과를 학습 성공으로 표현하지 않는다. [실제 결과](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/README.md).

- 손가락 진단v2의 `left_finger_motion.base_rotation`은4개 기저의 실제 palm 상대 회전과 zero-y 명령 참조 대비 SO(3) 오차를60Hz로 기록한다. qx/z 추종만으로 전체 자세·마찰 토크를 설명하지 않는다. y 성분이나 localxz 참조오차를 SDK 내부 축/실제 drive torque의 인증으로 표현하지 않는다. 4→16 물리 반복은 실제 소지 잔차 개선을 입증하지 못해 기본4를 유지했다. 새 진단 계약이 기존435소스 checkpoint의 strict resume를 자동 허용하지 않으며 CPU/오른손·학습 입력/보상·물리를 바꾸지 않는다.

- 이전 보상v4의436/진단v2 fresh2000회·65,536,000전이는6시간18분 연속 정상 종료했고 전체64,000행/2,000 CRC member·3331값 단계 재생·모델/optimizer 유한값·입력SHA를 검증했다. 고정1024 초기4.02734375→최종5.42578125/67음·safe1024→1019이며500/1000/1500/2000 중최종이최적이다. 단계0에서도손가락제어·접촉보상은유효하다. 중지/소지0·전체67음성공0·기존음성과보존실패가남아곡연주수렴으로확대하지않는다. 소지추종잔차·x87근본원인의해결이나새2000→2001실제재개를주장하지않는다. [보상v4의436소스 장기 학습·분석·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/README.md).


## 이전v5의 관절 분담·대기 자세 보상 기록

- `gpu/finger_reward.py`는 실제 palm/finger1/2/3의 전체 상대 회전으로 source−y 방향의 yz 투영각(MCP/PIP/DIP)을 구한다. source XML의 부모체인·identity rest rotation·+x 굽힘축을 검증해 계약에 SHA를 기록한다. native 구면 DOF 좌표나 인간 생리학적 정상 범위의 인증으로 표현하지 않는다. 퇴화/비유한 회전은 해당 손가락의 두 자세 보상을0으로 한다.
- 끝관절 쏠림은 DIP−PIP>20도, DIP−MCP>60도 및 DIP가 굽혀진 상태의 MCP 역신전에 부드러운 감쇠를 준다. 대기는 MCP[-15,110]·PIP[15,105]·DIP[-10,45]도 안의 넓은 영역을 같은 품질로 취급한다. 이는 실험적 soft prior이며 가동범위 축소·고정 자세·관절 비율 강제·자동정지·속도/가속도 제한이 아니다.
- 대기 가중치는 해당 손가락의 준비 시작(press−2초)~음 끝에0, 양끝 밖0.25초 동안 선형 전환하며 겹친 음은 busy의최댓값을 쓴다. 곡에 없는 손가락은 대기1이다. 두 자세 항은 각각 최대.05/s이고240Hz에서만 적분한다. 실패tick은 두 항 전체0, H32/부분reset에서 다른행은 보존한다.
- 표면 추종의 요청 비용은 자신의4축 제곱합/21로 기존 축당 계수를 유지한다. 다른 손가락/엄지의 요청으로 선택 손가락 보상을 깎지 않는다. 기존 제어·성공/안전·관측·3331curriculum·PPO/std는 유지하고 보상v4→v5 strict resume는 거부한다.
- 이전v4최종 영상·2000회 성과는 그대로 보존한다. 짧은v5 학습/저장·복구와 고정 명령 자세 대조는 새 정책의 자연스러운 연주나 성능 향상의 증거가 아니다. 새 장기 학습은 별도 요청을 따른다. [손가락 관절 분담 개선·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/README.md).


## 이전v6의 손가락별 목표·실제 자세 입력 기록

- GPU왼손만544상태/64×24전체토큰/8×24우선순위를쓴다. 각finger는tracking/next2slot이며순서index/middle/ring/pinky다. 공통 `finger_target_indices`의tracking은audible earliest end 우선,없으면press−2<=now<end earliest onset이다. next는같은finger의준비창안미래onset>now중tracking과다른earliest onset이다. 동률은원악보순서,무효index−1/토큰0/maskFalse다. 우선순위는전체토큰lookahead/capacity선택과독립적으로같은보상준비창을따른다.
- 실제32열은MCP/PIP/DIP sin/cos24·손가락valid4·idle4다. 자세보상과같은실제fullquaternion/source frame을사용하며한finger의어느joint라도투영무효면그finger6sin/cos전부0/valid0이다. native q/qd/target error는기존열에이미있다. 관측clip/scale1로append하고기존512열순서를보존한다.
- SpecialistPolicy/Encoder는명시GPUleft544/8slot/finger_targets schema/labels계약에서만8slot을허용한다. 기존2slot모델초기화순서·키·값·RNG는보존하고공통CPU/오른손/전문경로는확대하지않는다. reward/cost critic도같은8slot을받지만PPO공동행동확률/optimizer/수집/부트스트랩계산은유지한다.
- 추종v3의자기4축요청sqsum/21에만거리배율을곱한다: candidate또는거리<=.005m이면1,거리>=.02m이면.25,사이는선형이다. 실제속도오차·max4/s·자세항·성공/안전·제어·PD/관절범위는유지한다. 입력544/8·보상v6의구계약strictresume를완화하지않으며3331curriculum은보존한다.
- 1~3번 추가개선을 함께 연결한 검증과 이번 유효1300+700회 장기 학습은 각 항목의 독립 효과를 증명하지 않는다. 손가락별 성과 소실의 인과·native 원인 교정·H64/gamma/탐색 변경은 별도 실험이며 이번 결과에 끼워 넣지 않는다. [손가락별 입력·거리별 비용 구현/검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/README.md).


## 이전 보상v6 장기 결과와 복구 범위

- 이전v6의436/544상태/8슬롯·large1024/H32/seed7은 저장된1300회와 동일 계약 strict resume700회를 합쳐2000회·65,536,000전이를 완료했다. 모델·양 optimizer·RNG·3331 상태는1300에서 metadata 외 정확 복원했지만 물리 장면/부분 곡은 새035/v14로 시작했다. 최종2000→2001의 별도 실제 재개는 검증하지 않았다.
- 원실행의 전체 gzip EOF/native 정상 close는 주장하지 않는다. 선택1300 prefix의 CRC 완료41,600행과 새700의 전체 CRC/EOF22,400행·실제close를 구분한다. 별도13+62+5 업데이트/파일수80과 부분수집은 최종 경로에 합산하지 않으며, 명목전이 예산과 실제 raw 완전성/commit 인증을 혼동하지 않는다.
- 5고정평가의 초기3.8408203125/67음·safe1024, best500의5.4287109375음·safe414, latest2000의0.7451171875음·safe961을 함께 기록한다. best는 평가한 학습모델500/1000/1500/2000 중 전체1024 평균→안전수→최신 규칙의 선택이며 초기 모델은 기준값이다. 안전610실패를 포함한 best와 env0 안전 영상 예시를 혼동하지 않는다. 모든 모델은 단계0/67음 전체 성공0이고 학습 수집 평균·고정 평가·자세 분석은 별도 분모다.
- source436·이전v6/v5/v4 세 봉인 원문을 보존했다. NTFS/FUSE EIO와 Git 임시파일 저장공간 중단을 GPU 수치 오류나 모델 개선으로 설명하지 않는다. 원pin은 고치지 않고 SHA가 검증된 manifest로 경로 이전을 입증하며, 프로젝트 밖 durablecopy target과 phase alias를 별도로 봉인한다. 실제 자세의 끝관절 편중·대기 문제와 손가락별 성과 유지 부족이 남으므로 장기 연주·자연스러움 개선이나 원인 해결을 주장하지 않는다. [결과·원자료·검수](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/README.md).

## 이전 보상v7: 손가락 움직임 비용 없음

- GPU왼손만 엄지 포함LH21을 `action_change`에서 제외하고39분모/나머지축당 계수는 유지한다. 추종v4는 `exp(-distance/.02)*(1+candidate)`만 사용해 명령 크기와 실제 표면속도 감쇠도 제거한다. 움직임 크기·명령 반전만으로 손가락 보상을 낮추지 않는다.
- 목표 선택·PBRS/접촉·자세·누적clean 성공·안전비용/종료·50rad/s 극단속도 guard·범위·누적제어/PD·PPO는 유지한다. 관측과 진단의속도열은삭제하지않는다. CPU/오른손 비용은유지하며 새팔비용을추가하거나계수를높이지않는다.
- v6이하의strictresume는거부하고동일v7끼리의3331curriculum/model/두Adam/RNG 복원만허용한다. 과거v6의2000회평가/영상은보존하고v7성과로상속하지않는다. 비용제거를자연스러움·연주향상의증거로표현하지않는다. [구현/검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_motion_free_v1/README.md).

## 현재 보상v8: 목표 접근·손가락 분기·학습 신호

- GPU왼손544/8·명시 reward.v8만 전용분기를 쓴다. arm12+thumb5 공유출력과 손가락별4축 MLP를 ACTIVE_NAMES 순서로 결합한다. 각 분기는 shared context, 자신의 masked tracking/next encoded token2개, 이름으로 확인한 자신의 관절·실제 자세20열을 받는다. 단순 선형33 분할로 대체하지 않는다. legacy2slot/CPU/오른손에는 새 모듈/RNG 소비를 추가하지 않는다.
- 추종v5는 `(1+d/.04)^-2*(1+candidate)`이며 명령/속도 비용0과 최대4/s를 유지한다. PBRS v3는 같은 선택기 tracking slot0만 최대4개, 기존fingerweight/exp(-d/.03)/γ.99와 terminal0을 유지한다. 목표교체·H32 경계에서 potential을 임의 초기화하지 않는다.
- posture v2는 기존위반식에 `relu(min(PIP,DIP)-60도)`를 더하고 대기PIP band를[15,75]도로한다. 각각최대.05/s인 실험적 soft prior다. 가동범위 축소·관절비율 강제·속도 비용으로 대체하지 않는다.
- GPU왼손 PPO만 reward/cost GAE를각각표준화해가중결합후최종표준화하고 GAEλ.98을사용한다. H32/rewardγ.99/costγ1·critic 손실·costweight1·KLguard는유지한다. joint기본은기존계산·identity·RNG를보존하며설정JSON에도기본mode필드를추가하지않는다. diagnostics는원신호/각표준화신호/혼합신호를구분한다.
- 이전v7이하GPU왼손을strict resume하거나성과를상속하지않는다. 변경전원문은archive/20261022_before_targeted_finger_learning_v1/에보관한다. 짧은GPU실행/복구검증을연주성과/자연스러움향상으로표현하지않는다.
