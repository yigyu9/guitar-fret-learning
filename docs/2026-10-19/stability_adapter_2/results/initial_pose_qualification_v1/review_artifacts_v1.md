# 초기 자세 적합성 산출물 최종 독립 검수

요약 판정: **문제없음**. 미해결 Critical 0건, Warning 0건, Suggestion 0건. 실제 물리·측정 검수는 `review_final_v1.md`에 보존하며, 이번에는 복사 미디어·그래프·최종 권장 문서와 생성 근거를 검수했다. 검수자는 이 새 문서만 작성했고 원본·다른 담당자의 파일은 수정하지 않았다. 최종 보존 감사·봉인은 root 담당이다.

## 권장 문서와 정정

- 현재 검수 대상은 [결과 README V4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/README_v4.md:1), [변경 색인 V4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/changed_files_v4.md:1), [산출물 최종 설명 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/README_final_v2.md:1) ↔ [영상 색인 최종 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/README_final_v2.md:1)다. 이전 버전은 과거 기록으로 보존한다.
- 직전 final V1 색인의 상위 결과 링크가 이전 root V2로 이어지고 문서 생성 근거가 Luna의 이전 단계와 섞인 점을 전달했다. 새 final V2는 상위 결과 V4로 연결되고, root `final_docs_before_v2.json`/`final_docs_manifest_v2.json`과 미디어 복사 manifest/이전 Luna 문서 manifest를 구별한다. 현재 쌍의 양방향 링크와 모든 로컬 절대 링크·존재·명시 줄 범위를 확인했다.
- station 설명은 **새 cold 실행이 이전14초 B분리 자세를 초기값으로 사용**했고 새A 잡기 목표가 이전A 대비 G좌표[-1.170,+42.048,−0.034]mm로 **이전B잡기 지점에 가깝다**고 올바르게 설명한다. 이전 cycle 자체가 B분리에서 시작했다는 보존된 과거 문구는 권장 문서에 없다. 몸통 하나의 변수 비교라는 주장도 없다.
- 4개 완료 조건/1개 보호중단, 7.283333초 물리/7.266667초 마지막카메라/7.3초 표시길이, actor-root203.189mm와 BB115.508mm, 회전35° 중단 아님, B잡기 미수행을 구별한다. 실패 중 RH엄지3/중지3의181step 접촉과 별도 타현 시험의 오른손 접촉0도 정확하다.
- 60Hz81관절 표본0.19815°와240Hz active33 위치0.220198°를 구별하고, 나머지48위치의240Hz 최대가 미기록임을 밝힌다. 81속도240Hz 최대3.203110rad/s와 목표 변화율도 구별한다. near 기준의 왼손 접촉·타현41step 왼손 접촉·근한계 여유·Z+3mm에서 재계산하는 local motor reference·능동 유한 제어·비연주/비강건성 검증 한계도 사실과 맞다.

## 미디어·그래프 검증

[copy_manifest_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/copy_manifest_v3.json:1)의 **38개(20 MP4+18 PNG)** 모두 source SHA=복사 SHA=해당 visual report SHA임을 독립 확인했다. MP4는 각 복사본을 직접 ffprobe했고 다음과 같았다.

|조건|개별/합본 영상 수|각 프레임|fps|각 MP4 표시 길이|
|---|---:|---:|---:|---:|
|baseline|4|301|30|10.033333초|
|static|4|301|30|10.033333초|
|strike|4|151|30|5.033333초|
|left_cycle|4|219|30|7.300000초|
|Z+3mm|4|301|30|10.033333초|

모든 개별 front/right_side/top은1280×940, 모든 합본은1920×470이다. PNG18개는모두3840×940이다. 물리 경과와 영상 표시 길이는 초기0초 프레임 때문에 구별한다. 색인에서 영상20개를 Markdown MP4 이미지 문법으로 연결하고 대표 정지·실패 합본도 설명 본문에서 바로 재생할 수 있다.

