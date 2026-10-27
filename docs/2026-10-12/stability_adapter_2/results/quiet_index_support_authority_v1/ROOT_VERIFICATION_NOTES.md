# Root 검증과 해석 기록

기존 quiet 초기81각·held offset·기타fullstate·LA1.1018469719600776m·몸통9 PD×2/√2·root/하체 고정·원손목 sinusoid를 유지했다. 새 제어는 LH:index3 목표의 ±.005rad 보정뿐이며2~2.5초에 ramp하고5초까지 유지한다. 기존 source 출력통계 범위와 물리 native 한계를 구분하며 actor/training은0이다. 기타 고정·강제 손부착·시작 후 state/pose 쓰기·인위적 기타 복원힘은 추가하지 않았다.

첫 plus는105.843171195초 wall time,1초기화·1200physics step·5초·151frame·두 스트랩 영상을 완료했다. 원 minus는15.573737244초 후 native SIGSEGV(exit−11)로 종료됐다. 상태153개/최종step152·0.6333333333초와 명령/contact152개만 있으며 Pythonreport는 없다. 저장 state/trace/task/contact와 명령 공통필드가 원baseline prefix와 exact였고 보정 입력은0이었다. 원인 미확인이며 음수 보정의 물리 실패로 해석하지 않는다.

실패한86원본 파일의 SHA/크기·초기15검사와103입력/사본·전후SHA를 검산했다. Capture에 완성 기록된19frame(t0..0.6초)만 사용해 두 부분 영상을 저장했다. FFmpeg CLI 명령과 FFprobe 스트림 정보/SHA는 partial_videos/videos.json에 있다. 부분 재생시간19/30초를5초 완료 또는 마지막 시뮬레이션 frame의0.6초와 동일시하지 않는다. 원실패 JSONL/PNG/capture/log/실행기록은 수정하지 않았다.

별도 재시도 leaf로 최대 시도를2→3으로 명시하고 동일 runner/초기/물리/그래픽/목표 입력의 minus를 새경로에서 한 번 더 실행했다. 재시도는104.635076615초 wall time,107입력,1200step/151frame으로 완료했다. 기존실패86파일의 시작전/종료후 보존도 통과했다. 새시도 전체는3초기화·완료2400step·실패관측152step·총관측2552step이다. 두완료5초를 연속된10초로 연결하지 않는다.

저장분석v1은 미실행 상태로 보존했다. V2는 재시도와 실패 회계를 반영하고 실패실행↔crash SHA·전후입력/닫힌log·실패명령/tasks prefix를 추가로 검증했다. Root ONE분석은exit0/5.364229907초,47검사 통과다. Wrapper2054입력 전후/current·2053사본과 닫힌log SHA를 확인했으며 analyzer 직접2045입력을 포함한다. 실제 읽는 원자료/PNG와 compact runtime hash closure다. 원 quiet proposal의14,015 ancestry 전체를 새 입력에 다시 누적하지 않는다.

완료조건 둘 모두20초기필드 exact,0~2초 state/trace prefix exact,1200명령의 다른80목표 exact,첫484개 전체81목표 exact다. Step485부터 native 상태가 달라진다. 두모두 fresh 초기15검사/self1188·목표범위·palm상향·root하체·PD·조회/명령read-only를 통과했다. 실제 native 관절한계 초과 최대약0.000099950rad는 baseline과두완료조건에서 같으며 목표가 한계 안이라는 사실과 실제각의 완전한 한계 준수를 구분한다.

종료 기타오차 baseline13.819696mm/2.918277°,plus13.750278mm/2.921428°,minus13.887982mm/2.916812°다. Plus는 위치만 미세하게 줄고 회전은 소폭 늘며 minus는 반대다. 후기121개 완전1초창의 최대변화는baseline .648625mm/.115306°,plus .685555mm/.124373°,minus .604995mm/.106007°다. 작은 후기변화를 초기 p/q 복귀와 동일시하지 않는다. 정식 자연스러움/성공 기준·실제연주·정책호환은 미검증이다.

T5 world 위치와 같은 t5 baseline 대비 world회전log의 중앙차분을 명목0.01rad로 나눈6×1 응답을 기록했다. 이는 접촉/마찰이 있는 특정 자세·ramp·관측시간의 유한응답이며 globalJacobian·feedbackgain 인증이 아니다. 작은 검지 응답을 큰 굽힘각으로 외삽하지 않는다. LH:index3 양의raw lambda 접촉step1156은 동일하고 thumb3는baseline587/plus521/minus615였다. Palm 접촉은 없으며 rawlambda를 접촉력·forceclosure·cooked침투 깊이로 해석하지 않는다.

다음 계획은 초기와스트랩을유지한 L_Wrist_y 목표±.005rad의두actual 응답이다. 손가락을 항상 고정하는 안정화 제어로 승계하지 않고, 연주 손가락 목표와 팔 보정의 최종 목표 합성을 설계한 뒤 학습구조를 결정한다. 다음 Wrist_y계획은 아직미실행이다.

산출물 정리 중 이미 분석에 소비된 postprocess canonical에 기존video glob 한 줄을 지운 미실행 변경이 생겼다. 검수로 발견한 a52 변형을 source_drift에 보존하고 ea42 실행원문을 pre-analysis 사본에서 byte-exact 복구했다. Collection/artifact는 그 변형을 실행하지 않았고 native/분석 재실행은0이다. 원2054 입력current SHA를 다시 통과했다. 이후 root가 원ea42 wrapper로 ONE collection을 실행해 기존152영상+완료4영상+부분2영상=158개를검산했고6개실제FFprobe frame수도 확인했다.

Root가 실제plus손카메라 t0/t5와minus재시도t5 프레임을 열어 native장면과스트랩표시를확인했다. 첫 progress그림은index범례가plus곡선의후기plateau를가려원그림/소비producer/실행기록을보존하고별도v2로범례위치만수정했다. Root ONE v2그림실행은exit0이며동일자료/계산/축과완료2trial만사용하고물리·저장분석재실행은없다. 실제v2 PNG의모든곡선·시간축·단위·범례/캡션가독성을확인했다. 원/v2 각각2053입력전후/current SHA와19선택사본·닫힌log SHA를검산했다.

Final documentation check: Korean README/CHANGED_FILES and VISUAL_REPORT §118 (actual line2106) reviewed against the saved analysis and video metadata. Main README/PLAN append-only result summaries added; wrist next plan remains unexecuted. Final reviewer and one root seal follow this note.
