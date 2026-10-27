# V3 형상 보존·V4 목표 metadata 패키징 사전검수

요약 판정: 문제없음. V3의 목표 명칭 Warning은 새 V4에서 해결됐고 소비 V3/계획/결과는 보존됐다. 원본 수정·CPU/native 재실행은 하지 않았다.

Critical: 0

Warning: 0

Suggestion: 0

- [packager:20](/home/ajou/yigyu/3/stability_adapter_2/package_right_arm_wrap_forward_v4.py:20): 실제목표를 requested_palm5/10/15mm와 requested_elbow0으로 분리하고 elbow오차는 실제전방변위의절댓값으로 정정한다. 팔꿈치원점고정과 손바닥전방목표를 구분한 [계획:3](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_FORWARD_PLAN_V4.md:3)에 맞다.
- [packager:18](/home/ajou/yigyu/3/stability_adapter_2/package_right_arm_wrap_forward_v4.py:18): 원candidate deepcopy후 세metadata row만 교체한다. 실제 세candidate 전체를 독립대조해 q81/초기G p/q/G39/FK예측 및 cached·fresh지지점/모든 기타필드가 V3와exact이고, row차이는 목표필드와metadata_source뿐임을 확인했다. config는 candidate경로/hash외모든수치와설정이exact다. 물리적 cached-reference 전제는 V3 검수를 그대로 적용한다.
- [packager:9](/home/ajou/yigyu/3/stability_adapter_2/package_right_arm_wrap_forward_v4.py:9): source3JSON·자기파일/계획/helper와 소비V3전체입력을 SHA로확인하고 원candidate/config도 실제읽기전에 pin한다.990입력의 종료SHA와현재SHA가 모두일치한다. 후보연결의SHA도 실제파일과맞다. 기존source/output을쓰지 않고새search_v4경로를쓴다.
- [search_v4/search.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/search_v4/search.json): 세row는 accepted V3후보의metadata복사본이며 geometry_solver_proposals0/native_runs0이다. 추가최적화나새물리실행으로집계하지 않는 scope가정확하다. AST통과.

Native는정정된forward10 후보를 사용할 수 있다. 실제78각/G39/Thorax·Shoulder초기state 및 two_block_configuration의baselineexact, 원자료시계·유한명령·상완/waist/왼손기여·기타drift는 후속결과검수대상이다.

- Packager SHA256: `6dc8e3603e776652074643605f02f8435f4237d73e25b0d9335a274abadac644`
- Plan SHA256: `6786e6d41501f09cf38c5117e76978ac46ceb730b07df71903a0814c30edcaff`
