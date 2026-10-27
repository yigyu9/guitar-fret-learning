# Native topology V2: 생성자 후 checkpoint 우선 읽기

V1 source·CPU·검수·실제constructor실패와 Root before15839/after/input불변을 보존한다. V1은 이름 unique 합성assert에서 중단했고 joint와DOF 중 어느목록이 중복인지 원raw가 없어 확정할 수 없다. 성공으로 재표기하지 않는다.

1. 새 Guard.create_actor는 human asset handle만 Python list에 보관하고 원delegate를 인자 그대로 한 번 호출한다. 생성 중 새 asset topology getter는0이다. 원filter/mass/초기state reset/초기position target 등 원 생성자 동작은 그대로다.
2. 원Scene7 생성 완료 → steps0 native snapshot checkpoint → asset getter → actor getter 순서다. getter의 반환값은 의미assert 이전에 checkpoint JSON으로 즉시 저장한다. structured numeric ndarray는 dtype/shape/값과 .npy bytes/SHA도 보존한다. NaN/예상과다른dtype도 원checkpoint를 남긴 뒤 schema실패로 처리한다.
3. joint와DOF 목록은 index/name/type의 순서배열로 보존한다. duplicate/empty name은 raw 및 unique/empty-index 진단으로 기록하며 이름dict로 합치지 않는다. joint수를105 또는 실제가동97로 가정하지 않는다. asset↔actor name/count 관계는 진단bool로 분리한다. actor105·scene.names순서 및 count/각frame innerxyz/xyzw/각PD105행·finite는 원자료저장 뒤 검사한다.
4. 정상과getter/schema예외에서 finally Scene.close와 원Guard binding복원을 확인한다. 생성실패 cleanup은 원Scene constructor가 수행한다. 실패checkpoint/log를 남기고 완료result로 바꾸지 않는다.
5. 원Constructor 외 simulate/fetch/Controller/command/추가상태write/외력/PPO는0이다. frame freshness·parent/child local 의미·설치binary대응·solver원인·actualEPS0전기간준수·채택은 인증하지 않는다.

CPU는 실제 baseline8 DOF105 names/PD props 및 localSDK dtype만 재사용한다. joint개수/type 숫자·타입문자열은 합성fixture임을 명시한다. 중복·빈이름보존, 원delegate1회/constructor전getter0, lategetter/schema실패 checkpoint와close/binding복원, NaNraw/innerdtype/PD104행 거부를 검사한다. 독립review/frozenSHA/RootACK·외부prospectiveclosure 전 actualmain0이다. V1검수의상속chain·SDK/localAPI·모델108/생성자입력봉인은Root외부에서동일하게검증하며 이probe 자체가 전체closure를대신하지 않는다.
