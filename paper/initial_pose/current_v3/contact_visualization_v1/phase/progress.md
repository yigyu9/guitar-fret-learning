# 진행 기록

## 저장 접촉점 그림 v1

- 승인된 `render_v1.py` SHA-256 `8b0c847d3df3162e920ffa64cb5583de65c1a897dac8a8b334780f3e93593147`로 한 번 렌더했다. 별도 물리 실험이나 적분은 실행하지 않았다.
- 그림: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v1/recorded_contacts_29s.png` (900×650). 비교 패널은 source 시각 메시와 투명 source 충돌 형상+양성 접촉 표식이며, 각 패널에 정면·비스듬한 시점이 있다.
- 대상은 free_strike_v14의 29초/physics step 6960이다. 기록 8행 중 양의 raw lambda 7행을 표시했고 lambda=0 후보는 표시하지 않았다. 양의 행에 중복 좌표가 있어 7을 고유 접촉 위치 수로 해석하지 않는다.
- 보고서에는 새 물리 스텝 0, clock 0, 네 패널 각 106 body 변환 readback 통과, 입력 불변이 기록됐다. 118개 input pin을 독립 재검증: 누락 0·변경 0.
- positive raw row 점과 보이는 기타 source triangle 간 최대 unsigned 거리는 분석상 0.075346 mm이다. 이는 full mesh gap이나 PhysX cooked 표면과의 비교를 뜻하지 않는다. raw lambda를 뉴턴으로 해석하지 않는다.
- 산출 보고서: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v1/render_report.json`. 한국어 안내: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/README.md`.

## 저장 접촉점 그림 v2

- root의 좁은 카메라와 번호/leader label 수정 승인을 받은 `render_v2.py` SHA-256 `79a82c2b57bf684f57cbc115dc5e2bcce25d1af8cc2f155514b9525eff38ac69`로 새 `render_v2/`를 생성했다. v1과 README는 보존했다.
- 그림: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/render_v2/recorded_contacts_29s.png` (900×650 RGB). 보고서에는 양의 raw 행 7개, 67개 source collision overlay geom, 4개 패널의 106-body 변환 검사 통과, 물리 스텝 0이 기록됐다.
- 118 input pin을 다시 확인: 누락 0·변경 0. 오른쪽 그림의 점은 X-ray 투영 원자료 특징점이다. 원자료 중복 행 때문에 7개 표식을 고유 물리점으로 세지 않는다.
- 새 설명 문서: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/contact_visualization_v1/README_v2.md`. 29초 양의 raw feature points와 보이는 기타 source triangle의 최대 unsigned 거리 0.0754 mm를 제한된 범위로 기술하며 전체 mesh gap/PhysX cooked 비교를 주장하지 않는다. [MEDIA.md](/home/ajou/yigyu/3/paper/initial_pose/current_v3/MEDIA.md)에 연결했다.
