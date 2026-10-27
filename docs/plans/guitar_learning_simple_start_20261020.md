# 초기 자세에서 바로 손별 학습 시작

사용자 승인: “그렇게 하자 초반 흐름을 정리해줘”. 새 기본 실행을 확정 자세 → 손/기본 과제 → 새 PPO → 저장으로 단순화한다. 기존 재현 경로와 엄격한 checkpoint 재개는 보존한다.

- [x] 현재 초기 자세·세션·손별 환경과 runner 재사용 경로 조사
- [x] README/AGENTS 원본 보존, 구현 범위 확정
- [x] 새 train 진입점/설정·실행 연결 구현
- [x] BC·성공평가 없이 시작하고 반대 손0·정책 준비/안전 계약이 유지되는 CPU 검사
- [x] 실제 native 단기 수집·PPO 업데이트·모델 저장 확인
- [x] 안내/AGENTS 갱신, 관련 회귀 검사 실행과 별도 변경 검수 — 전체 회귀 통과는 아래 SIGFPE 제한으로 미확인

구현: 루트 train.py는 간단 CLI, training/start.py는 기존 train_parallel/parallel/SpecialistPolicy/quality worker 조합. 기존quality의 학습/초기화 wrapper는 호출하지 않는다. 기본 왼손 press/right strike 과제는 검수 번들의 첫 단음·563상태·39행동이며 선택 외 손은0잔차. native0초/정책7초(준비3초 포함)·240/60Hz·035/v14 snapshot과 물리 안전/관절 제한 보존. 양손 동시 학습은 기존 별도 진입점을 유지한다. 새 기본 학습에 과거 교사/BC/성공평가 gate를 요구하지 않는다.

완료 기준: 간단 명령으로 새 정책의 실제 native PPO1회와 저장 완료, 기존 gate/strict resume 경로 무변경, 실패/중단에도 전역 binding 복원·작업자 종료.

초기 단기 실행: 왼손/오른손 각각420전이·PPO1업데이트·7초1episode·final.pt 저장·persistent/원물리/source 검사 통과. 음악 성공은각0/1이다. 현재코드의 왼손 strictresume은20전이 추가해PPO업데이트1→2, initial payload는metadata를제외한모델/optimizer/RNG/identity가원final과정확히같다. 첫단기실행 뒤deviceauto를추가했고당시소스는별도보존했다. 첫CPU검사의Pool MagicMock 상속문제는실제fakeclass로바꿔동일한중단조건을확인했다. 새 train.py가 원래경로를 재사용하므로 기존 retired-source회귀검사는 같은원manifest의 여전히보관된auditv1경로로변경했다.

최종 관련CPU19검사pass. 전체 회귀 두 호출은 기존 transition/probe.py rawJSON 경로SIGFPE(exit136)로중단했고 isolated재현도같은callstack. 순서변경17개검사는pass, readonlyFP진단240tick/483check정상이나 원인해명은아님. capture이후분할검사도기존serialization_v2 float표현비교에서SIGFPE로중단. 제품코드/FPUmask/backend는변경하지않았으며 전체/분할회귀pass를주장하지않는다. 최종385Python SHA동일/native190/tool18·CAS·보관본검사, 독립검수에서새소스결함없음. 기존직렬화/native부동소수점오류의원인규명은남아있으며새초기실행연결은완료했다. 상세는 docs/2026-10-20/guitar_learning_simple_start_v1/README.md 참조.
