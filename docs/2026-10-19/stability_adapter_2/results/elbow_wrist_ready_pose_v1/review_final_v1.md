# Elbow·Wrist 준비 자세 최종 독립 검수

요약 판정: 문제없음. 선택 V7의 실제5초·기본 lane 양방향6줄 가상피크 한 주기 성공과 제어/접촉/산출물 제한이 원자료와 일치한다.

Critical: 0

## 확인 근거

- [분석 producer:30](/home/ajou/yigyu/3/stability_adapter_2/analyze_elbow_wrist_ready_v2.py:30)의 실제 pick/currentG60Hz 궤적으로 원 PickStrikeDetector를 독립 재계산했다. 최종 V7의12 RELEASE는 down[6,5,4,3,2,1], up[1,2,3,4,5,6]이며 모두 기본 lane core다. 검출은 가상 marker 교차·깊이·속도·재무장 기준이며 실제 song task 완주/음향 품질/학습 성공은 아니다.
- 다섯 실제 실행은 각각1200physics/300control/5초다. native 초기 state·첫480endpoint·첫121trace가 정확히 동일하며 LEFT 및 right distal 접촉0을 원자료에서 확인했다. 최종선택 상완1193/후기120, Hip1198/후기120, Thorax/Chest/trunk/head 접촉0이다. 다른75 논리 목표는 q_ref를 유지하나 실제75 상태는 고정되지 않는다.
- 실제 G body BB중심/SO3를 독립 계산했다. 모든 조건 최대11.410448692mm/3.872547878°, V7 최종9.917424810mm/3.358787520°로 문서와 일치한다. 초기69 scalar/G39 body states/mass는 이전 선택과 exact 동일하다. actual driveMode는33EFFORT/48POSITION이며 표의 오른12 초기각도 실제 native 값 반올림과 일치한다.
- [명령 감사 V2:35](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v2.py:35)와 독립 검산에서 전체1500control target75 동일/rate<3/norm<160,6000physics body 명령 finite/modelcap, LEFT OFF task/force0을 확인했다. V7의1200 pick 합성 `F→J[:,6]^TF→clip` 재현은 exact이고 velocity 이전/이후와 pick 이후 다른75 effort도 exact다. 최대 virtual force10.274880752N, 선택 Jacobian 속도오차 .001843988m/s다. 최종 명령 owner는 원 단일 human81 제출 경로다.
- [프레임 감사:92](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v2.py:92)의 각151capture를 독립 재계산해 rigid marker 오차가 모두 .000242mm 미만이고 render state 보존을 확인했다. 최종 native 전신0/5초 PNG도 직접 열어 캡션/부위와 대조했다.
- 현재 analysis_v4 입력4112개/command_audit_v2 입력3210개 SHA가 일치한다. native5 입력1523/1523/1529/1532/1535개는 현재 SHA 또는 승인 PLAN prefix snapshot으로 모두 닫힌다. 각 native 맵의 human37/guitar69 XML 전체 mesh 선언 포함을 확인했다. source V1/V2/V3 총6중1수락/5거절, 경로7점 clear와 depth6점 거절·V4 native0은 앞선 독립 검수와 일치한다.
- artifact V1/V2 producer/input 전후/current SHA와40개 byte-copy 출력(30PNG/10MP4) source/destination SHA가 일치한다. 실제 복사 MP410개 ffprobe는1280×720/30fps/151frame/5.033333초다. V3 링크 보완 producer·4입력·출력 SHA도 현재 일치한다. 물리5초와 영상 인코딩 길이를 구분한다.
- 기본 결과/색인/완료/영상/산출물 문서의 절대 링크132개 및 메인 추가 PLAN1272/A README2362/날짜 README195의 실제 제목·전후SHA·exact-prefix를 확인했다. 보충 [CHANGED_FILES_v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/CHANGED_FILES_v2.md:1)와 [최종 안내 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/FINAL_VERIFICATION_NOTE_v2.md:1)는 새 문서로 이전 문서를 보존한다.
- [봉인 소스:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/seal_outputs_v1.py:19)는 이전 chain/current 재귀 맵과 승인 append snapshot,source/native 수·초기조건·영상·XML pin·문서/AST를 검증하고 새 root 결과만 `open('x')`로 생성한다. [producer 현재 SHA 검사:101](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/seal_outputs_v1.py:101)와 V3 repair 직접 검증도 보완됐다. 검수한 현재 SHA는 `a308e2974437162be865192b3dcde54560b67ed714b995348c5c62e75f09b1f8`이며 AST를 확인했다. 봉인은 실행하지 않았다.

## Warning

- [완료 문서:5](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_COMPLETION_V1.md:5)의 성공은 해당 초기 자세/기타/기본 lane의 단일 down/up이다. 단현 정확도·반복 리듬·다른 lane/자세/기타 변동·checkpoint 전이·완곡/학습·무제어 평형으로 확대하지 않는다. 유한 PD/중력/currentG 상완 point 제어가 남아 있다. 접촉presence와 virtual force 명령은 측정 접촉힘/지지분담률이 아니다.
- [command 감사 보완:54](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_commands_v2.py:54): 이전 V1 static/strike maxcommand0은 새 stage 부재 집계였으며 실제 토크0이 아니다. V2 actual body 명령은 최대33.643734Nm로 보완됐다. 원본 둘을 보존하며 완료 문서도 이 의미를 명시한다. other75 effort exact는 추가 stage 전후 조건이지 다른 물리 조건들 사이 명령 동일성이 아니다.
- 역사적 미실행 wrapper V1의 Critical1은 requested/final norm hard gate 누락이며 V3 이후 새 버전에서 닫혔다. depth V4 envelope의 source ring3 교차는 실제 관통 깊이 측정이 아니며 native0으로 멈췄다. source 표본 감사는 연속/PhysX cooking 인증이 아니다.
- [artifact V1:126](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/README.md:126)의2개 및 원V2의3개 변수 링크는 원본에 남아 있다. 실제 절대 링크는 새 [README_v3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v3/README_v3.md:1)와 [보충 안내 V2:23](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/FINAL_VERIFICATION_NOTE_v2.md:23)에서 제공한다. sealer의 절대 링크 regex가 원 변수 링크를 검사한 것은 아니다. 실패 repair V1도 별도 원본으로 보존되며 성공 V2/current V3만 보완 증거로 사용한다.
- [완료 체크박스:57](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_COMPLETION_V1.md:57)는 작성 시점의 대기 상태다. 보충 안내의 최종 JSON 세 링크는 봉인 생성 예정이며 root가 생성 후 존재/값/링크를 마지막 확인한다. 이 리뷰는 현재 물리·명령·문서·봉인 소스의 읽기 검수이며 기존56446 입력 보존 chain의 전수 감사/새 final JSON 생성 성공은 root의 이후 실제 봉인 실행 범위다. 이전 chain의 문서화된 역사 제한을 소급 재인증하지 않는다.

## Suggestion

없음. 추가 물리 실행이나 원본 편집 없이 현재 봉인 단계로 진행할 수 있다.
