from pathlib import Path
import json
R=Path('/home/ajou/yigyu/3');A=R/'stability_adapter_2';D=R/'docs/2026-10-12/stability_adapter_2';B=D/'results';P=B/'palm_support_two_axis_fk_v2';F=B/'palm_support_runtime_fk_v1';OLD=B/'torso_hold_native_collision_v1'
def write(p,t):assert not p.exists();p.write_text(t)
write(P/'README.md',f'''# 실제 관절각–손바닥 FK 대조와 손가락 두축 가설

이번단계는완료된몸통PD×2의actual0~5초저장자료를읽은offline분석이다. 추가native초기화/physics/trial0이다. 손바닥·팔FK는실제상태와잘맞았지만손가락까지포함한전체손FK의기존gate는네가설모두미달했다. 기존FK로손가락각을바꾼미래형상을인증하거나제어를바로실행하지않았다.

## 초기값과 실제 실행 출처

[이분석의실제초기81각/G p·q/PD·LA]({OLD}/native/initial_values.json), [원실행trial]({A}/trials/palm_patch_priority_diagnostic_v1/palm_wide_near17.json:1)을사용한다. 기타최대14.052228mm/2.884291°·palmcontact0의기존실행이며다른실행을한것으로집계하지않는다.

![분석대상 기존실제Gym 손·스트랩0~5초]({OLD}/native/hands.mp4)

완료된native영상출처다. 주황실선/옅은점선은actualpassive strap 경로이며새source모델/아래그림을Gymrender로표현하지않는다.

## t0 calibration을 유지한 runtime FK

[최초runtime대조]({F}/analysis.json)는t0의relative transforms/q0를한번만calibrate했다. Step0/24/120/1200의actualq를입력하고actualChestpose변화로world변환했다. 각시점finger/armrelativepose를다시fit해정답을강제로만들지않았다.

Palm sourceanchor의실제점대조오차는최대0.000157460mm였고normal도매우잘맞았다. 그러나약지1의회전오차가손끝으로누적돼5초ring_top 원점오차1.221470mm·최대body회전0.017248rad가됐다. 기존전체body gate0.1mm/0.001rad는실패다. t0의거의0오차는calibration결과이며runtime정확성증명과구분한다.

## 두좌표 회전의네가설과heldout 대조

Same-body두좌표에만exp(sum),XML순서product,역순product,quaternion벡터basis×tan(q/2)·scalar1의정규화map을비교했다. 다른3좌표·1좌표와t0calibration은유지했다. 마지막가설은순수수학가설이며PhysX의확정계약으로설명하지않는다. 원인도아직확정하지않는다.

4시점0/24/120/1200과별도20heldout시점의동일native parent–child상대회전/전체chain을대조했다. 추가fit과gate완화는없다. V1세가설/source/wrapper/로그를보존하고V2네가설로추가했다. [V1결과]({B}/palm_support_two_axis_fk_v1/analysis.json)·[V2결과]({P}/analysis.json)에원자료를둔다.

| 두좌표 가설 | heldout20 최대body위치오차 | 최대body회전오차 | 전체손gate |
|---|---:|---:|---|
| exp(sum) |1.222811mm|0.017266rad|미달|
| XML순서product |0.835770mm|0.010405rad|미달|
| 역순product |1.727665mm|0.025484rad|미달|
| tangent-half quaternion |1.277136mm|0.017688rad|미달|

![실제저장24시점에대한source FK 오차]({P}/artifacts/whole_hand_FK_hypotheses.png)

위는왼팔·손각body원점오차의최대mm,아래는body SO(3)상대회전오차의최대mrad다. DOF좌표drift와다르다. 빨간선은기존0.1mm/1mrad대조기준이며모두미달했다. 선은표본연결이고연속오차측정이아니다. Source geometry/FK 그림이며native영상이아니다.

## 정확히확인된palm/팔범위와미실행각제안

[범위평가]({P}/palm_scope_assessment.json)에서24시점palm body원점최대0.000312034mm·회전6.383681×10⁻⁷rad,팔body원점0.000278428mm·회전6.380717×10⁻⁷rad였다. Palm/arm은기존기준안에들어오지만전체손실패는그대로유지한다. 이는해당24저장시점의좌표예측근거이며모든자세/PD목표/접촉응답을인증하지않는다.

![5초시점palm 위치미분과네시점기하각제안]({P}/artifacts/palm_J_and_geometric_proposals.png)

위열은왼팔12·행은world XYZ이며±0.0001rad source FK미분을mm/rad로표시한다. Native정적한계에접근한축은one-sided,actualq가한계밖이면unconstrained source미분이라고원자료에명시했다. 아래는position-only damped least-squares λ0.01m/rad의기하dq이다. Native한계∩actualq±0.05rad안에서제안하며이값은제출한PD목표/실제motion이아니다.

목표점은actualG의요청palm patch에서Gy/Gz를3.1mm안쪽으로clamp한plane점+outward unitnormal0.1mm다. 정확평행강제는없고normal미분은진단만계산했다. 대표source점오차0/0.1/0.5/5초0.759395/7.162044/16.045099/16.727384mm가가상각변경후0.000582/0.065918/0.334887/0.362148mm로예측됐다. 이것은기하계산이며nativePD로같이개선됐다는뜻이아니다. Wholehand겹침/상향조건/실제접촉은다음단계에확인한다.

기존81목표에이dq를더한float32목표의native한계와initial66offset±0.3rad는네시점계산에서통과했다. Actualq를기존base목표로치환하지않는다. Actualnativeangle은R_Thorax_x가전체1201표본중3step에서정적한계를최대0.000099935rad(0.005726°)넘었다. 목표의한계통과와actual물리상태를구분하고원자료를숨기지않는다.

## 다음방향과검증범위

[다음계획]({A}/PALM_MEASURED_POSE_RESIDUAL_PLAN.md:1)은미실행이다. Actualfingerbodypose의source형상에검증된palm/팔12기하변화를적용해1/0.5/0.25배제안의겹침/상향을먼저확인한다. Finger21의미래q→pose를가정하지않고현재sensorpose를읽는방식이다. Physics body/joint/guitarstate에는쓰지않는다. 안전한방향후기존81목표+bounded/rate-limitedpalm residual의한actual5초실행계약을정한다.

Finger21/R팔손/몸통9목표는다음소단계의비교중유지하지만최종66연주권한을제한하지않는다. 기타initial worldp/q복원·유지,thumb후면/다른손가락전면/palm옆면지지와연주안정화는미완료다. 제어합성관계/실제물리반응뒤학습구조를정하고WAIT→REACH→GRIP→TRANSPORT를연주필수선행과정으로만들지않는다.

4runtime검사·3가설V1/4가설V2각5검사·범위4검사와source/실행SHA를확인했다. Root가실제PNG와원자료·native프레임출처를대조했다. Luna/독립change-reviewer 도구threadlimit으로root산출물/자체검증이며독립검수는보류다. [변경파일절대경로·실제줄]({P}/CHANGED_FILES.md:1)을따른다. 이전FK/helper/계획/물리실행은변경하지않았다.
''')
phases=['palm_support_runtime_fk_v1','palm_support_runtime_fk_execution_v1','palm_support_two_axis_fk_v1','palm_support_two_axis_fk_execution_v1','palm_support_two_axis_fk_execution_v2']
for name in phases:
 f=B/name;write(f/'README.md',f'''# {name} 保存기록\n\n완료된body9 PD×2 저장자료의read-only FK대조/실행기록이다. 추가native초기화·physics0이며전체손FK gate실패를그대로유지한다. 실행source·wrapper·metadata·stdout은변경하지않았다. [결과·두그림설명·기존실제영상출처]({P}/README.md:1)에정리했다.\n'''.replace('保存','보존'))
