# 가까운 직립배치에서의 가슴 법선 누름 비교

정지V8은source9/RHip_xbias−.08로5초/직립각/안전조건을통과했으나Chest접촉0이었다. 종료sourceChestgap3.580mm,Spinegap−.148mm,RHip실제−1.673951rad다. Chest의고정materialpoint3D지원은거의아래10N에포화되어기타와의법선간격을효율적으로줄이지못한다. source2의normal10N단독시험은간격15.84mm로실패했으며그방법을정답으로채택한것이아니다.

이번은source9초기배치·모든관절각/upper/lowergain·토크cap/RHipbias−.08/RShoulder20N/모든물성·원모델·제약을같게두고Chest를기존독립검수된최근source법선방향의단측누름(controller7)으로바꾸며가상요청한도를10→20N으로둔다. penetration목표3mm,법선K2000N/m/D30Ns/m는같고접선slip을허용한다. 실제기타에직접힘을적용하거나붙이지않으며인체관절effort만기존원cap안에서제출한다. 20N은측정접촉력이아니다.

두항목(가슴힘방향/한도)이같이변하므로이시험만으로각효과를따로확정하지않는다. 앞선gap와관측된상체 compliance로남은수mm를검사하는유한접촉후보다. 실제정지5초에서Chest/RShoulder의양의solverresponse>95%(1초이후),Torso/Chest전체≤5/옆≤3,하체좌표/foot/속도/모든Guard·SHA를통과해야성공으로판정한다. 그뒤같은설정으로15초왼손해제,새PPO없음.
