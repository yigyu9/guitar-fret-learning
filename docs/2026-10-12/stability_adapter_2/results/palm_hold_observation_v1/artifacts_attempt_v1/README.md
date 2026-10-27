# Native 관절 좌표·힘 관측

기준 실행과 관측 추가 실행의 저장 자료에서 왼팔 `L_Shoulder_x`, `L_Elbow_y` 두 native revolute DOF를 비교한다. 분석 계약은 2회 초기화·48 physics step과 다섯 검사를 확인했다. 두 조건의 native DOF property readback은 같고, 축은 rotational DOF type 1, 힘 단위는 Nm다.

|축|개별 body 질량 (kg)|kp / kd / effort property|기준 total DOF force min…max; 종료 (Nm)|관측 추가 min…max; 종료 (Nm)|관측 추가 종료 좌표 오차 / 속도|
|---|---:|---:|---:|---:|---:|
|`L_Shoulder_x`|L_Shoulder 1.970297|200 / 50 / 150|−3.717557…0.268733; −0.456562|−3.766369…0.243067; −0.455170|0.338013 rad / 0.632681 rad/s|
|`L_Elbow_y`|L_Elbow 1.037222|60 / 15 / 100|−1.757495…0.372698; −0.149309|−1.765386…0.321044; −0.148909|0.208089 rad / −0.514639 rad/s|

관측된 왼팔 body 질량은 Thorax 1.086119 kg, Shoulder 1.970297 kg, Elbow 1.037222 kg, Wrist 0.027293 kg, LH:palm 0.119867 kg이다. 이 값은 각 body의 개별 질량이며 전체 팔 질량이 아니다.

![기준 및 관측 추가 실행의 native 좌표 오차와 total DOF force 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts/palm_hold_observation.png)

위 두 패널은 25개 저장 상태(0–0.1 s)의 native scalar 좌표 오차(rad)를 나타내고, 아래 패널은 완료 physics step마다 저장한 24개 total DOF force 관측(Nm)을 나타낸다. 첫 힘 샘플은 step 1 완료 후 1/240 s이며 t=0 힘 값은 측정되지 않아 그림에 0으로 채우지 않았다. 좌표 오차는 해당 조건에서 Python이 제출한 상수 target 기준이다. 검사는 Python `self.target` 제출값과 이전 raw의 일치 여부를 다루며, native target getter를 읽어 대조한 결과가 아니다. 곡선은 전체 joint SO(3) 오차가 아니라 해당 revolute 축 좌표다.

`total DOF force`는 해당 DOF의 전체 native force 관측값이다. actuator-only torque, effort 포화 여부, 또는 PD 부족의 원인을 분리하지 않는다. 관측을 위해 추가된 계측과 target/state 보존 검사는 비교 조건에서 기록된 확인이며, 이 0.1초 자료만으로 지지 유지나 안정 성공을 판정하지 않는다. 다음에는 별도 계획에 따라 PD 조건을 비교하며, 이 문서는 gain 변경이나 후속 실행을 뜻하지 않는다. 실행·raw 파일은 [baseline](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/baseline)과 [관측 추가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/full)에 있다.

재생성은 저장 raw만 읽으며 기존 출력 파일이 있으면 덮어쓰지 않는다.

```bash
cd /home/ajou/yigyu/3
env MPLCONFIGDIR=/tmp/stability2_palm_hold_mpl MPLBACKEND=Agg \
  python stability_adapter_2/plot_palm_hold_observation.py \
  --out-dir /tmp/stability2_palm_hold_replot
```

Producer는 `py_compile`과 PNG 렌더링 검사를 통과했다. 입력, producer, 결과 PNG의 SHA-256과 실제 실행 명령·종료 코드는 같은 폴더의 manifest와 execution 기록에 있다.
