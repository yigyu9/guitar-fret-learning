# 앞2초를 정책의 음악적 준비에 사용

사용자 요청으로 앞의 정책 비참여 native 정착2초를 행동 가능한 준비 시간으로 전환한다. 기존 음악 시각과 전체 물리 길이는 유지한다. 이전 논의의 정책 준비1초도 보존해 이번 변경의 효과를 분리한다.

## 계약과 성공 기준

- 기존: native2초+policy5초(pre-roll1초), 첫 음은 reset부터4.12초.
- 신규: native0초+policy7초(pre-roll3초), 첫 음은 reset부터4.12초. 처음부터 목표가 관측되고 첫 행동/물리/보상/비용이 PPO 전이에 포함된다.
- Root고정·하체유한·105/97/8·자유기타/중력ON/strapOFF·기존gain/의자/충돌/안전/행동39를 유지한다. 초기 state는 reset당1회만 복원한다.
- 첫2초 LH 준비 보상은 기존 target candidate의 previous/current 연속 접촉시간×.2/s이며 RH는 기존 guide를 사용한다. 거리 proxy는 이전 성공교사와 맞지 않아 채택하지 않았다. 준비 보상으로 기존 접촉/타현/음악 성공 판정을 바꾸지 않는다. 안전 실패tick의 양성 보상은 억제한다.
- 새로운 시작/시간 계약은 actor-only 명시적 이전을 사용하고 strict resume를 완화하지 않는다.536차원 timing history scale 보정과 행동 기준 일치를 확인하고 실제 성공은 별도 평가한다. 기존모델 성공을 상속하지 않는다.
- 기존 source/실행/실패/영상은 보존한다. 변경은새파일,이전버전 exact byte/SHA archive 후 진행한다. 환경·이전·실행기는소유파일을분담하고 source freeze 뒤native를실행한다.

## 단계

- [x] 기존구조 확인·이전버전/문서보관·새환경 및 이전 규약 구현. 환경9·이전6·runner3검사통과후source freeze.
- [x] CPU 검사: reset물리0,첫2초action적용·관측목표·보상/비용,420tick/horizon7,고정원음시각·안전/실패/재reset·엄격한checkpoint.
- [x] 양손 실제0초reset/첫2초행동·안전·전체7초평가. 기존Actor이전각2/2안전단계성공,LHcoverage1·RH오차57.98/104.19ms. 재BC없이진행,실행중소스불변.
- [x] N1/H420/PPO1update(역할별)로처음2초120전이포함과sim재사용·저장연결확인. 각420전이/1update완료·후속각1/1안전·LHcoverage1/RH86.215ms. 성능개선으로해석하지않음.
- [x] 독립검수·문서/권장config연결·입력과이전결과보존감사·완료정리. 검수문제없음,소비입력1649개SHA일치·115py불변·6scene종료·이전1075봉인/영상보존·source228사본확인.

결과경로: docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1. 코드: guitar_learning/. 테스트: guitar_learning/tests/.

최종native전 초안수정: 기존distal-origin거리식의한계를확인해접촉시간보상으로대체했다. proxy초안은archive/preparation_proxy_draft exact보존했으며, 수정중이던초안CPU실행은최종인증에사용하지않는다. 최종freeze후전체CPU검사를시작했다.

최종CPU discover256개100.320초PASS,동결115pySHA불변. native구동전GPU4070Ti사용0%/20MiB·availableRAM약28GiB확인.

최종결론: 첫2초정책제어/PPO120전이포함·전체7초안전연결완료. 실제준비접촉보상은이번모델에서0이고RH정밀도는기존보다악화했으므로조기준비/정밀학습완료로설명하지않는다. 추가장기학습은이번구현범위를넘어자동진행하지않았다.