status=dict(independent_review_completed=False,reason='agent thread limit reached',attempt='contact_footprint_review followup failed',actual_producer='Sol/root fallback',QA='both scientific PNG opened and matched to saved data; native baseline source previously opened and remains preserved',scope='whole-hand four hypotheses failed; accurate palm subchain is narrower evidence; no new physical execution or control success')
for f in [P]+[B/name for name in phases]:write(f/'review_status.json',json.dumps(status,indent=2)+'\n')
append=f'''\n\n## 현재native/FK대조와palm residual 준비 — offline계측완료\n\n저장body9×2의0/.1/.5/5초와추가20시점actualq/bodypose를t0한번calibrate한FK와대조했다. 추가native/physics0이다. 전체손FK는두좌표회전네가설모두미달했고약지손끝오차가약1.22mm까지누적됐다. 원인은아직확정하지않는다. Palm/팔24시점origin최대0.000312034/0.000278428mm·rotation약6.38e-7rad는잘맞았다. 전체손실패를palm범위통과로바꾸지않는다.\n\n[원자료/두그림설명·실제baseline영상]({P}/README.md:1), [변경파일실제줄]({P}/CHANGED_FILES.md:1)에남긴다. 기하dq의PD목표경계만통과했으며runtime접촉/안정화개선은아직검증하지않았다. Root실제PNG QA·자료검증완료,독립검수/Luna는도구threadlimit으로보류다.\n\n[다음계획]({A}/PALM_MEASURED_POSE_RESIDUAL_PLAN.md:1)은actualfingerbodypose의source mesh와검증된팔12기하제안의전체손겹침·상향을먼저확인한다. 센서pose로현재형상을읽고physicsstate를덮어쓰지않는다. Finger21예측실패는유지하며기존81목표+boundedpalm residual의안전범위/PD반응확인후실제5초를진행한다. 최종66제어권과initialG p/q복원/유지·세면지지·연주안정화전체목표는그대로다.\n'''
for f in (A/'README.md',A/'PLAN.md'):
 with f.open('a') as w:w.write(append)
