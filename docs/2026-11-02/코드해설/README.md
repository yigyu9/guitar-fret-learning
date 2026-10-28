# 현재 학습 코드 상세 해설

현재 기본 명령 `python -m guitar_learning.train`이 사용하는 **GPU 왼손 finger-skill v3**를 이해하기 위한 문서다. 추가 통합한 코드를 실제로 읽어, 각 파일의 역할뿐 아니라 주요 함수 안에서 값이 어떻게 만들어지고 다음 파일로 전달되는지를 설명한다.

요청한 `2026-11-02/코드해설` 경로에 저장했다. 문서가 설명하는 소스의 정확한 기준은 [소스기준.json](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/소스기준.json)의 파일 SHA와 정의 위치다. 이번 J 전용화에 맞춰 해설과 소스 기준을 갱신했다.

## 먼저 읽을 순서

1. [00 전체 흐름과 읽는 방법](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/00_전체흐름과읽는방법.md)에서 한 번의 행동·자료 수집·PPO 갱신·저장이 어떻게 이어지는지 읽는다.
2. [01 실행과 학습](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md)을 보면서 실제 `launch.py`와 `finger_skill_runner.py`를 연다.
3. [02 정책과 PPO](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/02_정책과PPO.md), [04 GPU 환경과 종료](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/04_GPU환경과종료.md)로 행동·보상·학습의 핵심을 연결한다.
4. 움직임·압현을 깊게 보고 싶으면05·06, 곡의 목표를 보고 싶으면07·08, 초기 자세·입력을 보고 싶으면09로 간다.
5. 특정 함수가 궁금하면 [11 클래스와 함수 찾아보기](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/11_클래스와함수찾기.md)에서 정의 위치로 이동한다.

각 해설에서 실제 소스 링크를 누르면 해당 파일·정의 행을 바로 열 수 있다. 함수의 모든 행을 그대로 옮기기보다 처리 순서·입출력·유지 상태·계산 의도·실수하기 쉬운 지점을 설명한다. 주요 함수에서 이해가 막힐 때 코드를 오가며 읽는 용도다.

## 문서 구성

| 해설 | 다루는 내용 |
| --- | --- |
| [00 전체 흐름과 읽는 방법](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/00_전체흐름과읽는방법.md) | 명령→행동→물리→보상→PPO→저장, 시간·자료 단위, 읽는 순서 |
| [01 실행과 학습](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md) | 진입점·설정·실행기·경험 수집 |
| [02 정책과 PPO](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/02_정책과PPO.md) | 인코더·손가락 출력·확률·가치·GAE·정책 갱신 |
| [03 저장과 로그](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/03_저장과로그.md) | 입력 SHA·JSON·전이·에피소드·저장본·자원·복구 |
| [04 GPU 환경과 종료](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/04_GPU환경과종료.md) | 공용 환경과 현재 자식 환경, 음별 원장·최종9보상·종료 |
| [05 물리장면과 제어](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/05_물리장면과제어.md) | GPU 장면·복원·충돌·목표각·PD·하체·좌표 변환 |
| [06 접촉과 손가락 보상](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/06_접촉과손가락보상.md) | 패드 표면·후면 엄지·오압현·목표 선택·대기·진단 |
| [07 곡과 목표 일정](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/07_곡과목표일정.md) | 전곡 목표·원시각/로컬 시각·악구 표본·손목 입력·단계 자료 |
| [08 악보 컴파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/08_악보컴파일.md) | 번들 출처·음 일정·운지·프렛·타현 목표 변환 |
| [09 초기 자세와 공통 기반](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/09_초기자세와공통기반.md) | 준비 상태·공통 제어/관측·과거 증거·내부 자산 경로 |
| [10 패키지 초기화 파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) | 실행 코드 없는8개 `__init__.py`의 역할 |
| [11 클래스와 함수 찾아보기](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/11_클래스와함수찾기.md) | 32파일의 정의533개와 실제 소스 행 링크 |
| [12 실제 첫 음으로 따라가기](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/12_실제첫음으로따라가기.md) | 현재 곡의 첫 목표에서 관측·행동·접촉·유지·로그까지 실제 값으로 추적 |

## 어떤 파일을 포함했는가

