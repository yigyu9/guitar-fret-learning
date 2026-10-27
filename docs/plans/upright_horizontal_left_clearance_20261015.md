# 수평·좌우 위치 유지, 왼팔 자기충돌 해소

source2는localfittrue이나전체source_audit_v1에서Torso-LShoulder−3.478mm/Torso-LElbow−15.943mm/Spine-LShoulder−6.345mm로실패했다. native미사용이다.

source3는기타position/rotation/넥0°/원lateral+150.035mm/body/head/lower24/rightarm/fingerq를모두source2와exact유지하고왼팔12축만다시계산한다. 같은LH:palm worldpose(따라서guitar-localpose)5mm/2°를유지하면서원nativefilter/parent/XMLexclude에따른관련capsule쌍에1mm분리soft목표를부여한다. 두seed/원range/±.9rad. finalfloat32clearance≥.1mm/나머지qexact검사,독립전체audit를다시통과해야native5초를실행한다. 사용자배치를팔충돌때문에풀지않는다. gain/cap/Root·기타조건유지,실패보존,PPO·15초시험은5초통과전실행하지않는다.

- [ ] 왼팔fit와원palm위치·방향확인
- [ ] 전체sourceaudit
- [ ] 통과후새native정지5초
