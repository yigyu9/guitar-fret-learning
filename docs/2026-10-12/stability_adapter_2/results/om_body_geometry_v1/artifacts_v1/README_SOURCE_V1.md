# OM body geometry source 단계 그림

이 source 단계에서는 실제 `body_visual.obj` 외관 메시를 세 각도에서 그렸고, `depth_v1.json`에 기록된 local depth 샘플을 DXF 단위로 표시했습니다. source 3D 그림은 OBJ 정점을 그대로 사용한 메시 그림이며 Isaac Gym native 장면도, PhysX cooked 충돌 인증도 아닙니다.

![실제 OM source visual mesh 정면·측면·사선 세 뷰](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/source_mesh_three_views.png)

![depth_v1 local thickness sample 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/local_depth_samples.png)

`depth_v1.json`은 DXF millimetres 값을 사용합니다. tail 104 mm, neck 약 85 mm, centerline 최대 depth 107.19786 mm입니다. side axis는 491.0 mm(49.10 cm)이며 평면 축 491.957431 mm(49.1957 cm)와 0.957431 mm 차이를 축 정규화로 맞췄습니다. 그림의 표본은 JSON에 있는 점 그대로이며 사이 값을 새로 계산하거나 선형 보간하지 않았습니다. 축의 보조 눈금만 같은 위치/깊이의 cm 단위 환산입니다.

geometry build는 49.1957×38.0632 cm 평면 rim을 사용하고 body frame 및 marker를 보존합니다. 63개의 convex collision pieces와 샘플 XY bounds 편차 0.5 mm 미만은 build 검사 결과이며 PhysX cooked shape 검증이 아닙니다. source 단계라 native 실행 결과, 음악·학습 성능은 포함하지 않습니다. native 영상 단계가 별도로 확인되면 최종 안내를 추가할 예정입니다.

source attribution: Acoustic guitar — Orchestra Model (OM), Christophe Grellier, 2007/2008. [원본 출처 페이지](https://www.grellier.fr/fr/telechargements), [원본 DXF](https://www.grellier.fr/static/data/plans/OM_acoustic_guitar/OM_acoustic_guitar.dxf). 이 파생 body mesh는 CC BY-NC-SA 3.0 Unported 조건으로 표시합니다. 이 attribution은 body derivative에 한하며 기존 neck·fret·string·코드/프로젝트 전체 라이선스를 바꾸지 않습니다. 상용 이용은 원저작자 조건을 별도로 확인해야 합니다. 상세 출처는 [ATTRIBUTION.md](/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v2/ATTRIBUTION.md)에 있습니다.

입력·출력 해시, 폰트 및 producer는 [source provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/source_provenance_v1.json)에 기록되어 있습니다.
