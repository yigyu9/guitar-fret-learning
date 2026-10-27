# 연구에 사용하는 모델

현재 학습은105채널 휴머노이드와OM 바디 기타를 사용한다. Root만 고정하고 하체는 유한 제어한다. 기타는 자유 강체·중력ON·스트랩OFF다.

| 자료 | 내용 |
|---|---|
| [휴머노이드](HUMANOID.md) | 원 자산·관절 구성·제어 범위 |
| [관절표](JOINT_SPECIFICATIONS.md) | 실제105개 순서·가동범위·정책 소유권 |
| [기타](GUITAR.md) | 바디·넥·프렛·현 표식과 물성 |
| [남은 점검](BUILD_PLAN.md) | 자산·접촉·시각화의 후속 검증 |

- [실제 휴머노이드 XML](/home/ajou/yigyu/3/tab2body/assets/smpl_mpl_hands_body.xml)
- [실제 기타 XML](/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml)
- [기준config](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json)
- [원native readback](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/initial_values.json)

자산의XML 선언값과 실제 적용한 구동·접촉·충돌 설정은 구분한다. 시각mesh와충돌 형상, 원점과질량중심을 혼동하지 않는다. 정책 출력39개는 모델 입력105채널과 다르다.
