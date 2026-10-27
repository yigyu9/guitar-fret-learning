# 이전 버전 보관

현재 개발 코드는 [상위 디렉토리](/home/ajou/yigyu/3/guitar_learning/README.md)에 있다. 새 버전을 만들 때 이전 코드·검사·관련 문서를 날짜와 작업명별로 먼저 보관한다.

- [20261018_before_archive_cleanup](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_archive_cleanup): 정리 직전 패키지의 28개 파일을 그대로 보존한 snapshot. 이전 22초 환경/실행기와 해당 검사도 이곳에 있다. archive_manifest.json에 원래 경로와 SHA가 있다.
- [20261018_before_training_interface](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_training_interface): 관측·음악·보상·네트워크/PPO 연결 전24파일의 원형과SHA. 당시 환경 진입점/README/검사를 보존한다. 현재 대체 구현과 사용법은 상위 TRAINING.md에 있다.
- [20261018_before_training_validation](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_training_validation): 기본 행동 범위 검증 전42파일의 원형과SHA. 검증기와 검사를 새로 추가했고 기존 학습/환경 코드는 유지했다.
- [20261018_before_parallel_tuning](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_parallel_tuning): 병렬 학습 구현 전44파일의 원형과SHA. 기존 환경·정책·PPO는 유지하고 pool/headless/runner/검사를 추가했다.
- [20261018_before_cuda_collection_timing](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_cuda_collection_timing): CUDA 수집 시간 동기화 개정 전runner·검사·관련 문서4파일. CPU 환경 수 비교는 이 runner, GPU pilot은 개정 runner를 사용했으며 변경은 수집 종료 전 동기화뿐이다.
- [initial_implementation](/home/ajou/yigyu/3/guitar_learning/archive/initial_implementation): 더 과거의 단계별 구현·실패·수정 버전이 있는 원 디렉토리로 연결한다.

보관본은 당시 경로를 전제로 한 원형이다. archive 안에서 직접 실행하지 않고, 재현이 필요하면 별도 작업 공간에 원래 상대 경로 구조로 복원한다. 과거 실제 실행의 입력/원자료/영상은 기존 docs 결과 경로에 그대로 있다. 현행 코드에서 archive 모듈을 import하지 않는다.
