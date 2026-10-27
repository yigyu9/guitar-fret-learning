# 기존 정책 없는 새 학습: 구현·소규모 실제 실행 검수

2026-10-14 change-reviewer 검수. 코드·기존 실행 원문은 수정하지 않고 이 검수 기록만 작성했다.

## 요약 판정

**문제없음. 미해결 Critical·Warning 없음.** 현재 검수 범위에서 64회 갱신×256 transition의 유한 Stage A 파일럿을 막는 정확성 결함은 발견하지 못했다. 이는 작은 손 이동 준비 과제의 실행 경로에 대한 판단이며, 압현·타현·음악 성공이나 안정성 보장은 아니다.

## 범위와 수정 확인

- 정책·학습: [policy.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/policy.py), [ppo.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/ppo.py), 두 CPU 테스트 모듈. 공유 인코더, support15/fret33/strike6 Actor, 보상·비용 Critic을 확인했다. 옛 정책 가중치·IK·고정 타현의 행동 덮어쓰기 경로는 새 제어 경로에서 발견하지 못했다.
- 실제 검증본: [environment_v2.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/environment_v2.py), [run_v2.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/run_v2.py), launch_v2.sh. v1의 초기화 실패는 [실패 보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/baseline_v1/report.json)에 보존되었다. v2는 이전 형상의 관성을 그대로 비교하던 검사를 수정하여, OM 형상의 COM을 유지하고 가져온 관성을 요청 질량/가져온 질량 비율로 조정한 뒤 요청값과 native readback을 대조한다. 기존 left_near_scene_v3의 질량 처리와 정합하며 양의 유한 관성도 검사한다.
- 다음 실행본: [run_v3.py](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/run_v3.py), [launch_v3.sh](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/launch_v3.sh). v2 대비 native 물성·PD 설정 저장과 종료 에피소드의 초기값 기록을 추가했다. 물리·행동·보상·PPO 변경은 없다. v3 자체의 장기 실행은 본 검수에 포함되지 않는다.
- 앞서 발견한 영상/seed를 포함한 전체 메타데이터 비교 문제는 고정 ABI와 에피소드 초기값을 분리하여 해결했다. 사용하지 않던 비용 한도 필드도 제거했다. 현재 방식은 비용 계수 1의 고정 패널티이며 제약 충족을 보장하는 알고리즘은 아니다.

## 검증 근거

- CPU 테스트 6개 통과: 정책 출력·유한 log probability, 실제 종료/시간 제한/rollout 경계 GAE, Actor와 두 Critic 갱신, RNG·Adam·가중치 복원, 기존 스키마 거부, 54개 행동 분할·양끝 매핑·나머지27개 보존. v2 환경·runner 및 v3 runner의 AST, v2/v3 launcher의 shell 문법도 확인했다.
- 현재 contract를 사용한 별도 CPU 대조에서 54개 인덱스는 중복이 없고 전 행동 범위가 양수였다. 0 행동은 초기 목표를 보존하며 ±1 행동은 각 소유 채널을 바꾸고 나머지27개 목표를 보존했다.
- [기준 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/baseline_v2/report.json): seed9001, 300 control/1200 physics step, 5초 시간 제한 완료. 최대 초기 기타 actor-root 이동 15.200773mm, 회전 4.408002°, 비용 합계 0.
- [짧은 새 학습](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/smoke_v2/report.json): seed101, CUDA 정책·최적화와 CPU PhysX, 2갱신/512 control, 가중치 최대 절대 변화 0.0021030903. 매 제어에서 53~54개 목표가 변했고 raw 전이의 나머지27개 목표 및 최종 목표와 노력 제어기 입력의 일치를 확인했다. 최대 기타 이동 19.268939mm, 회전 5.618647°, 비용 합계 0.
- [학습 체크포인트 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/smoke_eval_v2/report.json): 학습 seed와 다른 seed9001, checkpoint2를 로드하여 300 control/1200 physics step과 5초를 완료했다. 그래픽 -1 학습에서 그래픽0 영상 평가로 로드할 때 ABI 오류가 없었다. 최대 기타 이동 15.200652mm, 회전 4.413352°, 비용 합계 0.
- 세 v2 실행의 보고에 실패·입력 변경·금지 API 호출이 없었다. 검수 시 각 attempt의 입력 1274/1275개 SHA와 source_before의 Python 원문 933개 SHA를 재대조하여 불일치 0개를 확인했다. 실제 제어의 고정 하체·native POSITION readback·관절속도·노력 권한 검사가 오류 없이 통과했다.
- 기준 실행과 체크포인트 평가의 전신·손 영상은 각각 151프레임, 30fps, 5.033333초다. capture는 물리 step0~1200을 포함하며 전 프레임에서 렌더 전후 상태 보존, 저장 PNG 및 MP4 SHA 일치를 확인했다. 체크포인트 평가의 종료 전신·손 PNG도 직접 확인했다.

## 결과 해석의 한계

- 목표는 t=0의 기타 상대 손바닥 위치에서 반경 3mm로 생성된다. 정착 후 손바닥 기준과 별도로 재설정하지 않는다. seed9001 기준 실행의 종료 RMS 위치 오차는 약21.09mm였으므로 이를 3mm 추종 성공으로 설명할 수 없다.
- 이번 실제 전이의 비용은 모두 0이다. 두 Critic의 구현·갱신은 CPU 및 실제 optimizer 실행으로 확인했으나, 실제 비영 비용에 대한 학습 효과나 경계 준수 성능은 검증하지 않았다.
- 첫 smoke 갱신의 근사 KL은 0.0410334로 설정값 0.03을 넘었다. 현재 target_kl은 epoch 이후 다음 epoch를 중단하는 기준이다. rollback이나 매 갱신 KL 상한 보장으로 설명하지 않는다.
- 작은 단일 목표 평가와 2갱신은 정책 학습 경로 검증이다. 성능 향상·강건성·음악 성공을 입증하는 비교 실험으로 사용하지 않는다. 물리 상태의 연속 재개가 아닌 새로운 물리 에피소드에서 체크포인트를 평가했다.

## 검수 시 핵심 소스 SHA256

| 파일 | SHA256 |
|---|---|
| environment_v2.py | e18907d5d36e443c5bcf50e461edd8e69cf55a15f508957dd25aaabfafd845d1 |
| run_v3.py | 5c32477c14f8f6af75c32d77e7ae00bf86b93541358f0704e327e8b08d13eb14 |
| launch_v3.sh | 94890e7d460b251e47e5d40de3d08c87fb76df183a2f8b66fe538cad4146cab5 |
| policy.py | b6259a70a4b238d6a2120de787d3500c7e3b8d34200932e0f4d87f071f73f85b |
| ppo.py | d1bda98797479773d6ad2f1087bd8cda72975b384b0027d9b13d1e4cde8b60ad |

v3는 이 기록의 링크가 가리키는 파일과 v2 대비 위 기록 추가 차분을 검수했으며, 실제 실행 봉인·사후 불변 감사는 실행 담당자의 별도 범위다.
