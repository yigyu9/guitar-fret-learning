# Near-rear source 후보 산출물

이 단계는 기존 저장 source 결과 두 묶음을 읽어 PNG 두 장을 생성하는 후처리다. 새 물리 trial은 수행하지 않는다. source 검색의 네 후보는 전부 거절됐고 `accepted=0`, `native_initializations=0`, `physics_steps=0`이다. 엄지 후면 접촉·손가락 전면 접촉·손바닥 옆면 접촉 목표는 달성되지 않았다.

## 그림

![catalog의 적격 source centroid Gx/Gy, 후면 patch와 2 mm inset, triangle 303·1462·323](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifacts/rear_facet_catalog_Gxy.png)

368개 catalog 행 중 367개가 적격이며 triangle 786은 적격 집합 밖의 관측 source triangle이다. 가장 가까운 적격점 303/1462의 source 선형 필요 이동은 11.677484672/11.698917250 mm, 과거 최대면 323은 17.136177920 mm였다. 이 값은 물리적/FK 성공을 뜻하지 않는다.

![네 거절 후보의 저장 엄지·손바닥 목표 오차와 source 교차 개수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifacts/near_rear_rejected_candidates.png)

네 행의 엄지 목표 오차는 8.076657061/8.565519264/7.524248157/8.078905497 mm, 손바닥 목표 오차는 3.407506669/3.797805320/1.985672776/3.715975688 mm다. source 교차 수는 2/3/1/3이다. 가장 낮은 엄지 오차인 triangle 1462·0.3 mm 여유 행에서도 middle3–fret4의 source common radius는 0.040322319 mm이고 엄지 patch margin은 −2.969092 mm다. common radius는 물리적 깊이가 아니다. 같은 행의 witness는 후면 patch 방향 dot 0.267591이다.

그림 입력은 [catalog JSON 및 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_catalog_v1/catalog.json), [proposal JSON 및 검색 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/proposal.json)이며 모든 그림은 G 좌표의 원본 source 형상 관찰이다. 실제 cooked geometry나 contact depth·force를 인증하지 않는다. 이번 후보용 native 영상은 없다.

다음 [검지·중지 초기각 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FRONT_FINGER_INITIAL_PLAN.md:1)은 두 손가락8좌표도 ±0.10rad와 native/8월19일/기존목표 차이 한계 안에서 조정한다. 아직 미실행이다. 기존 기타 목표와 나머지 조건은 유지한다. 이 phase의 [독립 최종 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/review.md)은 예정 경로다.

## 재현 및 보존

Producer는 [make_near_rear_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_near_rear_artifacts.py)다. 그림 실행은6.020186초/exit0/native0이며 [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifact_execution.json)과 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifacts/artifact_manifest.json)에 입력11,374개 전후SHA 및 PNG SHA를 기록했다. 두 실제PNG를 원자료와 대조했다. 기존 입력 JSON, helper/source 복사본 및 실행 기록은 수정하지 않는다. 검색9.881798초/exit0/source후보4개이며 새 native/physics0이다. root가 저장 pose에서 전체 humanoid–기타 교차와8거리witness,13개 조건을 재계산했다. 실제 완료 검사는 [source 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/interval_data_verification.json)에 있다.

검색 소스의 사전 독립 검수는 완료했다. 결과·그림 최종 독립 검수 재호출은 에이전트 도구의 `agent thread limit reached` 오류로 보류됐다. root 검증과 독립 검수는 구분하며 [범위 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/review_status.json)에 남겼다. 최종 검수 완료로 주장하지 않는다.

root의 38개 실행·source·이미지·입력·이전자료 보존 검사를 완료했다. [최종 root 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/final_verification.json)은 독립 최종 승인과 구분한다.
