# StabilityAdapter v9: 손가락 대향 그립 학습 신호

현재 실행 위치는 `stability_adapter/development/pinch_underhand`이며 공개 태스크는
`--task stability-adapter` 하나다. v8의 11,400회 평가에서는 64/64가 그립 획득 없이 종료됐다.
손바닥 근접 또는 손의 순힘만으로 실제 넥 그립을 판단할 수 없었다.

## 변경

- 손바닥·엄지·두 손가락의 지정된 넥 면 접근 진전을 별도 episode-best 보상으로 계산한다.
  손가락 둘째 최근접 거리는 엄지와 넥 축상 9cm 이상 떨어진 손가락을 근접으로 보지 않도록
  축방향 어긋남을 포함하며, 같은 값을 정책 관측과 진단 로그에 넣었다.
  세 요소의 총 양의 보상 상한은 기존 3이며, 후퇴/재접근으로 반복 지급되지 않는다.
- 실제 대향 그립 전에는 위치·회전 및 오른쪽 팔·몸 접근 비용을 25% 적용한다. 충돌·힘·속도·
  자세·조기 종료 및 접촉 획득 후의 위치·회전 비용은 유지한다. 손바닥 접촉은 그립 보상으로 세지 않는다.
- 현재 통합 환경은 낙하·정지·아래 접근 시퀀스와 97축 제어를 유지한다. 별도 태스크나
  리셋 텔레포트 방식의 근접 초기화는 도입하지 않았다.
- PPO actor 학습률을 `3e-5`에서 `1e-5`로 낮췄다. 로그의 `ppo_policy_distribution_dims_mean`과
  `ppo_preupdate_kl_per_policy_dim`은 정책 분포의 차원 수로 환산한 진단 값이며 실제 움직인 관절
  수는 아니다. 조기 종료는 기존 총 KL 기준으로 판정한다.
- 손가락별 넥 면 거리/간격/측면 오차/순힘, 손바닥 순힘과 힘이 확인된 손가락 수를
  로그에 추가했다. 한 환경의 물리 접촉 쌍·관절 목표/실제 응답은
  `python -m tab2body.tools.probe_stability_grip --out <경로>`로 확인한다.

## 검증과 다음 실험

Stability 관련 테스트 289개 중 267개 통과·22개 GPU 의존 skip, PPO 표본 마스크 테스트 7개와 문법 검사가
통과했다. 현재 작업 컨테이너에는 CUDA 장치가 없고
환경이 GPU PhysX를 요구하므로 Isaac Gym smoke/접촉 probe는 GPU 호스트에서 실행해야 한다.
특히 보관된 관절 자세를 쓰는 probe의 실패는 현재 기타 자세가 그 자세에 닿지 않는 경우도
포함하므로, 실제 접촉 쌍·손가락 요청/응답을 함께 해석해야 한다.

새 학습은 v8 checkpoint 재개 대신 새 출력 디렉터리에서 시작한다.

```bash
cd /home/ajou/yigyu/3/stability_adapter/development/pinch_underhand
python -u -m tab2body.train --task stability-adapter --num-envs 1024 --iterations 50000
```

처음 100~300회 평가에서 `grip_left_finger_count`, `grip_left_force_corroborated`,
`grip_phase`, `grip_first_acquisition_seen`, `ppo_updates`, `ppo_preupdate_kl`을 본다.
손가락 거리만 줄고 접촉력 확인이 계속 0이라면 보상을 다시 높이기 전에 물리 접촉·관절 응답을 확인한다.
