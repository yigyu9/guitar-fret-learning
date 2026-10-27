# 오른 전완·손 소폭 전방 이동 native 독립 검수

요약 판정: 문제없음. 선정 Elbow3 후보는 기준 지지 강체·초기 기타·고정78각·제어 참조를 보존하고 실제5초 동안 손바닥 전방 변위를 유지했다. 이전 Shoulder+Elbow 후보는 보호중단으로 분리한다. 원본 수정·새 native 실행은 하지 않았다.

Critical: 0

Warning: 1

- [timelines_final_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/timelines_final_v1.json): 전체상완1196행은 endcap을 포함하며 raw축0~1 부분집합은181행, 왼팔·손 접촉1189행이 남는다. 절대기타 변화 최대34.012mm/16.514°,종료26.523mm/12.255°다. **작은 초기 손 이동과5초 관측 유지로 설명하고, 근위30% 지지·왼손 없는 유지·일반 연주나 반복 안정으로 확대하지 않는다.**

Suggestion: 0

검증 근거:

- [선정 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/native_elbow10_static/report.json):5초/1200physics/300control 완료. [이전 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/native_forward5_static/report.json)는0.633333초/152physics/38control guitar guard 중단이며 합계1352physics/338control이다. 둘 다 입력불변true·strap/checkpoint/training/금지호출0, 초기FK/sourceclear/모델한계/finger42/질량/PD 검사true다.
- [명령 감사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/timelines_final_v1.json): save를 메모리로 우회해 전체1352행의 기존 controller 실제G추종·가상요청·Jacobian·child0·body9중력/PD·좌우최종명령 합성/float32 cap/33EFFORT 소유권·48POSITION·실제시계를 재계산했고 canonical cases와1e−10 이내로 일치했다. 실제81목표·root/lower 최종exact도 raw로 확인했다. source 고정78초기각을 runtime 전체78상태 고정으로 설명하지 않는다.
- [arm 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/arm_final_v2.json): raw native초기78scalar·기타39body 전체state·Thorax/Shoulder 전체state 및 `two_block_configuration.json` 전체가 baselineexact다. 실제 초기 palm9.941820mm 전방/직교3.700455mm,5초 같은시각 baseline 대비8.562639mm 전방이며 관측최소도8.562639mm다.1200개 같은physics endpoint의 고정초기Gfront world수평투영을 read-only 재계산해canonical 전체와일치했다. 움직이는 기타에 대한 상대변위나 실제힘으로 표현하지 않는다.
- [analyzerV3:38](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_forward_v3.py:38): raw native 팔꿈치 초기 원점차는59.604645nm다.1µm기준을 공개하고 비영 변위를 보존하며 지원강체/G39/78각/reference exact 조건은 유지했다. source Elbow원점0·10nm gate를 바꾸지 않았다. [수치 기준 계획](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_FORWARD_ANALYSIS_PLAN_V1.md:3)과 실패 V2의 [보존 로그](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/arm_final_v1.log)를 확인했다. 원자료 덮어쓰기나 물리재실행으로 통과시킨 것이 아니다.
- [기타 비교 producer:14](/home/ajou/yigyu/3/stability_adapter_2/compare_right_arm_wrap_forward_guitar_v1.py:14): prior B의 sealed inventory에 닫힌 BB중심`[0,-0.4,-0.055937985]`를 사용하고,완전 두실행의301행·같은0..1200step을 대조한다. [비교 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/guitar_comparison_v1.json)를 read-only 재계산해 최대/최종 동시각추가1.323155956mm/0.555191656°가 일치했다. 서로 다른시각 peak값을 뺀 수치가 아니다.
- 선정case 상완 presence/positive1196/1200·후기120,waist1198/1200·후기120,left1189/1200이며 Chest/trunk/Thorax/rightforearm/rightdistal/head0이다. 실제G:body local접촉을world→actorG frame으로 독립 변환한 [waist 분류](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/waist_final_v1.json)도1198/후기120과일치했다. raw lambda를 Newton 접촉력으로 해석하지 않는다.
- Source물리최적화는V1~V3 총8행/기하수락5/거절3이다. V1의수락1행은 palm후퇴로 과제채택에서 제외됐고 native미실행이다. V4는V3수락3행의metadata 복사이며 geometry_solver_proposals0으로 추가CPU/물리후보 수에 더하지 않는다. 각 소비 input SHA 현재일치, V4의각도/G/FK/참조exact를 유지한다.
- 네canonical 분석의2209/12/7/6입력SHA와 source각map을 전부현재파일로 확인했다. 본단계 command audit는 새native2사례만 대상으로하고 이전baseline은 이미닫힌B봉인 근거를 사용해 과거mainPLAN 추가와 native raw 입력SHA를 혼동하지 않았다. 새두producer AST 통과.

- Arm analyzerV3 SHA256: `18342d3f58b201f8ba45ddd6a8d33820d745421e601b90ce133ec26c17da6a37`
- Guitar comparison SHA256: `aab9d77295bf7fd15938606af98f40b8f7a91dcb585c4e11e985e09bb42e6bc8`
