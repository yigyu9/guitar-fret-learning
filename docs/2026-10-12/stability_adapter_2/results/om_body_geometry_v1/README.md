# OM 도면 바디 외곽·두께 구현 결과

사용자 요청대로 Grellier OM 도면의 **바디 윤곽과 외부 두께**를 별도 회색 자산에 반영했다. 내부 구조·목재·텍스처·음향은 만들지 않았다. 사진 속 Gopher Wood의 정확한 제품 모델을 재현한 것은 아니다. 기존 기타 원본·공용 모델·이전 실험과 `stability_adapter/`는 보존했다.

## 형상과 도면 대응

| 항목 | 적용 값 |
| --- | --- |
| 바디 길이 / 최대 폭 | 491.957 / 380.632 mm |
| 넥 접합 쪽 중심선 깊이 | 약 85.000 mm (도면 끝 선 85.0017 mm) |
| 꼬리 쪽 중심선 깊이 | 104.000 mm |
| 최대 국소 중심선 깊이 | 107.198 mm |
| 앞판 / 뒷판 곡률 반경 | 7.620 m / 4.572 m |
| 충돌 형상 | 63개 작은 convex 조각; 실제 G:body shape도 63개 |

평면 외곽은 1:1 DXF의 16 spline에서 추출했다. 측면 앞 ARC 2FCE, 뒤 ARC 2EF2, 끝 LINE 63/64와 횡방향 곡률을 사용했다. 가려진 앞판 부분은 같은 원호를 이어 근사했다. 평면 길이 491.957mm와 측면 길이 491mm의 0.957mm 차이는 측면 조회 축만 정규화하여 연결했다. 이 선택과 구면 표면 구성은 명시적인 3D 복원 가정이다. 바디 전체 bounding-box Z폭 108.476mm는 서로 다른 위치의 극값 차이이며 최대 국소 두께와 다르다.

충돌 조각의 각 구간에서 101개 XY 표본을 검사했고 최대 내·외측 오차는 약 0.494mm였다. 이는 원본 형상의 표본 검사이며 PhysX가 변환한 3D 충돌 형상 전체의 오차나 관통 없음을 보장하지 않는다.

[실제 메시 3방향 소스 그림과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/README_SOURCE_V1.md:1). 이 그림은 Isaac Gym 렌더가 아니다.

## 실제 Isaac Gym 초기 장면

![새 바디와 기존 넥을 함께 표시한 실제 초기 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/native_v2/initial_OM_appearance.png)

바디의 허리·하단 곡선과 외부 두께를 확인할 수 있다. 넥·프렛·현·proxy의 기존 물리 형상과 body 좌표계를 유지했다. 첫 실행 native_v1에서는 넥의 시각 표시가 누락됐다. 이를 보존하고 시각 전용 넥 참조 및 회색 표시만 추가한 native_v2를 실행했다. 두 실행의 기타 actor-root 위치 궤적 차이는 0m였다.

## 5초 실행 결과와 조건

| 관측 | 최종 native_v2 결과 |
| --- | --- |
| 실제 물리 / 제어 step | 1,200 / 300 (5초) |
| 처음→5초 기타 actor-root 위치 / 회전 변화 | 113.200 mm / 4.858° |
| 2~5초: 2초 상태 대비 최대 위치 / 회전 차이 | 0.0008875 mm / 0.0001577° |
| 녹화 | 전신·손 근접 각각 151frame, 30fps, 5.033초 |
| 고정 조건 | root·하체 고정, 기타 자유 |
| 제어 | 초기 q_ref PD 유지, 정책·체크포인트·학습·초기 노이즈 없음 |
| 스트랩 | 기존 rest length 1.101846972m와 수동 힘 법칙 유지; 새 바디 버튼 위치 적용 |

새 형상과 기존 오른쪽 어깨가 정적 source 검사에서 겹쳐 오른팔 12관절 초기각만 최대 0.074425rad(약 4.26°) 보정했다. 손목 이동은 약 7.05mm였다. 기타 초기 p/q, 나머지 관절 목표, root·하체는 유지했다. 선택 자세의 정적 source 검사는 통과했지만 실제 접촉은 별도의 native 기록으로 보존한다. 접촉은 제어 직전 300회 기록했고 raw lambda를 N 단위 접촉력이라고 해석하지 않는다.

처음 약 11.3cm 이동한 뒤 거의 정지한 결과다. **초기 위치 유지 또는 연주 성공을 검증한 것은 아니다.** 다음에는 새 바디에서 허벅지·겨드랑이·왼손 지지 위치를 다시 맞춘 후 초기 이동 감소를 평가한다. 이번 작업에는 학습 재실행을 포함하지 않았다.

총질량은 이전 각 body 질량을 유지해 4.648716kg이다. 새 형상에서 읽은 COM과 관성에 이전/새 질량 비율만 적용했다. 초기화 전 한 번 설정했고 native readback·양의 관성·스트랩/관측 캐시를 검사했다. 이는 실제 중공 목재 기타의 무게·질량 분포를 재현한 값이 아니다.

![최종 실제 전신 영상; 주황선은 현재 스트랩 경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/native_v2/media/whole_body.mp4)

[손 근접 실제 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/native_v2/media/hands.mp4). 주황색 실선/옅은 점선은 실제 스트랩 경로의 보임/가림을 표시하며 천의 두께·처짐·추가 충돌 모델은 아니다. 영상 모음은 `/home/ajou/yigyu/3/docs/2026-10-12/video/om_body_geometry_v1/`에 별도 보관한다.

## 이용 조건과 검증 자료

비상업적 연구라면 제작자의 CC BY-NC-SA 조건에 맞춰 사용할 수 있는 것으로 판단했다. 출처·변경 이력·라이선스를 자산에 기록했다. 연구용이라는 명칭만으로 비상업 조건이 자동 충족되지는 않는다. 도면 기반 바디 파생 형상을 배포할 때 동일 계열 라이선스를 유지한다. 이 조건을 프로젝트 코드·휴머노이드·논문 전체에 자동으로 확대하지 않는다.

- [저작권 검토·원문 링크](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/LICENSE_RESEARCH_NOTES_V1.md:1)
- [최종 바디 자산의 출처·변경 표시](/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/ATTRIBUTION.md:1)
- [구현 계획](/home/ajou/yigyu/3/stability_adapter_2/OM_BODY_GEOMETRY_PLAN_V1.md:1)
- [소스·native 정량 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/verification_v1.json:1)
- [2~5초 전체 구간 측정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/settled_window_v1.json:1)

최종 검수·보존 감사 문서는 독립 검수 후 생성한다. 초기 검수는 `review_preflight_v1.md`, 최종 예정 경로는 `review_final_v1.md`와 `final_verification_v1.json`이다.
