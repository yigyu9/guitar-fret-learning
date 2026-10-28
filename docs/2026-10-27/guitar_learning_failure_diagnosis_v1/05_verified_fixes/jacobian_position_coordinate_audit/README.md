# 위치·속도 Jacobian 좌표 감사 — CPU 준비

원본 검지 reference 영상만 CPU에서 독립 재계산했다. qpos→FK pose가 맞아도 같은 위치 Jacobian에 native qd를 곱한 결과는 실제 손목 속도와 크게 다르다. 원인은 아직 확정하지 않는다. 동시 native Jacobian 자료를 얻는 단1조건 관찰 도구가 포함돼 있다. GPU는 root만 후속 인계 후 실행한다. 사용자에게 새 승인을 요청하는 절차가 아니다.

| 영상 endpoint(s) | qpos-J×native qd 선형오차(m/s) | qpos-J×중앙 qpos차분 오차(m/s) | 각속도오차 native/중앙(rad/s) | qpos-J DLS와 저장 delta 최대차(°) |
|---|---:|---:|---:|---:|
| 2.00 | .36925 | .01095 | 1.49419 / .11294 | .44572 |
| 2.50 | .43572 | .01568 | 1.80407 / .11834 | .52226 |
| 3.00 | .11693 | .01556 | .66126 / .09552 | 1.00000 |
| 3.25 | .13830 | .04808 | .93584 / .28891 | 1.00000 |

105열의 위치 유한차분은 float64 q±1e−5, world angular derivative는 `Rp*Rm.inv()`다. 손목 실속도는 native COM 속도를 원점으로 보정했다. qpos 중앙차분은 앞뒤60Hz 표본의 시간 평균 근사다. 시간 미분·접촉 과도·좌표 frame 가능성을 분리해야 한다. 원본에는t=0행이 없으며 첫 행은control1 끝이다. clock476/596/716/776의 q/body와 다음 row의 goal로 저장 pose error가 최대1.884e−8 이내 재현돼 precontrol 정합은 확인됐다. 상세 수치와 source SHA는 `cpu_evidence.json`에 있다. local spherical example의 nonzero quaternion→Exp roundtrip만 AST로 실행했고 simulator 예제는 import하지 않았다. 이 position 예제는 설치 Preview4 velocity 좌표의 증거가 아니다.

`child.py`는 원래 strict evaluator/ShortPool을 그대로 호출하며 네 startclock에서 q/qd/target/body/native humanJ/COM/action·실패·reset·first mask만 복사한다. humanJ는4환경×65body×6×105, 네 시점 전체 uncompressed4MB 미만이다. 같은 시점의 행/열/COM/world frame 비교를 위한 자료이며 native state/행동/target/solver/PD/gain/판정/보상 변경은 없다. 원래4환경 첫시도 분모·221control 상한·4substep·모델/RNG/updates0·소스/scene closed를 검사한다. failed/stale mask는 보존하며 향후 유효성 판단에 사용한다. 모든 원래 성공/실패는 분모에 남는다. 새 NPZ/report는 exclusive output 소유권 내에만 쓰며 원래 report는 보존한다.

CPU 준비 명령(root에서 실행, GPU를 사용하지 않음):

```bash
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/jacobian_position_coordinate_audit/cpu_audit.py
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/jacobian_position_coordinate_audit/prepare.py
```

CPU 산출물은 exclusive 생성이므로 이미 존재하면 덮어쓰지 않는다. `run_probe.py`는 기본 dry plan이며 원래 index_reference job의 child/out만 바꾼다. 원래 initial checkpoint670pins·완전 architecture/config identity·73 model tensors의 strict CPU load를 검증한다. 저장 CUDA RNG topology 때문에 CPU에서 전체 trainer.load를 실행했다고 주장하지 않는다. 실제 GPU runner는 원래 full trainer.load를 그대로 실행하며 `_validate_pins`를 완화하지 않는다. 독립검수 후 봉인 상태가 PASS일 때 root가 아래 단1GPU 실행을 직렬 수행한다:

```bash
/home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/jacobian_position_coordinate_audit/run_probe.py --execute
```

향후 비교는 `runs/index_reference/precontrol_native.npz`와 원래 생성되는 trace/evaluation/원장을 사용한다. 영상 및 원래 reference와 실제 동일성은 확인할 대상이며 보장하지 않는다. nativeJ와 qpos-J의 차이를 확인하기 전 좌표 교정·gain 탐색·생산 적용·이전 gain 결과 재분류를 하지 않는다. body resultant는 접촉쌍 압력이 아니며 이 도구는 힘 기준을 바꾸지 않는다.

이 CPU FK 미분은 full3축 ball인 wrist/팔 검산이다. qx/qz만 노출된 finger MCP의 회전 y 누락 가능성 때문에 손가락 위치좌표까지 같은 결론을 확대하지 않는다. 저장 fullhumanJ/q/body는 향후 MCP 자체 pose/FK 일치를 별도로 확인할 수 있으나 이번 범위를 넓히지 않는다.

독립검수: `review_policy_load` PASS. 작성자 CPU 결과를 쓰기 intercept 방식으로 재검산하여 exact 일치를 확인했고, 추가 CPU fixture에서 q/qd/target/body/J 전필드 clone 독립성과 first/physical/wrist/stale mask 보존을 확인했다. 실제 GPU 수집은 아직 하지 않았다. 원래 완전 trainer.load·scene close는 실행 시 반드시 통과해야 한다.

root 외부 실행기 종료 기록 권장 경로는 이 폴더의 `01_launcher.json`이다. 내부 `runs/report.json`의 returncode0은 run_child가 실제 child 종료0으로 반환했을 때만 생성되며, 외부 실행기 종료 여부와 구분한다. 기존 output이 있으면 재실행하지 않는다.
