# GPU 왼손 목표 접근·손가락별 출력·학습 신호 개선

사용자가 직전 제안의 개선 구현을 승인했다. 현재GPU왼손만 새보상v8로 진행한다. 손가락 움직임 비용0, 전체 native 가동범위·독립 누적제어/PD·물리·성공·안전종료는 유지한다. CPU/오른손·기존2슬롯 모델은 동작과 초기화·checkpoint 의미를 보존한다. 이전v7 이하 GPU왼손 저장본은 strict resume하지 않는다.

- [x] 변경 전17파일과 기존v7/v6 봉인SHA를 보관한다.
- [x] 원거리 품질 `(1+d/.04)^-2`, 접근 potential을 공통 tracking 목표4개에 일치시켜 γΦ(next)−Φ(current)/terminal0/H32 연속성을 유지한다. 기존준비창·관측·전체67음은 유지한다.
- [x] 손가락마다 현재/다음 목표토큰과 해당 관절 상태를 받는 작은 전용분기를 추가한다. 단순 마지막선형층 분할로 대체하지 않는다. 명시GPU왼손v8만 적용하고 기존CPU/오른손 초기화/RNG를 보존한다.
- [x] PPO의 보상/비용 advantage를 각기 표준화한 뒤명시적가중치로결합한다. 기존PPO 기본경로는 원식/identity를 유지한다. GPU왼손만 GAEλ .98로 하고 H32·rewardγ.99/costγ1·KLguard·PD는 유지한다. 진단에 원신호/표준화된 각성분을 기록한다.
- [x] 소프트자세 prior에 PIP/DIP동시60도초과굽힘을구분하고대기PIP상한을75도로조정한다(실험적범위,강제제한/인체인증X). 위치·자세가같으면명령/속도변화에보상불변을유지한다.
- [x] 각부분 단위/회귀·엄격저장복원/구계약거부/legacy RNG·gradient·target masking·potential telescoping 검사를통과하고독립검수한다. 기존512/GPU544가정실패1건은원인구분하며이번과무관한코드는수정하지않는다.
- [x] 소스동결후 실제GPU large1024/H32 fresh8 + strictresume1의실행·저장·원자료·정상종료를검증한다. 이는곡성능/자연스러움향상검증이나장기학습이아니다. 자원부족/수치문제는원자료보존후해결한다.
- [x] 현재4문서/새보고서와결과봉인·원본보존확인을완료한다.

역할: reward worker는gpu/finger_reward.py,gpu/environment.py,song/curriculum_runtime.py와관련3tests, policy worker는skills/specialist_policy.py와관련tests, PPO worker는training/ppo.py,ppo_diagnostics.py,start.py와관련tests를소유한다. Root는통합·현재문서/계획·실제GPU/GL·검수조정/최종봉인을맡는다. 모든worker는동시작업자변경을보존한다. 최종변경검수는별도change-reviewer가수행한다. native는root만동시에한context사용한다.

실행 결과: active438/changed15 동결. 관련CPU218 중217PASS+기존1FAIL, 실제GPU8+1 총294912전이 정상close·strictrestore·원자료CRC/EOF·583/584입력SHA PASS. 디스크부족으로GPU출력은임시메모리에서생성후41파일340093062바이트를무손실184217340바이트archive로SHA검증보존했다. 추가보관3원본은additional_before_manifest.json에기록했다. 현재4문서·독립검수(지적없음)·archive추출재검산·임시RAM해제·원본보존검증을완료했고 phase/result_manifest.json에최종결과를봉인했다.