- [비교 그래프 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/maxima_comparison_v3.png)를 직접 열었다. 두 패널이 BB이동mm/SO3회전도를 별도 축으로 표시하고,5조건 숫자가 원래 summary의 반올림 값과 같다. 실패 막대는 보호중단 명칭·해치·별표로 구별하며 본문은 불완전 실행 관측구간 최대임을 설명한다. 별도 시점의 두 최대를 같은 순간이라고 주장하지 않는다.
- 복사된 정지10초와 왼손6.5초 PNG를 직접 확인했다. 전신 앞/오른쪽 옆/위 시야, 원래 재질색과 원형 접촉 표시, 프레임 밖 범례가 맞다. 같은 해시의 부분실패 마지막7.267초 소스 PNG는 앞선 최종 물리 검수에서 직접 확인했다. 색·채움/빈원·X-ray·고정 원 크기 설명은 실제 프레임과 맞고, 힘N/접촉면적 인증으로 부르지 않는다.

## 입력·이전 산출물 보존

- artifact_before_v2/v3/v4/v6의 입력3,942/3,991/3,995/4,018개를 각각 현재 SHA와 대조해 차이가 없었다. 초기 manifest V1의 before/after3,942개 목록도 동일하다. producer SHA와 manifest V1/V3/V4의 기존 출력41/41/2개도 현재 해시가 모두 일치했다. 새 문서 때문에 원래 성공 산출물을 덮어쓰지 않았다.
- 현재 `final_docs_manifest_v2.json`의9개 입력과4개 출력 SHA가 모두 일치하고 inputs_unchanged=true다. 이 생성 근거가 현 권장4문서와 맞는다.
- 역사적인 root `final_docs_before_v1.json`의 메인 A/README·PLAN은 나중 승인된 append로 현재 전체 SHA가 다르다. 당시 SHA와 정확히 같은 사본을 `main_before_final_links_append`에서 확인했고, 현재 메인 파일의 바이트 접두사임을 검증했다. 이를 원래 전체 파일 SHA의 현재 일치로 소급 주장하지 않는다. 다른10개 입력은 그대로다.
- main_before_results/scope_append/final_append/final_links_append의 README/PLAN 경계 사본은 각각 현재 파일의 완전한 접두사다. 변경 색인의 실제 제목 줄 README2476/2481/2486/2491 및 PLAN1392/1397/1402/1407을 확인했다. 가장 최근 안내는 결과 V4와 final V2쌍을 가리킨다.
- native_static_v2의 원래 guardfalse와0-step 설정 실패/중단 batch/과거 source 실패는 과거 기록 그대로다. 본 권장 산출물의 current 문서 생성 guard와 물리 실행 완료 여부를 혼동하지 않는다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/README_v4.md`: `f9edd51ed09ea0387231d92cae7c209b7e1556eca72ecfbfbfcdaafcf57a206e`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/changed_files_v4.md`: `c1fd04945b6189b9b071d42c8aa8097ac1b0af30db0149a292c316dfd8a53a32`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/README_final_v2.md`: `de7ddbefc5c65c36b27fd486c53d72533bd55197c02ea82edc02c33fb81b45d5`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_qualification_v1/README_final_v2.md`: `b84b1a262a602aa64c76c8506aa9dc72a77b87469d06ec28d4c790bb3aac22af`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/copy_manifest_v3.json`: `0a022c8b1dbd4781603e7bbf365aa84fad06655c129e251e8a11a6b1e88f3783`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/copy_manifest_v4.json`: `f67f376df0e328ffb95f56337c02813c7f3ad32c3fab84585230d4f11dfd8688`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/artifacts_v1/maxima_comparison_v3.png`: `310e865f3a79b280a7889d01087de62e56e4fee241d2b2ab960ffe1d14f19ded`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_qualification_v1/final_docs_manifest_v2.json`: `d8dc5fb30ee20fda230821dbe1752953e718017818a96f7d991192c6e6027919`
