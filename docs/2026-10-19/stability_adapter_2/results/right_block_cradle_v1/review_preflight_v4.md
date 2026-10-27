# 사전 검수 — analytic 두 블록 후보와 native 진입점

요약 판정: **문제없음. 미결 Critical 0 / Warning 2 / Suggestion 0.** source3 seed0와 static_OFF0 설정으로 실제 초기 필수 검증을 거친 첫5초 진단 진행을 막는 사항은 발견하지 않았다. 두면 접촉·받침·팔꿈치 동작 중 유지 성공은 미검증이다.

해결한 항목:

- source1 자연기하/회전 조건의 hard gate 누락은 source2에서 해결됐다. source2 실제3후보는 모두 거절/native0으로 보존됐다. source3는 제안 잔차도 analytic capsule–63 convex distance로 바꾸고 두면2mm 목표/아래25mm 선호를 사용한다. final float32 모델/자연기하/회전/손가락42/전체 LP gate는 유지하며 genuine FK를 저장한다.
- [runner2:60](/home/ajou/yigyu/3/stability_adapter_2/run_right_block_cradle_v2.py:60)는 첫 FocusedRecording 캡처에 필요한1280×960 OM_appearance camera를 생성한다. 기존 runner1의 KeyError 예상 차단을 보고했고 수정본을 확인했다. [finally:87](/home/ajou/yigyu/3/stability_adapter_2/run_right_block_cradle_v2.py:87)는 마지막 capture/encode 예외가 원 실패를 가리지 않도록 처리하여 cleanup·원자료/report 저장을 유지한다.
- [helper2:58](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v2.py:58)는 부모 tracking의 추가 전 벡터를 before_thorax_efforts_Nm로 보존하고 실제 최종81벡터를 actual_combined_submitted_efforts_Nm로 갱신한다. Thorax10N ON에서 부모의 'final' 값이 실제 제출값과 달라지는 기록 문제를 해결했다. 원 helper1/runner1은 보존된 별도 버전이다.

현재 후보/제어 범위:

- source3 seed0는 source_clear/accepted true다. Thorax2.027727mm/근위상완1.968054mm/전완30.703318mm, Chest2.398105mm/RHip.913339mm를 저장했다. elbow 아래24.999652mm/밖269.727863mm/wrist 안쪽114.951890mm 및 Head/왼wrist 회전오차 약9e−6°가 gate를 통과한다. source3 입력의 현재 SHA 변경0을 확인했다. static_OFF0 config는 source config에 thorax_point_cap_N=0만 추가했으며 candidate SHA도 일치한다.
- runner2는 실제 t0 q/model·finger42/G fullstate/rootlower·PD/mass·FK1mm/.001rad·전체 actualpose source LP를 gate한다. 초기 body/head/양팔 각은 새 candidate가 권위이며 이전48 불변 조건을 재사용하지 않는다.57 POSITION/양팔24 EFFORT guard와 한 번81 제출/4 physics·300 control·5초/30fps 녹화 경로를 유지한다. 속도50rad/s 및 기타20cm/35° 보호 중단과 부분 저장을 구분한다.
- [Thorax 제어:37](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v2.py:37)는 기존 오른 지원/왼 wrist 추종을 한 번 계산한 뒤 Thorax source witness의 초기 world 목표를 사용한다. cap0 또는10N의 `2000e−30v` 요청을 native Jᵀ로 변환하고 R_Thorax3에만 합산·최종 모델 effort clip한다. shoulder/elbow/wrist child J열0·COM/origin 속도오차≤.01m/s·읽기 전후 상태 불변을 검사한다. 기타 힘·attachment·상태 setter를 추가하지 않는다. 전완의 가상 힘은0이며 전완 Jacobian 자체가0이라는 뜻은 아니다.
- 새 source3/helper2/runner2 AST 검사는 통과했다. 실행·계획·자산/모델 입력 pin과 정지 후 같은 초기/제어의 제한된 scalar elbow 시험 계획을 확인했다. 아직 native 결과를 실행하거나 검증하지 않았다.

Warning 1 — source의 근위0~30% 최소거리와 Thorax gap은 cooked 접촉/겨드랑이 영역/두 지지력 기여의 증거가 아니다. 실제 endpoint 접촉점·영역·presence/양성 rawlambda와 기타 중심·SO3를 따로 확인해야 한다. 손가락42는 초기 scalar 보존이며 실행 중 모든 실제 자세를 고정한다는 뜻은 아니다. 앞선 다른 팔자세의 ±5° 시험을 새 받침의 동작 인증으로 재사용하지 않는다.

Warning 2 — 새 Thorax10N과 기존 상완10N은 각각의 가상 요청 norm cap이며 합쳐서10N이라는 제한이 아니다. 왼 wrist30N도 별도 요청이다. 실제 접촉력/모멘트 분담 또는 전체 모델 안전 인증으로 읽지 않는다. 현재는 OFF0 진단만 준비됐으며 ON10N·동작 후보는 결과에 따른 후속 조건이다. Jacobian/중력 모델 및60Hz sample 안전 검사 한계는 이전 검수대로 유지된다.

검수는 변경 코드/계획·보존된 source2 거절·선택 source3/config·현재 입력 SHA와 AST에 한정했다. 추가 source 실행/native/정책추론/학습·다른 담당 파일 편집은0이다.

검수 SHA256:

- source3: `4102f67f387c2119103adbf0490cba2f591d0eedfc6d7103c24c71fc105687fd`
- source 계획V3: `a279098c8ff9bf3d3a86785edacdf494ab7ea2b61d2bda15daf40e2b3286088d`
- helper2: `828c0ece5e2975aad69cf8b0e8ae41d2cf329097384c18c06209f3e66be1eb55`
- runner2: `2eb990fbfc094d48370e21cf6ecba2fb23085ebce011d96130550d4d0272ebb5`
- native 계획V2: `cae9d4b08244337b0bc58d301c87d3cb5917ec07bf1591a43413ecc4cda7a138`
- static_OFF0 config: `976abb9b0eecf84a3d4e58df38635f7f8b8f1dea45dfd6135801e5999365d9ae`
