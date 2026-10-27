# 전신 세 시점 접촉 시각화 독립 사전 검수

요약 판정: **문제없음**. Critical0건·Warning0건. 새wrapper는기존16초제어를상속하며카메라와읽기전용접촉feature기록만추가한다. 실제화면구도/전체재현일치/후처리투영은실행후검증대상이다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음. 접촉feature두세계좌표의gap은표면간격/solver상태를포함할수있으므로전체를변환수식오차라고단정하지않는현재field이름을유지한다.

## 검토 근거

- `/home/ajou/yigyu/3/stability_adapter_2/run_contact_three_view_v1.py:98`: cycle(run)이원래왼손factory/Recording을설치한뒤run의Parent가그Recording을상속한다. 새클래스는기존super init/capture/encode를연결하고runner.main을실행하므로목표/PD/torque/상태초기화경로를교체하지않는다.
-37–44행: 기존상속카메라생성뒤whole_body/hands/chest_arm_close만1280×720/FOV55의정면(+Y)/오른쪽측면(+X)/위카메라로교체한다. 예상3view키및capture해상도와일치하고side/OM_appearance보조카메라와충돌하지않는다. 카메라전후native stateeq를검사한다.
-46–77행: 렌더전nativepose를보존하고supercapture후같은physicsstep에서actualget_env_rigid_contacts를읽는다. human–guitar쌍만포함하고두body의localfeature를정규화된SciPy pose로world에변환한다. body0/1순서에따라실제guitar-sidefeature를선택하며두bodyfeaturegap과rawcontact/positiveλ를함께기록한다. 상태쓰기/힘적용이없고nativeeq를다시검사한다.
- 설치된primaryRigidContact문서866–875행은local_pos0/1을각body의local-spacecontactfeature excludingthickness로정의한다. offset0/1의마찰표면위치와구분한다. 표시점은압력면적/힘N이아니다.
-68–73행: 실제새카메라의view/projection행렬을프레임마다저장하므로후처리는임의고정투영대신그행렬을사용할수있다. marker는X-ray투영임을형상밖범례로표시하는계획이며그림가시성/투영부호는후속검수한다.
-96행: 권장한beforefileexistsguard를실제적용해동일phase재실행이이전입력map을덮어쓰지못한다. Wrapper는고정P/native_v1출력을기대하는phase전용재현실행이며일반임의outputwrapper로광고하지않는다.
- ownmap은새source/leafplan/원래report/trace/contact/initial/config/primary문서를사전·사후대조한다. 기존runner의actualhelper/config/XML전체mesh/물성/초기상태1287계열입력pin도유지한다.원래실험/공용자산/fresh작업파일을수정하지않는다.
-101–104행에서완료후원래trace/actualcontacts/initialJSONexact를요구한다. 그래픽/조회가물리결과를바꾸지않았다는검증조건이적절하며,이검증완료전동일재현성공이라고선언하면안된다.
- 새Python AST parse통과. 검수자물리/GPU실행은0회이며실제16초완료/481frame/구도/변환잔차/후처리표시검증은후속대상이다.

## 검수 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_contact_three_view_v1.py`: `89d609eab5c03b879d4824b7c9527d737fdd9b0ea64c62978377ed9ad23692d5`
- `/home/ajou/yigyu/3/stability_adapter_2/CONTACT_THREE_VIEW_PLAN_V1.md`: `2d3348158dee35be2ac3aabc0f321cd168015a80e118170e0737ba322f8ce87c`
- `/home/ajou/yigyu/3/isaacgym/docs/api/python/struct_py.html`: `a8e2c2e12b4a26b053572adf60968e63fb4054bd73c7512ebdd3da6c53c0f7de`
