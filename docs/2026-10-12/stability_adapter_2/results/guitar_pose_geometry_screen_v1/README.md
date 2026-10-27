# 저장된 기타 배치 30개의 손·기타 형상 screening

## 목적과 구현

고정 기타 자세에서 손 관절만 조정한 기존 탐색은 겹침을 해소하지 못했다. 다른 축도
평가하기 위해, 정적 자연스러움 비교에서 저장한 기타 자세 25개 단독 변화와 5개 조합을
그대로 사용하고 사람의 저장 초기 상태를 고정한 채 source collision geometry를 조회했다.

- [screen_static_guitar_pose_geometry.py](/home/ajou/yigyu/3/stability_adapter_2/screen_static_guitar_pose_geometry.py)는 baseline 기타의 모든 body pose에
  후보 기타 root의 강체 변환을 적용하고 MuJoCo `mj_geomDistance`로 30개를 비교한다.
- [analyze_static_guitar_pose_geometry.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_static_guitar_pose_geometry.py)는 저장된 결과를 기존 native
  candidate 의미값과 연결해 요약한다. 기존 정적 캡처·시뮬레이터 결과는 수정하거나 다시
  실행하지 않았다.
- [원자료 screen.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_pose_geometry_screen_v1/screen.json)과 [요약 analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_pose_geometry_screen_v1/analysis.json)에 조건별 결과와 입력
  SHA를 보존했다.

## 결과

| 판단 기준 | 결과 |
|---|---:|
| 정적 후보 source geometry 조회 | 30개 (25 단독 + 5 조합) |
| 왼손과 기타 사이 겹침이 보고되지 않은 후보 | 1개: `audience_yaw+10deg` |
| 전신과 기타 사이 겹침이 보고되지 않은 후보 | 0개 |
| `audience_yaw+10deg`의 전체 human–guitar 겹침 쌍 | 20쌍, 주로 오른손·오른팔/기타 body |
| `elevation+10deg`의 왼손 겹침 | 1쌍, LH:thumb3–기타 signed gap −0.514 mm |
| 새 native 초기화 / physics step / actor / 학습 update | 0 / 0 / 0 / 0 |

따라서 기타 root만 움직이거나 돌려 왼손 겹침을 줄이는 방향은 일부 후보에서 보이지만,
사람 전체와 악기 사이 형상을 함께 clear하게 만드는 저장 후보는 없었다. 기타의 넥·바디
자세와 양손/팔을 함께 재정렬하는 방식이 다음 비교 대상이다. 현재 시각 제안 후보를 기본
시작 자세로 채택하지 않았다.

## 해석 한계

이는 저장된 native 상태를 기반으로 한 **source mesh 정적 signed-gap screen**이다. 20 mm
보다 먼 쌍은 결과 목록에 나오지 않는다. 음수값은 MuJoCo source geometry 거리값이며 PhysX
cooked contact의 보정된 관통 깊이나 동적 접촉·힘·지지 증거가 아니다. 입력 자세의 자연스러움,
연주 도달성, 스트랩 동작도 검증하지 않았다. 후보 간 gap 수치는 탐색 순서를 돕는 proxy이지
자세의 승인 점수가 아니다.

새 actual 물리는 full-body source gate를 통과한 후보가 없으므로 실행하지 않았다. strict G0
checkpoint 자격이 없는 현재 Fret 후보를 사용한 연주 replay/residual 학습도 수행하지 않았다.
