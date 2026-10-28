# 검지·중지 첫 마디 충돌쌍 분리 진단

승인된 실패진단 단계1~2의 원인 분리다. 현재 wristv3 index env0 음중 index1/middle1의 약73.4N resultant 벡터가11끝점 모두정확히반대이며, indexzero/random도첫마디가각63.7/49.9N이다. 끝마디는0N이다. 동일/반대 순힘만으로접촉쌍·원인을확정하지않는다. 손가락끼리 충돌해야한다는 사용자요구를삭제하거나기본filter를변경하는실험이아니다.

1. [ ] CPU 최소준비: 현재 native scene 생성 전에 진단 wrapper로 hand_collision_properties의 baseline 반환값을복사하고, index1/middle1 각각단일shape에만현재미사용bit25를OR한다. 55shape1485쌍 중 정확히그1쌍만enabled→disabled이고나머지1484와실제external[0,4096]관계·모든비filter속성불변을검증한다. scene native setter/readback/prepare_sim 순서그대로유지. 원90쌍계약·matrixSHA를거짓사용하지않고원계약+새89쌍matrix·명시진단scope·전후shape값을저장한다. 활성source/원본/보관본수정0, GPU0. late runtime refilter는사용하지않는다.
2. [ ] 독립 code/preparation review: docs아래최소probe만, 기존ShortPool/trajectory_actions/compact_episode/원성공판정재사용, 원indexrow1/2sramp/3sonset/음길이/tail/PD/범위/속도/엄지/비선택B/wristv3/seed7그대로. 두새scene(원90쌍/그한쌍제외89쌍), 각4env의첫시도1개,실패포함,원fullbody/force/q/target trace는사전env0만60Hz. NN/모델전이불필요. sourceSHA·output기존/symlink거부·close/실제실패전파검사.
3. [ ] root GPU 직렬실행: 진행중fingergrid와겹치지않고한조건씩. native읽기검증·원판정전체분모·같은submittedselectedtargets/손목追従·양쪽proximal/selecteddistal하중·다른finger오압현·실제제어응답을비교한다. 원90baseline 재현은기존기록과별도실행으로구분하고동일결과를가정하지않는다.
4. [ ] 실제분석·독립검수: 한쌍필터만바꾼finitecontrol조건의성과/실제자세효과를보고한다. 특정접촉쌍압력인증·모든finger/mainJ33/전곡의원인으로확대하지않는다. 개선해도원래허용충돌을영구제거하는수정은자동채택하지않으며proximal자산/경로·비선택B의원인을추가로분리한다. 불변이면다른기하/도달가설로돌아간다.

현재는계획·CPU구현범위다. GPU는root만스케줄하며새grid준비/진행과동일active코드봉인을보존한다. 진단자료정리중단/제외유지. 전체goal미완료.
