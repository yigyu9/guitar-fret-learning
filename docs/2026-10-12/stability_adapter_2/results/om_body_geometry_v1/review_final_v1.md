# OM 바디 형상 최종 독립 검수

판정: **문제없음 — 완료된 형상 구현·두 5초 진단·산출물 범위를 승인한다.** Critical 0건, Warning 1건, Suggestion 0건. 초기 기타 자세 유지 성공은 승인 대상이 아니다. 리뷰어는 지정 파일을 읽고 저장 자료를 재계산했으며 추가 물리·학습·원본 수정은 수행하지 않았다.

확인 범위:

- [생성기 v3](/home/ajou/yigyu/3/stability_adapter_2/build_om_body_geometry_v3.py:92)는 기존 넥·헤드스톡의 시각 전용 geom 3개만 추가하고 contact/density를 0으로 지정한다. v1/v2/v3 바디 OBJ 64개 동일, 39 body frame 및 기존 비바디 물리 geom 보존, 원본 도면의 단위·림·측면 깊이·정규화 및 구면 재구성 가정을 대조했다. 63 조각의 XY 오차는 구간당 101개 표본 검사이며 cooked 3D 형상의 오차 보증이 아니다.
- [runner v2](/home/ajou/yigyu/3/stability_adapter_2/run_om_body_geometry_trial_v2.py:85)는 회색 렌더 표시만 보완한다. 두 실행은 각각 exit0, 1,200 physics/300 control, 금지 API 0, strap force 호출 15,600회다. 실제 총 shape 91개 중 G:body 63개이며 질량·COM/관성 제출 및 readback, 양의 관성, construction setter 1회, 캐시와 source_clear를 확인했다. 각 body 질량은 이전 값, 총 4.648715728kg을 유지한다. 관성 요청/readback 최대 차이 `1.490116119×10⁻⁸ kg·m²`는 지정 허용오차 내 일치이며 exact 일치로 해석하지 않는다.
- [검증 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/verification_v1.json:1)의 입력 SHA 2,136개와 사전 핀 77개를 현재 파일과 대조했다. raw trace 재계산 결과 초기→5초 actor-root 이동 `113.199839mm`, SO3 회전 `4.857745°`; 2~5초 181개 표본의 2초 대비 최대 변화 `0.000887495mm / 0.000157702°`가 보고서와 일치한다. 초기 이탈 뒤 후기 정착이며 초기 자세 유지 성공이 아니다. 오른팔 12채널 초기각과 바디 스트랩 버튼도 변경되므로 외곽 변경 단독 효과를 주장할 수 없다.
- 실제 PNG 5개를 열어 source 메시·깊이 그림과 native 화면을 구분하고, 넥 보완 및 0/2/5초 프레임·캡션을 확인했다. 산출물 provenance의 입력 전후·출력 SHA가 일치하며 native 프레임 1,208개의 핀이 검증 입력에 포함된다. 영상 4개 원본/복사본 SHA는 동일하다. 물리 5초와 151frame/30fps MP4 약 5.033초는 구분되어 있다. 전체 영상 디코딩 검증이나 음악 성능 인증은 수행하지 않았다.
- [최종 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/README.md:42)와 산출물 설명은 초기 유지·연주 미성공, 내부 구조·목재·음향 미구현, 새 COM/I의 비실측성을 명시한다. 최종 문서 36개 절대 링크·줄 번호와 main4 완료 append의 prefix/SHA를 대조했다.
- [봉인 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/seal_phase_v2.py:19)의 입력/이전 inventory·main append chain·산출물 provenance·독립 리뷰 존재 검사와 새 경로 출력 생성을 읽기 전용으로 확인했다. 과거 main_before 보존본의 옛 링크 제외는 보존 SHA 검사를 제거하지 않는다. 봉인 실행 및 최종 inventory 결과는 이 리뷰 작성 뒤 root가 확인할 범위다.

Critical: 없음.

Warning 1건:

- [runner v2:86](/home/ajou/yigyu/3/stability_adapter_2/run_om_body_geometry_trial_v2.py:86): collision 카메라는 음수 handle 검사가 없고 appearance 카메라는 검사한다. 이번 두 실행의 영상은 정상 보존됐으므로 완료 결과를 차단하지 않는다. 후속 버전에서 동일 검사를 추가하면 카메라 생성 실패 원인을 명확히 기록할 수 있다. 소비된 소스는 수정하지 않는다.

Suggestion: 없음.

라이선스는 출처·변경·바디 파생 자산 범위 표시를 검토했다. 제작자 다운로드 안내와 CC FAQ의 후속 동일 라이선스 사용 설명이 [연구 노트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/LICENSE_RESEARCH_NOTES_V1.md:1)에 부합한다. 원본 조건은 계속 적용되고 연구/대학 명칭만으로 NC 충족을 확정하지 않는다. 특정 공개·산학 이용의 적법성 또는 전체 코드의 라이선스를 인증한 것은 아니다. 근거: [제작자 안내](https://www.grellier.fr/fr/telechargements), [CC FAQ](https://creativecommons.org/faq/#if-i-derive-or-adapt-material-offered-under-a-creative-commons-license-which-cc-licenses-can-i-use).

검수 SHA256: verification `d220cf2b58c55f35330365a2f8940c8400e0c8a3a888300828c3c49847e01872`; 생성기 v3 `809f48108d10a03eced77e8140dc4491b4bf76fb8eaee62ec5ff078f625dc8fc`; runner v2 `2fbe54f26343cf6e46676d789273c127d2570933359cce2d449c5b27a0f30d2c`; 봉인 v2 `14ee509e43786182d0c3aced549aa6439dcb1f11dcd504ba6aaad52785b8b25e`.
