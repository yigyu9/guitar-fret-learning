# 연동 초기 노이즈 사전 독립 검수

요약 판정: **문제없음(지적 수정 반영 후 코드 범위)**. 계획·초기4파일과 추가 pool/runner를 읽기 전용으로 검토했다. 실제 bank 검증·동작·CUDA 갱신·음악 효과는 후속 검증 대상이며, 검수자는 추가 native·학습을 실행하지 않았다.

## Critical — 해결 확인

- 최초 runner는 optimizer_steps=0이어도 갱신 counter와 completed를 저장할 수 있었다. [runner:52](/home/ajou/yigyu/3/stability_adapter_2/run_initial_noise_v1.py:52)의 accepted optimizer step 필수 gate로 허위 학습 통과를 막았다.
- 최초 builder는 trial0 거절 후 noise 후보만으로 zero reference 포함 bank를 저장할 수 있었다. [builder:103](/home/ajou/yigyu/3/stability_adapter_2/build_initial_noise_bank_v1.py:103)은 검증된 trial0이 첫 항목이며 전체≥3(그 밖의 noise≥2)인지 검사한다. trial0의 q는 q0 exact로 유지한다. 요청 count도2..32로 제한한다.
- [warm start:12](/home/ajou/yigyu/3/stability_adapter_2/run_initial_noise_v1.py:12)는 기존 source SHA·checkpoint ABI digest와 물리/관측/제어 core를 검사한 뒤 strict model load를 수행한다. 누락됐던 strap_enabled/strap/action_dimension도 비교한다. 모델/RMS만 이관하고 Adam/counters는 새로 시작하며 물리/RNG exact resume라고 주장하지 않는다.

## 계약 확인

[fit_hands:25](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_noise_v1.py:25)의 dr*gr는 world 회전이고 손 목표는 newp+dr(p−gp)여서 회전 중심이 기타 actor-root다. x/y±5mm·z0..5mm·rotvec 각 성분±1°를 검사한다. 이는 전체 회전각≤1°라는 뜻은 아니다. 좌우 팔12씩만 q0±0.15rad와 native 한계 내에서 IK하고 body/head/finger는 그대로 둔다.

[builder:85](/home/ajou/yigyu/3/stability_adapter_2/build_initial_noise_bank_v1.py:85)는 실제 기타 pose로 source hull을 다시 검사한다. native palm 오차2mm/1°·위쪽 normal proxy·fixed root/lower exact·DOF/기타 초기 속도0·금지 API0을 확인한 후보만 reference와 함께 저장한다. 이 정적 geometry 검사는 cooked PhysX 접촉·힘·동적 안정성 인증이 아니다.

[reset:26](/home/ajou/yigyu/3/stability_adapter_2/deadline_initial_noise_v1.py:26)의 factory patch는 선택한 검증 reference로 기존 native8 초기 exact 검사와 construction-only state write를 유지한다. preload는 sample q_ref+원래 고정 reference의 bounded preload correction이며 현재 실제 q로 매번 기준을 갱신하지 않는다. 제어 중 기타/손 pose overwrite 또는 부착을 추가하지 않는다.

[ABI:35](/home/ajou/yigyu/3/stability_adapter_2/deadline_initial_noise_v1.py:35)는 선택별 config/candidate/reference 입력을 전체 bank union으로 고정하고 선택 index·reset sequence는 metadata로 남긴다. sampling은 검증된 유한 bank의 균등 이산 복원추출이며 연속 균일 노이즈나 매 reset에서 0이 아닌 노이즈를 보장하지 않는다. [pool:45](/home/ajou/yigyu/3/stability_adapter_2/parallel_initial_noise_v1.py:45)는 기존 spawn/cleanup·collector/GAE/KL/RMS 계약을 재사용하고 실제 선택 및 초기/최종 native snapshot을 기록한다.

## 검수 SHA256

| 파일 | SHA256 |
|---|---|
| INITIAL_POSE_NOISE_PLAN_V1.md | `a5cd8afe076a10e816adc93cbcb5353a5ac6798cd7338a9e1579b79dc7b25745` |
| initial_pose_noise_v1.py | `a8014a77faec6c0509fb9b1493960c101fa224734a9717404141db8ef9e8a313` |
| deadline_initial_noise_v1.py | `72f68cfaa89be26b9b1105b8c8ef033ec9949182261ec80eecee2b241ddf8e7a` |
| build_initial_noise_bank_v1.py | `a9cac7e85892747cae53bcdd04917d7dcdea20f225070e2f2f5859363675bae0` |
| test_initial_pose_noise_v1.py | `596d29d512513636a030142f5d60e778057297bf5f1a6cf963cfe3667a0cb52a` |
| parallel_initial_noise_v1.py | `d9b637a759c96169f14b7761abd014b167dcf49c1f140c022b500fca052e729b` |
| run_initial_noise_v1.py | `ab75214bcd613813b8026979b07214c8879245514ec0ea16f3a93b069d0a4408` |

[실행 전 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/source_before_native_v1.json:1)의7파일 SHA가 검수 시점 현재와 모두 일치한다. CPU4는 FK/범위/seed sampling/입력변조 반례이며 native seam을 대신하지 않는다. 시작된 bank 실행 결과는 이 사전 기록에서 인증하지 않는다. 소유한 이 새 리뷰 외 파일을 수정하지 않았다.
