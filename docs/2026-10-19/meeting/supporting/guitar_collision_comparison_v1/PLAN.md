# 시각 메시와 native 충돌 형상 비교

- [x] 현재 OM v3 자산, 기존 source 검사 및 native collision-camera API 확인
- [x] 별도 정지 장면의 같은 actor/camera에서 visual/collision 색상·깊이·body segmentation 촬영
- [x] 바디 확대·윤곽 겹침 및 공통 바디 픽셀의 카메라 깊이 차이 분석
- [x] 입력 불변·원본 PNG·가시성·표시 범위 검증 후 result에 비교표와 설명 저장

사용자 요청에 한정한 별도 정지 시각화이며 물리시간·학습을 진행하지 않는다. 원래 모델/메시/실험을 수정하지 않는다. native collision 카메라는 충돌 표면을 표시하지만 contact_offset의 외곽 팽창이나 접촉력/solver 깊이를 표시하지 않는다. runtime에서 제외하는 proxy/pluck_range는 full collision camera에 보일 수 있으므로 별도 segmentation으로 구분한다. 깊이 차이는 같은 광선에서 두 바디가 모두 보이는 픽셀에 한정하며 3D Hausdorff 거리로 설명하지 않는다.
