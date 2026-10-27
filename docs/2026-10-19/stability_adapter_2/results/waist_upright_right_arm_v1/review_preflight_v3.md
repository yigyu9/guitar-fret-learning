# waist 자세 검색 V3 사전 검수

요약 판정: **문제없음**. Critical / Warning / Suggestion 없음. Source V3 미실행 상태의 변경 검수이며 물리 성공 판정이 아니다.

## 변경 검수

- [search_waist_upright_right_arm_v3.py:86](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v3.py:86): CPU least-squares의 팔꿈치 3D 목표 잔차 가중치만700→4000, 오른손 palm 위치 선호만200→100으로 바뀌었다. 새 출력 경로 `search_v3`와 계획 V3 참조 변경 외에 실행 코드 차이는 없다. 팔 접근 목적에 직접 연결되는 변경이다.
- [search_waist_upright_right_arm_v3.py:114](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v3.py:114): 축 투영 및 실제 bbox 중심 거리 감소 gate, 몸통 방향·기울기·waist·전체 source 비겹침·상완/전완 여유·왼손목/머리·finger42·모델 한계 수락 조건은 V2와 동일하다. 선호 가중치 조정이 비겹침 또는 거리 조건을 완화하지 않는다.
- [WAIST_UPRIGHT_RIGHT_ARM_PLAN_V3.md:22](/home/ajou/yigyu/3/stability_adapter_2/WAIST_UPRIGHT_RIGHT_ARM_PLAN_V3.md:22): 세 후보4°/8mm,8°/12mm,2°/5mm와 모델·초기각 범위·고정 기타 조건을 유지하며 이번 가중치를 CPU fitting으로 명시한다. 실제 PD/controller/토크 cap/학습 보상 변경은 없다. 사전 입력 SHA 순서와 종료 재대조도 V2 그대로다.

## Source V2 결과 대조

원자료 `search_v2/search.json`의 세 후보는 모두 거절됐고 `selected=[]`, `native_runs=0`이다. 현재 파일 SHA를 당시 input map과 대조해749개 모두 일치했다. 원본 V2와 결과가 보존됐다.

| 후보 | Chest 기울기 감소° | 팔꿈치 축 투영 mm | bbox 중심 거리 감소 mm | 전체 상완 gap mm | 수락 |
|---|---:|---:|---:|---:|---|
| relief4_arm8mm | 3.999999 | -0.910919 | -0.928072 | 0.085909 | 거절 |
| relief8_arm12mm | 7.999998 | -1.323672 | -1.347610 | -0.037976 | 거절 |
| relief2_arm5mm | 2.000000 | 0.646684 | 0.645213 | 0.479486 | 거절 |

세 후보는 요청 접근의25%보다 작은 실제 거리 감소로 수락될 수 없다.8° 후보의 상완 음수 gap도 수락을 막는다. CPU source fitting 가중치 조정의 근거와 계획 요약이 실제 원자료에 부합한다.

## 검증과 제한

V3 Python AST 문법 검사 통과. 검수 시 `search_v3` 폴더가 없고 V3 검색/native 실행을 검수자가 수행하지 않았다. 팔꿈치 접근 개선 여부와 전체 source audit 통과 여부는 실행 결과에서 확인해야 한다. source 비겹침은 cooked 접촉 또는5초 유지 성능을 인증하지 않는다.

검수 SHA256:

- Source V3: `290170c4e66041d0f75e0ede20a86f813224a641f85165854e2b23eba68ae1d5`
- Plan V3: `0ad116416738b8565c483f0d3392872bb9a944b39b77e445763843ab96ac0f52`

지정된 이 검수 파일만 생성했다. 다른 담당자의 원본/산출물은 수정하지 않았다.
