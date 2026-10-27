# 사전 검수 — 덜 숙이고 넥 쪽으로 더 돌린 자세

요약 판정: **문제없음.** 선택한 `bend-14_neckyaw30`의 정지 5초 진단 실행을 차단할 사항은 없다. Critical 0 / Warning 1 / Suggestion 0. 실제 native 실행·연주·장시간 유지의 인증은 이 검수에 포함하지 않는다.

- [source:23](/home/ajou/yigyu/3/stability_adapter_2/search_upright_neckward_pose_v1.py:23)의 world-Z yaw를 lean/forward 뒤에 적용하는 방향과 분산 목표, body±.20rad/head±.30rad 및 오른팔 모델 교집합을 확인했다. 선택 후보는 고정 54 scalar가 이전 seed와 exact이고 모든 81각이 native 한계 안이다. 기존 고정 항목의 경계값을 새 움직임의 여유로 해석하지 않았다.
- [source:37](/home/ajou/yigyu/3/stability_adapter_2/search_upright_neckward_pose_v1.py:37)의 genuine FK를 선택 candidate와 재대조했다. 최대 위치/회전 오차는 5.61e−16m/5.38e−16rad다. 기타 quaternion은 이전 seed와 동일하고 BB 중심 이동은 [−20, −5.21705, +8.46010]mm로 각축 ±20mm 안이다. 전체 source clear 및 capsule 하한, 근위30% 2.828883mm·전완13.995395mm·오른허벅지0.199637mm 조건이 통과했다.
- [runner:20](/home/ajou/yigyu/3/stability_adapter_2/run_upright_neckward_pose_v1.py:20)의 단일 인간 effort 제출 guard와 mixed-mode POSITION69/state 검사는 이전 실행 경로와 동일하다. 오른팔12 EFFORT, forearm point force 0, 상완 인간 motor점 cap10N, 나머지69 POSITION, 자유 기타·strap OFF·root/하체 고정 계약을 유지한다. 새 phase/계획 경로 외 제어 변경은 없다. config는 60Hz/240Hz, 5초, 학습 불가이며 정지 amplitude 0이다.
- [자세 측정:14](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/measure_torso_posture_v1.py:14)는 검증된 동일 기준 Chest 축을 native 회전으로 운반하고, 이전 `static_neckyaw12`를 실제 비교 기준으로 사용한다. [계획:10](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V1.md:10)의 실제 숙임 감소/넥 방향 증가·기타 및 접촉 gate를 통과한 뒤에만 ±5° 한 주기 비교가 가능하다.

Warning 1 — [source:39](/home/ajou/yigyu/3/stability_adapter_2/search_upright_neckward_pose_v1.py:39)의 −14°/30°는 원자연 기준에 더한 source 목표 성분이며 실제 절대 앞기울기/heading이 아니다. 근위0~30% 구간 최소 gap과 호환 키 `proximal_upper_arm65_witness`도 실제 해당 부위 접촉·힘 분담·해부학적 겨드랑이 지지의 증거가 아니다. native 자세 및 공간 분류 접촉으로 별도 판단해야 한다. 고정 54 scalar 역시 부모 몸통 회전 뒤의 world pose 고정을 뜻하지 않는다.

검증: source 입력 624개 SHA 현재 일치, config→candidate SHA 일치, 관련 Python 4개 AST 통과. 새 물리 실행/학습/소스 수정 0. 보존 전수 봉인은 root의 후속 범위다.

검수 시 SHA256:

- 계획: `5cd68112a367317364e891d158390d1acbe60c270aaff245748dd11e4fad8532`
- source: `b7b2a5edd7312d498572574f1f80d62f0b55465b8100ca307ee7158acbbb47b5`
- runner: `0cbeea2769c00f29147850afee0162b150f7a789548fd3e3718d96071457a60d`
- analyzer: `a3981c7d5f80ce1a76828731c6546d1b3370552a989943ce6cde98f3310cbfd2`
- 자세 helper: `fe951bb00cca2aecfd38f6a4ac775f9b2c2852e6c6334aaeb726c061224f9d82`
- search JSON: `96b5b60ad298c8963b4de0203247bc9d2a643e3e4972e5ba4ec42ffbc3e680af`
- 선택 candidate: `0dd81b9d554fbacb86b181422209cd0f52c21656f7575e1ad9f88d6b45216241`
- 선택 config: `9e2970a8694ab37f4ee49672892c7ba2df406ee05bcc2c7189608bfae15507fd`
