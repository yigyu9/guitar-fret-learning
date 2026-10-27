# 왼손 잡기·놓기 이미지와 영상

최신 가슴·오른쪽 위팔 초기 자세에서 실제 Isaac Gym16초 테스트를 수행했다. 기타는 자유·스트랩OFF, root/하체고정·자기충돌ON이다. 오른손 타현은 끄고 지지 목표를 유지했다. 기타 고정·외력·손 부착·실행 중 상태 덮어쓰기는 없다.

|구간|실제 접촉|
|---|---|
|A 잡기 유지3–4.5초|엄지·검지 양의 raw lambda 동시 접촉1.5초|
|A 놓기 유지6–7초|왼팔·왼손 접촉0,1초|
|물린 채 B 이동7–8.5초|왼팔·왼손 접촉0,1.5초|
|B 잡기 유지10–11.5초|엄지·검지 동시 접촉1.5초|
|B 놓기 유지13–16초|왼팔·왼손 접촉0,3초|

초기0–2초에도 일부 왼손 접촉은 있었으며, 엄지·검지의 동시 잡기는 없었다. 놓기에서는 추가 굽힘을 되돌리고 손목을 대각선으로 물렸으며, 모든 손가락이 완전히 펴졌다는 뜻은 아니다. 두 잡기 유지 구간의 평균 손목 넥축 위치 차이는41.418mm였다(목표40mm).

전체 초기 대비 기타 최대 변화는37.288mm/14.516°다. 마지막 놓기3초는 그 구간 시작 대비0.445mm/0.213°로 정착했다. 잡기·놓기는 확인했지만 전환 중 초기 위치/회전을 계속 유지하지 못했다. 지지 접촉에는 가슴·위팔·허벅지가 관여하고 구간에 따라 달라진다. raw lambda는 보정된 힘(N)이나 정식 힘 폐쇄 인증이 아니다.

## 실제 손 장면

왼쪽 위3.5초 A 잡기, 오른쪽 위6.5초 A 분리, 왼쪽 아래10.5초 B 잡기, 오른쪽 아래14초 B 분리다. 실제 native 카메라 프레임을 배치했고 캡션은 형상 밖에 있다. 기타 줄은 비물리적 선 표시다.

![잡기·분리의 실제 네 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/hands_cycle_four_moments_v1.png)

## 기타 움직임

그래프는 초기 상태 대비 바디BB 중심 거리와 SO(3) 회전이다. 전체3841시점에서 쿼터니언을 SciPy Rotation으로 정규화해 재계산했다. 곡선의 최대값은 서로 다른 시각일 수 있다.

![정규화한240Hz 기타 위치·회전 변화](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/guitar_motion_240Hz_v2.png)

[정규화한 CSV](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/motion_samples_240Hz_v2.csv) · [계산·전체 표본 대조 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/copy_manifest_v2.json) · [원래 단계별 물리 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/analysis_v1.json).

V1 CSV/그래프는 비단위 쿼터니언 계산 오류가 있어 이력으로만 보존한다. 이 문서는 수정된 V2 곡선을 사용한다. 실제 물리 실행·접촉 분석·원본 영상은 수정하지 않았다.

[전신·손·가슴/위팔 전체 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/README_final_v1.md) · [상세 결과·한계](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/README.md).