기본 진입점에서 `guitar_learning` 내부 import를 따라간 **정적 연결32개(구현24개·패키지 초기화8개)**를 빠짐없이 다룬다. 함수·조건문 안 import도 포함한다. 한 번의 학습에서 실행된 파일을 추적해서 센 수는 아니다. 정적으로 연결된 파일의 모든 함수가 기본60Hz 루프에서 실행되는 것도 아니다.

특히 공통 정책·악보 파일에는 현재 기본에서 사용하는 정의와 CPU·오른손·별도 song 경로에서 재사용하는 정의가 함께 있다. 해설은 이를 구분한다. 현재 기본은 J33 공동 학습·독립 탐색·K1·557상태이며, R/F 단계·정책 동결·상관 탐색·단계 이전·행동 유지 옵션은 삭제했다. 구간→전곡은 성공 관문 대신 계획 전이25% 이후의 reset에서 전환한다. 관측은 기존 왼손552+로컬 잔여시간1+손목 종료 타이머4이고, 정책 schema는 `guitar_learning.finger_skill_policy.v2`다. 이전 checkpoint는 지원하지 않으며 새 v3 학습 안에서 같은 소스·전체 계약의 엄격 재개를 사용한다.

학습 외부 라이브러리인 Isaac Gym·PyTorch·NumPy·SciPy 자체의 구현, 별도 평가·영상 도구, 과거 실험 전체는 이32개에 넣지 않았다. 소스 SHA의 입력 목록은 이보다 넓은 활성 Python281개 전체를 포함하므로, 체크포인트가 읽는 입력 수와 기본 경로 파일 수를 같은 숫자로 해석하지 않는다.

## 파일별 해설 대응표

