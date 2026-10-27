# 초기 위치 문구 정정

[결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/README.md:9)의 ‘기준 world p’는 **뒤30mm 이동 후 새 OFF/ON 초기 위치**를 뜻한다. 원 clear_reference 초기 위치와 구분한다. 검토에 소비된 README 원문은 보존한다.

| 조건 | native 초기 world p (m) |
|---|---|
| clear_reference | `[-0.2304154634,0.1217122748,0.7809729576]` |
| 추가 전경18°, 기타 뒤30mm OFF/ON | `[-0.2304154634,0.0917122737,0.7809729576]` |

세 조건의 기타 초기 quaternion xyzw는 `[-0.5,0.5,0.5,0.5]`로 동일하다. 결과 표의 이동·회전 변화는 각각 **자기 조건의 초기 p/q**에서 계산했다. 원기준 위치를 공통 이동오차 기준으로 쓴 비교가 아니다. 실제 초기 값·영상·검증 수치는 바뀌지 않았다.
