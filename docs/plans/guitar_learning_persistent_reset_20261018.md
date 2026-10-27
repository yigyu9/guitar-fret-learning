# 시뮬레이터를 유지하는 에피소드 초기화

목표: 매 episode destroy/create 대신 같은 sim/env/actor/assets를 유지하고 원래 준비 q/qdot·기타 pose/velocity·목표와 제어/측정 이력만 경계에서 초기화한다. 현재8환경 학습은 계속 유지하고 소비된Python을바꾸지않으며 새모듈/진입점으로 다음실행에적용한다. 초기화의2초준비·Root고정·105/97/8·유한하체·자유기타/중력ON/스트랩OFF·보상/성공판정은유지한다. 비공개PhysX접촉cache가수치적으로완전리셋된다고가정하지않는다.

- [x] 현행코드/검사/문서/설정과현재훈련입력무변경을보존·확인한다.
- [ ] 원Scene/Controller의고정FK/지지기준을유지하면서명시episode reset의state setter창/제어이력초기화와native생성횟수진단을새Session으로구현한다.
- [ ] 새ContactEnvironment/workerfactory/실행진입점으로기존수집·PPO·로그·엄격한checkpoint를연결하고기존진행중코드를수정하지않는다.
- [ ] CPU회귀검사와독립검수로scene재사용/예외close/누적guard·history를검증한다.
- [ ] 제한native반복reset과fresh대조에서sim/env/actor유지,생성1회/종료1회,복원값·물성·관절·지지·음악·메모리를검증하고필요시새버전으로수정한다.
- [ ] 짧은PPO·checkpoint복원·기존실행SHA무변경을확인하고새명령과실제결과/한계를정리·봉인한다.

소유권:worker_session은새persistent_session.py/해당tests만,root는새environment/factory/entrypoint와통합검증/문서/최종봉인,explorer는native상태조사,change-reviewer는검수. 기존코드/원자료/입력/공용자산은수정하지않는다.
