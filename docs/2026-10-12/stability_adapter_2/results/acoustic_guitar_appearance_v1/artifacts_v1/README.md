# Acoustic guitar 외관 표시 비교

## native t0 비교

아래는 기존 realistic 기타와 새 외관 표시 조건의 native raw t0 전신 프레임입니다. 두 이미지는 같은 카메라 설정과 같은 픽셀 크기로 나란히 놓았습니다.

![기존 realistic 기타와 acoustic appearance 기타의 native t0 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/native_t0_appearance_comparison.png)

아래 상세 이미지는 새 `native_v3/initial_guitar_appearance.png`를 바꾸지 않고 한국어 설명띠와 함께 배치한 것입니다. native Isaac Gym 렌더 이미지이며 AI 생성 사진이 아닙니다.

![native_v3 acoustic guitar appearance 상세 렌더](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/native_v3_appearance_detail.png)

외관 단계는 smooth visual shell, procedural wood, painted soundhole·bridge·binding, metal 시각 현·프렛·페그를 사용합니다. soundhole과 bridge는 texture/visual 표현이며 실제 뚫린 구멍이나 충돌 돌출부가 아닙니다. 실제 제품 사진과 완벽히 일치하는 재현이나 속이 빈 목재의 물성을 뜻하지 않습니다.

## 보관 영상

native_v2와 native_v3 모두 각각 5.0초 물리 구간, 1,200 physics step, 300 control step을 완료했습니다. 영상은 각 실행의 기존 전신·손 MP4를 새 보관 폴더에 바이트 그대로 복사했습니다. 네 파일은 원본과 보관본 SHA-256이 일치하고 ffprobe에서 30 fps, 151 frames, 5.033333초입니다. 물리 조건과 외관 시각만 분리한 이력이며, 성공이나 안정화 개선을 주장하지 않습니다.

| 실행 | 전신 | 손 |
|---|---|---|
| native_v2 | [전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/native_v2_whole_body.mp4) | [손 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/native_v2_hands.mp4) |
| native_v3 | [전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/native_v3_whole_body.mp4) | [손 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/native_v3_hands.mp4) |

v3 build 검사는 기존 collision geom 이름·range·물성을 유지하고 추가 geom을 visual-only로 확인했습니다. native_v3의 질량과 COM은 직전 native_realistic_v2와 exact 일치하며, 전체 관성의 native readback은 float32 재표현 차이(최대 약 1.49e−8 kg·m²)를 포함해 허용오차 안에서 일치합니다. 두 native 실행 모두 정책 호출·checkpoint load·music actor가 0이며, 총 질량은 4.6487157 kg입니다. 이는 외관 효과의 인과 안정성 비교나 연주 평가가 아닙니다.

이전 `native_v1` 로더 exit 139 기록은 보존되어 있습니다. native_v2와 native_v3 완료 파일을 사용했으며, 이 산출물을 위해 native/물리 실행을 추가하지 않았습니다. 별도 root verification 산출물은 아직 생성 전이므로 링크하지 않았습니다.

입력·출력·폰트·producer SHA는 [provenance.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/provenance.json)에 있습니다. 영상 복사 SHA 및 ffprobe 결과는 [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/manifest.json)에서 확인할 수 있습니다.
