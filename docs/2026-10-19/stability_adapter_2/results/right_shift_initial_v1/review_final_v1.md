# 현재 자세 보관·오른쪽 이동 최종 독립 검수

요약 판정: 현재 결과·최신 문서·봉인 코드 문제없음. Critical: 0

원자료 및 새 producer/preset/문서/미실행 봉인 코드의 읽기 검수와 독립 수치 검산을 수행했다. 추가 물리 실행 및 기존 파일 수정은 하지 않았다. 이전 대규모 보존 체인 전체 재감사는 root 봉인 실행 범위이며, 이 기록은 봉인 실행 완료를 뜻하지 않는다.

## Critical

- 현재 버전: 0. 새 native wrapper V2의 기준 initial_values pin 보완과 metadata-only package는 [사전 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/review_preflight_v1.md:1)에 기록했다. 실제 초기 invariants/FK/whole source LP·PD·질량 및 57 DOF/G39 검사도 통과했다.

## Warning

- [RIGHT_SHIFT_INITIAL_COMPLETION_V1.md:29](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_SHIFT_INITIAL_COMPLETION_V1.md:29): 시작 기타 이동은 약1cm지만 native 정착 변화는 최대22.910122mm/5.009737°로 기존10.021289mm/3.317190°보다 크다. 후기 변화가 작다는 사실을 초기 drift 개선·수동 평형·반복 견고성으로 확대하지 않는다.
- [RIGHT_SHIFT_INITIAL_COMPLETION_V1.md:31](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_SHIFT_INITIAL_COMPLETION_V1.md:31): 후기2초 이후 엄격6면 동시 gate는0%이며 왼손 접촉이 남는다. 종료 중지 plane gap16.516475mm가16mm 상한을 넘고, 전체기간 엄지 최대18.888136mm·검지 최소1.591463mm·손바닥 최대25.243507mm도 초기 범위를 이탈했다. 초기6면 pass를 지속적인 grip 또는 왼손 해제 성공으로 설명하지 않는다. facet plane gap은 anatomical pad/최단 유한면 거리/접촉력 인증값이 아니다.
- [command_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/command_audit_v1.json:1): 단일 native case의 첫2초 exact는 자기비교다. JSON의 계승된 `across cases` scope 문구를 이전 baseline dynamics equality의 근거로 사용하지 않는다. 새 viewer의0.2초 prefix exact는 별도로 확인한 재현 근거다.
- [right_shift_pose_test_v1/README.md:19](/home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/README.md:19): DISPLAY 부재로 실제 데스크톱 창·키/reset 통합은 미검증이다. 완전5초 native 카메라 기록과 짧은 headless 재현을 GUI 통합 인증으로 확대하지 않는다.
- [artifacts_v1/README_v4.md:71](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/README_v4.md:71)의 후보 FILES.md 및 :72의 baseline README_v2는 이전 안내로 연결된다. 최신 사용자 진입은 [initial/README.md](/home/ajou/yigyu/3/docs/2026-10-19/initial/README.md:1)에서 양쪽 README_v3를 사용한다. 기존 잘못된 DOF 설명·미치환 archive 경로·실패 패키징 영상 경로는 소비본을 보존하고 최신 문서에서 보완했으며, 실패 V1 부분 출력은 납품 성공본으로 인증하지 않는다.

## 독립 확인 근거

