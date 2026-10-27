# 기본 학습과 전문 도구 분리

2026-10-20. 기본 실행은 `python -m guitar_learning.train --hand left/right --out NEW`로 유지한다. 공용 환경·정책·PPO·기록을 메인 구현으로 남기고, 부가 실행·전문 실험을 tool/ 아래로 모았다.

- 전문 패키지8개: `tool/experiments/` (song의 task 계약 파일은 기존 경로 유지).
- 전문 학습11개·평가4개·시연2개: `tool/training/`, `tool/evaluation/`, `tool/demonstration/`.
- 검증 전용 환경·단일 수집기: `tool/validation/`. 기존 설정12개: `tool/training/configs/`.
- 공용 runner: `training/runner.py`. 공용 worker/logger: `quality/runtime.py`, `timing/recording.py`.
- 재수출만 하던 루트 environment.py는 보관본을 남긴 뒤 제거했다.

[사용 안내](/home/ajou/yigyu/3/guitar_learning/README.md), [도구 안내](/home/ajou/yigyu/3/guitar_learning/tool/README.md), [공용 구현 유지 이유](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md), [385개 파일별 검토](file_review.md), [상세 정의·참조](file_review.json), [이동표](move_map.json), [변경 전 전수 목록](inventory_before.json), [현재 전수 목록](inventory_after.json).

## 파일별 판단

변경 전 Python385개 전부의 정의·정적 참조·용도를 기록했다. Python107개를 포함한140개 파일을 이동했으며 기본 학습은 전문 도구를 import하지 않는다. 공용 라이브러리는 환경/관측/보상/정책/수집/기록과 여러 전문 도구에서 공유하는 입력 검증·명시적 Actor 이전을 포함한다. 기본 train의 보수적 정적 import closure114개에는 tool이 없지만 함수 내부의 미실행 import도 포함하므로 실행 최소 파일 수로 해석하지 않는다.

| Python 범위 | 변경 전 | 변경 후 |
|---|---:|---:|
| 메인·공용 구현 | 245 | 141 |
| 선택 실행 도구·지원 구현 | 17 | 128 |
| 검사·fixture | 123 | 124 |
| 합계 | 385 | 393 |

공용 함수 분리2개·패키지 초기화6개·검사1개를 추가하고 재수출 facade1개를 제거해 전체 수는8개 늘었다. 기본 구현과 선택 도구의 경계를 만드는 정리이며 기능 삭제로 파일 수만 줄이지 않았다. native의 버전별 구현은 실제 import 사슬에서 재사용하므로 보존했다. 8줄 이상 최상위 함수 중 AST가 같은 두 묶음은 CLI main 본문이며 서로 다른 전역 파서/run에 연결되므로 동일 동작이라고 판단해 합치지 않았다.

song/task.py와 music_task.py는 checkpoint task provenance에 실제 경로·SHA·크기가 들어가므로 원문도 그대로 유지했다. 과거 단일 checkpoint 이전 도구의 고정 경로/SHA/byte 조건도 바꾸지 않았다. 루트 environment.py의 유일한 probe는 실제 구현을 직접 사용한다. 검증 전용 압현 환경과 단일 rollout 기준 구현은 tool/validation에서 계속 검사한다.

## 검사와 실제 실행

[최종 회귀 결과](module_tests_final.json):121개 검사 모듈·692개 검사 모두 통과. 각 모듈을 별도 프로세스로 실행한 결과이며 단일 프로세스 discover 전체 통과와 구분한다. [초기 결과](module_tests_summary.json)의 두 실패는 이동한 모듈의 embedded script 경로를 수정하고, 단독 실행에서 sys.modules 복원 뒤 남는 package 속성 때문에 생긴 fixture 순서 의존성을 의존 모듈 선로딩으로 해결한 뒤 재검사했다. assertion이나 제품 검증을 완화하지 않았다. 이와 별도로 초기 관련 검사 로그의 옛 경로 잔존도 수정했으며 원로그는 남겼다.

[CLI 확인](cli_help.json):54개 도구의 --help를 프로젝트 밖 /tmp에서 실행해 모두 통과했다. [독립 검수](review.md)는 추가 지적0건이다. [종합 검증](verification.json)은393개 소스 SHA, 현재 import·문서 링크, 과거 원문·보관본·자산 출처를 확인한다.

실제 native 실행은 CPU정책·small모델·1추가 PPO업데이트로 수행했다.

| 실행 | 환경 수 | 수집 전이 | 최종 PPO 업데이트 | 완주 episode / 음악 성공 | 결과 |
|---|---:|---:|---:|---:|---|
| [왼손 새 학습](native_left_v1/report.json) | 2 | 840 | 1 | 2 / 0 | 저장·입력 SHA·persistent·물리 조건 통과 |
| [오른손 새 학습](native_right_v1/report.json) | 1 | 420 | 1 | 1 / 0 | 저장·입력 SHA·persistent·물리 조건 통과 |
| [정리 전 모델 재개](native_resume_v1/report.json) | 1 | 20 | 2 | 0 / 0 | strict load 후1회 추가; 부분 episode를 완주로 세지 않음 |

[재개 비교](resume_parity.json): 정리 전 final.pt와 새 경로의 initial.pt는 metadata를 제외한 identity·model·양 optimizer·cost_weight·업데이트 수·Torch/NumPy/Python/CUDA RNG 전체가 정확히 같다. 최종 업데이트는1→2다. 모든 reset의 native 준비시간/실제 물리 step은0이며 원 snapshot step5280이다. 수집 연결·저장·호환성을 검증한 결과이며 음악 수렴을 의미하지 않는다.

이전 작업의 단일 프로세스 전체 discover에서 발생한 JSON/float 표현 SIGFPE는 이번 이동으로 수정했다고 주장하지 않는다. 이번에는 전체 모듈을 각각 실행했으며 단일 프로세스 discover는 반복하지 않았다. 물리·JSON backend·FPU mask·보상·PPO·strict checkpoint 검증을 변경하지 않았다.

## 원본과 경로 보존

변경 전 소스·검사·문서·설정·CAS index449개를 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_main_tools/manifest.json)에 기록하고 전부 원래 경로/SHA로 CAS에 등록했다. 기존2,220개 version/default metadata를 그대로 유지했고, 현재 CAS2,391개 object의 바이트 해시와 참조를 검사했다. 이전 결과·로그·checkpoint는 수정하지 않았다.

native provenance190개 원문은 그대로다. tool provenance18개는 바뀐 probe import와 안내의 현재 SHA를 갱신했고 원본 SHA는 유지했다. origin_manifest의 이전 루트 경로를 가리키던 현재 포인터4개도 실제 공용 구현 경로로 맞췄으며 original/organized SHA는 보존했다. 현재 문서·설정·하위 프로세스·worker는 새 경로를 사용한다. 과거 증거의 식별 경로와 schema 문자열은 변경하지 않았다.
