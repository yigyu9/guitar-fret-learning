# 접촉 시각화 자세의 초기 배치 적합성 검증

**판단: 정지 지지용 초기후보로는 유망하다. 양손 연주용 기본 초기값 확정은 보류한다.** 왼손을 놓고도10초 정지하고 오른Elbow/Wrist6만의 가상피크 왕복도 가능했지만, 왼손 잡기·놓기 후에는 지지가 무너졌다. 기존 기본값은 변경하지 않았다.

## 실제 시험 결과

최댓값은 초기 대비 BB 바디 중심 이동과 정규화 쿼터니언 SO3 각도다. 두 최댓값의 발생 시각은 다를 수 있다. 위치/회전의 축별 자연스러움 허용집합을 새로 검증한 것은 아니다.

|조건|실제 경과|최대 바디 이동|최대 회전|왼팔·왼손 접촉 없는 표본|판정|
|---|---:|---:|---:|---:|---|
|기존 near 초기·정지|10초|2.811mm|0.693°|145/2400|대부분 왼손 접촉을 동반|
|14초 자세에서 새 초기·정지|10초|2.719mm|0.826°|2400/2400|왼손 없이 정지 유지|
|새 초기·오른 팔꿈치/손목 타현|5초|6.145mm|4.237°|1159/1200|왕복6줄 검출, 왼손 잠깐 접촉|
|새 초기·왼손 잡기/놓기/이동|7.283초/목표16초|115.508mm|30.527°|1084/1748|보호 중단, B잡기 미도달|
|새 초기·기타 Z+3mm|10초|5.181mm|0.958°|2400/2400|초기 배치 차이 한 방향에서 정착|

정지 후보의 마지막2초 변화는0.01591mm/0.006185°, Z+3mm는0.02414mm/0.009668°다. 완료한 정지/타현/초기차 조건의 오른손목·손–기타 접촉은 모두0이었다. 타현은 팔꿈치·손목6개의 목표만 변경했으며 다른75개 목표는 초기값을 유지한다. 실제 관절 상태 고정과 구분한다. 원본 가상피크 검출기의 실제 RELEASE는 내려치기6→1, 올려치기1→6이었다. 기존 분석기의 올려치기3.95초 이후 집계 누락은 원자료를 보존하고 [실제 명령 구간 집계](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/strike_actual_windows_v1.json:1)로 분리했다. 학습 체크포인트·곡 연주는 연결하지 않았다.

## 왼손 시험의 실패 지점

A잡기3–4.5초에는 엄지+다른 손가락의 양의 raw lambda가360/360표본에 동시 존재했다. 잡기에서 놓기로 전환한 뒤6–7초에는 왼팔·손 접촉이240/240표본에서 없었지만, 가슴의 양의 접촉은0, 오른 위팔은91/240으로 감소했고 오른 허벅지는240/240이었다. 지지 전환과 기타 이탈이 함께 관찰되며 이것만으로 인과 기여나 접촉 힘 분담을 확정하지 않는다. 실패 구간에는 오른손목·손 접촉도181표본 생겼다.

중단 기준은 **actor-root 이동203.189mm가20cm를 넘은 것**이다. 회전35° 초과가 아니다. BB 바디 중심115.508mm와 actor-root203.189mm는 서로 다른 위치다. 물리는7.283333초, 마지막 카메라는7.266667초로1/60초 차이가 있다. 저장 영상은219프레임/30fps=7.3초이며 끝은 보호 중단 직전이다.16초 완료·수동 평형으로 해석하지 않는다.

이번 A/B는 새 시작점 기준 이름이다. 새 A 손목 목표는 이전 A보다 기타 좌표에서 약(-1.170,42.048,-0.034)mm 이동해 이전 B에 가깝다. 시작 관절각·기타 pose·제어 참조점·왼손 station을 함께 재구성했으므로 이전16초 시험과의 차이를 초기 몸통 자세 하나의 효과로 단정하지 않는다. [station 대조](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/left_station_comparison_v1.json:1).

## 초기값과 제어 범위

