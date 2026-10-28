# 첫 하중부터 새 안쪽 증분 억제 — 단일 timing 진단

상태: root 구현 승인 범위의 CPU 준비·독립 change-review PASS 완료. **GPU는 root 인계 전 금지한다.** 소유권은 이 새 폴더뿐이다. 기존696봉인·producer·활성 source·학습 입력·원자료는 보존한다. 별도 사용자 승인 요청은 없으며 GPU 인계는 내부 자원 조정이다.

- [x] 최소 프로토콜/성공 검증 기준을 기록(root 승인 범위).
- [x] 기존 wrapper의 timing gate만 변경하는 새 버전 준비.
- [x] CPU timing/보호/수학·명령/실제 prefix 비교 검사.
- [x] 독립 change-reviewer 검수, 새 준비 봉인.
- [ ] root의 별도 GPU 인계 후 단1조건 native 실행(현재 금지).

같은 corrected baseline final300 strict checkpoint·218×128×4 선택 중지 명령 tape·source clock480의128개 고정 body-local material point를 그대로 사용한다. 정책을 새 관측에 적용한 성과 비교가 아니며 원래 팔 teacher/B/엄지035와 이후 feedback 혼입은 남는다. 기존 original/2초 뒤 증분억제/증분억제+오차완화의 세 raw는 대조군으로 재사용한다.

유일한 제어 변경은 `first & clock>=480 & ...`에서 **clock>=480 제한 제거**다. 현재 control snapshot의 signed selected-distal press-normal resultant>기존0.01N, first attempt·prior native/wrist failure 없음·reset snapshot 아님·q/qd/pose/force/native J finite gate를 그대로 지킨다. 첫 하중이4개 물리 substep 중간에 생겨도 target은 다음60Hz 경계에서만 바꾼다. 과거 source의 최초 loaded clock으로 강제 예약하거나 영구 하중 latch를 새 gate로 쓰지 않는다. 힘이 내려가면 기존 gate대로 통과시킨다.

수학은 봉인된 projection 함수를 그대로 import해 `relax=False`, `g·δ>=0`의 box Euclidean 최소 변경만 사용한다. 최종 변화 전체가 native/action/rate 교집합·4rad/s 안에 있어야 한다. dtype 수치 허용오차/alias column assignment/scene 제출 일치도 원래 그대로다. 실제 q/state 덮어쓰기, 기존오차 직접 제거, 새 force/기하/J 문턱·PD·reward 변경은 없다. 고정점이 최초 실제 candidate witness라는 주장은 하지 않는다.

환경별 최초 **실제 target 변경** control의 start clock을 기록한다. 그 clock까지의 모든 실제 physics 필드(30개)와 그 전 모든 control 필드를 원래 source와 exact 비교한다. 첫 gate clock과 첫 실제 변경 clock을 구분한다. 변경이 한 번도 없으면 관측한 첫 시도 전체를 비교한다. 원래 명령 tape는 전체 첫 시도에 exact여야 한다. 128 첫 시도 quota·실패 분모·218 control/872 endpoint·원래4substep·source/model/RNG/업데이트/scene closed 감사를 그대로 재사용한다. prefix 불일치면 matched timing 효과 해석을 보류한다.

추가 기록은 기존 bounded60Hz schema뿐(약13.73MB), 기존 관찰과 합쳐100MB 미만이다. 전후 source/입력/새 wrapper/공유 projection/이전 driver·봉인·대조 raw를 pin한다. 기존 out은 native import 전에 거부하고, 원래 exclusive mkdir 뒤 dev/inode가 소유한 새 out에만 추가 report/raw를 쓴다. 오류도 보존한다.

CPU는 이전/새 measure의 AST 차이가 clock gate 하나인지, nested target hook은 `relax=False` 지정 외 동일한지 확인한다. 실제 nested hook의 가짜 CPU scene으로 480 이전 첫 loaded·unloaded·reset·failure·invalid/first mask·tape/rate/alias를 검사하고, 환경별 first-change prefix fixture는 경계 직전/직후 변형을 정확히 검출해야 한다. 기존 output 보호와 공유 projection 독립 수학 검사도 재사용한다. 실제 native prefix 동일성은 CPU 준비만으로 보장하지 않는다.

원인 질문은2초 이전 preload를 덜 쌓았을 때 같은 명령의 하중·성공이 달라지는지다. 자유 손 압현·생산 controller 개선으로 확대하지 않는다. body resultant는 접촉쌍 압력이 아니고 Jn 오차는 실제 침투가 아니다. 접선 변경과 teacher 요청차·유효 J 속도잔차·원래9지급·실패를 함께 읽는다.
