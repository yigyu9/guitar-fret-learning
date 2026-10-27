# 첫 새 명령의 command 좌표 제한 진단

## 실제 관측

새 native_baseline_v9는 3844 outer step, 실제16.016666666666666초에서중단했다. 새보정첫목표를계산하던중guard가거부하여새Body증분/손명령이실제로제출되기전이다. 원하는actual12의손목fit은위치16.145nm/회전3.399e-8rad이며desiredactual원범위검사는통과했다. 그러나command=desiredactual−fixed_e16에서L_Thorax_x(39)는상한보다0.000770419836rad,L_Wrist_y(49)는하한보다0.000042140484rad벗어났다. raw/F32 둘다실패했다.

원코드/입력/partial raw/reference/failure/로그를보존한다. 입력15142 SHA는사후전부일치하고forbidden_calls/cleanup_errors는빈목록이다. wrapper.physical_seconds=28은원구현에서설정요청길이를저장한값이며, 실제경과는report.physics_steps=3844/physics_seconds=16.016666666666666이다. 28초완료로설명하지않는다. 총정규시도는21회/593.0166666666667초/142324outer이며별도solver4회20초4800outer와constructor2회0step는별도다. 새후보의보정후정지5초·타현·해제는실행하지못했다.

## 다음 검증

1. 실제3844 failure와원solver/actual16/held3836을사전SHA로닫고원desired/command위반을재현한다.
2. desiredactual의허용집합을원actual범위와command허용범위+e16의교집합으로구성한다. qref±.8의command변환도포함하고원solver의1e-6설계내부여유를유지한다. Scene/native bounds는수정하지않는다. 최종raw/F32 명령을몰래clip하지않는다.
3. seed=held와seed=held+e16을원수학으로비교하되원래해·원실패를보존한다. 초기값clip은최적화초기값처리이며제출명령clip이아님을기록한다.
4. 코드/실제schema/IEEE경계 CPU·독립검수FINAL·RootACK후실제IK진단만실행한다. 먼저3844에서엄격목표fit와두좌표의bounds/qref/principal/F32를검사한다. 가능하면기존baseline/repeat16초이후모든controlgrid에서진단해드문첫step공백을방지한다.
5. 목표fit가능성은동적추종·source지지성공이아니다. thumb/전체source/finite유지및새native는별도검증하며새PPO0이다. 원limitEPS0/원인미확정/최종채택False는계속보존한다.
