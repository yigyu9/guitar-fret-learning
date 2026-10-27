# 사용자 기준 no-left V9/V10/V11 source 검수

요약 판정: 현재 결과의 제외 판정은 문제없음. V11은 2후보 모두 오른손 목표 오차로 제외되어 native에 사용할 수락값이 없다. 계획상 soft 목표와 최종 수락 기준의 차이는 아래 Warning으로 남긴다. 기존 실패/source 원본은 보존한다.

Critical: 0

## Critical

- 현재 원자료 판정과 코드 사이의 필수 수정 없음. [search_user_guided_no_left_v11.py:58](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v11.py:58)의 active 배열은 body9+right12=21축이고 centre3과 함께 24변수 joint fit을 수행한다. :75–80에 full upper/forearm/Hip gap, RH palm, forearm fraction 및 Wrist clearance residual이 함께 있다. :103의 source clear·정확 LEFT certificate·모델·finger42·RH오차25mm gate 때문에 실제 두 후보가 제외됐다. native 실행 0이다.

## Warning

- soft와 hard의 차이: [PLAN V11:6](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V11.md:6)은 Thorax sourcegap 1mm 이상과 Wrist gap15mm 유지로 읽히지만 [source:76](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v11.py:76), :79는 soft residual이고 최종 :103에는 Thorax>50µm/전체 source clear만 있다. 다음 계획에서 soft 선호인지 hard 수락 기준인지 명확히 맞춘다. 현재 두 후보는 RH오차로 제외되어 native 영향은 없고 실제 Thorax gap도 88.9mm 이상이다.
- endpoint 받침의 범위: [source:104](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v11.py:104)의 full upper/forearm witness는 두 후보 모두 상완 fraction1, 전완 fraction≈0이다. 상완 끝과 전완 시작 endcap에 대응하는 source 최단거리이므로 중간 전완이나 넓은 상완 면이 감싸 지지한다고 표현하지 않는다. :78의 fraction≤.65는 soft 선호이고 midpoint 접촉을 보장하지 않는다. 실제 접촉 위치/지속성은 후속 native에서 별도로 확인해야 한다.
- RIGHT principal 제한 범위: [source:80](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v11.py:80)의 오른 distal 150° norm은 soft이며 hard<160°는 :102–103의 LEFT만 검사한다. 현재 RIGHT 네 ball은 모두 108.13° 이하라 초기 pi 경계 이상은 없지만 다음 수락값에서도 실제 오른 ball norm을 별도로 보고한다. 기존 native qdot/finite guard는 그대로 유지한다.

## Suggestion

- [source:26](/home/ajou/yigyu/3/stability_adapter_2/search_user_guided_no_left_v11.py:26)의 별도 guitar XML discovery를 다음 버전에서 :30의 discovery 재확인에 합치면 기록과 assertion 범위가 일치한다. 현재 저장 discovery/full input/current 파일 SHA는 실제로 모두 같아 이번 결과 증거에는 불일치가 없다. 소비된 V11을 수정하지 않는다.

## 확인 근거

- V9는 93행의 중복 comma 때문에 AST에서 예상 SyntaxError가 재현된다. `syntax_failure_v9_record.json`은 source/계획/로그 SHA와 producer main 이전 실패·geometry/native 0 범위를 기록한다. V10 diff는 새 버전/출력 경로와 comma 한 개 삭제이며 V9 원본을 수정하지 않았다. V10/V11 AST 검사는 통과한다.
- V10 두 후보는 RH오차 `132.558/128.388mm` 및 R_Wrist↔G:body source overlap으로 제외됐다. centre는 `[.098234,−.002548,.705360]`/`[.098536,−.000663,.705248]m`로 사용자 centre에서 world X 약−7.7cm/Z 약+4cm다. source audit의 overlap 수치를 cooked 관통 깊이로 표현하지 않았다.
- V11 upper50/65 모두 source clear, LEFT certificate 각1780쌍 미보장0. RH오차는 `59.284309/57.715342mm`로25mm gate 미달, LH오차는 `.003196/.003530mm`다. U/F/H gap은 upper50 `.208784/.762807/.279421mm`, upper65 `.196895/.754345/.290215mm`; Thorax는 `90.005375/88.931611mm`다. forearm fraction은 `0/6.49e−17`, upper는 둘 다1이다.
- 저장 q를 독립 검사해 모델 한계, 사용자 body±15°/Thorax±20°/Shoulder±30°와 rightdistal±1.6rad, LEFT±1.5rad, finger42 exact를 확인했다. RIGHT ball norm 최대108.120504°, LEFT 최대95.932427°다. 30/45/65 legacy alias는 fresh full upper witness와 exact다. 머리는 기존 head-world soft refit이며 root/lower·원assets·G회전·full81 제어·gain·helper 변경은 없다.
- V11 입력1008개 SHA가 종료 원자료와 현재 파일에서 모두 일치한다. human XML 선언37 mesh와 guitar XML 선언69 mesh가 before pin에 전부 포함되며 별도 manifest/input union도 그대로 포함한다. discovery/full input은 contract/FK/형상 구성 이전에 저장되고 :109에서 전수 SHA를 다시 확인한다. 이전 완료 source map도 불일치0이다.
- geometry 총계는 V1=3, V2/V3/V5/V6/V7/V8/V10/V11 각2로 **19후보/5수락/14제외**다. 진단1은 별도, V4 metadata package와 syntax V9는 solver0이다. V11 native_runs0을 확인했다.
- 직전 `native_upper50_v8_static`은 기타 safety displacement로96 physics/24 completed control/0.4초 중단, completed false다. 실제 endpoint96행에서 LEFT contact71step을 독립 집계했으며 입력 보존 true/forbidden0이다. source LEFT clear를 움직인 뒤 actual LEFT0 또는 안정성 성공으로 재해석하지 않았다. V11 코드검수는 이 원물리를 바꾸거나 다시 실행하지 않았다.

검수 SHA: V11 source `8ff349ec82e7440bc5f77e14cf0e93caad4805d70a59eeef2f8812a0eb10e3ba`, PLAN V11 `f162a8cafa1e594d2c4019c5a5d03c8e555bec9a33a7b76b7aa7f2dceb6172db`.

검수자는 이 문서만 생성했으며 source·설정·assets·native 원자료 변경 및 추가 물리 실행을 하지 않았다.
