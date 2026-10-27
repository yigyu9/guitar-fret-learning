# OM 바디 외곽 추출 최종 독립 검수

요약 판정: **승인·문제없음 — 2D 도면 외곽 추출과 현재 시각 윤곽 비교 범위.** 미결 Critical은 없습니다. 두께·3D 자산·native 접촉/안정성 검증은 이번 단계에 포함되지 않습니다.

- [공식 도면 페이지](https://www.grellier.fr/fr/telechargements)와 다운로드 경로/제작자·라이선스 링크를 확인했습니다. 보존 DXF는3,770,408바이트이며 [다운로드 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/download.json:1)의 SHA와 일치합니다. 특정 고퍼우드 제품 스캔·정밀 복제라고 설명하지 않습니다.
- 실제 DXF를 ezdxf1.4.4로 읽어 INSUNITS=mm와 선택된16 SPLINE의 handle/type/layer/control points·샘플을 직접 대조했습니다. 전체 도면 배치도에서 이 곡선들이 브레이싱 배치가 있는 위쪽 바디 평면도의 외곽 rim임을 육안 확인했습니다. 다른 완성 정면 뷰·옆판 템플릿·내부 bracing 선을 선택한 결과가 아닙니다.
- [추출:38](/home/ajou/yigyu/3/stability_adapter_2/extract_om_body_outline_v2.py:38)의0.02mm flattening,구간 역순/연결,mm→m와 bounding 중심 변환을 원DXF에서 재계산했습니다. 최대 연결 오차1.4211×10⁻¹⁴mm,원본 꼬리 틈0.0169340000001mm이며 첫 점을 덧붙여 이 틈만 닫았습니다. 샘플 좌우 점집합 대칭 오차는4.94×10⁻¹⁶m,엄격 선분 교차는0입니다.
- 도면 샘플 길이49.195743cm·폭38.063205cm와 현재 visual_body.obj의 실제 앞판 정점 길이48.789606cm·폭37.303454cm를 재계산했습니다. 현재 앞판 bounding 중심은0이며 서로 같은 cm 축척·bounding 중심 정렬입니다. 도면을 임의 humanoid 비율로 재확대하지 않았습니다.
- PNG2개를 실제로 열어 곡선·범례·단위·설명을 대조했습니다. v2는 범례를 축 밖에 두어 외곽을 가리지 않습니다. 소스 diff는 그림 배치/새 출력 경로 변경이며 v1/v2의 추출점·source entities는 exact 같습니다. 두 JSON의 전체 입력 SHA와 PNG 출력 SHA,문서 링크/텍스트 실제 줄,main4 append의 원문 prefix·전후 SHA를 확인했습니다.

## 범위와 Warning

[결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/README.md:3)대로 기존 시뮬레이션 자산·초기 자세·물성·제어는 변경하지 않았고 native 실행은0입니다. 색/재질·내부 구조·외부 두께·앞뒤판 곡률은 확정하지 않았습니다. 비교 그림은 CAD 후처리이며 Isaac Gym 렌더가 아닙니다. 제작자 출처·공개 라이선스 링크와 원본 표제의 기록을 보존했습니다.

[좌표 변환:51](/home/ajou/yigyu/3/stability_adapter_2/extract_om_body_outline_v2.py:51)은 CAD X/Y를 교환하므로2D 변환의 determinant가−1이고 winding이 뒤집힙니다. 현재 대칭 외곽 비교에는 문제가 없지만 후속3D mesh 생성에서는 중복 연결점 제거와 winding/normal 방향을 명시적으로 정규화해야 합니다. 엄격 선분 교차0을 모든 endpoint 접촉·퇴화에 대한 일반적 mesh 유효성 인증으로 확대하지 않습니다.

[봉인 구현](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/seal_phase_v1.py:27)을 읽기 전용으로 검토했고 중요한 범위 누락은 없습니다. 이전 phase 전체 보존·최종 source_final/inventory/verification 실행은 root의 후속 봉인 대상입니다.

DXF SHA256: `472006119c3b13ae091e8a57894cb458541cc1a0a714e9059bbf6d8c83f03932`. 권위 outline_v2 SHA256: `581c093642a24b2ee521cb88b4c10b02af5a365a9ba9ebe17a51339c540d9e7b`. 검수자는 이 새 리뷰만 작성했으며 기존 파일 수정·추가 native/물리/학습은 하지 않았습니다.
