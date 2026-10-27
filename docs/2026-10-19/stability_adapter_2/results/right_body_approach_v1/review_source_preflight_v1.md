# 몸 쪽 기타 접근 — source 사전 검수

요약 판정: **문제없음 — CPU source 탐색 진행 가능**. 현재 Critical 0 / Warning 2 / Suggestion 0. 실행 전 발견한 기타 mesh 입력 핀 누락 1건은 수정 확인 후 닫았다. 수락 후보·새 native 실행 결과는 아직 검수하지 않았으며 source 통과가 실제 두 블록 지지 회복을 뜻하지 않는다.

## 확인한 변경

- [source:24](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:24)의 기준은 현재 waist 정지 실행 초기 상태다. 설정 q_ref81과 해당 native 초기 q는 float32 exact로 같고 joint 순서도 같다. 몸통9/오른12/왼12/머리6 총39개를 각각 ±0.15/0.35/0.4/0.35rad와 모델 범위 안에서 맞추고 손가락42를 고정한다.
- [source:52](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:52)의 수평 전방 `[-right_y,right_x,0]`은 현재 오른 축 `[0.9992527,0.0386535,0]`에서 계산된다. 반대 방향 3/6/10mm 이동은 몸 쪽 접근이며 world −Y와 완전히 같은 축은 아니다. 회전은 유지하고 두 허벅지 전체 capsule 최소 gap 0.3mm에 맞춰 높이를 재조정한다.
- [source:82](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:82)의 최종 float32 후보에서 실제 FK·전체 source LP·6 capsule 양의 거리·waist flank·모델 한계·왼 손목/머리 방향·자연 팔 조건을 다시 검사한다. 초기 q/G 변화가 genuine predicted pose/G39에 반영되고 수락된 config의 후보 SHA를 갱신한다. 세 이동값을 모두 검사하며 첫 수락에서 중단하지 않는다. 팔꿈치 ±5° 모델 여유도 탐색 bounds에 포함된다.
- 처음에는 manifest 목록 밖의 neck1/neck2 및 realistic upper/lower/headstock 5개 mesh 핀이 누락돼 있었다. **미실행 상태에서** [source:45](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:45)에 actual guitar XML의 compiler.meshdir/asset mesh 전체 경로를 추가했다. XML mesh 69개와 human37 모두 파일이 존재한다. 기타 manifest의 별도 항목을 합친 mesh pin union은 70개다. config·원 XML·기준 native·후보/reference·전체 A Python 및 OM mesh도 기록하고 종료 SHA를 대조한다.
- 추가 검토한 [새 native entry:36](/home/ajou/yigyu/3/stability_adapter_2/run_right_body_approach_v1.py:36)는 보존된 waist runner3 대비 설명과 해당 mesh pin만 추가했다. single-owner 제어, 33 EFFORT/48 POSITION, 초기 fullG/FK/PD/질량/root·하체·finger42 검사, 기존 guard·기록 경로에는 변경이 없다. 새 후보/config의 실제 검수 전 native 승인으로 확대하지 않는다.
- 두 Python 파일 AST 구문 및 입력 경로를 읽기 전용으로 확인했다. source 최적화·native·정책·학습은 실행하지 않았고 소유한 새 리뷰 파일만 작성했다.

## Warning

1. [source:94](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:94)의 수락은 초기 source proxy 거리/겹침 검사다. 근위 상완 0~30% 최소 gap은 단일 부위의 cooked 접촉이나 힘·모멘트 기여 인증이 아니다. 몸 쪽 이동과 IK 초기각 변경이 함께 있으므로 이후 개선을 이동 하나의 인과효과로 단정하지 말고 실제 240Hz 접촉·후기 동시 접촉·기타 변화를 확인해야 한다.
2. [source:40](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:40)의 새 pin 보완은 이번 실행의 근거다. 이전 waist 단계의 누락된 기타 mesh 5개 및 source1의 human35 사전 핀에 대해 소급 before 인증으로 사용하지 않는다. 현재 baseline에 왼손 손가락 접촉이 있었으므로 회복 결과도 무왼손/수동 집게·장기·연주 유지로 확대하지 않는다.

## 실행 전 확인 SHA-256

- `search_right_body_approach_v1.py`: `4bfe788ae7cc4370e8b460b179833b78063bf106eb1a34b6d5afa69675c509c1`
- `run_right_body_approach_v1.py`: `420f8fffd4b9d87087c2fe2d6019485e5d34bb5d52b929d60bec0bc74525ad72`
- `RIGHT_BODY_APPROACH_PLAN_V1.md`: `54b29ea173356928040238b4ef8f1be0ec99eaae9c2df440ae52137a1e3d0b85`