| 현재 소스 | 상세 해설 |
| --- | --- |
| [__init__.py](/home/ajou/yigyu/3/guitar_learning/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [core/__init__.py](/home/ajou/yigyu/3/guitar_learning/core/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [core/control.py](/home/ajou/yigyu/3/guitar_learning/core/control.py:1) | [09_초기자세와공통기반](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/09_초기자세와공통기반.md) |
| [core/geometry.py](/home/ajou/yigyu/3/guitar_learning/core/geometry.py:1) | [09_초기자세와공통기반](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/09_초기자세와공통기반.md) |
| [gpu/__init__.py](/home/ajou/yigyu/3/guitar_learning/gpu/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [gpu/contact.py](/home/ajou/yigyu/3/guitar_learning/gpu/contact.py:1) | [06_접촉과손가락보상](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/06_접촉과손가락보상.md) |
| [gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:1) | [05_물리장면과제어](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/05_물리장면과제어.md) |
| [gpu/environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1) | [04_GPU환경과종료](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/04_GPU환경과종료.md) |
| [gpu/episode_diagnostics.py](/home/ajou/yigyu/3/guitar_learning/gpu/episode_diagnostics.py:1) | [06_접촉과손가락보상](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/06_접촉과손가락보상.md) |
| [gpu/finger_reward.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py:1) | [06_접촉과손가락보상](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/06_접촉과손가락보상.md) |
| [gpu/finger_skill_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:1) | [04_GPU환경과종료](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/04_GPU환경과종료.md) |
| [gpu/scene.py](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:1) | [05_물리장면과제어](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/05_물리장면과제어.md) |
| [historical_inputs.py](/home/ajou/yigyu/3/guitar_learning/historical_inputs.py:1) | [09_초기자세와공통기반](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/09_초기자세와공통기반.md) |
| [native/__init__.py](/home/ajou/yigyu/3/guitar_learning/native/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [native/paths.py](/home/ajou/yigyu/3/guitar_learning/native/paths.py:1) | [09_초기자세와공통기반](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/09_초기자세와공통기반.md) |
| [runtime/__init__.py](/home/ajou/yigyu/3/guitar_learning/runtime/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [runtime/prepared_reset_v1.py](/home/ajou/yigyu/3/guitar_learning/runtime/prepared_reset_v1.py:1) | [09_초기자세와공통기반](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/09_초기자세와공통기반.md) |
| [score/__init__.py](/home/ajou/yigyu/3/guitar_learning/score/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [score/canonical.py](/home/ajou/yigyu/3/guitar_learning/score/canonical.py:1) | [08_악보컴파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/08_악보컴파일.md) |
| [score/strike_goal_compiler.py](/home/ajou/yigyu/3/guitar_learning/score/strike_goal_compiler.py:1) | [08_악보컴파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/08_악보컴파일.md) |
| [song/__init__.py](/home/ajou/yigyu/3/guitar_learning/song/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [song/curriculum.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum.py:1) | [07_곡과목표일정](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/07_곡과목표일정.md) |
| [song/finger_phrases.py](/home/ajou/yigyu/3/guitar_learning/song/finger_phrases.py:1) | [07_곡과목표일정](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/07_곡과목표일정.md) |
| [song/task.py](/home/ajou/yigyu/3/guitar_learning/song/task.py:1) | [07_곡과목표일정](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/07_곡과목표일정.md) |
| [train.py](/home/ajou/yigyu/3/guitar_learning/train.py:1) | [01_실행과학습](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md) |
| [training/__init__.py](/home/ajou/yigyu/3/guitar_learning/training/__init__.py:1) | [10_패키지초기화파일](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/10_패키지초기화파일.md) |
| [training/finger_skill_runner.py](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py:1) | [01_실행과학습](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md) |
| [training/launch.py](/home/ajou/yigyu/3/guitar_learning/training/launch.py:1) | [01_실행과학습](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md) |
| [training/policy.py](/home/ajou/yigyu/3/guitar_learning/training/policy.py:1) | [02_정책과PPO](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/02_정책과PPO.md) |
| [training/ppo.py](/home/ajou/yigyu/3/guitar_learning/training/ppo.py:1) | [02_정책과PPO](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/02_정책과PPO.md) |
| [training/rollout.py](/home/ajou/yigyu/3/guitar_learning/training/rollout.py:1) | [01_실행과학습](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/01_실행과학습.md) |
| [training/training_log_io.py](/home/ajou/yigyu/3/guitar_learning/training/training_log_io.py:1) | [03_저장과로그](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/03_저장과로그.md) |

## 이미 알고 있어도 다시 확인할 개념

- **관절 목표각과 실제 관절각:** 정책 명령이 물리 결과를 즉시 덮어쓰는 것은 아니다.
- **접촉 후보와 압현 달성:** 한 프레임의 후보·하중, 연속 clean 유지, 음악 목표 달성은 서로 다른 판정이다.
- **H32와 에피소드 종료:** 수집 창이 끝나도 살아 있는 에피소드의 시계·접촉·누적 제어를 유지한다.
- **계획 전이25%와 실제 구간 비율:** 문턱을 넘은 뒤 reset하는 환경부터 전곡으로 넘어간다.
- **공용 부모 코드와 현재 총보상:** 자식 환경의 최종 선택·계수까지 확인해야 한다.
- **sampled와 committed:** 수집한 경험이 모두 모델에 반영됐다는 뜻은 아니다.
- **실행 완료와 음악 성공:** `completed`가 true인 것과 달성음이 많은 것은 다른 결과다.

작성 범위·작업 체크리스트는 [작성계획](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/작성계획.md), 파일별 해설 대응은 [문서대응표.json](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/문서대응표.json)에 남겼다. 검수와 문서 링크 검증 결과는 [검증결과](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/검증결과.md)에서 확인한다.


현재 해설은 J 전용화 후의24개 구현·533개 정의를 기준으로 갱신했다. 변경 전 R/F/J 소스와 해설은 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_joint_only_v3/manifest.json), 새 계약의 검사 결과는 [J 전용 정리 기록](/home/ajou/yigyu/3/docs/2026-10-28/guitar_joint_only_v3/README.md)를 따른다.


J 전용화 이전 원문·검사·해설·SHA는 [J 전용화 전 보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_joint_only_v3/manifest.json)에 보존했다. 현재 해설의 구현24개·초기화8개 구성은 유지된다.

현재 과거 전문 학습·실험193개 Python을 보관한 뒤 활성281개를 기준으로 SHA와 링크를 갱신했다. J 기본의32파일·533개 정의는 그대로다. 보관 범위·공용 초기화 분리·실행 검증은 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/README.md)를 따른다.

현재 해설은 가독성 정리 후 지역명과 코드 위치를 반영했다. 파일 수·533개 정의·학습 계약은 유지하며, 한 줄 복합문을 풀고 주요 흐름과 축·수명 설명을 코드 안에도 붙였다. [변경·검증 기록](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/README.md).
