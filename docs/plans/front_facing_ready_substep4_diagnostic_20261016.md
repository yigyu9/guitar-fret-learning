# 내부 시간분할 1/2/4의 5초 대조 진단

원4/2/substeps1,8/4/substeps1 및4/2/substeps2가 완료됐다. substeps2는 최대 잔차 감소10축/증가3축/동일92축이며 exact bound false·원인미확정·채택false다. 특정축 peak만으로 성공을 선언하지 않는다. 원 source/leaf/raw/result는 그대로 보존한다.

## 실행·검증 체크리스트

- [ ] 기존원자료의 spherical qdot/SO3 Jacobian과native dq의 경계방향·PD교차항을 읽기전용으로 비교한다. 반사실제어효과를 실제운동의인과로 설명하지 않는다.
- [ ] 새생성자조건은 원4/2에서 substeps만4로둔다. 외부dt1/240/target60Hz/원28초cfg/initialq/body/model108/gain/cap/Root고정/하체16유한/zero8보존/Gfree중력ONstrapOFF/PPO0은 그대로다. 원 bounded5초1200외부step만 실행한다. 내부4800step은960Hz전행측정이 아니다.
- [ ] typed factory예상과 actualget_sim_params의 명시필드를 대조한다. 원PRESETS복사binding만사용하고 정상/예외/잘못된getter모두원상복구한다.
- [ ] 새producer/wrapper/sourceclosure를독립검수하고RootACK·CPU원문사본뒤실행한다. 기존4/2 reference raw4의전체exact검사도유지한다.
- [ ] 전105축·초과전체구간·최초/최후/최장/peak시각·초기0..1초/후기1..5초·1초별창과동일preparedgain/target/commandcap를비교한다. max비영97/zero8·boundeps0 false를별도로기록한다. 원값대비감소를실행성공gate로두지않고혼합/비수렴도남긴다.
- [ ] 1/2/4에서감소하는성분은시간적분/제약풀이수치잔차범주근거를평가하고, 비수렴성분은미해결로남긴다. 정확SDK내부루틴/수학원인단독확정/정규28초·전체안정화채택으로확대하지않는다.

CC_LAST_SUBSTEP 접촉은마지막내부step만이며,외부q/dq는내부960Hz최대값을보장하지않는다. feedback궤적은달라질수있고같은제어식·initial·gain/cap만고정한다. 준비·중단·실패는전부보존한다. 이진단은사용자최종조건의완료선언이아니다.
