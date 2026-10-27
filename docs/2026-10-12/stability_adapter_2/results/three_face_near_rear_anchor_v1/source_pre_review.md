# 근접 후면 anchor search 사전 검수

**최종 요약 판정: 문제없음.** 잔여 Critical / Warning / Suggestion 없음. 아래 발견 Warning은 소비 전 수정되었고 수정본을 확인했다.

범위는 아직 소비되지 않은 `search_near_rear_anchors.py` 및 `THREE_FACE_NEAR_REAR_ANCHOR_SEARCH_PLAN.md`다. 이전 rear source의 보존본과 diff를 대조하며 변경 부분에 집중했다. 기존 search/helper 검수는 신뢰했다. Native scene/physics/source main은 실행하지 않았다.

## 발견 및 수정 확인

- 수정 전 Warning — [search_near_rear_anchors.py:296](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:296): 왼쪽 edge가 `x=-width(y)`이므로 inward normal은 `[1,-0.01631590413943356]`이다. 수정 전 `[1,+0.01631590413943356]`은 오른쪽 edge 부호였고 실제 수직 reserve가 약0.499734mm였다. Parent에 즉시 수정 권장을 전달했다.
- 수정 후 — 현재 line296은 `[1,-0.01631590413943356]/norm`이다. 저장 원 rear quad의 왼쪽 edge inward normal과 일치한다. 실제 수직 추가 reserve는 `0.5000000000000001 mm`, 두 목표의 왼쪽 margin은 각각 약2.5mm이고 다른 edge margin도 2mm 이상임을 계산했다.

## 변경 계약 대조

- [search_near_rear_anchors.py:35](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:35): catalog와 기존 proposal의 예상 SHA 목록을 충돌 검사와 함께 병합한다. 실제 두 목록의 충돌은 0이다. 새 catalog/raw source·계획·producer·보존 source/manifest를 추가하고 종료 전 다시 검사한다. 보존 rear source SHA는 `0120843f1a07d51f65f35fe0666652dbcbf319b6408260719a22b24badc2be33`이며 manifest와 일치한다.
- [search_near_rear_anchors.py:139](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:139): catalog 선택 triangle의 centroid와 local normal을 fresh source mesh와 대조하고 관측 source anchor를 별도로 보존한다. catalog303/1462 × clearance0.3/0.7mm의 네 조합을 생성하며 각 후보마다 thumb anchor를 바꾼다.
- [search_near_rear_anchors.py:288](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:288): 기존 17좌표 actual bounds와 catalog lower/upper의 exact 일치를 요구한다. 시작 q81·preserved81T·LA는 저장 catalog와 exact 일치한다. 후보는 17좌표만 수정하며 나머지64 초기각, 기존81T/gain, G pose 및 LA를 변경하지 않는다.
- [search_near_rear_anchors.py:199](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:199): 이전 실제 교차 목록에서 추출한 soft pair는 index3–guitar/fret3, middle3–guitar/fret4의 네 쌍이다. 같은 G 좌표계로 vertex/plane을 변환한 face-plane gap에서0.1mm 선호 residual을 추가한다. 이는 soft 근사이며 full SAT·actual clearance 인증으로 쓰지 않는다.
- [search_near_rear_anchors.py:345](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:345): 이전 full human–guitar / cross-hand / 비인접 왼손 LP 교차 검사, angle/offset/target exactness, palm-up, point margin, hull finite-patch primal/dual distance 및 rear witness hard gate는 diff에서 그대로 유지됨을 확인했다.
- [search_near_rear_anchors.py:419](/home/ajou/yigyu/3/stability_adapter_2/search_near_rear_anchors.py:419): 행마다 source_anchors/source_facets를 deepcopy해 저장하고 통과 행의 별도 native_proposal_path에 그 행의 facets/anchors와 단일 row를 기록한다. [run_seed2_support_warmstart.py:27](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_support_warmstart.py:27)의 `--proposal` 입력, trial_path/sha 검증, [multi_face_grip_audit.py:38](/home/ajou/yigyu/3/stability_adapter_2/multi_face_grip_audit.py:38)의 facets 소비 schema와 맞는다. 실제 native 전달 시 각 행의 native_proposal_path를 사용해야 한다.

## 검증

문법 compile 통과. 새 separating_gap 함수만 AST로 추출한 합성 box 사례에서 분리+1mm와 교차-1mm를 정확히 구했다. Personalized context의 단일 row 및 facets/anchors 교체 schema를 합성 자료로 확인했다. Catalog의 낮은 선형 잔차는 신규 search나 물리 성공을 보장하지 않으며 이 검수는 후보의 실제 통과 결과를 만들지 않았다.

최종 검수 SHA256:

| 파일 | SHA256 |
|---|---|
| search_near_rear_anchors.py | 9f77f616691e552d3635e7ff2553a7b5f8a8263bee3a79247ccccf198465b89a |
| THREE_FACE_NEAR_REAR_ANCHOR_SEARCH_PLAN.md | 0d6267fbca44730b91a9a32c7a57a3371e3c7822102d5d2212b891498b576354 |

이번 검수는 이 `source_pre_review.md`만 생성했다. Code/input/기존 소비 파일을 수정하지 않았다.
