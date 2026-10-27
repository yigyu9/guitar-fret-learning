# 낮은 OM 초기 높이 최종 독립 검수

판정: **문제없음 — 완료된 높이 진단과 다음 비교 후보 추천 범위를 승인한다.** Critical 0건, Warning 1건, Suggestion 0건. 신규 native는 두 조건 각5초이며 높은 OFF 기준은 이전 저장 자료 재사용이다. 추가 native·학습·원본 수정 없이 읽기 전용 대조와 순수 재계산을 수행하고 이 리뷰만 작성했다.

직접 확인한 결과:

| 조건 | 종료 이동 mm | 종료 SO3 ° | 최대 이동 mm | 최대 SO3 ° |
|---|---:|---:|---:|---:|
| 이전 높은 OFF | 114.259337 | 6.512226 | 114.259348 | 9.751527 |
| 양Hip 최소 source gap8mm | 41.009180 | 10.177273 | 41.011242 | 10.177737 |
| 양Hip 최소 source gap3mm | 29.992751 | 7.201794 | 29.993153 | 7.333630 |

저장 trace를 자기 초기 actor-root p/q 기준으로 재계산해 [verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/verification_v1.json:1)과 일치했다. 낮은3mm 후보는 낮은8mm보다 종료/최대 이동·회전이 작지만 높은 OFF보다 종료 회전이 조금 크며, 초기 종료 Δz=−27.835667mm가 남는다. 후기 정착을 초기 자세 완전 유지로 해석하지 않는다. [recommended_initial](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/recommended_initial_v1.json:1)은 성공 조건이 아닌 다음 높이 진단 기준이라는 제한과 실제 config/candidate SHA가 맞다.

source 목표는 양Hip 최근접 거리의 최솟값이며 가까운 왼Hip이 기준이다. 3mm 후보의 오른Hip 간격은11.666880mm, world z 초기 하강은107.109548mm다. 거리·수직 높이·PhysX cooked clearance는 구분되어 있다. candidate의 x/y/quaternion은 유지되고 native float32 읽기의 작은 위치 차이는 README가 공개한다. 낮은 두 후보의 변경은 양팔24 초기각이며 body/head/finger 초기목표와 root/lower 초기 상태는 유지된다. 실제 동작 동안 상체 관절각이 초기 목표에 완전히 고정됐다는 뜻은 아니다.

두 actual 실행은 각각 1,200 physics/300 control/151frame로 완료됐다. 모든301trace 제출 목표가 q_ref와 exact이며 PD·질량/COMI·캐시는 기존 높은 OFF와 같다. 단일 정상81D POSITION PD·noPI·기타 자유·기존 passive strap ON/원LA·초기 두 state setter·runtime 금지 API0 경로를 대조했다. 151개 표본의 현재 계산/직전 적분 commanded 장력0N은 센서 힘이나 모든 physics step의 장력 인증이 아니다.

추천 후보 접촉 raw를 독립 집계한 G:body–L/R Hip 양의 lambda는292/294표본이고 Chest/Spine/R_Shoulder/R_Elbow는0/300이다. 바디 이외 기타 부품에 LH:thumb2/3/middle3는283/299/257, palm은0/300이다. 이는 전용 넥면 압현·palm grip·힘 분담·연주 성공의 판정이 아니다. 60Hz 접촉 query가 모든240Hz 적분 시점의 접촉/비접촉을 인증하지 않는다.

분석 입력2,792개·각 native attempt closure·사전 핀·provenance 입력 전후/출력/producer SHA를 대조했다. 이전 phase2,889개 파일은 main 시작 snapshot 대체로 SHA가 모두 일치하며 완료 main4 append prefix/SHA도 통과했다. 보관6MP4 원본/복사 SHA가 동일하다. 물리5초와151frame/30fps 영상5.033333초를 구분했고 전체 영상 디코딩은 수행하지 않았다.

원 전신·initial strings 및 [최신 측면 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v2/initial_side_comparison_v2.png)를 직접 열었다. v2의 64px 하단 캡션은 잘리지 않고 양Hip 최소 간격 라벨이 맞으며 세 이미지 영역을 원 native와 픽셀 exact 대조했다. 전신 카메라의 비교 시점 view/projection은 세 조건에서 동일하다. 초기 측면은 기타를 따라가는 카메라이므로 픽셀 높이를 world 하강량으로 읽지 않는다. 높은 기준 측면만 기존 ON 초기 이미지를 재사용했으며 OFF/ON initial JSON byte-exact 근거와 구분 설명이 있다. 소비된 잘린 v1은 보존하고 [최신 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/ARTIFACT_INDEX.md:1)이 v2를 연결한다.

Critical: 없음.

Warning 1건:

- [원 README의 접촉 해석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/README.md:37): ‘받침은 주로 양 허벅지’는 힘·모멘트 분담을 확정하는 문장으로 확대할 수 없다. [해석 보완](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/README_READING_NOTES_V1.md:3)은 허벅지와 빈번한 바디 접촉·가슴/상완 표본0이라는 관측으로 제한하고 손가락의 지지 기여를 배제하지 않아 적절하다. 최종 설명은 이 보완을 따른다.

Suggestion: 없음. 반복 재현성·연주·왼손 철수·겨드랑이 유지·formal 안정 허용영역은 미검증이다. [봉인 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/seal_phase_v2.py:14)는 v1/v2 모든 provenance로 검사 범위를 확장하고 기존 버전을 보존한다. 입력·이전 inventory/main snapshot·append·6영상·리뷰 존재 검사와 새 출력 생성을 읽기 전용 확인했으며 실제 봉인 결과는 root 후속 범위다.

검수 SHA256: verification `4960bc464f4010e10c4db5e87707a9fbba6afdae813e6434751636f980c9e77d`; 분석기 `13942dca4dc9fef113cc09be6f31b21cb0e6c55870347ccd7fc738b0566e254b`.
