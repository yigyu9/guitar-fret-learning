# 오른손 피크 타현 환경

2026-11-03. 기존 물리·제어·오른손 정책·PPO를 재사용해 단일 타현 환경과 진단 경로를 구성했다. 실행 코드는 guitar_learning, 입력은 data, 모델·원시 로그·촬영 원본은 runs에 둔다. 이 디렉토리는 결과·분석·대표 영상만 보관한다.

## 구현 위치

| 역할 | 코드 |
|---|---|
| 오른손 환경·품질 원장 | [right_strike_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/right_strike_environment.py) |
| 목표 생성·검증 | [prepare.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/prepare.py) |
| 신경망·학습 설정 | [settings.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/settings.py) |
| 기존 PPO 연결 | [runner.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/runner.py) |
| 실제 제어·촬영·정책 평가 | [native_probe.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/native_probe.py), [evaluate.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/evaluate.py) |
| GPU 유휴·입력 동일성 검사 | [runtime.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/runtime.py) |
| 실제 도착 상태의 기하 후보 | [geometry.py](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike/geometry.py) |
| 저장 형식 보정 | [right_strike_io_v2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike_io_v2) |
| 교차 시간 비교 | [right_strike_protocol_v3](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right_strike_protocol_v3) |

과거 버전은 봉인 상태로 보존했다. IOv2는 도착 계약의 NumPy 값을 JSON으로 저장하는 처리만 분리 수정했다. protocol_v3는 제어기·판정을 유지하고 교차 시간만 별도 조건으로 비교한다.

## 목표와 성공 기준

표준3번 줄(runtime2), down(+1), 시각3초의 타현1회, 전체5초다. 기존 공용 곡 컴파일러 입력 형식을 유지하기 위한 명목6프렛/검지 표기는 왼손 압현이나 음고 성공의 근거가 아니다. 새 품질 성공은 왼손 clean을 요구하지 않는다.

기존 피크 그립·오른팔꿈치/손목6축, PD·힘·가동범위·물리·원래 타현 깊이/속도/시간/zone/재무장을 유지한다. 원래 관측·보상·stage_success는 보존하고, 별도 right_strike_quality에서 준비2관측→정확한 유효타현1회→이후 분리2관측·완주 안전·오타현/중복0을 요구한다. 기하적으로 지나갔어도 속도·깊이 등이 맞지 않는 원시 교차는 유효 타현과 분리한다.

기존 strict50/100 음악 지표는 왼손 clean과 결합돼 있으므로 오른손 단독 품질과 별도로 보고한다. 성공 범위는 피크 표식·현 선분의 기하 통과이며 개별 현 변형·압력·진동·소리 측정이 아니다. 오른손 손가락으로 뜯는 제어는 포함하지 않는다.

## 입력과 실행 결과 위치

- 입력: `/home/ajou/yigyu/3/data/diagnostic_inputs/right_strike_v1`
- 봉인 명세: 같은 상위 디렉토리의 `right_strike_execution_v1.json`, `right_strike_execution_io_v2.json` 및 후속 조건 명세.
- 원시 기록·모델: `/home/ajou/yigyu/3/runs/right_strike_v1/`
- [독립 검토](분석/독립검토.md)
- [구현·검증 결과](분석/환경구성결과.md)

기존 압현 실험·봉인 소스·입력·모델은 변경하거나 이동하지 않는다. 새 모듈만 추가했다. 다른 GPU 작업은 중단하지 않고 유휴 시점에만 새 진단을 실행한다.
