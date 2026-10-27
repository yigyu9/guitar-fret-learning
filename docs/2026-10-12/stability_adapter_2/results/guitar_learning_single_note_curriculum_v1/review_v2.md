# 단음 조건부 확장 코드 최종 독립 검수

- 요약 판정: **문제없음**.
- 상태: **코드 사전 검수 completed=true**. 실제 watcher 시작·진급·pool native 실행 결과의 검수와 구분한다.
- 범위: 새 `guitar_learning/curriculum/`5파일·관련3개 검사 파일, watcher와15개 검사, phase 계획·설정·README. 기존 [review_v1.md](review_v1.md)는 보존했다.
- 검수자는 이 신규 보고서만 작성했으며 생산 소스·기존 모델·봉인 결과를 수정하거나 native 실험·학습을 추가 실행하지 않았다.

## Critical / Warning / Suggestion

남은 차단 문제·필수 수정·추가 구현 권고는 없다. 아래 발견 사항은 실행·봉인 전 수정과 CPU 회귀 확인을 마쳤다.

## 원칙과 watcher

- 최근64개 닫힌 episode 중 최소58개 품질 성공, 안전한7초 완주 이외의 종료0개와 결정적4/4 품질·안전 성공을 모두 요구한다. invalid/물리 terminal을 분모에서 버리지 않으며 열린 prefix는 제외한다. 손별 독립 진급이고 같은 시작 반복을 일반화 성공으로 설명하지 않는다.
- 진급 뒤 실제 두 목표 preflight2회에서 안전·7초 완주·입력 불변·coverage를 요구한다. 새 목표 preflight에 음악 성공을 요구하지 않는 점을 기존 단음 진급 게이트와 분리했다.
- watcher의 자식 종료 경쟁, 확장 trainer 실패를 정상 종료로 보고하던 경로, 상태 저장 IO 오류가 종료 정리·원 예외 전달을 가로막던 문제는 해결됐다. 원 실행은 watcher 자식이 아니며 watcher가 종료하지 않는다. 순수 품질 미달과 실행 오류의 상태·종료코드를 구분한다.
- 검수자가 watcher **15개 CPU 검사 통과**를 확인했다. 단계적 own-session 정리·종료 경쟁·상태 저장 실패·원 예외 보존·확장 실패 전파 회귀를 포함한다.

## 환경·계약·이전

- [environment.py](/home/ajou/yigyu/3/guitar_learning/curriculum/environment.py:70)는 매 reset 전에 원 task와+3초 실행 task를 선택하고 기존 reset 체인을 호출한다. 측정기·음악/skill/timing/quality ledger·guide·관측 builder가 새 task로 재구성되는 CPU 근거를 확인했다. native session은 재사용한다.
- 각 worker는 두 episode 주기마다 event `[0,2]`를 한 번씩 선택한다. 실제 선택은 reset·step·terminal의 `episode_task`에 남고, 정책/worker 계약에는 전체 후보를 일정한 순서로 담는다. 선택 순서·worker가 달라도 상태563와 계약이 안정적이다.
- 목표 차이는 기존 현2와 추가 현3의 fret7/finger3/down 단음이다. 동일 episode에서 두 음을 연속 연주하거나 화음을 연주하는 경로가 아니다. 기존 action39·clock7초·native정착0초·관측 scale·보상·안전 제어의 변경은 없다.
- [transfer.py](/home/ajou/yigyu/3/guitar_learning/curriculum/transfer.py:19)는 원563 완료 PPO·역할·architecture를 확인하고 원 fixed task가 변형 없는 pool member인지 검사한다. 그 밖의 관측/행동/보상/물리/안전 계약은 같아야 한다. 모든 state tensor의 shape/dtype/유한성과 source SHA를 확인한 뒤 선택 손 Actor와 해당 std만 복사한다.
- critic·다른 손·optimizer·RNG·update counter는 원 checkpoint에서 가져오지 않는다. fixed-task checkpoint의 pool strict resume는 거부하고 같은 pool의 정확한 identity로만 strict load한다. 새 목표의 성공을 상속하지 않는다.

## 학습·평가 연결과 발견 사항 해결

- [train.py](/home/ajou/yigyu/3/guitar_learning/curriculum/train.py:43)는 기존 quality→actionable→timing→specialist→parallel 실행기를 재사용한다. pool spec과 module-level worker factory가 중첩 경로 끝까지 전달되고 Actor 이전이 optimizer 생성보다 먼저 실행된다. strict resume에서는 Actor 재이전을 건너뛴다. 정상·예외 뒤 patch binding 복원 검사도 통과했다.
- 검수자가 fresh subprocess에서 첫 compact의 **RecursionError**를 재현했다. 새 factory가 원 specialist logger를 미리 bind하지 않은 것이 원인이었다. [train.py:27](/home/ajou/yigyu/3/guitar_learning/curriculum/train.py:27)의 선행 binding으로 수정됐고, specialist 모듈이 미로드인 새 subprocess에서 factory→실제 compact 호출 회귀가 통과했다.
- 검수 중 관찰된 반복 helper 선택 문제는 테스트의 `patch.dict(sys.modules)`가 새 모듈을 삭제하고 package attribute를 남긴 harness 문제였다. 담당자가 runtime 모듈을 context 전에 import하도록 검사만 보완했다. 이를 별도 생산 결함이나 native 실패로 기록하지 않는다.
- [evaluate.py](/home/ajou/yigyu/3/guitar_learning/curriculum/evaluate.py:35)는 episode에 기록된 실제 event index로 group·coverage를 집계한다. 설정된 후보 전체를 실제 실행했다고 간주하지 않는다. CPU double에서 서로 다른 두 목표의420tick 실행·terminal metadata·quality와 timing-only 구분·840행 출력·close를 확인했다. 이 double은 native 안전 검증이 아니다.
- 미래 `long_{left,right}_v1/final.pt`를 가리키는 pool 설정은 기존 실행이 끝난 뒤 검증하는 설계다. 현재 파일 미생성을 사전 검수 실패로 처리하지 않았다.

## 실제 검증과 남은 범위

- 담당자 동결 통보 뒤 검수자가 새 환경·이전·runner/evaluator의 **11개 focused CPU 검사 / 13.768초 통과**를 확인했다. watcher15개와 별개다. 전체 기존 unittest는 root가 실행 중이었으며 이 보고서에서 완료를 주장하지 않는다.
- 원 장기 실행의 source pin **169파일을 재해시해 변경0개**를 확인했다. 새5파일은 원169개를 대체하지 않는다. 검수한 `train.py` SHA는 `2334b379d2ed72cd12ee1d2d3156eaf399fafc9b8f0d8c156ab38e22999d349e`다.
- [execution_pins_v1.json](execution_pins_v1.json)의 신규15파일과 원 장기 실행의6개 execution pin을 독립 재해시해 모두 일치함을 확인했다. 실제 `watch_v1/status.json`은 아직 생성 전이며, 전체 기존 CPU 검사 완료와 detached watcher의 대기 상태는 추가 확인 범위다.
- 실제 최근64개 진급 판정·결정적4회 평가·새 pool native2회 preflight·확장 PPO는 아직 실행하지 않았다. 조건이 충족되어 해당 단계가 실행되기 전에는 새 pool의 native 안전·성공·장기 수렴을 주장할 수 없다.

README는 이 범위와 일치하며, 원 단음 학습을 유지한 채 종료 후 조건을 확인하고 통과한 손만 제한된 두 단음 pool로 확장하는 구현으로 설명한다.
