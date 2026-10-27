# 후면 엄지 source 면 catalog 실행 계약

현재같은half초기native저장pose에서thumb3 활성sourcehull을재구성한다. 이전rear_facet_v2의소비source/출력/한계를expectedSHA로대조후read-only사용한다. Newsource변경범위는catalog지점선택뿐이며PD/초기값/physics변경은없다.

- 후면지향initialG+Z dot>.75인모든triangle centroid와면적/법선/G위치를기록한다. 선택을해부학적pad인증으로표현하지않는다.
- 원rearquad의모든edge에서수직2mm 안쪽으로줄인finitepolygon의최근점거리를구한다. RearGZ−8mm를그대로사용한다. 각지점의diagnostic goal은그최근점에서rear바깥으로.7mm offset한점이다. 이taskspacegoal은source계측이며기타에힘을주거나pose를고정하는명령이아니다.
- 동일17좌표에서sourceFK를±.0001rad centraldifference로평가하고모든centroid를같은bodypose에적용해각3×17Jacobian을구한다. NativeDerivative가아니며state를제출하지않는다.
- 이전.20범위의실제bounds를읽고순수선형box constrained least-square예측/residual/축별min-max변위를기록한다. Linear residual은정적FK/겹침/actual접촉/물리유지/제어가능성의인증이아니다.
- Offsetgoal까지초기필요거리순으로정렬하고centroid간격≥2mm인최대2점을선택한다. 최대면적323과원관측최근면786을별도source기준으로보존한다. 기준786이후면조건미달이어도비교기준에서숨기지않는다.

Plan/구현은stability_adapter_2, catalog/raw/log/그림은docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1에둔다. 이번catalog의native/physics0을명시하며후속bounded각검색은별도leaf계약으로진행한다. 최종66권한/몸통9PD목표/root하체물리고정/자유기타·수동strap/selfcollisionON조건은같다.
