# 사용자 허용 범위·연주 우선 계약 독립 검수

요약 판정: **문제없음**. 이번 범위는 문서와 저장 pose의 오프라인 회전·위치 검산이다. 새 구현·native·physics·actor·학습·렌더 실행은 없으며 다른 담당자의 파일이나 이전 자료를 수정하지 않았다. Critical/Warning에 해당하는 미해결 문제는 없다.

[계약:7](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:7)의 위치는 전체 기타 mesh/바디 중심과 구분한 world actor-root이며 X[-.50,-.15]m/Y[-.15,.15]m/Z[.65,z_chest]m를 기존 [위치 박스 계획:6](/home/ajou/yigyu/3/stability_adapter_2/POSITION_REGION_BOX_PLAN.md:6)대로 유지한다. Chest body-origin 높이는 기존 근사치이며 미래 환경에서 재측정하고 표면/충돌 경계로 인증하지 않는다. [회전 계약:11](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:11)의 extrinsic xyz X[45,90]°/Y[50,100]°/Z[135,180]°는 [기존 main 기록:1382](/home/ajou/yigyu/3/stability_adapter_2/README.md:1382)과 같다. 이전 임시 30mm/5°나 수평 비교 ±10°를 강제 허용 경계로 승계하지 않는다.

저장된 실제 수평 pose의 actor-root `[-.2304154634475708,.08671234548091888,.6759729981422424]m`는 기록된 위치 상자 안이다. xyzw q=`[-.5,.5,.5,.5]`와 `Rotation.from_euler('xyz',[67.5,90,157.5],degrees=True)`의 독립 SO(3) 차이는 **1.1017764609091714e−14°**로 [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playable_envelope_contract_v1/verification.json:1)과 일치한다. Euler 세 값은 모두 허용 구간 안이며 q와 -q의 차이는0이다. 반면 동일 q에 대한 단일 as_euler 결과는 `[-90,90,0]°`와 gimbal-lock 경고이므로 단일 Euler 축별 판정으로는 이 허용 회전을 잘못 거절할 수 있다. [계약:13](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:13)은 이를 명시하고 Euler 상자가 만드는 quaternion 집합의 포함/최단 SO(3) 거리와 경계·특이점·q부호 동치 검사를 향후 구현 과제로 둔다. 현재 일반 회전 판정기를 구현하거나 검증했다고 주장하지 않는다.

[연주·보정 계약:17](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:17)은 범위 안 유효 배치에서는 연주를 우선하고 내부 초기점 복원 비용0, 경계 접근/이탈에는 부드러운 보정·가까운 허용 상태 복귀를 설계한다. 범위 포함과 fret/strike 정확도·타이밍·도달/관통/지지 성공을 분리하며 WAIT→REACH→GRIP→TRANSPORT 또는 작은 떨림으로 연주를 막는 필수 절차를 추가하지 않는다. 임의 경계 문턱·종료 기준도 아직 정하지 않는다. [합성:20](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:20)은 동결 fret/strike+안정화 보정을 하나의 최종 관절 목표에 합치고 기존 root/하체 고정·몸통 목표·66관절 권한·고정 스트랩·모델 관절 한계/충돌 검사를 유지한다. 기타 고정·강제 손 부착·지속 pose 덮어쓰기나 별도 PD 경쟁을 도입하지 않는다.

[최종 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playable_envelope_contract_v1/README.md:1)와 [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playable_envelope_contract_v1/CHANGED_FILES.md:1)은 기존 native t0 사진 재사용·새 이미지/물리0·판정/합성 미구현을 정확히 설명한다. [main README:1407](/home/ajou/yigyu/3/stability_adapter_2/README.md:1407), [PLAN:2234](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2234), [VISUAL_REPORT:2218](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2218)의 새 설명도 동일하다. Verification의 입력3 current SHA와 main3 기존 prefix SHA exact, 최종 문서의13개 링크 존재/줄 범위를 확인했다. root가 기록한 위치 포함 true는 현재 저장 예시의 오프라인 사실이며 런타임 경계·연주 성공 인증으로 확대하지 않는다.

검수 시점 SHA-256:

- PLAYABLE_ENVELOPE_CONTRACT.md: `f6c28379c5e13bcd2b0caaf9580c2ff294608072c6669c4a79ec12b0597ea450`
- README.md: `04dfbbee5c437d361e6aa0fbaeafd188bc311f0d332568f6dceb53f562b4d590`
- CHANGED_FILES.md: `6983310f216aa2b0022e27b5e488ed6bb1ee798be2add8624a88f608cb558020`
- verification.json: `2b024db1c5c2e5bfe7ad9ff899d4382342f25ac56524a2d61e3e8bd5344272a1`

최종 판정: PASS


## Root 최종 기록 추가 대조

[final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playable_envelope_contract_v1/final_verification.json:1)의 5checks 全True·새 physics/actor/training/image 각각0을 읽었다. 계약 plan SHA와 source_final 사본 byte exact, 최종 결과문서2 SHA current exact를 추가 대조했다. 입력3 SHA·main3prefix·위치/Euler 동치는 위 독립 계산에 이미 포함되어 있다. 이전 horizontal54파일 보존은 root의 previous_phase_files_preserved 기록이며 이 추가 문서 검수에서 이전 phase 전체를 재감사했다고 주장하지 않는다. 새로운 material blocker는 없다.

최종 판정: PASS
