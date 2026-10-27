# 어쿠스틱 기타 외관 최종 독립 검수

요약 판정: **승인·문제없음 — 완료된 외관 구현과 native_v2/v3의5초 진단 범위.** 미결 Critical은 없습니다. 외관 개선을 안정화·왼손 없는 유지·음악 성능 개선으로 인증하지 않습니다.

## 원자료 확인

[권위 검증25개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/verification_v2.json:1)의 입력 SHA와 실제 report/초기값/물성/궤적을 대조했습니다. 두 실행은 각각1200물리 step/300제어/301상태·151프레임을 완료했고,q_ref·PD·초기 strap 정보가 직전 기준과 같습니다. 정책·체크포인트·음악 호출과 금지 API는0,property setter는 construction1회·거절0이며 캐시 검사는 통과했습니다.

native의39개 body 이름·30개 collision shape·body별 range·7개 shape 속성은 직전 asset과 exact 같습니다. source에서는 기존 물리 geom/frame을 rgba 외 보존하고 추가 시각 geom의 비충돌·무질량을 따로 확인했습니다. **질량·COM은 exact,관성은 수치 허용오차 내 일치**이며 전체 물성 JSON의 bitwise equality를 주장하지 않습니다. 실제 관성 최대 차이는1.490116119×10⁻⁸kg·m²,허용은atol1e-12/rtol5e-7입니다. 총질량4.6487157kg 통제는 실물 목재 질량 분포 인증과 다릅니다.

기타 위치/quaternion을 직접 재계산한 결과 native_v2/v3의301표본은 서로 같습니다. 초기→5초 이동0.131853411m·SO(3)10.00016054°,직전 기준 대비 최대 궤적 차이는1.5701567mm·1.12424759°입니다. 따라서 이전 물리 궤적까지 bitwise 같거나 외관으로 안정성이 개선됐다고 설명할 수 없습니다. 이 차이의 원인을 관성 반올림 하나로 확정하지 않습니다.

## 실제 외관·문서·보존

[비교·상세 PNG2개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/README.md:5)를 실제로 열어 native 원이미지와 대조했습니다. 목재 앞판/짙은 측판·지판,둥근 시각 윤곽,사운드홀·브리지·바인딩 표현 및 금속 현·프렛·페그가 보입니다. 상세 이미지는 Isaac Gym 렌더이며 생성 사진이 아닙니다. 사운드홀·브리지는2D 텍스처이며,매끄러운 시각 shell은 기존 근사 충돌 외곽과 완전히 같지 않습니다. 사진의 정밀 제품 복제·실측 질감·중공 목재 물성 재현은 아닙니다.

[provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/provenance.json:1)의30입력 전후/6출력/producer SHA와 [영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/acoustic_guitar_appearance_v1/manifest.json:1)의4개 원본·보관 SHA가 일치합니다.151프레임/30fps/MP4 5.033333초는 t0를 포함하며 물리5초와 구분했습니다. [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/CHANGED_FILES_V1.md:1)의 링크·텍스트 실제 줄과 main4 완료 append의 원문 prefix·전후 SHA도 확인했습니다.

native_v1 절대 mesh 경로 로딩 오류/exit139 및 관성 JSON== 실패 분석은 보존됐습니다. 실패한 verification_v1을 새로 만들어 성공으로 소급하지 않았으며,상대경로 v2 및 금속 시각 요소 v3와 구분했습니다. 소비 builder/asset/runner와 사전 리뷰는 수정하지 않았습니다.

[봉인 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/seal_phase_v1.py:34)를 읽기 전용으로 검토했고 중요한 감사 범위 누락은 없습니다. 이전1343개 전체 보존/이전 seal manifest·두 main append chain·최종 source_final/inventory/verification의 실제 실행은 root 후속 봉인 범위입니다.

## Warning·Suggestion

- [산출물 설명:24](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/README.md:24)의 build와 range/물성 문구는 source/native 단계를 합친 요약입니다. [root 설명:11](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/README.md:11)처럼 source4검사와 실제 native API equality를 분리해 읽어야 합니다. 원본 문서를 보존합니다.
- 접촉60Hz query/raw λ는 전체240Hz substep 또는 뉴턴 지지력 인증이 아닙니다. 기존 추가 camera 실패 경계 처리 Warning은 이번 정상 실행으로 모두 해소됐다고 볼 수 없습니다.
- [산출물 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/artifacts_v1/CHANGED_FILES.md:8)의 PNG `:1`은 바이너리에 실제 줄 개념이 없으므로 향후 색인에서는 생략하는 것을 권장합니다. 파일 존재·이미지 확인에는 영향이 없습니다.

검증 SHA256: `dc180d6ecb27d83fd71abc0601866d2dad25ea506a3b687d2c0d260938f017bd`. 검수자는 이 새 리뷰만 작성했고 추가 native·물리·추론·학습과 기존 파일 수정은 하지 않았습니다.
