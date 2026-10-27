# 교정 후 자세에서 압현·타현 지지 안정성 시험

사용자가 오른쪽 교정 후 자세에서 압현과 타현을 수행하도록 새로 요청했다. 이전수평phase는전체5초기준실패인상태로보존한다. 이번은사용자가명시적으로요청한동작진단이며기존실패를통과로바꾸지않는다. 15초왼손해제/PPO학습은하지않는다.

## 입력·물리 조건

source4초기candidate/initialupper목표/scene8/controller_horizontal_v4를유지해0~5초를동일하게진행한다. 오른쪽비교이미지는그5초종료이므로전신을그프레임상태로재주입하지않고같은시뮬레이션을계속진행한다. Root·의자고정/하체finite SPD/105채널·97비영원범위·명목zero8/기타freegravityONstrapOFF/동일물성·gain·cap·rate. 기타고정·직접힘·강제부착·매step상태덮어쓰기금지.

## 비교 순서

새phase에서각9초의정지대조/압현만/타현만/압현+타현을독립초기화해비교한다. 모두0~5초는원제어와같고동작은5초이후다. 원5초rawstate·effort·target배열prefix가같은지확인한다. 안전중단시실제경과와미실행동작을명시한다. 먼저단독동작을실행하고가능한경우결합을실행한다.

압현은이전5초의실제LH:index3 marker에가장가까운실제string/fret구간을고르고index4 native POSITION관절목표만IK로변경한다. 왼팔/손다른목표는기존대로이며목표를순간이동주입하지않는다. 5~5.8s hover접근/5.8~6.3s 줄면−4mm목표/6.3~8s유지/8~8.5s해제/8.5~9s관찰. finger bodyorigin은해부학적pad가아니다. 지정손가락 실제guitar접촉과XY10mm/Z−6..+10mm밴드/연속100ms를함께통과한경우에만압현후보성공이라고부른다. 줄은marker이므로압력N/음향/실제줄변형성공으로확대하지않는다.

타현은기존solve_pick 6DOF 위치IK를105FK에연결해최종command직전R_Elbow/Wrist6만override한다. 기존right12IK에서proximal6목표와finite사람지원task는유지하지만타현동안distal6소유권은동작에있다. 다른fixed-lower81 scene/정책/effortwrapper는이식하지않는다. 가상RH:pick이G:y−.325m에서6개줄범위밖12mm→줄면−4mm진입→6.5~7.1s down→7.3~7.9s up→8.5s철수한다. 실제손가락/기타접촉은따로기록하고원PickStrikeDetector속도/깊이/zone/rearm판정으로줄통과를평가한다.

## 판정

초기0~5s와동작5~9s를분리한다. 기타몸통AABB중심의동작시작대비이동30mm/회전5도/넥abs3도/원래좌우±20mm/TorsoChest total5·옆3도/위팔양의접촉95%를동작중진단기준으로사전고정한다. Chest도별도로빈도를기록하며원full조건은가슴·위팔동시95%가추가된다. 원래초기5초기준은미통과상태이며그것을제외한동작구간통과와혼동하지않는다. 실제압현후보/유효타현통과가없으면손이움직인것만으로연주중안정성검증성공이라고하지않는다.

안전은기존native qd50rad/s/Groot이동.20m/회전35도/상체J속도.01m/s/하체좌표질량/finitecap/금지API기준을유지한다. 계산IKerror2mm/finger3mm/원범위/principal160도확인. 필요조정은실패원본을보존한새버전에서하고gate를소급완화하지않는다.

- [ ] 입력보존·목표도달preflight와실행계획기록
- [ ] 동일5초준비후단독압현/타현/결합진단실제실행
- [ ] 전표본동작성립·기타움직임·접촉·prefix대조/실제영상
- [ ] 독립검수·새소스사본/로그·기존자료보존감사
