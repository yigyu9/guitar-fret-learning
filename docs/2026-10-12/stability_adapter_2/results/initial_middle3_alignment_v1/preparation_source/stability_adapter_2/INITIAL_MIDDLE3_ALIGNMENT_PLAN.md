# 중지3 초기각과 유지목표 정렬 — 같은절대목표 비교

직전총−.15rad actual5초/후처리31검사/최종109검사를완료한progress다. 중지3은60.145874°에서52.090865°로펴졌고기타후기1초.437387mm/.080289°를관측했다. 이번은시작부터그목표에가깝게배치하여초기손모양과초기접촉/기타변화를검증하는다음한후보다.

## 변경과검증할계약

직전fixed_strap_middle_relax_v2/native를기준으로LH:middle3 초기q만기존heldgoal0.9091416597366333rad(52.089980°)로설정한다. 이관절offset은0으로하여같은최종절대81목표와같은1200손목명령을제출한다. 다른80초기각/목표·기타초기world p/xyzw q·PD/body9·LA1.1018469719600776m·root하체고정·selfcollision·양측Thorax이하66권한은유지한다. 중지2/어깨/더큰굽힘완화/LA는동시변경하지않는다.

Float64합→float32무clipping·모델bounds·offset±.3rad·손목±.005극값을검산한다. 기존검증CoupledSnapshot의18좌표중middle3 하나만변화시키고source예측state에서는middle3와하위top 두body pose만갱신한다. 다른body/기타state는정확히보존한다. Zero-delta FK를원rawpose와대조하며source인체–기타/양손/1188개정책상self쌍·손바닥위반구를초기검사한다. 이source예측은물리실행/해부학패드/cooked관통인증이아니다.

Source gate탈락이면trial/proposal/교차상세를보존하고native시험을실행하지않는다. 통과시frozen run_palm_witness_initial_diagnostic를재사용하여fresh14/1188 및native q/FK를대조한후한초기화/1200step실제5초·두151frame스트랩영상을기록한다. 실패/partial도남긴다. 초기body pose중실제로바뀐범위를raw로대조하고최종81명령/시계가이전조건과exact인지확인한다.

초기대비30mm/5°와후기완전1초5mm/1°는임시관찰구역이며0~.5초의G위치/회전·속도도별도로본다. 중지3초기목표오차/5초추종·접촉rawλ·self접촉·palmproxy·실제관절bounds와기존2초참조값을함께평가한다. 자연성/연주완료를선언하지않는다. 손분포는soft참고이고중지2크기만으로펴지않는다.

## 작은단위체크리스트

- [ ] 초기q/offset/예측source FK·gate·목표보존을준비하고독립검수한다.
- [ ] 통과후fresh native검사와실제5초/스트랩영상을확보한다(탈락시0물리기록).
- [ ] 저장raw2조건·최종81명령·초기변경범위·기타/관절/접촉/임시구역을분석한다.
- [ ] 한국어결과·초기/종료이미지·영상모음·독립검수·보존감사를완료한다.

## 입력·소스보존

직전입력closure와직전봉인inventory1561파일의전후/current SHA를유지한다. 이전snapshot내py는이번에실행하는module이아니므로새source snapshot에재귀복사하지않고기존보존경로와SHA를참조한다. 이번에실행/재사용하는canonical stability_adapter_2 모듈·새leaf·이전decision·invocation은실행전에새snapshot에복사한다. 입력closure자체를잘라내거나기존bytes를바꾸지않는다. 이구분으로이전source사본의중복재복사를줄인다. 명령/env/log/exit·전후SHA를저장한다.

메인계획·구현은 /home/ajou/yigyu/3/stability_adapter_2,결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1 이다. 기타고정/손부착/지속pose덮어쓰기/world목표인위적힘은없고새actor/학습/controller/reward도없다. 최종66연주권한과자유G를유지하며스트랩출처pending은현재고정길이시험을막지않는다.
