# 사전 검수 — 현재 기타를 따르는 상완 목표

요약 판정: **문제없음.** 동일26° 후보의 정지 5초 follow 진단을 차단할 사항은 없다. Critical 0 / Warning 1 / Suggestion 0. 실제 운동 진입은 새 정지 조건의 gate 통과 뒤에만 가능하다.

- [runner:110](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v2.py:110): 기존 인간 상완 참고점의 초기 4mm 안쪽 희망점을 기타-local로 저장한다. [runner:118](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v2.py:118)은 현재 normalized 기타 회전, root-origin 위치, COM 선속도와 각속도를 사용한다. 목표 위치는 `p+R local`, 속도는 `vCOM+ω×R(local−COM)`이므로 COM 보정과 감쇠 `−D(vhuman−vgoal)`의 부호가 맞다. 순수 중앙차분 점속도 대조 오차는 1.55e−11m/s다.
- [runner:119](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v2.py:119): K2000/D30/cap10N 및 human Jᵀ 합산·모델 effort clip을 유지한다. 이전 v1과의 diff에서 제어 변경은 상완 목표의 frame/속도뿐이다. child Elbow/Wrist J열 guard, 오른12 단일 actor effort 제출, other69 POSITION/readback/state 보존, forearm force0, root/하체 고정·strap OFF·자유 기타 및 1200 physics/300 control 기록 경로는 같다. 기타 force/setter/attachment가 추가되지 않았다.
- [analyzer:39](/home/ajou/yigyu/3/stability_adapter_2/analyze_upright_neckward_pose_v2.py:39)와 [analyzer:46](/home/ajou/yigyu/3/stability_adapter_2/analyze_upright_neckward_pose_v2.py:46): 현재 command 직전의 initial/직전 endpoint 상태에서 목표·속도·힘을 재계산한다. 기존 posture/합산 torque/clip/child J/69POSITION 검사도 유지한다. 관련 Python 2개 AST 통과.
- 기존26° config/candidate SHA와 저장 native 정지 초기 q81 exact를 대조했다. candidate 회전과 native 초기 readback의 차이는 3.05e−7rad로 수치 roundtrip 범위이며 이를 JSON exact로 주장하지 않는다. 이번 runner는 같은 config를 재사용하며 새 실행의 전체 초기값 exact 여부는 결과에서 다시 비교해야 한다.

Warning 1 — [계획:5](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V2.md:5)의 고정 world 목표가 접촉을 잃는 원인은 가설이다. 현재 기타를 따르는 인간 motor점은 가상 제어 목표이며 접촉·지지 힘 또는 기타 안정화의 증거가 아니다. 앞선30°/26°의 후기 상완 접촉 및 운동 gate 실패는 그대로 보존하고, [계획:10](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V2.md:10)의 접촉·정착·실제 자세 gate를 새 조건에 적용해야 한다. 기존 `safety_stopped`는 관측 latch이고 토크 중단이 아니다.

검수 범위는 새 source diff·수식·메타데이터와 기존26° config의 대조다. 추가 native/학습/소스 수정 0. 새 실행의 물리 결과·원인 확정·지지력 분담·장시간 또는 연주 인증은 포함하지 않는다.

검수 SHA256:

- 계획V2: `0db99279a181753813c989e666a0773642590dcaaca4a0940e6a827e72dc5903`
- runnerV2: `320f5197611acfdbfe514eab32bcf633284d0260f967aee46e1fd0bc1b6ced1e`
- analyzerV2: `feca4c1e6cd4d07473e60657368bde5f4ed0a480a171260851b51846b81da0bd`
- 기존26° candidate: `ac7498d11ebb86dbbd78758b2e78119d75163ecd17593d3b26ef9d7d07766f3d`
- 기존26° config: `2be814686566785b42083319694070103263929db1907c565ebc38bdd4ee3516`
