# 기타 오브젝트2 — 바디 중심 root

2026-10-09 별도 대화에서 생성한 독립 자산이다.

- [새 기타 MJCF](/home/ajou/yigyu/3/stability_adapter_2/assets/guitar_asset_body_root_v2.xml:18)
- [원점 변환 메타데이터](/home/ajou/yigyu/3/stability_adapter_2/assets/guitar_asset_body_root_v2.json:1)
- [생성 코드](/home/ajou/yigyu/3/stability_adapter_2/build_guitar_body_root_v2.py:17)

새 root는 `G:body` 박스의 기하학적 중심이다. 기타 전체의 질량중심과는 별개다.
축 방향은 원본과 같으며 local +Y는 넥 방향, +Z는 앞판 법선 방향이다.
root의 위치는 바디 중심 위치이고 root 주위 회전은 바디 중심 주위 회전이다.
원본의 body 이름·형상·재질·마찰·자식 내부 좌표를 유지한다. 메시 원본도 공유한다.

기존 자세와 같은 world 배치로 불러오려면 다음 변환을 사용한다.

```text
c = [0, -0.4, -0.0217] m
p_new = p_old + R(q_old) * c
q_new = q_old
root_local_point_new = root_local_point_old - c
```

예를 들어 기존 root 기준 스트랩 앵커 두 점은 새 root 기준에서
`[-0.1557, 0.1757, 0]m`, `[0, -0.178, 0]m`가 된다.
기존 root 기준 관측·목표·스트랩 앵커를 새 모델과 연결할 때도 위 변환이 필요하다.
현재 환경 설정과 기본 모델 선택은 변경하지 않았다. 이 자산을 별도로 선택해 사용한다.

검증: [최종 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_body_root_v2_side_native_v3/verification.json:1)의12개 검사 모두 통과.
CPU Isaac Gym 로드에서39개 body 이름, 바디 중심/root 일치, 동일 world 자식 자세,
질량·관성 및 root COM 좌표 변환을 확인했다. 자식 위치 최대 차이는9.54e-8m다.
물리 적분은0회이며 자유 기타 동역학과 렌더 이미지는 검증하지 않았다.
양 모델에서 SDK의 CUDA 장치/visual geom 경고가 있었으나 CPU 로드·좌표 검사는 완료됐다.
검사 코드의 SDK COM 필드 처리 실패2회는 각각 별도 소스·로그로 보존했다.

메인 대화의 코드·모델·계획·실험은 수정하지 않았으며 이 별도 자산과 검증만 추가했다.
