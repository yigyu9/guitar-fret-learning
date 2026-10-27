# 고정 스트랩·중지3 목표 총−0.15rad 비교

직전−.05rad actual5초/영상/분석19검사/최종96검사를봉인했다. 중지3은57.820850°까지펴졌고후기1초.437298mm/.081147°로기타유지가무너지지않았다. 따라서이번은progress뒤의다음한후보다. 스트랩출처질문은길이변경의승인이아니며현재LA를유지한다.

## 변경과 불변 조건

관절18baseline에서LH:middle3 유지목표만총−.15rad(직전−.05보다추가−.10)를준다. 예상목표약52.09°이며초기각60.145874°는그대로다. 초기81각/G p·q/LA1.1018469719600776m/root·하체고정/몸통9목표와PD×2/양측Thorax이하66권한/self-collision/손목±.005rad1Hz를보존한다. 중지2와어깨는다른후보로분리하고이번에바꾸지않는다. 초기자세변경이아닌유지목표변경임을영상과문서에명시한다.

기존모델한계·offset±.3rad·float64합→float32무clipping·손목극값을검산한다. Fresh14/1188source admission후frozen native runner로한초기화/1200step 실제0~5초를녹화한다. CPU/GPU는실제로그로명시한다. 원본native와실제passive 스트랩13route표시PNG·두151frame30fps영상을보존한다. 실패/partial을숨기지않는다.

## 검증 순서

- [ ] 새leaf/producer/기존봉인입력closure와trial준비를기록·검수한다.
- [ ] 동일초기값fresh gate후실제5초와두영상을저장한다.
- [ ] 기준/−.05/−.15 세조건의raw초기값·다른80목표·1200명령시계·고정root하체·PD를대조한다.
- [ ] 중지3실제추종·중지2목표보존·bounds·palmproxy·rawλ/self접촉을비교한다.
- [ ] 초기30mm/5°와후기완전1초5mm/1°임시구역,이전2초참조지표를분리해평가한다.
- [ ] 실제초기/5초장면·그림·영상모음·한국어결과·독립검수·최종보존감사를마친다.

이번범위안유지만으로자연성/연주성공을선언하지않는다. 중지분포는soft선호이며공용hard limit변경은없다. Source gate는cooked동적관통/해부학패드인증이아니며rawλ는N이아니다. 더펴는목표가접촉/유지를악화시키면그대로기록하고초기q또는다른중지관절분리를다음단위로결정한다. 기타고정/손강제부착/지속pose덮어쓰기/인위적인world목표힘은금지한다. 새actor/학습/controller/reward는없다.

메인계획·구현은 /home/ajou/yigyu/3/stability_adapter_2, 이번원자료·로그·미디어는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2 에저장한다. 실행전producer/helper/leaf/invocation을full path/SHA로보존하며명령·환경·exit와전후SHA를남긴다. 이전실험/공용자산은보존한다.
