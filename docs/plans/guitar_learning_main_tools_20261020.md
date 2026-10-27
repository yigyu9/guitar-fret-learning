# 기본 학습과 전문 도구 정리

사용자 승인: “정말 필요한 것인지 전부 검토해서 메인인 것들만 남기고 나머지는 도구화 해서 정리해줘”. 현재 기본 학습은 합의한 자세에서 손별 PPO를 시작하는 train.py다. 기능·보상·물리·checkpoint 검증을 변경하지 않고 기본 구현과 선택 실행 도구를 구분한다.

- [x] AGENTS/README 읽기, 기본 경로와 전문 패키지 파일별 독립 조사
- [x] 활성 파일 전수 목록·import/참조·역할 기록, 변경 전 소스/문서/설정/CAS index449개 보관
- [x] 이전 실행 입력의 정확한 경로/SHA 원문 CAS 등록, 기존2,220version/default보존
- [x] 기본 학습의 공용 quality worker/logger를 전문 CLI에서 분리, 원함수4개AST동일
- [x] 공용 runner는 training/, 전문 CLI는 tool/training·evaluation·demonstration/, 전문 패키지는 tool/experiments/로 이동
- [x] 현재 import·작업자·프로젝트 루트·하위 프로세스 명령·설정·문서·provenance 갱신
- [x] 전체385Python 분류/이동표, 중복·유지 이유, 기본 학습 구조 안내 작성
- [x] 문법/import/도구54help·입력SHA·기존계약·121모듈692검사와실제좌840/우420PPO1/저장,정리전모델strictresume20전이·update1→2확인
- [x] 독립 change-reviewer 검수 지적0건과 최종 기록

완료 기준: 기본 train 경로가 tool/전문 실행기에 의존하지 않고, 전문 기능은 역할별 도구에서 실행된다. 모든 원래 활성 파일에 유지·이동·보관 사유가 있으며 유실이 없다. 기존 입력 증거는 수정하지 않고 CAS로 검증한다. 기본 학습 명령·563상태·39행동·035/v14·native0/정책7초·240/60Hz·물리 안전·strict resume는 보존한다.

검토상 환경 버전은 상속·공유 구현이므로 이름만으로 삭제하지 않는다. song/task.py와 music_task.py는 전곡 task provenance가 실제 파일 경로/SHA를 담으므로 그대로 유지한다. 옛 checkpoint 계약의 일괄 허용이나 source SHA 무시를 도입하지 않는다. 이전 작업의 전체 회귀는 기존 JSON/float 표현 SIGFPE로 중단됐으므로 같은 제한이 반복되면 통과로 처리하지 않고 관련 검사·실제 학습 검증과 분리해 기록한다.

완료: 메인/공용Python245→141,기존도구17→128,107Python포함140파일이동. 전체Python393은공용분리/패키지초기화/검사추가와facade제거의결과다. 검사모듈별별도프로세스692검사pass이며단일프로세스discover는재실행하지않았다. 과거SIGFPE원인해결을주장하지않는다. 초기embeddedscript잔존경로·단독실행sys.modulesfixture순서문제를수정한재검사기록을보존했다. 최종결과: docs/2026-10-20/guitar_learning_main_tools_v1/README.md.
