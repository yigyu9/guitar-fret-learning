# 동일한 JSON 계약 표기를 보존하는 학습 실행 경로

기존 `transition_refinement`의 물리·관측·보상·정책·PPO를 변경하지 않는 실행 어댑터다. 이전 코드와 실행은 보존했다.

첫 어댑터의17유효숫자 표기는 읽은 float64 값은 보존했지만 기존 canonical JSON의 SHA와 달라 과거 BC의 정상 증거 검증에서 거절됐다. 이 버전은 설치된 NumPy의 Dragon4 shortest formatter로 Python 기본 JSON과 동일한 숫자 표기까지 보존한다. 경계값·임의 float64·실제 계약의 JSON 문자열과 SHA, 원 BC 증거 전체 검증으로 확인한다. 파서는 정수 비율을 사용하며 문제의 CPython dtoa/strtod 경로를 피한다.

FP 제어 상태는 변경하지 않는다. C 관찰기는 fnstcw/fnstsw/stmxcsr로 읽기만 한다. JSON 호출 전후 예외 마스크·rounding·FTZ/DAZ가 지원 조건과 다르면 실패로 종료한다. 지원 조건은 round-to-nearest·FTZ/DAZ OFF다. 비정상 상태를 초기화하거나 예외를 숨기지 않으며 근본 원인을 해결했다는 뜻도 아니다. 원본 자료·모델·물리 감사와 유한값 검사를 그대로 유지한다.

부모와 각 spawn worker에서 동일한 경로를 사용하고 종료 시 원 JSON API를 복원한다. 초기 성공4회는 native 감사뿐 아니라 정상 종료·오류 없음·관찰 횟수를 증명하는 별도 runtime 감사도 검증·SHA 고정한다. 학습 종료도 모든 worker의 별도 감사가 통과해야 완료로 보고한다.

관찰 C소스와 빌드된 공유라이브러리도 실행 입력으로 고정한다. Linux x86_64 빌드 명령:

```bash
gcc -shared -fPIC -O2 -Wall -Wextra -Werror \
  guitar_learning/tool/experiments/transition_refinement_runtime_v2/fpu_state.c \
  -o guitar_learning/tool/experiments/transition_refinement_runtime_v2/fpu_state.so
```

Isaac을 NumPy·Torch보다 먼저 불러오는 진입점이다. 기존 설정 형식을 사용하고 항상 새 출력 경로를 지정한다.

```bash
python -m guitar_learning.tool.experiments.transition_refinement_runtime_v2.run eval \
  --settings /absolute/settings.json --out /absolute/new_evaluation

python -m guitar_learning.tool.experiments.transition_refinement_runtime_v2.run train \
  --settings /absolute/settings.json --out /absolute/new_training
```

실제 장기 실행과 결과: `docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_long_v1/`. 이전 어댑터·기존 실패를 보존하며 새 어댑터의 존재 자체를 학습 성공으로 설명하지 않는다.
