# 왼손 엄지 초기값 최종 독립 검수

요약 판정: 문제없음. 엄지5 초기값만 바꾸고 실제 nonthumb 초기 배치와 기존 타현을 유지한5초 사례의 원자료·문서·산출물 범위가 일치한다.

Critical: 0

## 확인 근거

- [엄지 감사:13](/home/ajou/yigyu/3/stability_adapter_2/audit_left_thumb_natural_v1.py:13)와 별도 raw 비교로 다른76각, 모든 nonthumb human raw pose,PD 및 기타39body raw state가 이전 EW V7 초기값과 exact 동일함을 확인했다. 회전 정규화 연산의1.3947e−16rad는 실제 자세 차이가 아니다. thumb2/3의84.826/81.272→65.000/.467° 및 표의 엄지5 값이 native 초기값 반올림과 일치한다.
- native_v1은5초/1200physics/300control 완료, forbidden0·입력 unchanged다. 엄지5 요청/최종 목표는300control에서 고정이며 실제60Hz 최대 scalar 오차 .019657284°다. 실제 endpoint1200개의 LEFT 및 right distal 기타 접촉0을 확인했다. 다른75 목표 보존은 실제 관절 상태 고정과 구분된다.
- 실제 pick/currentG60Hz 궤적으로 원 PickStrikeDetector를 독립 계산하여12 core RELEASE,down[6,5,4,3,2,1]/up[1,2,3,4,5,6]를 확인했다. G body BB중심 최대11.402870517mm/최종9.853485235mm,SO3 최대3.871587709°/최종3.304836745°를 별도 계산해 문서와 대조했다.
- EW6 요청/최종 목표의75 동일·rate/norm,1200 velocity 차분/clip 및1200 Cartesian force→J[:,6]^T→clip과 단계 전후75 effort exact를 독립 검산했다.33EFFORT/48POSITION 및 원 cap/단일human81 합성 경로를 유지한다. 엄지 POSITION 목표만 초기값이 달라지며 새 기타 외력/state setter가 없다.
- [facet 감사:35](/home/ajou/yigyu/3/stability_adapter_2/audit_left_thumb_natural_v1.py:35)의 plane gap도 별도로 계산해 초기39.424163548mm/최종62.575971158mm를 확인했다. 명목 back24와 실제 최소거리/접촉의 차이를 결과 문서가 명시한다.
- current strike_analysis1856개/thumb_audit2305개/command_audit948개 입력 SHA가 모두 일치한다. native 입력1544개는 current SHA 또는 승인 PLAN snapshot exact-prefix로 닫힌다. human37/guitar69 mesh 선언 전체 pin을 확인했다. source V1/V2 각2개,기하수락 각1개이나 V1 끝범위 후보는 미실행이고 V2 back24만 물리 시험했다.
- artifact producer16입력 전후/current SHA 및10출력(7PNG/3MP4)의 원본·복사본 SHA가 일치한다.3개 실제 MP4 ffprobe는1280×720/30fps/151frame/5.033333초다.151capture 모두3view/render state 보존과 rigid marker<3µm를 확인했고,thumb_back0/5초 이미지를 직접 열어 부위·시간·카메라 visibility를 대조했다.
- 결과/색인/완료/산출물/영상 문서의 절대 링크59개와 실제 줄 범위를 확인했다. 메인 PLAN1281/A README2371/날짜 README204의 실제 제목·전후SHA·snapshot exact-prefix가 일치한다. 변수 링크 오류는 없다.
- [봉인 소스:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/seal_outputs_v1.py:19)는 prior chain/current 재귀 맵/승인 append,source4·기하수락2/native1·1200/300·영상3,초기 nonthumb raw exact,목표/접촉/RELEASE,XML pin 및 현재 artifact producer SHA/복사 SHA·링크·AST를 검사한 뒤 새 root 결과만 `open('x')`로 생성한다. 현재 SHA는 `5fc8de1e52dc4e5cccd032b47f6a2364af94ed7ac4986a22dd7d4f6624cf013d`이고 AST를 확인했다. 봉인 실행은 하지 않았다.

## Warning

- [완료 문서:27](/home/ajou/yigyu/3/stability_adapter_2/LEFT_THUMB_NATURAL_COMPLETION_V1.md:27): 선택 facet plane gap은 초기39.424→최종62.576mm다. 엄지지지/실제 최단거리/접촉력/피부 패드 또는 현재G 추종 인증이 아니다. 자연스러움은 사용자 시각 판단으로 남으며 anatomy·fret 학습/곡 완주·무제어 평형 주장은 없다.
- [command 자기비교 설명:50](/home/ajou/yigyu/3/stability_adapter_2/LEFT_THUMB_NATURAL_COMPLETION_V1.md:50): 이번 command audit first2s 필드는 단일case 자기비교다. 이전 EW와 dynamics 동일을 인증하지 않는다. raw75 effort 동일도 추가 controller stage 전후 조건이지 이전 실행 전체 토크 동일성이 아니다.
- [V1 late pin 및 V2 보완:37](/home/ajou/yigyu/3/stability_adapter_2/LEFT_THUMB_NATURAL_COMPLETION_V1.md:37)의 범위를 유지한다. V1 early read를 독립 새 before로 소급 인증하지 않는다. V2 임시 box65°보다 float32 후 .00000067° 큰 값은 모델 범위 내 수치 차이며 strict65° exact 판정이나 새 anatomy limit이 아니다. legacy camera_config_source는 새카메라 출처를 모두 설명하지 않아 runner SHA/actual matrix를 사용한다.
- [artifact 캡션:21](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/README.md:21)의 '오른쪽/양쪽'은 실제 문서에서 위아래로 놓인 이전/현재 이미지에 대한 작은 위치 설명 오류다. 각 이미지 label·원본 byte 출처는 올바르며 root 결과 README는 단일 엄지 이미지로 명확히 제공한다. 소비 문서를 소급 편집하지 않는다.
- 기존59786 입력 chain 전수 보존과 새 final JSON 생성은 root의 이후 실제 봉인 범위다. 이 리뷰는 현재 변경·원물리·명령·문서/새sealer 읽기 확인이며 그 실행 성공을 미리 인증하지 않는다. 이전 chain의 문서화된 역사 제한도 소급 복구하지 않는다.

## Suggestion

없음. 현재 봉인 단계로 진행할 수 있으며 추가 물리 실행은 필요하지 않다.
