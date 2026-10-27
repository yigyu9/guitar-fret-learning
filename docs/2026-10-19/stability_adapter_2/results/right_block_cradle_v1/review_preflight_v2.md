# 사전 검수 — 오른 근위 두 블록 받침 source 제안

요약 판정: **V2 코드 문제없음. 미결 Critical 0 / Warning 3 / Suggestion 0.** CPU source 탐색 진행을 막는 오류는 발견하지 않았다. V2 결과·native 후보·새 제어 구현은 아직 검수하지 않았다.

해결한 Critical — V1의 elbow 아래/밖·wrist inward 및 머리/왼손목 회전 유지 조건이 soft residual에만 있고 최종 accepted gate에 없음을 보고했다. 실제 V1 세 후보는 Thorax gap21.044/25.356/9.419mm로 모두 거절·selected 없음/native0이다. V2는 최종 float32 FK에서 elbow 아래≥19.9mm/밖≥119.9mm/wrist 안쪽≥24.9mm와 Head/왼손목 회전오차≤1°를 hard gate와 기록에 추가했다. 수치여유 .1mm는 계획V2에 명시했다.

- [short capsule:32](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v2.py:32)는 원 R_Shoulder 캡슐 radius/quat를 유지하고 centre=`a+.15*(b−a)`, half-length=`원 half-length*.3`으로 바꾼다. 축 a→a+.3*(b−a)의0~30% 부분에 맞다. 평탄화된 body world pose/FK 및 xyzw→wxyz 매핑을 유지하며 static mj_kinematics/query만 사용한다. query 후 원 geom size/pos를 복원하고 다음 residual 시작에서 world geometry를 갱신한다. 실제 asset/native 형상을 줄이는 변경은 아니다.
- [최종 analytic/LP:84](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v2.py:84)는 별도 analytic capsule 구간0~30% 측정과 전체 mesh LP source_audit를 사용한다. MuJoCo short query는 목적함수 제안용이며 단독 최종 수락 근거가 아니다. 모든 q는 float32로 변환한 뒤 모델 한계를 다시 검사하고 genuine predicted_human_poses를 저장한다. legacy65 key의 실제 fraction .3도 기록한다.
- V2의 변경은 source 거리 목적함수1400→6000/오른 palm 위치 선호120→50, 보존된 V1 seed2와 몸통±.04 시작점, 유한차분/반복 제한 및 final 자연기하 gate다. 물리 PD/solver/기타 힘/제어 코드를 변경하지 않는다. body9±.2/right12±.35, left12±.4/head6±.3는 native model bounds와 교집합이다. 손가락42는 exact 유지한다.
- 새 계획과 seed2/계약·형상·Python 의존성 입력 pin, exclusive search_v2 경로, 종료 후 입력 SHA 불변 검사를 유지한다. source2 Python AST도 통과했다. 원 V1 소스/거절 결과를 수정하지 않았다.

Warning 1 — .5~2mm는 제안 목표이며 최종 수락상한은 Thorax6mm/근위상완4mm다. accepted source만으로 두 부위의 cooked 접촉·받침·force 기여나 팔꿈치 동작 중 유지가 입증되지 않는다. native에서 각 부위의 접촉점/영역/양성 rawlambda와 실제 G 변화를 별도로 확인해야 한다. 근위 구간 최소거리도0~30% 단일점이라는 뜻은 아니다.

Warning 2 — Chest/R_Hip analytic gap은 저장하지만 현재 eligible의 양수 gate에는 포함되지 않는다. 전체 LP source_clear는 기존 convex/polygon capsule proxy 기준이다. 이를 true analytic 모든 capsule 또는 cooked clearance 인증으로 확대하지 않는다. 후속 초기/실제 접촉 해석에서 해당 수치도 함께 확인하는 것이 필요하다.

Warning 3 — 기타 geometry 기준은 기존 실제 초기 body pose다. seed quaternion과 native quaternion roundtrip의 물리 방향차가 약3.05e−7rad이며 byte exact와 normalized rotation 동일성을 혼동하지 않는다. 최종 실행 전 V2 보완은 후보의 position/quaternion을 seed 원본 배열로 저장해 입력값 자체를 보존한다. 새 runner의 t0 기타 상태 검증에서 실제 측정과 선언된 초기값을 대조해야 한다. 현재 검수는 source 제안에 한정되며 원 팔꿈치 ±5° 결과를 새 두 블록 받침의 동작 인증으로 재사용하지 않는다.

검수는 계획V1/V2·source diff·캡슐 좌표/수식·V1 저장 거절 결과 및 AST에 한정했다. 추가 source 실행/native/학습/추론·다른 담당 파일 편집은 없었다.

검수 SHA256:

- sourceV1: `066aedf3cd22090c521c4b5bd558b1fd6b2d23cfa487f08144afbca09b64a620`
- sourceV2: `7ae88ebafc30fa5869976dbe9729bd613e3fa6de65c6715f6dac856c9bc21432`
- 계획V2: `e5a1012217e1587e29dc50bb95e2f3e4bc3f1e0830e8dd84dc0b5c8739cb5416`
