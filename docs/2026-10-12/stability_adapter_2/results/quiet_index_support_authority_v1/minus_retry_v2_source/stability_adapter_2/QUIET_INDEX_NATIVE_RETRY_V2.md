# 검지 음수 조건 native 종료 후 동일 입력 한 번 재시도

첫 plus는 실제 1200step/5초·151frame·두 스트랩 영상을 완료했다. 첫 minus는 15.573737244초 wall time 후 native exit −11(SIGSEGV)로 끝났다. Python report가 없으며 step152/t=0.6333333333333333초까지 153 state/trace/task와 152 control/contact를 남겼다. 이때는 2초 보정 입력 전이고, 확보된 상태·trace·task·contact 및 공통 목표 prefix가 원 quiet baseline과 exact였다. 초기 직접검사 15항목도 통과했다. 종료 원인은 미확인이다. 로그의 CUDA 경고만으로 원인을 확정하지 않는다.

원 minus output 전체 파일 SHA/크기와 실행 metadata를 `minus_native_crash.json`에 보존했다. Capture에 완전히 기록된 19frame(t=0..0.6초)만 사용해 `partial_videos/`에 두 부분 영상을 저장했다. 파일 재생시간은 19/30초이며 시뮬레이션 5초 완료가 아니다. 원본 JSONL/PNG/capture/log/실행기록은 수정하지 않는다. Python report를 사후에 만들어 원래 runner가 정상 종료한 것처럼 표현하지 않는다.

기존 계획의 최대 두 초기화는 plus 완료와 minus crash로 소진됐다. 사용자 자율 진행 지침에 따라 **동일 minus 조건 한 번의 추가 초기화**를 이 새 leaf로 정한다. 결과는 `native/minus_retry_v2`, 실행기록은 `minus_retry_v2_*`에 별도 저장한다. 처음 두 시도의 기록과 분리한다. 총 시도는 최대3회이며 성공한5초가 최대2회다. 다시 native 오류가 나면 이 leaf에서 더 재시작하지 않고 확보 자료로 원인을 진단한다.

물리 runner·초기81각·기타fullstate·PD·LA·root/하체·몸통9·목표파형·시계·그래픽/물리 설정을 바꾸지 않는다. 소비된 기존 runner/wrapper는 수정하지 않고 별도 retry wrapper에서 원 runner에 `--condition minus`를 전달한다. Fresh direct gate를 다시 통과한 같은 초기화만5초 촬영한다. 실패한 실행의0.633초 기록 뒤에 재시도 영상을 이어 붙이지 않는다.

분석에는 plus와 완료된 minus_retry_v2를 비교하고, 실패한 minus의 실제 step/frame/원본SHA/초기prefix를 별도로 집계한다. 총 native 초기화3과 physics step 1200+152+재시도실제step을 명시한다. Source/actor/training은 추가하지 않는다. 재시도 성공 전에는6×1 양방향응답이나 음수방향 성능을 결론 내리지 않는다.

- [x] 첫 minus terminal −11·입력103 전후exact·partial prefix/초기검사/19frame 검산
- [x] 원 실패 파일SHA 보존·부분영상 두 개 확보
- [ ] 새 wrapper/leaf 독립검수 후 동일minus 한 번 실행
- [ ] 재시도 실제 결과에 따라 저장 분석·산출물 또는 native 진단
