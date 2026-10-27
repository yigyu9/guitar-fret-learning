# 기타 위 볼록부 · 겨드랑이 쪽 상완 접근 결과

**초기 간격은 줄였지만, 겨드랑이 쪽 접촉은 아직 만들지 못했다.** 가장 가까운 어깨쪽0~35% 상완 간격을 이전14.150mm에서4°후보5.669mm/6°후보5.029mm로줄였다. 최종 약한접근 조건은 머리·왼팔 접촉 없이 상완 전체 접촉1075/1200을 보였지만, 실제 접촉은 상완 중간 부근이다. 초기 기타 자세 유지 성공으로 채택하지 않는다.

## 무엇을 맞췄나

사용자 지정 방향은 player-right=정면 화면 왼쪽=기타 바디 쪽이다. 위 볼록부는 현재 상완 아래의 큰 바디 외곽(Gx<−.17m, Gy−.55..−.43m)으로 해석했다. 모델에 겨드랑이 살이 따로 없으므로 R_Shoulder capsule의 어깨 쪽0~35%를 접근 대리구간으로 썼다. 기타의 해부학적upper bout(넥쪽작은폭) 전체라는 의미가 아니라 현재world위쪽의큰볼록외곽이다.

초기 몸통은 원 자연 오른팔 기준 추가Chest4°/6°,Torso25%·Spine62.5%를주고Head초기world방향을보정했다. 오른Thorax/Shoulder/Elbow9각을모델한계안에서맞췄다. 손목·손가락·왼팔 초기 scalar각은 유지했다. 세실제시험 모두 기타초기p/q가동일하고,조건2/3은휴머노이드를포함한fullnative초기상태까지정확히같다. body scalar관절변화와world회전각은같은양이아니다.

root·하체 고정,스트랩OFF,왼손지지없음,기타자유를유지했다. 기타직접힘·손부착·진행중pose덮어쓰기는없다. 오른팔12는humanEFFORT,나머지69는기준각POSITION PD다. source 전체겹침검사와analytic capsule 검사는실제PhysX cooked인증이아니다.

[이전 기준 간격 계산 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/baseline_source_probe_v1.json:1).

## 실제 0~5초 비교

| 조건 | 바디BB중심 이동 | 전체SO(3)회전 | 최종넥고도(초기0°) | 전체상완접촉 | 머리접촉 | 지정35%·볼록부접촉 |
|---|---:|---:|---:|---:|---:|---:|
| right4_upper35 | 303.680mm | 113.813° | 63.971° | 135/1200 | 796/1200 | 0/1200 |
| right6_upper35 | 234.261mm | 82.276° | 56.665° | 180/1200 | 728/1200 | 0/1200 |
| right6_gentle_press | 59.465mm | 53.935° | -13.709° | 1075/1200 | 0/1200 | 0/1200 |

세조건의왼팔·왼손접촉은모두0/1200이다. 접촉표본은240Hz에서각물리step후관측한presence다. positive rawlambda표본·힘(N)·지지비중을동일시하지않는다. 바디BB중심은질량중심이아니다.

첫두조건은상완기준점을초기기타surface6mm안쪽으로맞추고각점요청힘cap30N을사용했다. 큰기타회전과머리접촉으로거절했다. 세번째는같은6°초기값에서상완human표면기준점2mm안쪽/cap5N으로줄이고,전완human표면기준점8mm접근방향을이전양호조건의Gnormal로맞췄다. 전완cap30N·K/D·posture/gc·모델토크한계는유지했다. 두점목표는초기world에고정된인간motor목표다. 실제접촉력명령이나기타힘이아니다. **여러제어요소가함께바뀌어서어느하나의인과효과를분리한실험은아니다.**

약한조건의2→5초추가변화는바디0.132568mm/전체회전0.066829°로작다. 하지만이미59.465mm/53.935°변화한자세에정착했기때문에초기상태유지성공이아니다. 이전양호4°조건47.501mm/47.662°보다도초기기타변화는컸다. 상완전체접촉256→1075표본증가를겨드랑이지지성공이라고설명하지않는다.

## 실제 접촉 위치 확인

raw contact의localPos+offset을각nativebody의p/q로world변환했다. 양쪽feature일치최대오차는약1.23e−7m,source캡슐반경과contact위치의차이는최대.220mm였다. COM좌표로임의변환하지않았다. human캡슐축투영fraction≤.35와G위볼록영역을함께검사했다. 이전조건과이번3조건모두qualified0/1200이다. 약한조건positive접촉fraction은약.490~.619로어깨쪽목표구간보다팔꿈치쪽이다.

[실제접촉지역원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/contact_region_v2.json:1), [실제이미지·참고점/접촉점표시](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/README_V2.md:1). 표시한어깨쪽참고점은실제접촉점으로설명하지않는다. 위치검사도해부학적살/지지력/전체solver내부접촉을인증하지않는다. source4/5의추가mid-depth Gz조건은별도초기후보조건이며현재native지역판정의Gx/Gy조건에합쳐서검사했다고주장하지않는다.

## 검증과 파일

세시험모두1200physicsstep/300control/151frame으로실제5초를끝까지실행했다. 영상은30fps/5.033초다. 출발감지래치가서도시뮬레이션/토크를멈추지는않는다. checkpoint/학습/노이즈는이번단계에서사용하지않았다. 분석은초기값·기록·두점요청토크합/모델clip·POSITION69readback·제한된point속도일치검증이며중력/Jacobian전체인증은아니다.

[조건1검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v1/verification.json:1) · [조건2검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v2/verification.json:1) · [조건3검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v3/verification.json:1) · [요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/result_summary_v2.json:1) · [영상6개색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/INDEX_V1.md:1).

## 중간 시도 보존

- source1은근위4mm/팔꿈치아래20mm의임시기하문턱에서거절해native0. source2는진단문턱6mm/15mm로원해를바꾸지않고수락했지만필수predicted_human_poses누락을사전검수에서발견해native0. source3은genuine calibrated FK66body를추가하여같은q/G를actual에사용했다.
- source4는추가앞굽힘6°와전완받침유지를함께맞추지못해거절했다. source5의기타몸쪽최대20mm/위12mm초기이동탐색도전체상완음수간격·근위문턱실패로거절했다. **이두source해는native실행하지않았다. 세actual조건의기타초기높이/위치를바꾼것이아니다.**
- source/계획/준비파일/실패검수/첫두native악화/이전양호후보를모두보존한다.

## 다음 판단

어깨쪽참고점과실제접촉점이아직다르다. 상완전체접촉을겨드랑이지지로등록하지않고이전양호조건을보존한다. 다음에는이전전완지지를유지한채어깨쪽기준점의위치와바디외곽을한요소씩바꾸어접촉지역을확인하는편이적절하다. 누름크기만늘리는방향은현재결과로권장하지않는다.

[현재제어비교계획](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BOUT_AXILLA_PLAN_V6.md:1) · [변경파일과실제줄번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/CHANGED_FILES_v1.md:1).
