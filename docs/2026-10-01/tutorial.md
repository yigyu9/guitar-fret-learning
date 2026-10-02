나중에 GPU 서버에서 명령 몇 개로 바로 확인할 수 있게 Isaac 확인 스크립트 [strap_chain_isaac_check.py](tab2body/tools/strap_chain_isaac_check.py)를 추가로 만들어 두었습니다. 다만 이 스크립트도 이 맥에서는 문법 검사만 했고 **한 번도 실행하지 못했습니다.** 처음 돌릴 때 에러가 나면 로그를 가져와 주세요.

## 0. 서버로 코드 옮기기
지금 변경 사항은 **커밋하지 않은 상태**입니다. 서버에서 쓰려면 커밋하고 push한 뒤 서버에서 pull해야 합니다. 원하시면 브랜치를 따로 만들어 커밋해 드리겠습니다.

## 1. 서버 환경 준비
[tab2body/README.md](tab2body/README.md)에 적힌 방식 그대로입니다.
```bash
cd /path/to/레포
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR="/tmp/torch_extensions_tab2body"
```

## 2. 확인 순서
```bash
# (1) CPU 테스트: Isaac 없이 스트랩 계산만 검사 (약 20초)
python tab2body/tests/test_strap_chain.py

# (2) Isaac 확인: env 1개, 4초, 영상 포함
python -m tab2body.tools.strap_chain_isaac_check

# (3) 대조 실험: 스트랩 없이 자유 기타 (기타가 떨어지거나 미끄러져야 정상)
python -m tab2body.tools.strap_chain_isaac_check --no-strap --out tab2body/_gen/diagnostics/strap_none

# (4) 속도 측정: 학습 규모 env 4096개, 영상 없이
python -m tab2body.tools.strap_chain_isaac_check --num-envs 4096 --no-video --seconds 2 --out tab2body/_gen/diagnostics/strap_bench
```
(2)에서는 몸은 앉은 자세로 고정되고, 기타만 풀린 상태로 스트랩과 허벅지·손 위에 놓입니다.

## 3. 결과 위치
`tab2body/_gen/diagnostics/strap_chain_check/` (git에서 무시되는 폴더)
- `report.json`: 수치와 자동 검사 결과. 하나라도 실패하면 종료 코드가 1입니다.
- `final_front.png`, `final_side.png`: 정면·측면 최종 장면. 스트랩은 주황선으로 겹쳐 그려집니다.
- `strap_front.mp4`, `strap_side.mp4`: 영상 (서버에 ffmpeg가 있을 때만)

**자동 검사 항목**
- NaN 없음
- 기타 처짐 5cm 이내
- 마지막 0.5초 흔들림 2mm 이내
- 스트랩 관통 5mm 이내
- 스트랩이 실제로 하중을 받음

## 4. 가져오실 것
- 각 실행의 터미널 출력 (특히 에러가 나면 전체 traceback)
- (2)의 `report.json`, `final_front.png`, `final_side.png`
- (4)의 `step_ms_median` (스텝당 걸린 시간)

이 실행 방법은 [env/README.md §6.7](tab2body/env/README.md)에도 적어 두었습니다.