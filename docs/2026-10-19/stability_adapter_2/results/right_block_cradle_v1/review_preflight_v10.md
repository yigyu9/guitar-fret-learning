# Thorax 30N/12mm 사전 검수

요약 판정: **문제없음 — 제한된 5초 진단의 실행 차단 없음.** Critical 0건, Warning 2건, Suggestion 0건. 새 물리 실행이나 이전 원자료 전체 재감사는 하지 않았다.

이전 버전과 대조한 변경은 Thorax 가상점의 안쪽 목표 오프셋 8→12mm와 요청 상한 20→30N이다. Shoulder 4mm/10N, 초기 상태·물성, 몸통 외부 PD 150/1, 33 EFFORT/48 POSITION, 현재 기타 점·속도 계산, 관절 한계와 단일 81 제출 및 상태 가드는 유지된다. 새 Python 3파일 AST 검사를 통과했다. 설정은 [static_Thorax30.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/config_v1/static_Thorax30.json:31), 실행 연결은 [runner](/home/ajou/yigyu/3/stability_adapter_2/run_right_block_cradle_v8.py:15)에서 확인했다.

## Warning

- [right_block_effort_v5.py:32](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v5.py:32), [같은 파일:52](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v5.py:52): 12mm는 인간 모터점의 희망 오프셋이고 30N은 가상점 요청 상한이다. 실제 관통깊이·접촉력으로 해석하지 않아야 한다. 깊이와 상한을 함께 변경했으며 이전 종료 요청 17.113N은 기존 상한 20N 미만이므로 상한 부족이라는 원인을 확정할 수 없다. 계획의 개별 인과효과 미분리 설명을 유지한다.
- [계획 V8:5](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_NATIVE_PLAN_V8.md:5), [같은 문서:7](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_NATIVE_PLAN_V8.md:7): 법선 차이 28.88°인 같은 측면의 근접점은 수동 잠금이나 완전한 force closure를 증명하지 않는다. 실제 두 부위의 동시 접촉, 근위 구간, 몸통 실제각 및 동일 조건 팔꿈치 동작을 확인해야 한다. 허벅지·왼손 접촉의 힘/모멘트 기여는 분리 측정되지 않았으며 연주나 반복 강건성 인증으로 확대하지 않는다.

## 검수 시 SHA-256

| 파일 | SHA-256 |
|---|---|
| RIGHT_BLOCK_CRADLE_NATIVE_PLAN_V8.md | d27b32712e8c26b139e8c86d01859ba46e175d880176ea970d51fe3393ee8ac9 |
| right_block_effort_v5.py | 28731672b1b61dd1fd60aad22b4dd1d347056196646d796a755972ac3ac5ca6c |
| right_block_body_effort_v4.py | 7a88b3abc3f3e3744e056aad3002f56e78300490b09374e9f0ca28a9f62eca6c |
| run_right_block_cradle_v8.py | 556ea7b13b38c47ad628c95d3ab3e60905e9a264f4f2e3557e3d0dcf6617e631 |
| static_Thorax30.json | c41d6871370b73553eb0cf7a5a34aaa03c2c4b069416aaff36b419864876df4a |

위 판정은 읽기 전용 코드·계획·설정 대조에 한정한다. 새 조건의 native 결과와 최종 보존 봉인은 이 사전 검수의 인증 대상이 아니다. 다른 소스·결과·기존 리뷰는 수정하지 않았다.
