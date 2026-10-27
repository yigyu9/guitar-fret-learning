# 세 면 접촉 footprint source 후보 비교 v2

## 범위와 기준

이 단계는 기존 손 지지 목표를 위한 **저장된 CPU source geometry/FK 후보 검사**다. 분석된 네 후보(V1/V2 × 0.3/0.7 mm)는 모두 거절됐다. 이 단계에서는 새 native 초기화·물리 step·현재 조건의 프레임을 만들지 않았고, 다음 물리 trial을 위한 성공 후보도 없다. 그림의 삼각형과 화살표는 source collision facet와 그 바깥 방향을 나타내며, Isaac Gym 렌더, cooked 형상, SDK 접촉 법선, native force 또는 해부학적 손바닥/엄지 표면을 나타내지 않는다.

기준 입력은 [세 면 지지 손실 실행의 native initial values](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/initial_values.json>)다. 이 파일은 실제 초기 81 관절각·81 PD 절대 목표·기타 시작 state와 world 목표를 보존한다. 목표 기타 pose는 `p=[-0.1972053649442413, 0.11878119221286644, 0.8277786273204872] m`, `q_xyzw=[-0.3412600918621295, 0.5816458777723966, 0.5857788413284049, 0.44954729631550555]`이며 절대 strap rest length는 `1.1018469719600776 m`다. 해당 저장 native 실행은 1회 초기화, 1200 step/5 s였다. 그 영상은 이전 실행의 reference 자료로만 재사용한다.

v1에서 시작한 source 기준과 원래 절대 목표를 유지했다. 팔 12개와 엄지 5개, 총 17개 좌표만 source 후보에서 조정하고 나머지 관절 목표·몸통 9 목표·오른팔/손은 유지했다. 탐색 범위는 native joint limit, 2026-08-19 손가락 joint-limit 자료, C02 팔 자세와 기존 절대 목표의 ±0.3 rad 제한을 교차 적용했다. PD gain, 기타 p/q, 절대 strap 길이, 물리 고정과 양팔·손 제어 구성은 후보 생성에서 바꾸지 않았다. 기준 입력과 source 탐색 설정은 [v1 proposal](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v1/proposal.json>) 및 [v2 proposal](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/proposal.json>)에 기록되어 있다. PD의 실제 초기값/gain/한계 배열은 위 native initial-values 원자료를 따른다.

| Source 후보 | 판단 근거 |
|---|---|
| V1 · rear patch 0.3 mm | 목표점 오차는 0.06 mm 미만이었으나 source thumb/palm 교차의 공통 내접반경이 각각 1.370114 mm / 0.214141 mm. 거절. |
| V1 · rear patch 0.7 mm | source thumb/palm 교차의 공통 내접반경이 1.336307 mm / 0.031669 mm. 거절. |
| V2 · rear patch 0.3 mm | 전체 사람-기타 및 양손 source 교차는 없지만 엄지 대표점이 rear patch 왼쪽 경계 밖 0.200727 mm. 목표점 오차 3.200398 mm, thumb hull-to-finite-patch gap 0.232736 mm로 요구 0.3 mm에 못 미침. 거절. |
| V2 · rear patch 0.7 mm | 엄지 대표점이 경계 밖 0.395092 mm, 목표점 오차 3.412930 mm. hull-to-patch gap 0.421864 mm여도 점 여유 조건을 통과하지 못함. 거절. |

두 V2 palm 대표점은 finite side patch 안쪽 4.721738 mm와 4.960842 mm에 있다. hull-to-patch gap은 0.305334 mm와 0.493368 mm다. 선택된 palm triangle의 이웃 vertex는 patch 밖으로 뻗으므로 그림은 facet 전체가 patch 내부라고 주장하지 않는다. V2 엄지 facet 바깥 방향은 +Gx 성분이 큰 source 방향이다. 기존 관측점을 native 힘 방향으로 해석하지 않는다.

![저장 source 후보의 엄지 후면 patch와 손바닥 side patch 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifacts_v2/source_candidate_comparison.png)

그림 좌측은 G-root X/Y mm 좌표의 finite rear patch, 네 엄지 source point/target, source facet 방향 및 요청한 왼쪽 경계 안쪽 2 mm 선을 표시한다. 우측은 G-root Y/Z mm 좌표의 V2 finite palm region, 두 source triangle과 대표점을 표시해 삼각형 vertex의 overhang을 그대로 보인다. `SOURCE` 방향 표시는 source facet outward 방향일 뿐 native 힘이나 PhysX 접촉 방향이 아니다. 수치 원자료는 [analysis_v2.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/analysis_v2.json>), figure producer는 [make_contact_footprint_artifacts_v2.py](/home/ajou/yigyu/3/stability_adapter_2/make_contact_footprint_artifacts_v2.py:27)다.

참조용 실제 5초 native whole-body 영상은 이전 기준 실행의 영상이다. 이번 후보의 영상이 아니다.

![기존 saved finger targets 기준 실행의 실제 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/whole_body.mp4)

다음 미실행 계획은 [후면을 향하는 thumb source facet 선택 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md:1)이다. 네 후보 모두 source 단계에서 제외됐고, 이번 결과로 초기화·실제 접촉·지속 지지·안정성 또는 연주 성공을 주장하지 않는다.

## 실행과 검수 범위

팔12는 현재각±0.05rad, 엄지5는±0.10rad 범위에서 탐색했다. 나머지64 초기 좌표와 모든81 절대PD목표는 유지했다. Source 교차의 공통 내접반경은 물리 관통 깊이가 아니다. 실제 환경 실행은 승인 후보0 때문에 수행하지 않았다.

V1/V2 source 검색은 각각8.128650/8.374150초에exit0이었다. Canonical 분석은 `analysis_v2.json`, 그림은 `artifacts_v2/source_candidate_comparison.png`이며 그림 생성10.895391초/exit0/native0이다. [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifact_execution_v2.json)과 [입출력 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifact_manifest_v2.json)을 저장했다. 분석v1은 자신의 stdout 로그를 입력에 포함해 후처리 검증에 실패했다. [원본 보존](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/analysis_bookkeeping_v1/preservation.json) 후 explicit source 입력만 읽는 새v2를 사용했고 네 후보 수치는 exact 같다. 첫 wrapper의경로보호 실패도 v1 phase의 wrapper_start_failure에 보존했다.

[Source V1 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v1/review.md)와 [Source V2 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/review_v2.md)는 완료했다. 뒤의 검수에서 이전 feature-mapv2/PNG3개의 최종 독립 검수도 완료했다. 새 요약v2/그림의 최종 독립검수는 재호출 도구 thread limit 오류로 보류했고 root의 수치·실제PNG QA와 구별한다. 미래 간격 경계 후보는 QP primal–dual 거리 구간을 확인한다.
