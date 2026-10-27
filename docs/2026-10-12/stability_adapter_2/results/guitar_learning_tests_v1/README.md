# guitar_learning 테스트 하위 디렉토리 정리

사용자 요청에 따라 테스트 파일 7개를 [guitar_learning/tests](/home/ajou/yigyu/3/guitar_learning/tests)로 이동했다. 테스트 간 import는 유지하고, 실행 모듈 import와 프로젝트 자산 경로를 한 단계 깊어진 위치에 맞췄다. 실행 코드 자체는 변경하지 않았다. 과거 코드와 이전 작업의 snapshot/로그는 보존했다.

프로젝트 루트에서 다음 명령으로 CPU 검사 40개를 모두 통과했다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -m unittest discover -s guitar_learning/tests -t . -v
```

[실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_tests_v1/checks.json) · [전체 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_tests_v1/tests.log). README와 원본 대응표를 갱신하고, 이후 테스트도 tests/에 작성하도록 작업 기준에 기록했다. 새 물리 실행과 PPO 업데이트는 0이다.