- [native_right10_v1/report.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/native_right10_v1/report.json:1):5초1200physics/300control 완료, failure null·입력 동일·금지 호출0·strap/checkpoint OFF·학습0이다. 초기57 DOF 비교와 G39 quaternion raw exact/공통 이동 잔차3µm 이내를 유지한다. 예측 pose byte exact는 주장하지 않는다.
- [comparison_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/comparison_v1.json:1): 초기+1200개 실제 guitar pose에서 동일 BB 중심과 SO(3)를 독립 재계산했다. 새 후보 최대/종료 이동22.910122/22.885667mm, 최대/종료 회전5.009737/3.079151°다.2초 이후 최대 추가 변화는 새 후보0.383415694mm/0.120636786°, 기존0.372159011mm/0.300022417°다. 종료점 차(+27.716064,−4.645105,−12.291978)mm도 일치했다.
- [face_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/face_audit_v1.json:1): 실제 endpoint 1200개의 pose로 공유6면 측정을 다시 계산해 저장 gap/error/alignment 최대차6.66e−16, 모든 pass boolean 일치를 확인했다. 접촉 원행 재집계는 상완1185/허벅지1187, Thorax·전완·몸통·오른 distal0, 왼 엄지858/검지224/새끼191/손바닥0이다. contact step은 서로 겹칠 수 있고 측정 접촉력은 아니다.
- [command_audit_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/command_audit_v1.json:1):300개의 최종 target에서 다른75개 q_ref exact를 직접 확인했다. velocity 및 pick 각각 실제1200행을 원 D6·J[:,6]^T F·모델 clip으로 검산해 최종 command 오차0, 다른75 effort exact였다. 유한 pick 요청 최대10.990803N, Jacobian velocity 오차 최대0.003106m/s이며 동일한6개 human actuator에 합성한다. 실제 다른75 관절은 최대 약3.262° 움직였으므로 target 보존과 actual 고정을 구분한다.
- [strike_analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/strike_analysis_v1.json:1): 원 detector 결과12 RELEASE는 down6→1/up1→6이고 모두 core lane·깊이1mm 이상·속도절댓값0.05m/s 이상 조건을 만족한다. 이는 virtual-pick 판정이며 오른 손의 실제 현 접촉이나 학습된 곡 연주 인증은 아니다.
- [right_shift_pose_test_v1/run.py:11](/home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/run.py:11): 기존 current_pose_test_v1.run_v2의 LAB/REFERENCE/RESULT만 바꾼 별도 preset이다. 완료된 [headless report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/interactive/sessions/20261014_224653_041339/trial_000/report.json:1)는48physics/12control이며,48 endpoint/12 target/48 pick command 행을 위 native5초 prefix와 직접 비교해 정확히 일치했다.
- 보관 [baseline provenance](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/artifacts_v1/provenance_v1.json:1)22개 및 [성공 candidate provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/provenance_v2.json:1)31개의 source/destination SHA가 모두 일치하고 producer before/after/current도 같았다. Producer V2는0/1200step capture SHA와151frame·1280×720·30fps·5.033333초 영상 probe를 검사한다. config는 원래 절대 참조를 유지하므로 공용 모델까지 포함한 독립 배포 bundle은 아니다.
- 최신 root/I/artifact/V 문서83개 링크의 존재·텍스트 실제 줄·binary 무행번호를 확인했다. [navigation_update_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/navigation_update_v1.json:1)의 before/after SHA·exact prefix와 실제 main PLAN1302/A README2392/D README225행을 확인했다. Native attempt 입력에서 미해결 SHA 변경은0이며 승인된 main append는 snapshot으로 해결한다.
- [seal_outputs_v1.py:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/seal_outputs_v1.py:19)는 이전 chain/current recursive maps·초기/명령/타현·headless prefix·22/31 copies·최신 doclinks 및 AST를 검사하고 Critical0 기록 이후에 새 source_final/inventory/final_verification만 생성한다. 코드 AST와 [sealer_before_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/sealer_before_v1.json:1)의 현재 SHA `47d4e564feaa4575dd38aa0f064556a1676dac8e20bf2c4a19d54c83ab441671` 일치를 확인했다. 실제 전체 체인 봉인 실행은 root가 수행한다.

## Suggestion

- 선택적 최신 탐색 링크 보완 외 추가 구현/시험은 요구하지 않는다. 기존 baseline/default·실패/이전 산출물을 유지하고 성공 V2 archive와 최신 initial README_v3를 사용자 진입점으로 사용한다.
