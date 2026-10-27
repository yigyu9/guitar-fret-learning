# Spine .12mm 후보의 유한 목표 경로

Root의 후속 설계 결정이다. 직전 mixed-space V3의 엄격 Chest 전행 결과는 selected=None/False로 보존한다. .12/.15 후보의 source 여유는 두run 모두 통과했지만, 관절 증분에 smoothstep를 곱하는 중간 경로는 비선형 FK에서 Chest pose를 완전히 보존하지 않았다. .15는 별도 actual 보조조건도 실패했으므로 후속 후보로 쓰지 않는다.

원 사용자의 필수 조건은 실제 접촉 지지와 안정성이다. 목표 경로를 모든 순간100nm/1µrad 수준으로 동일하게 유지하는 것은 내부 설계 제약이었다. 이를 위해 별도31점 비선형 경로 최적화와 lookup 제어를 추가하는 대신, 작은 .12mm 후보 하나의 **중간 목표 경로**에 명시적 허용량을 둔다. 원 형상1mm/Spine5도 및 내부 source.95mm/Spine4.95도, actual 보조 pose·관절 제한은 유지한다.

새 목표 경로 조건은 다음과 같다. 실제 native 평가 전에 고정한다.

- 새 증분 smoothstep의 strict interior16<t<16.5초에서만, 기존 FK Chest 목표에 대한 변화≤1µm/0.001도.
- t≤16 및 t≥16.5에서는 기존 strict≤0.1µm/1µrad를 유지한다.16경계 증분0 및 기존11..16 정지 목표는exact다.
- 두 목표 가산경로 A/B와 float64/float32 각각 적용한다. 다른96/zero8 exact·전105 submitted bounds/principal·actual 보조 pose/tilt·source 전행 .95mm를 AND한다.
- 지정 후보는 기존 point의index0(.12mm) 하나이며 .15로 자동대체하지 않는다. 모든 원 체크의 exact 집합을 검사하며 old target_goal_Chest_exact=False는 원 진단값으로 남긴다.
- 기존 두run의1381개 저장측정에서 새 경로조건을 전행 집계하고, summary/frames의 기존checks·source쌍수·samplecount와 대응을 검증한다. 기존 source/gain/physics/optimizer는 다시 실행하거나 결과를 변경하지 않는다.

1µm/0.001도는 새 **관절 목표 경로의 설계 한도**다. task-chain FK 계측오차를 물리 허용값으로 전용하지 않으며, 실제 접촉력/물리 추종/동적 안정성의 보장은 아니다. 기존실패를소급PASS로바꾸지않고새판정·새선정자료로기록한다. 기존 point/전행 기하/strictFalse/실제repeat Spine·LH 실패544/건강원인미확정은모두보존한다.

코드·최소CPU→독립검수 FINAL·RootACK→저장측정 전행평가 순서다. 이 단계에서 새 runtime/설정/물리/PPO는0이다. 선정되어도 실제5초/타현/해제/재접촉/연속/fresh와전체source·건강검사를다시받아야한다.
