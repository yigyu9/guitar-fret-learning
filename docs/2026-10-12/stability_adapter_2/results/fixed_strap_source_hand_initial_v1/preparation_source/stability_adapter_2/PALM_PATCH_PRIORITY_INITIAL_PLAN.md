# 요청한 손바닥 옆면부터 맞추는 다음 초기 배치

## 실제 결과와 방향

three_face_near_contact_diagnostic_v1의 같은 초기81q·LA에서 기존손가락목표는최대25.779645mm/7.800837°, 새초기21목표는37.615076mm/8.587915°로악화했다. 따라서21개전체초기목표를새기준으로채택하지않는다. 기존목표에서thumb3 SDKfeature 후면source patch근접(투영내부·plane±2mm) 양λ고유30step/last260, middle3전면1082/last1200은있었으나 palm요청옆면0이다. palm body양λ와요청patch는다르며근접거리19.323948~20.518808mm를관측했다. 초기source palm hull거리2.157424mm와actual접촉특징을구분한다.

여러면을같은weight로동시에맞추기보다, 다음새source단위는파란영역의손바닥옆면지점을먼저맞추고엄지후면/전면손가락을보완한다. 중요한범위·목표변경은사용자의자율진행지침에따라기록한다. 원본source/native·실패분석·영상은수정하지않는다.

1. 앞선wide old_near17과support-plane old_near17의두완료q를새seed로사용한다. 왼팔12±.15rad/손가락21±.3rad와native/Aug19/C02/oldtarget한계의교집합,other48/기타p·q/LA1.1018469719600776m/PD·solver를유지한다. 초기최적화목적은palm source대표점–finite옆면patch 우선, 평행soft·up반구와wholepalm/wholethumb 분리다. 특정대표점은해부학적pad인증으로쓰지않는다.
2. 첫단위는두source후보로제한한다. native전source전체human–guitar/양손/비인접왼손겹침0과nativebounds/상향/FK를다시검사한다. 엄지/각tip의point/wholehull거리·방향·margin을그대로기록하고, 지지미달을성공으로바꾸지않는다. 접촉이없는source검색과actual5초trial집계를분리한다.
3. 실행시간을줄이기위해self-pair 분리penalty 계산을읽기전용기하검사로점검한다. 현재support-plane3후보14.74분·residual당dense요소46,619,840개다. 허용분리축으로전체hull을project해clearance이상임이증명된pair만dense검사를생략하는후보를검토한다. source최종LP교차gate는유지하며, old/new residual대조에서차이가나면새목적함수변경으로명시한다. 단순성/소수후보가우선이고과도한최적화는하지않는다.
4. 안전한근접후보가나오면최대두actual5초진단: 기존81목표를기준으로하고필요한엄지/손가락의작은개별목표변화만비교한다. blanket21초기목표를승계하지않는다. 모든새trial초기값/전신·손0~5초영상,SDKfeature옆면/후면/전면위치를기록한다. baseline변화만으로기타feedback/학습을확정하지않는다.

현재기타제어는passivestrap+물리PD와접촉이며기타목표p/qfeedback은이단계에서추가하지않는다. 연주목표+안정화보정을최종66목표로합치는권한관계는유지한다. 몸통9목표PD유지와실제약4.23°drift를구분하고root/하체는물리적으로고정한다. 기타고정/강제부착/pose덮어쓰기없음. 이계획은미실행이다.

- [ ] source분리계산 검증·두seed/palm우선 목적 준비
- [ ] 두source초기배치/겹침·지지점 대조
- [ ] 안전후보actual5초/기록과후속제어방향
