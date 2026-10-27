# Elbow·Wrist6만으로 현재 기타 타현이 가능한가

**현재 어깨 기준 자세·손가락 준비 자세를 유지하면 기본 타현 영역에는 길이가 부족하다.** 전완+Wrist→피크의 최대 반경388.125mm보다 기본 lane의 줄까지 거리가 초기10.67~30.32mm 더 멀다. Elbow/Wrist6만으로 위치오차2mm 목표를 만족할 수 없다. 준비 자세를 바꾸면 결론도 달라질 수 있다.

## 위 영상의 기타 유지 조건

이전 [실제 팔꿈치 운동 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/native_upper50_v14_elbow5_whole_body.mp4)은 왼팔·손·손가락 기타 접촉0·왼손 추종task0으로5초 완료했다. 기타는 자유 상태이며 root/하체만 고정했다. 오른 상완·허벅지 접촉과 인간의 유한 PD·중력·point 제어를 유지한 결과다. 상체 관절 상태나 기타 pose를 계속 덮어쓴 결과가 아니다.

이번 검사는 그 초기값을 바꾸지 않고 source 경로7개를 계산했다. 수락0으로 새 native 타현 실행은0이며, 기존 영상은 새 타현 영상이 아니다.

## 검사 결과

전완 길이249.810mm + 현재 손가락 준비 자세의 Wrist→피크138.315mm = 최대388.125mm다. 아래는 기본 lane Y=−.325m의6줄을 비교한 값이다.

| 기준 pose | 여섯 줄 중 최소/최대 위치오차 하한 |
|---|---|
| 초기 | 10.67 / 30.32mm |
| 실제 정지 reference2초 | 6.53 / 27.11mm |
| 실제 정지 reference5초 | 6.75 / 27.35mm |

후기 pose의 하한도 초기 손가락 준비 자세의 길이를 유지한다고 가정한다. 구 안쪽은 관절 한계·충돌·타현 성공을 보장하지 않는다. 전체 상체나 손가락 준비 자세를 바꾼 경우는 이번 조건 밖이다.

원detector 최소깊이1mm를만족하는모든깊이중가장유리한Z를골라도초기10.657~30.308mm가부족하다. 원기본궤적깊이1.5mm에서도거의같아이번경로깊이4mm가길이부족의원인은아니다. [깊이최적화필요조건원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/depth_bound_v1.json:1)에결과를보존했다.

위치-only V1의4경로와 전완 source 여유를 포함한 V2의3경로 모두 수락하지 않았다. 브리지 쪽 허용 영역−.375/−.365와 부분줄 sweep−.360도 검사했으며 V2 최대 위치오차는21.419/28.852/24.109mm였다. 원 `single` label 경로도±12mm sweep로인접줄을포함하므로한줄전용경로가아니다. 최적화 실패를 모든 near-bridge 경로의 불가능 증명으로 설명하지 않는다.

![초기/정지2초/5초 pose에서 계산한 도달 범위와 거리 하한](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/artifacts_v2/radial_reach_bound_v2b.png)

왼쪽 수평 점선은 가능한 최대 길이, 각 곡선은 줄까지 필요한 거리다. 오른쪽은 각 위치에서6줄중가장큰거리부족분이다. 저장된nativepose의기하학적분석이며시뮬레이션렌더가아니다. 원V1그림과범례QA중간버전도보존하고범례를그래프밖에둔V2b를표시했다.

V1 raw MuJoCo signed query는 초기 상태에서 전완–바디−14.355mm를 출력했지만 같은 초기의 analytic capsule–body 간격은+.425mm였다. query 불일치를 실제 관통으로 단정하지 않으며 원본 검사 결과를 보존했다. 수락된 source가 없어 새 타현 영상이나 RELEASE 성공률은 없다.

## 다음 방향

받침을 보존하면서 준비 단계에서 어깨 목표를 조금 조정해 **팔꿈치 축을 타현 영역에 가깝게 옮긴 뒤**, 타현 자체를 Elbow·Wrist 중심으로 수행하는 방향이 적절하다. 현재 어깨 값을 유지한 채6관절 학습만 늘리는 것은 기본 lane의 길이 부족을 해결하지 못한다.

- [계획·경로·검사 기준·다음 단계](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_STRIKE_COMPLETION_V1.md:1).
- [초기/2초/5초 radial 하한 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/radial_bound_v1.json:1).
- [V1 경로 검사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/source_v1/report.json:1) · [V2 전완 여유 포함 검사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/source_v2/report.json:1).

기존 모델/원본 기타/기존 stability_adapter/ 및 이전 실험을 보존했다. 이번 단계는 도달성 진단이며 실제 타현 성공이나6관절 학습 구조 확정을 뜻하지 않는다.
