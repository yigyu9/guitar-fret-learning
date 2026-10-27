# 변경 파일·절대 경로와 실제 줄 번호

기존 stability_adapter/·공용자산·이전 결과·독립 학습은 보존했다. 이번 권장 실행/분석 파일은 아래와 같다.

|파일·줄|역할|
|---|---|
|[INITIAL_POSE_QUALIFICATION_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_QUALIFICATION_PLAN_V1.md:1)|원래 조건·단계·평가·중단 계획|
|[prepare_initial_pose_qualification_v4.py](/home/ajou/yigyu/3/stability_adapter_2/prepare_initial_pose_qualification_v4.py:21)|권장 cold 초기후보 생성·analytic capsule/source·EW도달·설정 생성|
|[run_initial_pose_qualification_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py:17)|실제 native 초기 검증·유한 제어·전신3카메라·raw접촉/제출토크 기록|
|[run_initial_pose_qualification_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_v2.py:109)|정지/타현과 왼손 protocol 선택·초기 release offset|
|[analyze_initial_pose_qualification_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_initial_pose_qualification_v1.py:19)|완료 조건240Hz BB/SO3·접촉·관절/명령 검사|
|[analyze_initial_pose_qualification_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_initial_pose_qualification_v2.py:19)|미완료·보호중단도 그대로 분석|
|[render_initial_pose_qualification_v1.py](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v1.py:11)|정상 시험의 전신3시점 접촉점 영상 후처리|
|[render_initial_pose_qualification_v2.py](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v2.py:11)|실패 영상의 실제길이·마지막 카메라와물리 차이·중단직전 캡션|
|[INITIAL_POSE_QUALIFICATION_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_QUALIFICATION_COMPLETION_V1.md:1)|완료 체크리스트·판단·다음 작업|
|[README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2476)|메인 안내 결과 추가|
|[PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1392)|메인 계획 결과 추가|

## 보존된 시도

prepare_initial_pose_qualification_v1/v2는 import 실패, v3는 보조 analytic capsule 음수 간격 때문에 채택하지 않았다. v4가 실제 초기값 생성이다. run_initial_pose_qualification_v1은 OM_appearance 카메라 누락으로0step 종료했고 v2가 실제 실행이다. run_initial_pose_qualification_batch_v1은 운영검수후 자식 실행 전 중단해 사용하지 않는다. 이 파일들은 실행/검토 이력으로 보존하며 재사용 권장 진입점과 구분한다.

## 결과·초기값·검토

- [결과·판단·영상 안내](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/README_v4.md:1).
- [초기81관절각·기타 pose](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/source_v4/candidate.json:1).
- [native 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/native_static_v3/initial_values.json:1).
- [원시 측정·실제 완료 여부](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/qualification_summary_v1.json:1).
- [예비/운영 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/review_preflight_v1.md:1), [후처리 해결 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/review_post_resolution_v1.md:1).

main_before_results에 이번 결과 append 직전 원문을 보존했다. 메인 문서는 이후 다른 승인된 작업이 추가될 수 있으며 줄 번호는 이 색인을 만들 때 실제 제목 위치다.

## 검토 보충에서 추가된 파일·줄

- [audit_initial_pose_qualification_240hz_v1.py](/home/ajou/yigyu/3/stability_adapter_2/audit_initial_pose_qualification_240hz_v1.py:11): 240Hz active33위치·81속도 보충 검사.
- [INITIAL_POSE_QUALIFICATION_REVIEW_ADDENDUM_V1.md](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_QUALIFICATION_REVIEW_ADDENDUM_V1.md:1): 검토 보충과 권장 문서.
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2481): 현재 권장 결과 안내 추가.
- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1397): 계획 검토 보충 추가.

## 최종 자료 안내 추가

- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2486): 현재 권장 결과·최종 영상 안내.
- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1402): 현재 권장 결과·최종 영상 안내.
- [최종 이미지·영상 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/README_final_v2.md:1), [최종 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/README_final_v2.md:1).

## 최종 연결 안내 줄

- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2491): 현재 최종 권장 자료 연결.
- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1407): 현재 최종 권장 자료 연결.