기준은 직전16초 영상의14초 자세다. 저장된81실제 관절각과 기타 pose를 바탕으로 **속도0·새 solver 상태**로 시작했다. L_Wrist_y의 약0.00251° 한계 초과를 한계 안으로 보정했고 기타는 world(오른쪽1.847,앞0.415,아래1.359)mm 옮겨 source analytic capsule 간격도 확보했다. coarse source hull만의 통과와 구분하며 native 초기 FK/모델 한계/속도0/source proxy 검사도 확인했다. 연속 움직임의 cooked 비관통 인증은 아니다.

- [초기81관절각·기타 pose](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/source_v4/candidate.json:1), [현재 후보 source 검사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/source_v4/proposal_audit.json:1), [실제 native 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/native_static_v3/initial_values.json:1).
- [정지 실행 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/source_v4/config_static.json:1), [왼손 시험 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/source_v4/config_left_cycle.json:1).

기타는 자유·스트랩OFF, root/하체 고정·자기 충돌ON이다. 상체/양팔의 유한 목표각/중력보상/근위팔 task 제어를 유지한다. 기타 고정·부착·외력·지속 pose 덮어쓰기는 없다. 따라서 유한 능동 제어하의 안정성이며 무제어 수동 평형은 아니다. Z+3mm 조건은 같은 reset/제어 법칙에서 지지 motor의 local 참조점도 초기화 때 재계산한다. 고정 참조점의 외란 복원력 인증으로 부르지 않는다.

초기 L_Wrist_y는 모델 한계 여유0°, R_Thorax_y와 L_Thorax_z도 한계에 매우 가깝다. [팔 관절의 scalar 한계 여유](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/initial_arm_limit_margins_v1.json:1)는 해부학적/월드 회전축 검증이 아니다. 모든 목표각/변화율/실제 제출 토크는 한계 안이고 실제 관절각의 최대 한계 초과는 실패 시험에서0.19815°였다. candidate의 inherited left_neck_near/body_side_lean_axilla 항목은 이전 호환 메타이며 새 손바닥/엄지/손가락 접촉 판정으로 사용하지 않는다. 최신 결과는 proposal_audit와 native 관측을 따른다.

## 재현성과 보존

새 초기 정지 두 실행의 초기값·전체60Hz 상태 trace·240Hz 접촉·최종 상태·최종 제출 토크는 byte 단위로 같았다. [재현 대조](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/static_reproduction_v1.json:1)를 따른다. 첫 static_v2 실행은 실행 중 root가 별도 후처리 파일의 helper 봉인을 보완해 보수적인 Python glob 입력 guard가 실패했다. 원래 False 보고는 보존하고, 해당 이전 소스도 예상 SHA와 일치하도록 별도 복원했다. 새 static_v3는 전체 guard를 통과했다.

최초 native_baseline은 녹화 카메라 누락으로0step 종료한 기록, source_v1/v2는 import 환경 오류로 물리 실행0회인 기록을 보존했다. batch_v1은 운영 검수의 대기/읽기 문제 때문에 자식 실행 전 중단하고 이후 시험을 root가 직접 관리했다. 실제 물리는0step 설정 실패1회, 정지 기준1회/새 후보2회/타현1회/왼손1회/초기차1회, 총6개 비영 실행(물리 관측구간 완주5회 중 static_v2의 입력 guard 실패1회, 보호중단1회), 마지막으로 정상 guard를 통과한 서로 다른 조건은4개다. 후처리에는 물리 실행이 없다.

## 다음 작업

지지부 자세를 유지한 채 왼손 해제 제어를 먼저 분리 검증한다. 손가락과 엄지를 먼저 펴서 실제 접촉이 줄어드는지 확인한 뒤 손목을 작게 물리는 순서를 비교하고, 가슴·상완 지지가 끊기는 시점을 함께 기록한다. 이어서 손목/Thorax 관절 한계 여유를 확보하면서 같은 지지와 타현 도달을 보존할 수 있는지 검사한다. 그 결과가 확인된 뒤 압현/타현 학습 초기값으로 채택한다. 이번에는 이 개선을 구현했다고 주장하지 않는다.

[이미지·그래프·전체 영상 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/README.md:1) · [측정 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/qualification_summary_v1.json:1) · [완료·체크리스트](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_QUALIFICATION_COMPLETION_V1.md:1) · [변경 파일·줄 번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/changed_files.md:1).
