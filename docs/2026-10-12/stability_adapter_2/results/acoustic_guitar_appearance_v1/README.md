# 사진을 참고한 어쿠스틱 기타 외관 개선 완료

사용자 사진에서 밝은 목재 앞판, 짙은 측판과 지판, 잘록한 바디 곡선, 사운드홀/로제트·브리지·바인딩 및 금속 현·프렛·튜닝 페그를 참고해 별도 시각 모델을 만들었다. 치수는 직전 휴머노이드 기준 콘서트형 모델(바디48.8×37.3cm, 깊이8.8–10.8cm, 전체100.2cm)을 유지한다. 제품 로고나 사진을 텍스처로 복사하지 않았으며 정밀 제품 스캔/복제가 아니다.

![실제 Isaac Gym 외관 상세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/native_v3/initial_guitar_appearance.png)

위 이미지는 새 시각 모델을 읽은 실제 Isaac Gym 초기 장면이다. AI 생성 사진이나 MuJoCo 렌더가 아니다. 몸체의 촘촘한 PCHIP 곡선 시각 메시와 OBJ UV를 만들고 procedural 목재 텍스처를 적용했다. 사운드홀/로제트·브리지·바인딩은 앞판의 텍스처 표현이며 실제 구멍이나 돌출 접촉부가 아니다. 현과 프렛·페그는 별도 시각용 금속 메시다. source 현/프렛 좌표는 유지했다. 이 단계는 실물 중공 목재 구조·실측 질감/무게/재료를 재현한 결과가 아니다.

## 물리와 외관의 구분

원래 물리 geom의 크기·mesh·변환·관절 및39개 body 이름/순서/원점은 유지하고 기존 mesh의 시각 alpha만 바꿨다. 추가 시각 geom은 contype0/conaffinity0/density0이다. source build의4검사는 원본 물리 속성/좌표와 추가 시각 geom, 입력 보존을 확인한다. 별도로 native importer API에서 직전 모델과30개 collision shape, body별 range, filter/friction/restitution/rolling/torsion/contact/rest offset를 exact 대조했다. 단순 충돌 카메라 이미지만으로 비충돌 여부를 판정하지 않았다.

직전 native의 per-body 질량·COM·전체 관성을 초기 construction window에서 제출했다. readback에서 질량과 COM은 exact, 관성은 float32 재표현으로 최대1.4901161e-8kg·m² 차이를 보였으며 atol1e-12/rtol5e-7 안에서 일치했다. 총질량은4.6487157kg이다. cache/guard도 통과했다. 실행 중 body-property 변경·기타 고정·강제 손부착·지속 pose 덮어쓰기는 없다. 시각 곡면은 기존 근사 충돌 형상과 완전히 같은 외곽은 아니므로 이 외관을 정밀 접촉 모델로 해석하지 않는다.

## 실제 실행 결과

시각 바디만 적용한native_v2와 현/프렛/페그를 보완한native_v3는 모두5초·1200physics step·300control을 완료했다. 직전 모델의 초기 배치·관절 목표·PD·고정root/하체·스트랩 길이/버튼/법칙을 유지했고 체크포인트·음악·학습·노이즈·새 보정 제어는0이다. 두 시험 모두 초기값, 실제 전신/손151frame·30fps 영상과 실제 strap route를 저장했다. MP4 길이는t0 포함5.033333초다.

두 실행의 기타 궤적 수치는 동일했으며 초기→5초 actor-root 이동13.1853cm, 회전10.0002°였다. 직전native_realistic_v2 대비 전체301표본의 최대 차이는 위치1.5702mm/회전1.1242°다. 관성 readback 미세 차이 등을 포함하므로 이전 궤적이 bitwise 같다고 주장하지 않으며 외관 개선을 안정화 개선으로 주장하지 않는다. 기타 안정성/왼손 없는 유지/연주 성능을 추가 검증한 단계도 아니다.

![최종 외관 실제5초 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/native_v3_whole_body.mp4)

## 보존한 실패와 보완

첫v1은 MJCF loader가 절대 mesh filename을 asset directory 뒤에 이어 붙여 로딩 오류/exit139로 중단했다. v1 소스/asset/attempt/로그를 보존하고 v2에서 상대경로로만 고쳤다. v3는 금속 시각 현/프렛/페그를 추가했다. runner는v1 소비본을 수정하지 않고 재사용했다. 첫 분석의 관성 JSON== 조건은 native float32 재표현 차이로 실패해 verification_v1.json을 생성하지 않았다. 소비 분석을 보존하고v2에서 질량/COM의exact와 관성의수치 허용오차를 구분했다. 이 후처리 보완의 물리 재실행은0이다. 기존 일부 humanoid visual-geom 경고는 로그에 보존했고 새 기타의 실제 이미지/정상완료와 구분한다.

- [최종 private MJCF](/home/ajou/yigyu/3/stability_adapter_2/assets/acoustic_appearance_v3/guitar_asset.xml:1)
- [source build/입력·자산 manifest](/home/ajou/yigyu/3/stability_adapter_2/assets/acoustic_appearance_v3/manifest.json:1)
- [25개 native·source·영상 검증과 측정치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/verification_v2.json:1)
- [기존/새 외관 비교 그림·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/README.md:1)
- [초기81관절·PD·기타 상태·물성·스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/native_v3/initial_values.json:1)
- [동영상 보관 안내](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/README.md:1)
