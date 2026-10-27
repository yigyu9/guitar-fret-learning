# 덜 굽힌 몸통과 오른팔 근접: 오른 허벅지 waist 자세 비교

기존 [waist 걸침 기준](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/README.md:1)의 기타 초기 위치·회전을 유지하고, 상체의 초기 전방 기울기를 줄이며 오른 팔꿈치를 바디 쪽으로 접근시켰다. 4° 완화 자세가 2° 완화 자세보다 5초 동안 기타의 최대 이동·회전이 작아 다음 **시각적 자세 검토 후보**다. 이전 waist 기준의 기타 최대 이동 11.831 mm / 회전 6.095°보다 이번 4° 조건 14.545 mm / 8.013°가 커, 안정성 향상이나 학습 기본값 교체로 판정하지 않는다.

| 실제 5초 시험 | 초기 Chest 전방 기울기 proxy | 팔꿈치–기타 BB 중심 초기 거리 감소 | 기타 BB 중심 최대 이동 | 최대 회전 | 결과 |
|---|---:|---:|---:|---:|---|
| 4° 완화 정지 | 61.412° | 3.119 mm | 14.545 mm | 8.013° | 5초 완료 |
| 2° 완화 정지 | 63.412° | 2.090 mm | 17.005 mm | 8.473° | 5초 완료 |
| 4° 완화 + 팔꿈치 ±5° 목표 | 61.412° | 3.119 mm | 14.545 mm | 8.013° | 5초 완료, 실제 운동범위 10.078° |

4° 팔꿈치 시험의 같은 시각 정지 대비 기타 추가 변화는 최대 **0.181 mm / 0.084°**다. 두 4° 시험의 초기값과 첫 2.5초 trace는 정확히 같다. 세 시험 각각 실제 오른 허벅지 waist 접촉은 1198/1200 step, 후기 120/120 step 양의 raw lambda였고, 근위 오른 상완 접촉도 후기 120/120이었다. 오른 Thorax 접촉은 후기 **0/120**, 오른 전완·손 기타 접촉은 0이다. 왼손 손가락 지지의 기여도 남아 있다. 따라서 오른쪽 두 블록의 지속 끼움과 왼손 없는 수동 유지는 확인하지 못했다.

초기 기타 39 rigid body p/q는 기준과 최대 1.1151×10⁻⁷ m / 1.3009×10⁻⁷ rad만 달랐다. Chest 기울기는 강체 축의 world 전방 투영 proxy이고 임상적 척추 각도가 아니다. 몸통9+팔24 EFFORT, 머리6+손가락42 POSITION의 81 목표를 유지했고 기타는 자유, 스트랩 OFF, root·하체 고정, 내부 충돌 ON이다. Fret/Strike 체크포인트와 학습 업데이트는 이 시험에서 0이다.

[실제 초기 비교·경과 이미지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/README.md:1)와 [전신·손 영상 6개 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/INDEX.md:1)을 참조한다. 각 영상은 물리 5.000초를 기록했으며 30fps·151프레임의 재생 길이는 5.033333초다.

[세부 판정·다음 단계](/home/ajou/yigyu/3/stability_adapter_2/WAIST_UPRIGHT_RIGHT_ARM_COMPLETION_V1.md:1) · [초기 탐색 v3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/search_v3/search.json:1) · [실제 초기 자세](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/posture_final_v1.json:1) · [접촉·명령 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/analysis_final_v1/analysis.json:1) · [독립 native 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/review_native_v1.md:1)

source 6후보 중 2개 수락/4개 거절했고, 실제 native 3회는 모두 5초 완료했다(총 3600 physics step / 900 control tick). 원본 v1 prototype, v2 거절과 v3 탐색 기록, 이전 phase, 현재 원시 로그·영상은 모두 보존했다. [변경 파일·줄 번호 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/CHANGED_FILES_v1.md:1)에 새 파일 경로를 모았다.
