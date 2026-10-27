# 최종 환경 연결 사전 검수

**판정: 문제없음 — environment_v3 + run_smoke_v6의 제한된 native smoke 진행 가능.** 실제 준비 자세와 행동 연결의 물리 결과는 후속 시험으로 판정한다. 검수자는 native/GPU/물리 실행을 하지 않았다.

이 문서는 이전 `environment_preflight_v1.md`의 run_smoke_v4 실행 차단 및 메타데이터 경고에 대한 수정 확인이다. 이전 기록은 보존했다.

- runner v6의 `bridge_dependency`는 이번 새 bridge와 재사용 CPU codec 두 패키지를 원 native expected SHA 대상에서 분리한다. 이 파일들도 실행 전 pin과 실행 후 불변/실제 import 검사를 받는다. 원 runtime과 model assets는 원 manifest expected SHA 검사를 계속 적용한다.
- env v3의 제어 경로는 v2와 동일하다. codec 메타데이터를 deepcopy한 환경 설명에서만 finite lower24 역할을 명시하며 원 codec은 변경하지 않는다.
- 초기0초/준비22초 실제 상태, 원 baseline과 행동0의 별도 실험 범위, 인코딩 실패 기록 및 입력 SHA 검사는 유지된다.
- 준비 최종 목표 기준39 행동, upper42 유지, lower24 원 유지 제어, 단일 최종 목표 제출/원 effort 사용, 105/97/8 및 자유 기타 계약에 새 변경은 없다.

독립 CPU 검사: `PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -m unittest stability_adapter_2.free_guitar_learning_v1.test_environment_v3 -v` → **8 tests, OK**. 실제 `.environment_v3` import 확인. CPU fake-session 검사이며 native 재현 성공을 주장하지 않는다.

| 최종 파일 | 검수 SHA256 |
| --- | --- |
| environment_v3.py | `124f3556ffece4f3416973e50d34b5b6517fb3e17c3261474a125282ff35d4f7` |
| test_environment_v3.py | `8f10691eb90ea220cebfd48e6738e87e2e0f3de8dbff2ccc1dfedf52778f883e` |
| run_smoke_v6.py | `566e94294a1ac54c5069e7ad5b40913651ffb88fca552e70c337ad4489352090` |

남은 검증: 실제 두 독립 초기화의 설정/준비 상태, 행동0 및 작은 비영행동에서 목표·effort 소유권과 금지 호출, 자유 기타의 상태, 실제 native 입력/코드 불변성. 음악 보상·타현/압현 성공·PPO·장기 안정성은 이 검수의 범위가 아니다.
