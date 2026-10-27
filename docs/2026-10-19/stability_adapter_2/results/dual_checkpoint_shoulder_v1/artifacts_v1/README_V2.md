# 두 체크포인트 연결 확인과 첫 원본 종료 기록

현재 어깨 전방 10 mm 후보의 기타 초기 상태를 유지한 채 Fret 035000과 Strike 010000의 고정 baseline checkpoint를 실제로 연결했습니다. 이 시험은 초기 연결과 전환을 확인하는 짧은 점검이며 곡을 완주하지 않았습니다.

![native2 전신 및 왼손·기타 넥 방향 손 카메라의 0.00초, 2.00초, 2.05초 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/native_v2_whole_and_hands_0_2_2p05.png)

위 패널은 `capture.json`에 물리 step 0/480/492로 기록된 실제 native 렌더러 프레임입니다. 윗줄은 전신 카메라, 아랫줄은 왼손과 기타 넥 방향 카메라의 확대 화면입니다. 오른손은 전신 화면에서 보이며 아랫줄은 오른손 근접 화면이 아닙니다. 2.05초 종료 프레임도 표시했습니다. 원본 MP4는 63프레임 ÷ 30fps = 2.1초로 인코딩됐습니다. 인코딩 길이와 물리 계산 시간은 다르며 종료 뒤 정지 프레임을 추가하지 않았습니다. 손 화면의 기타 줄은 물리 상호작용이 없는 시각 표시입니다.

## 연결한 고정 checkpoint

| 연주 actor | checkpoint 경로 | SHA-256 |
|---|---|---|
| Fret | `/home/ajou/yigyu/3/fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/checkpoints/fret_035000.pt` | `a6f0c303f69686eb02ebed5f7dce743fdc223fd89c8a8fb2b40303d0abeab5ca` |
| Strike | `/home/ajou/yigyu/3/strike/training/runs/20260920_Jazz1_sync_baseline/checkpoints/strike_010000.pt` | `9244b33c87426afb28c10a1176b88f23832a50a57605586d4e28084a48160e87` |

[connection_verification_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/connection_verification_v3.json)은 두 checkpoint action 재생의 최대 오차가 0이고 가중치가 동결됐으며, baseline과 초기 상태·PD·질량이 정확히 같다고 기록합니다. 준비 구간 2.0초 동안 관절 q와 root 위치도 정확히 같고, quaternion 정규화 뒤 물리 방향 차이는 0이었습니다. 준비 구간 480개 물리 step 동안 오른팔 effort 명령도 정확히 일치합니다. 이는 초기 상태와 연결 검사이며 연주 결과 검증은 아닙니다.

## 종료 이유와 마지막 손 위치

native1은 카메라 키 `OM_appearance` 누락으로 물리 실행 전에 설정 단계에서 실패했습니다(물리 0 step, 영상 없음). 이 실패 기록은 보존했습니다. native2는 물리 492 step과 제어 123 tick 뒤 첫 source actor 종료 조건에서 멈췄습니다. 준비 구간은 2.0초(480 physics step, 120 control tick)였고, PLAY는 0.05초(두 checkpoint의 동시 추론 3 tick)뿐이었습니다.

첫 종료 조건은 Fret 손목 안전(wrist-safety)과 손가락 뒤쪽(finger-back) 조건이었습니다. Fret `goal_finished`는 false였고 Strike `done`, `goal_finished`, `physical_target_hit`도 모두 false였습니다. 실제 누름, 해결된 관절 event, 관절 crossing은 관측되지 않았습니다. 곡을 완주하지 않았으며 전체 곡의 성공률이나 음악 품질을 0/42로 평가하지 않았습니다. PLAY 시간이 너무 짧아 음악 성능은 판단할 수 없습니다.

마지막 왼손 손목의 source 기준 기타 G 좌표는 `[0.128451675, -0.093393892, -0.568670034] m`입니다. source 손목 안전 및 손가락 뒤쪽 종료 표식은 true였고, 손가락 뒤쪽 최소 local z 표본은 약 −0.470~-0.462 m였습니다. 마지막 확대 화면에서 손이 기타 뒤쪽에 놓인 위치를 볼 수 있습니다. 이는 기록된 source 판정기 위치와 종료 결과이며 native 물리 누름을 뜻하지 않습니다.

종료 시 기타 body bounding-box 중심의 변화는 9.617284 mm, 전체 SO(3) 방향 변화는 2.983343°였습니다. 실행 중 최대 변화는 중심 10.455249 mm와 방향 3.343712°였습니다. 2.00→2.05초 구간의 관측 변화는 0.037970 mm / 0.012452°이며 checkpoint 연결에 인과적으로 귀속하지 않습니다. 오른 상완 접촉은 492개 표본 중 458개였고 왼손·머리·오른쪽 손목 이하 접촉은 0개였습니다.

## 조건과 해석 범위

strap은 꺼져 있었고 기타는 자유 상태, root와 하체는 고정, 기타 직접 힘은 없었으며 학습 update는 0회였습니다. 다음 단계의 후보는 PREP 중 기타 기준 왼손 READY/wrist/finger 안전 전환을 추가하되 기존 안전 장치와 actor 인계 규칙을 유지하는 것입니다.

수정 분석의 기준 자료는 [connection_verification_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/connection_verification_v3.json)입니다. 분석 v1은 quaternion 표현 비교 오류, v2는 raw OBJ bounding-box 좌표 오류가 있어 결론에 사용하지 않았습니다. v3는 XML body offset을 반영했으며 기타 body bounding-box 중심의 G 좌표는 `[0, −0.4, −0.055937985] m`입니다. 자세한 내용은 [분석 메모](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/ANALYSIS_NOTES_V1.md), [native1 설정 실패 보고](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v1/report.json), [native2 보고](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v2/report.json)를 참조합니다.

원본 전신·손 영상 2개는 [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/INDEX_V1.md) 및 [SHA-256/ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/manifest_v1.json)에서 확인할 수 있습니다. [이전 V1 문서(보존)](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V1.md)
