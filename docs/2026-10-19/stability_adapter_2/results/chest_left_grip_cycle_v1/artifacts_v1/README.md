# 왼손 기타 잡기·놓기 한 사이클

16초 native 실행이 3,840 physics step 완료됐다. 기타는 자유 동역학이며 strap·인위적 기타 힘·상태 덮어쓰기 없이 root와 하체를 고정했고 self-collision을 켰다. 오른손 타현은 끄고 오른쪽/몸통 목표는 유지했다. 왼팔 12개와 왼손 21개 target만 사이클 중 변경했다. 실제 구동 모드는 POSITION 48개와 EFFORT 33개이며, 상속된 POSITION 57 라벨은 현재 명령 구성을 나타내지 않는다.

| 시간 | 단계 | 측정 접촉 |
|---|---|---|
| 0–2 s | 준비 | 잡기 접촉 전 |
| 2–3 s | A 닫기 | 접촉 전환 구간 |
| 3–4.5 s | A 유지 | 엄지+다른 손가락 양의 raw lambda 360/360 |
| 4.5–6 s | A 놓기 | 해제 전환, 구간 최대 16.522 mm / 14.717° (4.5 s 기준) |
| 6–7 s | A 열린 손 | 왼팔·손 접촉 없음 240/240; 구간 최대 13.903 mm / 8.433° (6 s 기준) |
| 7–8.5 s | 열린 채 B로 이동 | 접촉 없음 360/360; B−A 평균 손목 이동 neck축 41.418 mm (요청 40 mm) |
| 8.5–10 s | B 닫기 | 접촉 전환 구간 |
| 10–11.5 s | B 유지 | 엄지+다른 손가락 양의 raw lambda 360/360 |
| 11.5–13 s | B 놓기 | 전환 구간 |
| 13–16 s | B 열린 손 관찰 | 왼팔·손 접촉 없음 720/720; 구간 최대 0.445 mm / 0.213° (13 s 기준) |

놓기 동작은 각 지점에서 G=[0.070, 0.080, 0] m 대각 방향 목표(norm 106.3 mm)를 사용했다. 초기 기준 전체 최대 기타 BB 중심 변위는 37.288 mm, SO(3) 회전은 14.516°였다. 2초 기준 최대는 35.574 mm / 14.569°다. 따라서 손을 실제로 잡고 놓는 동작과 마지막 열린 손 구간의 정착은 관찰됐지만, 정적 유지보다 큰 전환기 기타 자세 변화가 있었다. 시작 자세 불변, 강한 안정성, force closure 또는 음악 연주 성공을 뜻하지 않는다.

B 지점 열린 손 구간 말기에도 오른쪽 위팔과 오른쪽 허벅지의 양의 접촉은 각각 720/720 표본이며 Chest는 716/720 표본이다. 왼쪽 허벅지 접촉 가능성을 배제하지 않으며 지지가 오른쪽 접촉만으로 이뤄졌다고 단정하지 않는다. raw lambda는 보정된 힘(N)이 아니다.

## 프레임과 움직임

아래 네 장은 native 손 카메라 원본 프레임을 그대로 축소·배치했으며 설명 문구는 영상 바깥에 있다.

![3.5초 A 유지, 6.5초 A 열린 손, 10.5초 B 유지, 14초 B 열린 손 native frame 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/hands_cycle_four_moments_v1.png)

[240 Hz 기타 BB 중심·SO(3) 그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/guitar_motion_240Hz_v1.png) · [시계열 CSV](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/motion_samples_240Hz_v1.csv)

## 실제 native 영상

각 영상은 16초 native Isaac Gym 카메라 캡처다. [전체 보기와 링크](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/README.md).
