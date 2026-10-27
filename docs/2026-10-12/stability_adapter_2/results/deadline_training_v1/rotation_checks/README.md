# 회전 집합 CPU 검증 결과

최종 사용 파일은 [deadline_rotation_v3.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py:20)다. `RotationEnvelope.distance(quaternion_xyzw)`는 `inside`, `upper_rad`, `lower_rad`, `nearest_euler_deg`, `nearest_quaternion_xyzw`, `uncertainty_rad`를 반환한다. simulator·GPU를 import하지 않는다.

허용 집합은 scipy extrinsic xyz X[45,90]°, Y[50,100]°, Z[135,180]°다. 포함 판정은 두 Euler branch와 Y=90°의 전체 X−Z 가족을 다룬다. quaternion 합·차로 잘 조건화된 X−Z를 유지하고, 실제 허용 Euler 후보를 재구성하여 SO(3) 오차가 64 machine eps(1.4211e−14rad) 이하인지 확인한다. 이는 부동소수점 반올림 허용이며 단일 `as_euler` 축별 비교가 아니다. 초기 q=[−0.5,0.5,0.5,0.5]와 q/−q 동치가 통과했다.

범위 밖의 거리 상한은 bounds 안의 least-squares 후보와 5° 격자 후보 중 실제 SO(3) 오차가 작은 값이다. 격자 최근접 노드와 이전 fit을 시작점으로 사용하며 전역 최근접임을 주장하지 않는다. 하한은 `max(0,min_grid_distance−covering_radius−1e−12)`다. 회전 곱 불변성과 삼각부등식으로 각 Euler 축 차이의 합이 회전 거리의 상한이고, 모든 박스 점은 격자 노드에서 각 실제 간격의 반폭 이내에 있으므로 이 하한은 전역적으로 보수적이다. 기본 격자는1100점, covering radius=7.5°이다. 100회 표본의 최대 구간 폭도7.500000000057° 수준으로 넓다. 내부 판정은 거리0을 반환한다. **정확한 최단 거리 인증과 production gate는 미완료다.**

- [x] 첫 실행 전 매 버전 소스 사본·SHA·명령을 새 `attempt.json`에 기록했다.
- [x] v1/v2의 near-gimbal 경계 실패 로그와 소비된 소스를 수정하지 않고 보존했다.
- [x] v3의8 CPU검사 묶음이 기본 Python 및 rl38에서 모두 통과했다. 포함 검사는81 경계/면/near-Y90 조합, 1000 무작위 허용 회전, gimbal 가족·양 branch·작은 경계 교란·잘못된 입력을 포함한다.
- [x] 24 heldout 바깥 회전에서 허용 후보의 실제 거리 상한을 확인하고1000 허용 후보·2° 격자 결과와 하한을 대조했다.
- [x] rl38 outside100회: 평균2.302ms, p95=5.020ms, 최대7.386ms. 기본 Python은 평균3.588ms, p95=7.996ms, 최대11.948ms였다. 이는 해당 실행의 CPU wall-clock 표본이며 실시간 보장은 아니다.
- [x] 각 실행 뒤 소스 SHA가 실행 전 SHA와 일치했다. 새native0회, 새학습0회다.

[기본 Python 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/rotation_checks/attempt_v3/report.json:1) · [rl38 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/rotation_checks/attempt_v3_rl38/report.json:1) · [검사 소스](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_rotation_v3.py:19)

구현 위치: [포함 판정](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py:38), [거리 API](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py:79), [전역 하한](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py:100), [허용 후보의 bounded fit](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py:111). 공용 원본·기존stability_adapter·타인 담당 파일은 수정하지 않았다. 최종 독립 검수와 전체 결과 봉인은 root 담당이다.
