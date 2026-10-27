# 왼손 엄지의 과한 접힘 완화

엄지5관절 초기각만 변경하고 손바닥·다른 네손가락·왼팔과전체받침 자세를 유지했습니다. 실제초기 nonthumb pose 및76각이 이전EW 준비값과exact 동일합니다.

| 엄지 관절 | 이전 초기각 (°) | 새 초기각 (°) |
|---|---:|---:|
| LH:thumb1_x | 0.050 | 30.303 |
| LH:thumb1_y | -76.200 | -75.000 |
| LH:thumb1_z | 0.000 | 34.080 |
| LH:thumb2 | 84.826 | 65.000 |
| LH:thumb3 | 81.272 | 0.467 |

## 넥 뒤쪽에서 본 초기 엄지

![왼엄지 완화 초기 모습](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/current_t00_thumb_back.png)

끝관절을 펴고 중간관절의 굽힘을 줄인 준비 후보입니다. 엄지는 넥과 접촉하지 않은 상태이며 자연스러운 정도는 이미지에서 검토해주세요. 현재selected facet-plane gap은초기39.424mm/5초62.576mm로,back24mm 라벨이나최단접촉거리와다릅니다.

## 실제5초 영상

![왼엄지 뒤쪽 확대 — 실제 Isaac Gym](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/thumb_back.mp4)

![전체 자세와 Elbow·Wrist 타현](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/whole_body.mp4)

물리5초/1200step/300control,151frame MP4길이5.033333초입니다. 처음2초정착 후 양방향6줄 타현을 유지했습니다. 왼손·엄지와 오른손 접촉0,기타최대이동11.402871mm/회전3.871588°,최종9.853485mm/3.304837°입니다. StrapOFF/자유기타/root하체고정/selfcollisionON/finitehuman제어는 동일합니다. 무제어평형이나fret체크포인트 연결을 뜻하지 않습니다.

## 상세 자료

- [이전/현재 전면 이미지·초기/2초/5초 뒤쪽 이미지와 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/artifacts_v1/README.md:1)
- [모든3영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_thumb_natural_v1/INDEX_v1.md:1)
- [전체 초기81값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/native_v1/initial_values.json:1)
- [실제config](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/search_v2/back24mm/config.json:1)
- [타현·접촉·기타변화 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/strike_analysis_v1.json:1)
- [초기손바닥/손가락 보존 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/thumb_audit_v1.json:1)
- [설계·입력범위·다음검증](/home/ajou/yigyu/3/stability_adapter_2/LEFT_THUMB_NATURAL_COMPLETION_V1.md:1)
- [변경파일과실제줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_thumb_natural_v1/CHANGED_FILES_v1.md:1)

source4중기하수락2·기각2,모델끝후보는미실행으로보존했고V2선택한조건만native1회실행했습니다. 그림과영상은원native바이트사본이며기존프로젝트/실험/자산은유지했습니다.
