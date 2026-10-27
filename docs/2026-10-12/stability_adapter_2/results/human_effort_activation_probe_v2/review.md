# 독립 검수

요약 판정: 문제없음. OFF/ON 소비 소스·native 원자료·저장 분석·미디어·최종 문서를 읽기 전용으로 대조했다. 물리/actor/producer/렌더 재실행과 타인 파일 수정은 없다.

- 같은 native 초기81관절·body/G 상태·목표·원래 PD 속성·EFFORT 속성 readback을 확인했다. 변경 대상은 RThorax/Shoulder/Elbow/Wrist12의 driveMode EFFORT 및 stiffness/damping0뿐이며 다른69속성과 effort/limits/friction/armature는 exact다. 초기 native readback이 제출 전체81속성과 exact인 실제 자료를 확인했다.
- 분석기 자체의 coverage 검사는 두 조건의 상호일치에 한정되므로, 독립 검수에서 상태 목록이 정확히 [0,4]+range(8,1201,8)의152개이고 명령300개가 before_step=4×tick인 것을 재계산했다. OFF는300개 전량0,ON은 첫 tick에서만 초기 float32 kp×(goal−actual)의 effort-bounded 벡터이며 R_Shoulder_z10.000001907348633Nm와 다른80개0이다. 이후299개도 전량0이다. 실제 저장 명령과 기대 벡터가 exact다.
- 소스는 두 typed wrapper를 확인한 뒤 raw normal human DOF tensor API만 지정하며81DOF/RH12 범위로 제한한다. 최초4physics에는 같은 첫 벡터를 각 step에 제출하고,step4 직후 원래POSITION 속성을 복원한다. 복원 getter exact와 복원 호출의 state 보존 검사는 저장 report에서 true다. 이후0벡터 제출·정상PD로5초까지 이어지며 source상 normal joint API 호출은1200회다. 기타/root/body 외력 또는 관절/actor state 덮어쓰기 경로를 추가하지 않았다. 요청 Nm는 측정 torque가 아니다.
- 전체152개 저장 native 상태의81 DOF와 body p/q/linear/angular velocity finite 및 초기 exact를 대조했다. 각 summary 행의 ON−OFF DOF 위치·속도 차이를 독립 재계산했다. step4의 R_Shoulder_z Δq=+0.03924226760864258rad,Δv=+3.84698648750782rad/s이며 전체 저장 최대 관절좌표 차이는0.04284012317657471rad다. OFF/ON 상태가 달라지는 정상EFFORT의 짧은 응답 증거이며 기존POSITION stiffness0의 무응답 결과와 혼합하지 않는다.
- 두 실제 초기 질량행렬이 exact하고 shape(1,81,81)·finite·최대 비대칭4.470348358154297e−8을 원행렬로 재계산했다. acquire/refresh의 readonly 검사도 true다. 행렬은 torque 계산에 사용하지 않았으며 SPD·GPU 동등성·장기제어 또는 source-like hybrid 채택을 인증하지 않는다.
- 각 실행은1init/1200physics/151camera frames·9개 검사 통과,실패없음이다. 각각1045입력·301소스 사본 SHA 및 종료 unchanged를 확인했다. 이후 승인 mainREADME/PLAN 두 append는 사전 snapshot prefix가 보존됐으며 다른1043입력은 current exact다. 분석 직접15개 입력도 전후/current exact다. 분석기 coverage/schedule의 좁은 Warning은 소비본을 수정하지 않고 위 독립 원자료 검산으로 보완했다.
- 두 capture의151개/604PNG SHA·readonly 및 네 actual MP4 SHA와 ffprobe151frames·30fps·5.033333초를 확인했다. 실제ON5초 손 프레임도 보았다. simulation 마지막5초와 MP4 길이를 구별하며 새 음악 정책/학습/연주 성공을 주장하지 않는다.

README:15의 과거 ‘POS 모드 토크0’ 표현은 원문 SHA56dfc67fb19a8f4628a91bc93c15e39a5125f02efecd5e8909ab1e643681caa0 사본을 D/doc_before_POS0_wording_correction/README.md에 보존한 뒤 ‘POSITION(강성0), 동일API OFF0/ON10Nm’로 정정됐다. 최종 수치·측정/요청 구별·미디어·파일 링크는 정확하고 미해결 Critical/Warning은 없다.

소비 runner SHA:b5800920bcdb084330f67ffad06cdafaedd82f825ed16b57ffcd127b8dcc84c9. wrapper SHA:4065a6b0212b385de2f3275f1ad6dce49511bd09acc3bde60a07c5d82e2d91fa. analyzer SHA:05650b709849fbcce48bbbcd2ba38844d07a29428ef2b761f5274a6cbe8baa9b. 최종 README SHA:c54e85b770ebf565620c855f680e01dd44c916f0fcb10d650b5f798cb75f3806. CHANGED_FILES SHA:528f440331aa356ef4362c68a265266533a805f61dd2c73e9282000a2b393e6c.

PASS는 이번 짧은 EFFORT 응답 진단의 계약·관측·보존·설명 판정이다. damping 인과·후속POSITION tuning 성공·반복 재현성·전체연주 성능은 별도 미검증 범위다.

최종 판정: PASS
