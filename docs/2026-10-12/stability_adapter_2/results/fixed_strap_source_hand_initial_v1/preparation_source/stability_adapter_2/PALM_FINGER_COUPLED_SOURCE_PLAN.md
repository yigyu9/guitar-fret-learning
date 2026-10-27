# 다음단위: 팔12+엄지·검지·중지singlehinge6의연동source보정

Measured-pose 팔12보정은t0 quarter만새source교차증가없이통과했고그이후는검지·중지의G교차를증가시켰다. 손바닥대표점오차가줄어도전체손지지/안전성을뜻하지않는다. 해당방향의nativeON은실행하지않았다.

추가24시점×6관절에서actualparent조건부singlehinge bodypose는최대0.000130835mm/1.878054e-7rad로기존gate안에들어왔다. 사용할수있는관절은LH:thumb2/3,index2/3,middle2/3다. 두좌표finger1 map실패는아직미해결이며현재measuredpose로만읽는다. 이18축은초기지지보정의임시범위이며최종66권한을제한하지않는다.

1. 각저장시점actual부모·자식relativepose를현재source snapshot으로읽는다. 팔12의예측변화와여섯singlehinge각변화를조합해source bodypose를계산한다. Finger1/다른heldfinger의relativepose는현재measured값을유지하고새two-axis FK를가정하지않는다. Physicsjoint/body/guitarstate에는쓰기없다. Fraction0 worldmesh identity와palm/각hinge차분·형상을검사한다.
2. Palm 요청옆면지점/법선,thumb rear plane, index/middle front plane을함께고려한다. 최소제약으로palm+Z반구,모델/Aug19한계·initialoffset±0.3·원래PDbase와현재q의차이를보존한다. 원본PDbase+residual이최종목표이고actualq로base를치환하지않는다. 정확평행은hard하지않고normal정렬을soft로한다.
3. 첫source18각범위는팔±0.05rad/finger6±0.10rad와모델/Aug19/최종PDtargetoffset경계의교집합이다. 현재손shape vertex/점의position·normal Jacobian을central±0.0001rad로계산한다. Palm접근과동시에front index/middle가더깊게들어가지않고thumb후면으로이동하도록bounded least-squares/선형plane제약을검토한다. Wholepalm·frontdistal·thumbshape전체를sourceLP/유한patch witness로검사해대표점만통과시키지않는다. Fraction1/0.5/0.25를원범위안에서비교한다.
4. Source self-screen에서연결body capsule의원래겹침을실제native접촉으로동일시하지않는다. 이전측정의mask허용source selfpair에는Chest–Thorax/Shoulder–Elbow같은연결부큰겹침이포함된다. Nativepolicy는그대로두고,source후보선별의연결graph거리≤2 제외는기존near_contact_initial_audit와같이적용하며해당쌍도별도진단으로보존한다. 실제SDK selfcontact는계속전체기록한다. Finger–G의새/증가source교차는연결부문제로없애지않는다.
5. 안전한연동방향이있으면PD잔차상한/변화율/적분gain의명시적실행계약후ON 한actual5초를진행한다. Body9PD×2·initial81/G/LA·나머지목표·자유G/passivestrap/root하체fixed는같다. Grip/위치·회전이실제개선되는지동시에측정하고초기값·스트랩전신/손151frame영상과원자료를저장한다. Source고정G/순간finger가정은실제PD컴플라이언스/자유G반응과다르다.

- [ ] 실제18축snapshot FK·source형상/차분검증
- [ ] 연동후보의모델/PD경계·상향·whole-shape/pair진단
- [ ] 실행계약후ON 한5초·strap영상·G p/q/면근접·후속복원제어

계획은미실행이다. 목적은palm옆면·thumb후면·나머지finger전면지지로자유G의초기p/q유지와이후복원을가능하게하는것이다. 연주66목표+안정화보정의최종target/우선순위·clipping/antiwindup을설계한뒤학습구조를정하고WAIT→REACH→GRIP→TRANSPORT를연주필수선행상태기로두지않는다.
