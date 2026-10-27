# 사용자 기준 no-left V12 metadata 및 V13 source 검수

요약 판정: 현재 V13 source 수락 두 후보는 문제없음. RH:pick 목표 프레임·model/scalar/principal 범위·원본 형상·root/lower·finger42 및 입력 보존을 확인했다. 현재 진행 중인 native의 완료 또는 안정성은 이 검수 판정에 포함하지 않는다.

Critical: 0

## Critical

- 추가 필수 수정 없음. [search_user_guided_no_left_v13.py:77](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v13.py:77)은 FK `RH:pick`의 **body origin**과 `gp+gr·[0,−.36,.075]`를 비교한다. :100의 최종 오차와 :105의 실제 G좌표도 같은 점·프레임이다. 이는 XML [RH:pick:297](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:297)의 virtual 준비 marker이며 palm origin이나 실제 strike/접촉 성공과 구분된다. RIGHT 네 ball norm은 float32 저장 후 :103에서 다시 계산하고 :104의 `<160°` hard gate에 포함된다.

## Warning

- V12 before-pin 범위: [package_user_guided_no_left_v12.py:17](/home/ajou/yigyu/3/stability_adapter_2/package_user_guided_no_left_v12.py:17)의 `diagnostic_v1/diagnostic.json` 직접 read와 사용 helper의 `A/config.json` read는 package 자체 input map에 없다. 두 파일은 V11 before map에 명시적으로 포함되고 그 SHA가 현재 파일과 exact로 일치했으며 package의 나머지 map도 불변이다. 따라서 현재 결과는 **V11 map과 package map의 합성 확인**으로 보증한다. V12 standalone before-pin이 완전하다거나 뒤늦은 before-map 보완으로 표현하지 않는다. 소비 원본은 수정하지 않는다.
- BBcentre와 COM의 범위: [PLAN V13:5](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V13.md:5)의 선호 `[.11,0,.705]`는 transformed local body BBcentre이다. 전체39body 질량가중 COM 또는 world-axis AABBcentre와 같지 않다. 실제 전체 COM은 아래 수치처럼 별도 계산해 제시하고, hip axis의 x범위와 COM x투영만으로 안정성이나 접촉 모멘트의 원인을 확정하지 않는다. 접촉점/방향·활성 인간 제어·전체 동작은 actual native 분석 대상이다.
- soft 여유의 범위: [source:78](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v13.py:78)의 forearm fraction≤.65, :79의 Wrist15mm 및 :76의 torso5mm/Thorax1mm는 soft다. hard 수락 기준은 :104의 별도 source clear·capsule 최소50µm·U/F/H 근접·LEFT10mm·목표오차·모델/principal 기준이다. 초기 source 수락이나 LEFT10mm는 동작 중 actual LEFT0·무제어 평형을 보장하지 않는다.

## Suggestion

- [PLAN V13:6](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V13.md:6)의 upper/forearm minimum .1mm penalty 표현과 [source:75](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v13.py:75)의 upper .2mm·forearm :78의 .1mm를 다음 설명 문서에서 정확히 구분한다. 현재 upper gap은 둘 다 .56mm 이상이라 수락에 영향이 없다. RIGHT norm150° soft 항은 distal 두 ball이며 네 ball 전체의 hard160°와도 구분한다. 현재 소비 계획/코드는 보존한다.

## 확인 근거

- V11→V13 diff는 soft centre 선호/가중치·초깃값, palm 목표→virtual pick 목표 및 실제 G좌표 로그, RIGHT4 hard principal gate와 버전 경로다. 사용자 기준 centre와 허용 bounds `x[.095,.255],y[−.13,.05],z[.625,.735]m`는 유지된다. body9+right12+centre3의 24변수 joint fit을 유지하고 실제 gain/material/controller/helper는 변경하지 않는다.
- upper50/65 모두 source clear·LEFT certificate1780쌍 미보장0·model bounds·body±15°/Thorax±20°/Shoulder±30°/rightdistal±1.6rad·finger42 exact를 통과했다. RIGHT max norm은 `108.364498/108.814787°`, LEFT max는 `96.014990/95.941133°`로 hard<160°다. 30/45/65 alias는 fresh full upper witness와 exact이며 config candidate SHA도 일치한다.
- actual body BBcentre는 upper50 `[.099992189,.009665542,.704883482]`, upper65 `[.099190119,.004505437,.705089178]m`로 기존 bounds 안이다. RH:pick G좌표로 독립 계산한 목표 오차는 `1.646399/.589360mm`; 저장 RH error `1.646387/.589343mm`와 약12/16nm 차이는 목표 생성 후 기타 p float32 저장 순서에 따른다. LEFT 오차 `.007639/.005862mm`다. 두 값 모두 수락 기준에서 충분한 여유를 가진다.
- U/F/H gap은 upper50 `.567574/.425375/.559421mm`, upper65 `.607478/.411617/.499076mm`; Thorax `30.421354/31.378659mm`다. upper fraction `.615404/.658237`, forearm `.173137/.159160`로 이전 V11의1/0 endpoint witness와 다르다. 실제 접촉 위치·지속 지지는 후속 native에서 확인한다.
- 후보 q로 FK를 독립 재계산해 저장 전신 p·RH:pick G좌표·모든 capsule gap exact 일치를 확인했다. root/lower body p 변화0. G39의 rigid local p 변화≤`5.56e−17m`, 회전≤`1.25e−16rad`로 동일 회전과 rigid 초기 배치다. LEFT certificate를 정적 probe에서 재계산해 두 저장값과 exact 일치했다. 추가 physics step0.
- 원 native applied 질량·body-local COM과 각 G39 pose로 계산한 총질량은 `4.648715728kg`다. V12 actual initial 전체 COM_W는 `[.175029628,−.015478495,.679473136]m`; V13 **source predicted** 전체 COM_W는 upper50 `[.071796889,.018123789,.705992967]`, upper65 `[.070994819,.012963685,.706198662]m`다. 후자는 새 native 실측값으로 표시하지 않는다.
- V12 native는 actual104 physics/26 completed control/.433333초, completed false·guitar safety displacement 중단이다. endpoint104행에서 LEFT0/U45/F82/Hip101 contactstep을 독립 집계했다. LEFT0을 기타 안정성 성공으로 재해석하지 않는다. package의 q81은 V11 원 source와 같고 새 geometry solver0이다.
- V13 input1010개 SHA 현재 일치, 두 후보 source 수락·native_runs0. 누적 geometry는 V1=3 및 V2/V3/V5/V6/V7/V8/V10/V11/V13 각2로 **21후보/7수락/14제외**다. 진단1 별도, metadata V4/V12는 solver0, V9 syntax 실패도 solver0이다. 신규 source AST 검사 통과. 기존 완료 source/input/raw 파일은 보존되었다.

검수 SHA: V13 source `871c0688917876e14b58f4a962a9b0ed4a8f28f9f57d40a4ecf34479726e831a`, PLAN V13 `9ec54a577f249062df3f604fddd8e80dc9c61e271bededaede6ca6f1b76dbed5`.

검수자는 이 문서만 생성했다. source·설정·assets·native 원자료 변경 및 추가 물리 실행은 하지 않았다.
