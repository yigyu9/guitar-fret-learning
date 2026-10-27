# Native joint/DOF topology의 무step getter 진단

원 제한 좌표 진단은 native joint type·joint frame이 미기록인 점을 명시했다. 공개 SDK와 설치 binary의 대응을 추측하지 않고, 기존 baseline8 초기 설정을 같은 Scene7 생성자로 불러 native asset joint/DOF type과 actor frame을 기록한다. 기존 코드·설정·모델·결과는 보존한다.

- Scene 생성자의 원 초기화만 허용한다. cfg의 attempt_out만 새 출력 경로로 바꾸며 실제 물리 simulate/fetch·Controller 생성·목표 제출·외력·상태 추가 쓰기·PPO는0이다.
- human asset handle이 지역변수이므로 기존 Guard의 create_actor 호출에 getter만 추가하는 새 Guard를 생성자 범위에서 연결하고 finally에서 원 binding을 복원한다. 원 create_actor 및 초기 mass/filter/pose 적용은 그대로 위임한다.
- native joint 이름·type과105 DOF 이름·type을 분리한다. actor 이름/수와 asset 이름/수를 대조하고 DOF105를 실제 가동97이나 native joint 개수로 바꿔 부르지 않는다.
- actor DOF frame(origin/axis), joint transform(p/r), 실제 DOF 속성 및 초기 state를 getter로 읽고 전후 native snapshot exact/steps0를 확인한다. frame 수·dtype·finite를 검사한다. 반환이 예상 schema와 다르면 실패를 보존한다.
- 이 무step 기록의 frame freshness와 parent/child joint-local 의미는 미확정으로 표시한다. 초기화 직후의 접촉·force buffer를 fresh 동적 측정으로 해석하지 않는다. 실제 관절 제한 준수·solver 원인·최종채택은false다.
- CPU는 실제 baseline8 초기 metadata의105 names와 local API의 structured dtype를 사용한다. getter-only 호출, 수·이름·dtype·NaN 오류, 정상·예외 Guard 복원과 physics0를 검사한다. 실제 native main은 독립 검수 final/frozenSHA·RootACK·prospective 입력 봉인 후에만 새 출력에서 실행한다.
- 결과가 getter 자체의 실제 schema/미지원 때문에 실패하면 원문과 로그를 보존하고 새 버전으로 보완한다. 정규 동작 실험이나 성공 횟수에 포함하지 않는다.

local source: isaacgym/docs/api/python/gym_py.html의 get_asset_joint_type/get_asset_dof_type/get_actor_dof_frames/get_actor_joint_transforms, struct_py.html의 DofFrame dtype. 문서에서 DOF origin은 environment 좌표, axis는 action direction이라고 설명한다. parent/child local frames나 importer limit 수학의 증명이 아니다.
