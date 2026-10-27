# 지정 압현준비의 source 기하 감사

새 Body9 실제 baseline_v8의 정지11..16초를 평가한다. 후속 regrasp/continuous의 protocol3 dwell도 동일한 연속5초 기준으로 검사한다. 실제압현력/현진동/음향과 source 준비기하는 구분하며 기존 고정3번줄·fret5 nut측2.7mm 단일hinge 실패를 그대로 보존한다. 새 native/제어/모델·initialFK 보정 변경은 없다.

## 사전 기준

1. 대상은 LH:index3 원STL 삼각형과3번줄/fret5 marker다. 목표 교차허용선분은 fret5 바 nut측모서리에서+0.5..+5mm, 즉 바 중심 nut측+1.2..+5.7mm의4.5mm다. 바면에서0.5mm를 띄운다. 현재 기타G frame의+Y가nut방향인 원모델 정의를 확인한다.
2.5초창의 actual native pose는60Hz301개(양끝 포함)를 검사한다. 각시각마다 대상선분과 하부 source 표면의 교차가 하나 이상 있어야 한다. 유효교차점은 native활성physicalG89 source convex piece 내부가 아니며, 각쌍의 unit-plane 직접투영 분리여유가0.25mm 이상이어야 한다. 원vertices와 현재normalized nativebodypose를 사용한다. MuJoCo signeddistance/minDist의 침투량 변환은 하지 않는다.
3. 다른5개줄의 여유는 더넓은 바 nut측모서리+0..+5mm 전체5mm선분에서 계산한다. 각선분–index3 원STL surface unsigned거리≥0.1mm, 시작점이 source z범위 바깥이며 교차가없음을 확인한다. marker 반지름은0이다.0.1mm는사전기하여유이며 실제현굵기·압력·뮤팅 기준이아니다.
4. 실제240Hz1201개 body/접촉 표본과원target60Hz 전체sequence를 확인한다. 원105 requested/final bounds·targetownership은 완료된core29/30gate로AND하고 선택index3 actual bounds를240Hz로검사한다. 원actual105 EPS0 잔차는진단으로보존하며 joint-health평가를대신하지않는다. 원wholeindex3/G1mm는완료된planes3의LHgrip 전행1602쌍/각시점과해당index3 89쌍 coverage·원model108·현재inputSHA 검증으로AND한다. 그수식을새로재실행하지않는다.
5. 선택index3의raw/양성(lambda>0) 접촉을physicalG/neck/fret5/Gbody 등body별·시각별로보존한다. native lambda를Newton으로변환하지않는다. 실제선택현 압현force_N은측정채널/현물리없음으로null이다. 일반neck95를선택현압력 성공으로 대체하지않는다.

하부표면 분류는 원segment/triangle 교차와 원z-ray의가장낮은surface 교차를대조한다. ray저장의12자리반올림과선분수치계산의closure는1nm 이내로확인해수치도구오류를거부한다. 이값은0.25/0.1/1mm 기준을완화하는epsilon이아니다. source가닫힌원피부여도 fingerpad 의미표식이없음을기록한다.

## 실행 순서

- [ ] 새PLAN/before와원문을고정한다. flat map/envelope/model108을실제metadata로확인하며 중복expectedSHA충돌은거부한다. 새 A glob pin은하지않는다.
- [ ] frozen triangle/segment primitive를재사용해최소readonly코드를작성한다. actualbaseline16의작은entryschema CPU와경계/잘못된줄·교차·다른줄근접 반례를검사한다.
- [ ] source/CPU/SHA를동결해독립검수와RootACK를받는다. 이이전actualmain은0회다.
- [ ] Root가완료된core/planes와명시run/out경로로본진단한다. 미충족이면원기준으로기록하고수치완화/생산수정을하지않는다.

기하준비 통과와 실제압현 성공은별도필드다. 이번자료로새 .15mm자세의실제현압력이나최종채택을인증하지않는다.
