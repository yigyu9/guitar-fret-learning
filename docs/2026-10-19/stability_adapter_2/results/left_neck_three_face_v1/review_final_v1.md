# 왼손 넥 세 면 초기 준비 배치 최종 검수

요약 판정: 문제없음. 초기 세 면 배치 통과와5초 관측 완료, 후기 엄격 gate 유지 실패를 구분한 기록이 원자료와 일치한다. 지속적인6면 유지/grip 성공은 아니다.

Critical: 0

## 확인 근거

- [공유 geometry](/home/ajou/yigyu/3/stability_adapter_2/left_neck_three_face_geometry_v1.py:8)의 현재G 아래+X/뒤−Z/앞+Z와 inward facet normal/worldpalmup 부호가 source/native에 동일하게 적용된다. V1 setup 실패0후보, V2~V4 각2거절,V5 station20 하나 LP/공유 초기 gate 수락의7후보 이력을 보존한다.2.5/1.5mm separation은 soft preference이며 최종 hard 최소거리로 승계하지 않는다.
- 실제 초기48각/G39 raw state/PD/mass를 이전 left-thumb baseline과 별도로 비교해 exact 동일함을 확인했다. native_off_v1은5초/1200physics/300control 완료이며 initial source/FK/model 및 공유6면 gate를 통과했다. 실제 runtime 상태를 고정하지 않고 기존 finite33EFFORT/48POSITION·V7 rightEW6·LEFT wrist taskOFF를 유지한다.
- [면 감사:21](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_three_face_v1.py:21)와 별도로 actual6 body/currentG1200행을 재계산하여 vector/scalar 재구성 차이0을 확인했다. 초기 gap은 palm12.832574/thumb15.464336/index4.834820/middle14.188131/ring13.762913/pinky9.098700mm다.5초 gap은9.192220/17.993063/2.517328/11.180327/11.340925/6.506088mm로 표의 반올림과 일치한다.
- strict 전체 통과는 초기 포함8/1201표본(.6661%)이며2초부터721표본에서는0/721이다. 실제 part contact는 palm/thumb/middle/ring0,index109,pinky1183step이다. plane 지표·접촉 query와 readonly 재구성 감사의 passed를 구분한다.
- 실제G BB중심 최대10.021288948/최종7.600458600mm,SO3 최대3.317190467/최종2.902975243°를 독립 계산했다. 원 PickStrikeDetector60Hz 재계산에서 down[6,5,4,3,2,1]/up[1,2,3,4,5,6]의12 RELEASE가 저장 분석과 일치한다. 단일 가상피크 왕복이며 checkpoint/곡/학습 성공이 아니다.
- current face_audit1672/strike_analysis1866/command_audit949개 입력 SHA가 일치한다. native input 맵은 현재 SHA 또는 승인 PLAN snapshot으로 닫히며 새 메인 PLAN1290/A README2380/날짜 README213의 exact-prefix·전후SHA·실제 제목을 확인했다. 공유 측정/native callback/분석 및 새sealer AST를 확인했다.
- artifact producer17입력 전후/current SHA 및8 byte-copy(5PNG/3MP4) 원본/복사 SHA가 일치한다. MP43개 ffprobe는1280×720/30fps/151frame/5.033333초다. root/완료/산출물/영상/두 변경색인 절대 링크89개를 읽어 확인했으며 binary 줄 참조8개의 제한은 아래에 분리했다. [새 전체 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/CHANGED_FILES_v2.md:1)도 확인했다.
- [봉인 코드:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/seal_outputs_v1.py:19)는 prior chain/current 재귀 maps/승인 append,source7·수락1/native1·1200/300·영상3/초기6면·readonly 감사·XML 선언pin/producer 현재SHA·복사SHA·링크/AST를 확인하고 새 root 출력만 생성한다. 검수 현재 SHA는 `84797bdac8bc81815759abf3bba694161b8f8ebe02256b6e73b5e45ec4a5b95b`다. 봉인은 실행하지 않았다.

## Warning

- [동적 결과:30](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_COMPLETION_V1.md:30): 후기 엄지 gap은16mm 상한을 넘고 최대18.569699mm다. 또한 index 최소1.887050mm는2mm 하한 미달이다. 후기0% 이탈 원인을 엄지만의 문제로 한정하지 않는다. 완료/native audit의 passed는 기록 무결성·실행 및 초기 통과이고6면의 지속 유지 인증이 아니다.
- [면 지표:28](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_COMPLETION_V1.md:28): selected collision facet plane gap은 최단거리·finite face containment·anatomical pad·접촉압력/힘 인증이 아니다. source LP clear와 실제 index/pinky 접촉을 모순으로 단정하거나 실제 관통 깊이로 변환하지 않는다. 이후 currentG wrist 보정/압현은 별도 단계다.
- 단일 command case의 first2s 필드는 자기비교다. 이전조건과 settling dynamics가 같다는 근거가 아니다. 목표75 유지와 추가 stage 전후75 effort exact도 실제75 상태 고정이나 이전조건 토크 동일성을 뜻하지 않는다.
- [분석 입력:13](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_neck_three_face_v1.py:13)의 직접 before 맵은 실제 읽는 cfg/candidate를 별도 열거하지 않는다. 이 두 파일은 unchanged native attempt input map으로 합성 보존되는 범위로 확인했으며 독립 새 read-before 인증으로 부르지 않는다.
- 원 artifact FILES_v1의PNG5/MP43에 붙은 `:1`은 binary의 실제 줄 번호가 아니다. 파일/SHA 및 root README/INDEX의 미디어 링크는 정상이다. 소비 원본을 보존한 [FILES_v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/artifacts_v1/FILES_v2.md:1)의8개 binary plain-path/5개 text line 링크를 확인했다. artifact 제목 '왼목'과 완료문서:12의 '3시점151프레임'은 작은 표현 오류이며 실제 대상은 왼손·기타 넥, 실제 녹화는3view각151frame이다. 측정·미디어 바이트 오류는 아니다.
- [완료 체크박스:15](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_COMPLETION_V1.md:15)는 문서 작성 시점의 pending이다. 기존60833 input-version 보존 chain 전수 및 새 final JSON 생성·소규모 링크 보완 provenance 전수 감사는 root의 이후 실제 봉인 범위다. 이 리뷰는 그 실행 성공을 미리 인증하지 않으며 기존 역사 제한을 소급 복구하지 않는다.

## Suggestion

없음. 현재 결과를 초기 준비 후보·후기 유지 실패로 보존하며 root 봉인 단계로 진행할 수 있다.
