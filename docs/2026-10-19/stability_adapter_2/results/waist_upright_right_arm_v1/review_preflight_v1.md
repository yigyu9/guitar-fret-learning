# waist 척추 굽힘 완화·오른팔 접근 사전 검수 V1

요약 판정: **수정 권장**. Critical 없음. Source 검색·native 실행 전의 계획/소스 검수다. 검수자는 원본을 수정하거나 검색을 실행하지 않았다.

검수 범위는 새 `WAIST_UPRIGHT_RIGHT_ARM_PLAN_V1.md`, `search_waist_upright_right_arm_v1.py` 및 그 실행 계약에 필요한 helper 부분이다. 프로젝트 전체가 untracked인 상태여서 새 파일 전체를 변경 범위로 보았다. `AGENTS.md`, `EXPERIMENT_WORKFLOW.md`, README의 최신 waist/body-approach 요약을 대조했다.

## Critical

없음.

## Warning

- [search_waist_upright_right_arm_v1.py:27](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v1.py:27): `calibrated_upper_fk`의 human XML 소비(26행), `CapsuleBodyDistance`의 guitar XML/OBJ 소비(27행), clearance XML 소비(35행)가 `inputs_before` SHA 생성(49~50행)보다 먼저다. 목록 자체는 완전하지만 형상 소비 전 봉인이라는 보존 규칙을 충족하지 않는다. 경로 발견 후 SHA를 저장하고 FK/거리 helper를 구축하도록 순서를 바꾸며, 발견에 사용한 manifest/XML도 SHA와 재대조한다.
- [search_waist_upright_right_arm_v1.py:110](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v1.py:110): `elbow_inward > .25*inward_m`는 기준 팔꿈치→bbox 중심 축에 대한 변위의 양의 투영만 확인한다. 축에 수직인 변위가 크면 실제 중심 거리는 증가해도 수락될 수 있다. 요청 방향을 검증하려면 `||elbow_after-centre_W|| < ||elbow_before-centre_W||`도 검사하고 전후 거리 또는 목표점 3D 오차를 기록한다. 실제 후보가 이 문제를 보였다는 뜻은 아니며 아직 검색하지 않았다.

## Suggestion

없음. body9 scalar 변화와 부모–자식 회전 변화 표는 계획에 명시된 후속 산출물 단계에서 각각 확인한다.

## 확인된 내용과 한계

- `right_axis`는 두 Hip origin의 수평 차이이며 `[0.9992526738574109, 0.03865350939843399, 0]`다. `front_axis = [-right_y, right_x, 0]`와 world up에 대해 `right × up = -front`이므로 61행의 양의 world 오른축 회전은 뒤로 기울이는 올바른 부호다. 초기 Chest up-vector 전방기울기는 **65.4123192184°**이며 56~57행의 atan2 정의와 106행의 감소량 부호도 맞다.
- Torso/Spine/Chest world 목표는 누적 .25/.625/1 비율이고 body9를 먼저 맞춘 뒤 고정한 `q`에 right12만 대입한다. left12/head6 후속 fit 역시 body9/right12를 바꾸지 않는다. DOF suffix를 world축으로 사용하지 않는다.
- 몸통±.15, 양팔±.4, 머리±.35rad는 native model 한계와 교집합이다. R_Elbow_y의 ±5° 여유도 별도로 둔다. float32 양자화 후 모델 한계·finger42 exact·Thorax <3mm·상완 근위30% <4mm·전완 >12mm·waist 영역·전체 source 비겹침·왼손목 p/q·머리 방향을 검사한다.
- 기준은 기존 `right_thigh_waist_v1/search_v5/shift95_front30_roll-5/config.json`이며 최근 6mm body-approach 조건을 소비하지 않는다. 기준 candidate SHA/native reference SHA가 config와 일치하고, 기준 native 초기 81각과 candidate 81각 및 joint 이름 순서가 정확히 같다.
- guitar XML 69개 실제 mesh 경로, XML/manifest union 70개, human XML 37개 실제 mesh 경로가 모두 존재하며 새 SHA 목록 구성에 포함된다. 보존된 asset·질량·hip/하체와 finger42를 바꾸는 로직은 없다.
- 기타 root p는 native 기준 복사, q는 같은 Rotation 객체이며 후보의 G39 body state는 기존 강체변환 helper로 만든다. 직접 force/부착/runtime pose 덮어쓰기는 새 검색 소스에 없다. native 판정은 기존 runner의 p <3µm/q <1e-5rad 및 root/하체 exact 검사로 재검증한다.
- 재사용 `run_right_body_approach_v1.py`가 새 candidate의 `right_block_cradle`/예측 pose 계약을 받을 수 있다. 초기 정지 설정의 elbow amplitude는 0이다. ±5° 1주기 후속 조건은 별도 설정/실행이 필요하며 이번 검색 소스가 그 단계를 이미 실행한 것은 아니다.
- Python AST 문법 검사 통과. 전체 source audit, 수렴 결과, 실제 cooked 접촉과 5초 유지 성능은 미검증이다. 기존 runner는 수정하지 않았고 native도 실행하지 않았다.

## 검수 입력 SHA256

- `search_waist_upright_right_arm_v1.py`: `762297cc887eae100b6c21790df2ad8e960525995e98727b64deace28951f84a`
- `WAIST_UPRIGHT_RIGHT_ARM_PLAN_V1.md`: `c353d7d1397c8fca83c93de62a445612729463d6f4887eca33aed59487515c6f`

새 검수 기록만 생성했다. 다른 담당자의 파일은 수정하지 않았다.
