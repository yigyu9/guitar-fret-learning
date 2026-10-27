# 사전 검수 — 상완 가상 요청 cap20N

요약 판정: **문제없음.** 동일26° 초기 후보의 정지 `follow20` 5초 진단 실행을 차단할 사항은 없다. Critical 0 / Warning 1 / Suggestion 0. 운동 진입 승인은 포함하지 않는다.

- [runnerV3:112](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v3.py:112)와 [runnerV3:119](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v3.py:119)의 metadata cap 및 실제 norm clip이 모두 20N이다. v2 대비 변경은 계획 참조·cap10→20·보고 설명뿐이다. 초기 후보, K2000/D30, 현재 기타 기준 목표/COM 점속도, 인간 Jᵀ와 gravity/posture 합산 및 기존 모델 effort clip은 동일하다.
- 오른팔12만 단일 actor effort 제출, other69 POSITION/readback/state 보존, child Elbow/Wrist J열·속도 guard, forearm force0·자유 기타·strap OFF·root/하체 고정 및 1200 physics/300 control 기록 계약이 유지된다. 직접 기타 힘/구속/pose 쓰기는 추가되지 않았다. runnerV3 AST 통과.
- [analyzerV2:48](/home/ajou/yigyu/3/stability_adapter_2/analyze_upright_neckward_pose_v2.py:48)은 저장 metadata의 cap으로 force를 재계산하므로 20N 조건을 지원한다. 이전 source/runner와 사전 리뷰는 보존한다.

Warning 1 — [계획V3:5](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V3.md:5)의 오차 및 cap 도달은 가상 인간 motor점 요청의 관측이다. 실제 접촉력/힘 부족의 인과 확정 또는 cap 증가에 따른 접촉 회복 보장이 아니다. 이전 세 정지 진단의 후기 상완 접촉 및 운동 gate 실패를 성공으로 등록하지 않고, [계획V3:9](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V3.md:9)의 실제 접촉·정착·자세 gate 통과 뒤에만 같은 초기값의 ±5° 한 주기 비교가 가능하다.

새 코드 diff·계획·분석기 호환성에 한정한 사전 검수이며 추가 native/학습/소스 수정 0. 새 실행의 초기 JSON exact·물리 결과·연주/장시간 인증은 후속 범위다.

검수 SHA256:

- runnerV3: `fb1fc2cb67beba4ce81115a7315f184a43e44b5afe41cbba8e54a72b0a9ba585`
- 계획V3: `dd7b93a4e11b5b97bfd1eb7650659cd86ac2df00f735dbdf4723b8814e251904`
- 재사용 analyzerV2: `feca4c1e6cd4d07473e60657368bde5f4ed0a480a171260851b51846b81da0bd`
