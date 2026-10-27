# OM 제작 도면의 바디 외곽 추출

사용자 최신 요청에 따라 바디 외곽만 다룬다. 색/텍스처는 후속 Blender 작업에 맡기며 이번에는 내부 구조를 모델링하지 않는다. 앞서 추천한 Grellier OM 도면을 첫 기준으로 사용했다. 현재 시뮬레이션 자산/초기자세/물성/스트랩/제어는 변경하지 않았다.

![같은 축척의 바디 외곽 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/body_outline_comparison_v2.png)

검은 실선은 도면의 바디 외곽이며 회색 점선은 현재 acoustic_appearance_v3의 시각 바디 외곽이다. 바디 XY bounding-box 중심을 맞추고 같은 cm 축척으로 표시했다. DXF의 넥 방향 +X를 비교 그림 +Y로 바꾸었다. 바디 길이는 도면49.1957cm/현재48.7896cm, 최대 폭은 도면38.0632cm/현재37.3035cm다. 도면의 상부 볼록부와 허리 위치·곡률은 현재 임의 profile과 다르다. 후속 모델은 도면의 윤곽점을 직접 사용하며 색/재질은 추가하지 않는다.

도면의 위쪽 바디 평면도(브레이싱 배치가 함께 그려진 뷰)에서 외곽 rim의16개 SPLINE만 선택했다. 내부 선/사운드홀/부품/다른 정면 뷰/옆판 템플릿은 추출에 사용하지 않았다. DXF INSUNITS=4(mm), 전체 도면 축척 표기는1/1이다. 곡선을0.02mm flattening 거리로 샘플링했고 구간 연결 오차는 부동소수점 수준이다. 꼬리 이음의0.016934mm 원본 틈은 첫 점을 추가해 닫았다. 추출점과 control points·knots·정확한 source handle 순서는 outline_v2.json에 보존했다. 이는 제작자 OM 설계 도면이며 특정 고퍼우드 모델의 정밀 스캔/복제가 아니다.

v1에서는 범례가 꼬리 곡선을 가릴 수 있어 소비된 소스/JSON/그림을 보존하고 v2에서 범례만 축 밖으로 옮겼다. 두 버전의 추출점은 exact 일치한다. 비교 그림은 source CAD 기반 후처리이며 실제 Isaac Gym/PhysX 렌더·접촉·안정화 검증이 아니다. 이번 native 실행은0회다. 외부 두께와 앞/뒤판 곡률은 이 소단계에서 아직 추출/확정하지 않았으며 후속 무채색 바디와 접촉 형상 단계에서 별도 확인한다.

- [제작자 공식 도면 페이지](https://www.grellier.fr/fr/telechargements)
- [보존한 원본 DXF](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/OM_acoustic_guitar.dxf)
- [다운로드 출처·원본 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/download.json:1)
- [추출 윤곽·치수·입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1/outline_v2.json:1)
- [다음 단계까지의 계획](/home/ajou/yigyu/3/stability_adapter_2/OM_BODY_OUTLINE_PLAN_V1.md:1)

제작자: Christophe Grellier. 공개 페이지의 라이선스 링크는 CC BY-NC-SA2.0이며 DXF의 언어별 표제에도2.0/3.0 링크가 있다. 원본 출처와 표제는 그대로 보존한다.
