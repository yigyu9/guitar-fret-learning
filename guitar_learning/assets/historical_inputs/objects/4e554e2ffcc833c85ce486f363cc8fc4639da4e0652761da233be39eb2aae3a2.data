# 보완 학습의 수치 기록 실행 경로

기존 `transition_refinement`의 환경·보상·정책·PPO를 그대로 실행하는 별도 어댑터다. 기존 동결 소스·모델·결과는 수정하지 않는다.

기존 실행은 JSON 실수 기록 중 CPython `format_float_short`에서 간헐적으로 SIGFPE가 발생했다. 이 경로는 Decimal의17유효숫자 표현과 정수 비율 파서를 사용해 실수 값의 float64 왕복 동일성을 보존하면서 해당 JSON 실수 포맷 함수를 피한다. JSON 숫자의 글자 표기는 달라질 수 있으나 읽은 실수의 비트 값은 같아야 한다. 문자열로 바뀌는 float 사전 키는 조용히 변환하지 않고 거절한다. 현재 프로젝트 원자료의 객체 키는 문자열이다.

오류의 근본 원인을 해결했다고 주장하지 않는다. FP 제어·예외 마스크·플래그를 초기화하거나 수정하지 않는다. `fpu_state.c`는 fnstcw/fnstsw/stmxcsr로 읽기만 하며, 각 JSON 호출 전후 예외 마스크의 비정상 상태를 발견하면 실패로 종료한다. 비표준 rounding 및 FTZ/DAZ도 거절하며 원 상태를 바꾸지 않는다. 비트 왕복 검증은 round-to-nearest·FTZ/DAZ OFF 조건이다. 전체 실행을 연속 관찰하는 장치는 아니며 기록 함수 밖의 SIGFPE도 여전히 정상 실패로 남긴다. NaN/Infinity 거절과 기존 물리·원자료 감사는 유지한다.

부모와 각 spawn worker에 같은 기록 경로를 설치한다. 초기화와 종료 시 원 JSON API를 복원하며 관찰 횟수·제어값·이상 유무를 `*_runtime_json_audit.json` 또는 worker의 `runtime_json_audit.json`에 남긴다. 새 네이티브 증거에는 어댑터 Python파일과 관찰 C소스/공유라이브러리의 SHA도 포함한다. 이전 경로의 성공을 새 어댑터의 성공 증거로 상속하지 않는다.

관찰 라이브러리는 이 프로젝트의 Linux x86_64 환경용이다. 생성 명령:

```bash
gcc -shared -fPIC -O2 -Wall -Wextra -Werror \
  guitar_learning/transition_refinement_runtime/fpu_state.c \
  -o guitar_learning/transition_refinement_runtime/fpu_state.so
```

실행은 Isaac을 Torch/NumPy보다 먼저 불러온다. 기존 설정 형식을 사용하며 항상 새로운 출력 경로를 지정한다.

```bash
python -m guitar_learning.transition_refinement_runtime.run eval \
  --settings /absolute/settings.json --out /absolute/new_evaluation

python -m guitar_learning.transition_refinement_runtime.run train \
  --settings /absolute/settings.json --out /absolute/new_training
```

장기 학습의 실제 설정·검사·결과는 `docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/`에 기록한다. 이 어댑터의 존재 자체가 실제 실행 성공을 뜻하지 않는다.
