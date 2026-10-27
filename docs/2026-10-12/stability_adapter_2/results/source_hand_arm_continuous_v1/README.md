# 연속 팔 source 평가의 진행 경과

두 시작점에서 제한된 Powell 검색을 각 400회 평가했다. 각 패널의 옅은 점·선은 해당 평가의 최대 human–guitar(HG) LP 공통내접반경이고, 굵은 선은 그 수치의 누적 최솟값이다. 선의 best-so-far는 이 한 가지 반경 기준이며 weighted objective 최소와 다를 수 있다.

![두 source seed의 HG 최대 반경과 running minimum](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/artifacts/arm_continuous_progress.png)

| Seed 시작점 | 기준 최대 HG 반경 | Weighted objective 최저 | 최대 HG 반경 최저 |
|---|---:|---|---|
| 원 초기 pose | 4.288365 mm | 전역 row 398 (seed 평가 399), 2,105,994.484; 최대 HG 1.066590 mm, 4쌍 | 전역 row 260 (seed 평가 261), 0.879617 mm, 4쌍 |
| Wrist_y −0.1 rad + Thorax_z +0.025 rad 이전 row47 source 가설 시작점 | 1.231576 mm | 전역 row 798 (seed 평가 399), 1,270,160.432; 최대 HG 0.783417 mm, 3쌍 | 같은 row 798, 0.783417 mm, 3쌍 |

seed 0에서는 weighted objective가 가장 낮은 row 398과 HG 반경이 가장 낮은 row 260이 다르다. seed 1에서는 두 기준의 최저가 같은 row 798이다. 이 표와 그림은 선택이나 실제 후보의 성능을 말하지 않는다.

두 Powell 호출은 각각 400회 한도에 도달해 status 1로 끝났다. 이는 예산 종료이며 수렴 성공이 아니다. 800개 전체 평가에서 HG 교차가 남아 source-clear 후보는 0개이고 선택도 없다. 양손 간 형상 검사와 self 1,188쌍 검사는 이번 800개에서 미측정이다. 검색 완료나 그래프의 감소를 전체 가동범위의 불가능성 증명으로 해석할 수 없다.

원 검색은 10개 검사와 72개 입력 SHA 사본 검증을 통과했고 exit 0이었다. 최초 저장 analyzer는 row 33의 충돌 목적값 재계산 차이 `1.490116119e−8`이 그때 설정된 `1e−8` 허용치보다 커져 실패했다. 해당 source·failed invocation·partial manifest는 보존했다. v2 분석은 같은 저장 평가를 다시 읽었고 목적함수 산술 재계산 허용치만 `1e−10 + 8·float64 epsilon·scale`로 바꿨다. 입력 범위나 source·native 조건은 바꾸지 않았으며 v2의 11개 검사가 통과했다.

그림은 저장된 정적 source 형상 평가다. LP 공통내접반경은 PhysX cooked 형상 관통 깊이나 실제 접촉을 뜻하지 않는다. Cross/self 검증, 후보 선택, 새 native/physics/actor/training, 5초 안정성 측정은 없다. 두 검색 모두 평가 상한에서 끝났고 이번 후처리에서는 기존 영상 152개를 유지했다.

| 기록 | 파일 |
|---|---|
| 원 검색과 800회 원자료 | [search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/search.json:1), [evaluations.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/evaluations.jsonl:1) |
| 분석 오류·보존된 첫 시도 | [analysis_failure.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/analysis_failure.json:1), [첫 invocation](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/analysis_invocation.json:1), [첫 partial source manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/analysis_source_manifest.json:1) |
| 보정된 저장 분석 | [analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/analysis_v2.json:1), [v2 invocation](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/analysis_v2_invocation.json:1) |
| 탐색 범위·후속 방향 | [실행 leaf](/home/ajou/yigyu/3/stability_adapter_2/ARM_CONTINUOUS_EXECUTION.md:1), [v2 분석 leaf](/home/ajou/yigyu/3/stability_adapter_2/ARM_CONTINUOUS_ANALYSIS_V2.md:1), [원 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_CONTINUOUS_PLAN.md:1), [quiet 기준 후속 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md:1) |

다음 quiet 기준 입력 계획은 아직 실행되지 않았다. 이번 그래프는 그 계획의 실제 제어 응답이나 기타 유지 결과를 대신하지 않는다. 실행 명령·환경·입력 및 소스 사본 해시·PNG 해시는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/CHANGED_FILES.md:1)에 정리했다.
