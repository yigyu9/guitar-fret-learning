# 어쿠스틱 기타 외관 사전 독립 검수

요약 판정: **문제없음 — source 자산과 native 진입 경로의 사전 범위.** 현재 검토에서 확정된 실행 차단 오류는 없습니다. 실제 importer의 시각/충돌 분리·재질·외관 품질은 native 결과로 확인해야 합니다.

## 확인 사항

- [builder:116](/home/ajou/yigyu/3/stability_adapter_2/build_acoustic_appearance_v1.py:116)은 기존 물리 mesh의 rgba만 숨기고 frame/geometry를 보존합니다. source XML을 직접 대조하여 기존 body 이름·frame 및 모든 기존 geom의 물리 속성이 일치함을 확인했습니다. 추가 body shell/넥/헤드스톡/튜너 geom은 모두 contype0/conaffinity0/density0입니다. 사운드홀·로제트·브리지는 앞판 텍스처이며 실제 물리 구멍·브리지 접촉 형상이 아닙니다.
- 실제 OBJ4개의 vertex/UV face 참조 범위를 검사해 유효했습니다. wood MTL·procedural texture·asset 및 이전 자산 입력 SHA가 manifest와 일치합니다. dense body shell은 시각 윤곽용이고 기존 물리 bout를 바꾸는 소스 변경은 아닙니다.
- [runner:40](/home/ajou/yigyu/3/stability_adapter_2/run_acoustic_appearance_trial_v1.py:40)은 새 asset에서 mesh 재질을 허용하고 직전 asset과 native body names/shape ranges/7개 shape 속성을 비교하여 다르면 물리 적분 전에 거절합니다. [색상 callback:55](/home/ajou/yigyu/3/stability_adapter_2/run_acoustic_appearance_trial_v1.py:55)은 guitar actor의 기존 파란 덮어쓰기를 건너뜁니다. 실제 alpha0/UV/MTL 처리 지원을 source 검사만으로 확정하지 않습니다.
- [runner:66](/home/ajou/yigyu/3/stability_adapter_2/run_acoustic_appearance_trial_v1.py:66)은 직전 native mass/COM/전체 관성을 복원하고 요청/readback을 대조합니다. construction window·지속 property guard와 실제 호출 카운터를 유지하고 total mass/route_COM/관측 COM 캐시를 검사합니다. 이전 실험과 같은 초기 q_ref 고정 PD·원본 strap 법칙·5초 진단 경로이며 음악·Actor·학습 연결은 없습니다.
- [계획:15](/home/ajou/yigyu/3/stability_adapter_2/ACOUSTIC_GUITAR_APPEARANCE_PLAN_V1.md:15)은 자연스러운 외관을 성공 기준으로 두고, importer가 분리를 지원하지 않으면 물리 변경을 별도 버전으로 검증하도록 구분합니다. 소비된 builder/asset은 수정하지 않고 실패·불충분한 외관도 보존한 새 버전으로 진행해야 합니다.

## Warning

- [runner:90](/home/ajou/yigyu/3/stability_adapter_2/run_acoustic_appearance_trial_v1.py:90) 및98행의 추가 camera handle에는 음수 실패 검사가 없고,102–103행은 이미지 None/크기 확인 없이 reshape합니다. 향후 새 버전에서는 실패 handle·누락 이미지를 query/reshape 전에 명확히 거절하는 것을 권장합니다. 이는 현재 정상 camera 경로를 차단하는 확정 오류로 판단하지 않습니다.
- collision names/ranges/7props equality와 source 물리 mesh 보존은 유용한 gate이나, 실제 cooking·재질 처리·시각 shell과 collision 차이까지 source만으로 인증할 수 없습니다. 실제 native 시각/충돌 이미지·물성 readback 및 가능하면 직전 trace 비교를 통해 외관 변경과 물리 반응을 분리해야 합니다. 외관 확인을 초기 유지·왼손 비지지·음악 성공으로 확대하지 않습니다.

## 검수 SHA·제한

[source_before_native_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/source_before_native_v1.json:1)의14파일 핀을 현재 SHA와 대조했습니다. builder SHA256은 `c28aa5116f91dbb6f3d9ad2a01c5cf1aefe95049ffa316696fff2adc34cac570`, runner는 `22dc603496530f8ab51312f495169b690d0efa69b92e8efe87839f1aa30c304b`, 새 MJCF는 `e8a846b3236540c175f48560ce437b74c6eb4b4f148459e9eb62b35937354735`입니다.

이 기록은 읽기 전용 source·자산 확인이며 실제 native 실행·렌더 결과의 최종 승인 기록이 아닙니다. 검수자는 이 새 리뷰만 작성했고 기존 파일 수정·추가 물리·추론·학습은 하지 않았습니다.