with (A/'PLAN.md').open('a') as w:w.write('''\n- [x] currentactual4+20시점·t0-only FK/Chest대조\n- [x] 두좌표4가설/wholehand실패·palmsubchain 범위평가\n- [x] source미분·미실행dq/PD목표경계·PNG두개/문서\n- [ ] 독립검수 — 도구thread limit\n- [ ] actualfingerpose source형상/팔12 residual안전성 — 미실행\n''')
with (D/'VISUAL_REPORT.md').open('a') as w:w.write(f'''\n\n## 92. 현재actualq의FK대조와palm잔차 방향 준비\n\n완료된body9×2 actual5초의저장자료만읽어새native/physics0이다. t0-onlycalibration/actualChest이동을포함한FK를4진단+20heldout시점에대조했다.\n\n![네두축회전가설의전체왼팔손오차]({P}/artifacts/whole_hand_FK_hypotheses.png)\n\n전체손gate0.1mm/1mrad는모두미달했다. 표본연결이며원인/전체importer계약을확정하지않는다. Exp(sum) heldout최대1.222811mm/0.017266rad,XMLproduct0.835770mm/0.010405rad다.\n\n![palm미분과미실행기하dq]({P}/artifacts/palm_J_and_geometric_proposals.png)\n\nPalmarticulation24시점최대origin0.000312034mm/rotation6.38e-7rad는잘맞았다. 위미분mm/rad·아래dqrad는source기하계산이지PD/접촉응답이아니다. 전체손실패를통과로바꾸지않는다.\n\n![분석대상의기존실제Gym손·strap0~5초]({OLD}/native/hands.mp4)\n\n이영상은새실행이아니며최대G14.052228mm/2.884291°·palmcontact0인직전물리실행이다. [상세설명/initial값/원자료]({P}/README.md:1), [다음actual손pose기반안전성계획]({A}/PALM_MEASURED_POSE_RESIDUAL_PLAN.md:1)에기록한다. Physicsposeoverwrite는없으며최종66권한·기타초기복원/유지/연주안정화목표를유지한다. Root그림QA완료,독립검수는도구한도로보류다.\n''')
index='# 이번소단계 변경파일과 실제줄\n\n기존consumed FK/source/물리실행/계획/산출물은보존했다. 새scope평가는palm부분증거와전체손실패를구분한다.\n\n'
for name in ['PALM_RUNTIME_FK_EXECUTION.md','audit_palm_support_runtime_fk.py','PALM_FK_TWO_AXIS_DIAGNOSTIC.md','palm_two_axis_fk.py','compare_palm_two_axis_fk.py','PALM_FK_TWO_AXIS_QUATERNION_PLAN.md','palm_two_axis_fk_v2.py','compare_palm_two_axis_fk_v2.py','assess_palm_runtime_fk_scope.py','make_palm_runtime_fk_artifacts.py','PALM_MEASURED_POSE_RESIDUAL_PLAN.md']:
 f=A/name;n=next((i for i,t in enumerate(f.read_text().splitlines(),1) if t.startswith('def main') or t.startswith('def left_fk')),1);index+=f'- [{name}]({f}:{n})\n'
for f,key in [(A/'README.md','## 현재native/FK대조'),(A/'PLAN.md','## 현재native/FK대조'),(D/'VISUAL_REPORT.md','## 92.')]:
 n=next(i for i,t in enumerate(f.read_text().splitlines(),1) if t.startswith(key));index+=f'- [{f.name} 추가기록]({f}:{n})\n'
index+=f'\n[결과/이미지설명]({P}/README.md:1)·[기존actual초기값]({OLD}/native/initial_values.json:1)에연결한다. 새native/physics/trial은0이며물리환경초기값/gain/목표/strap을바꾸지않았다.\n'
write(P/'CHANGED_FILES.md',index);print('docs written',P/'README.md')
