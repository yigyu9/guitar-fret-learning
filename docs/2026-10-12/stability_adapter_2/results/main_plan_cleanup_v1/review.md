# 메인 계획서 간결화 독립 검수

검수 범위는 사용자 승인에 따른 [현재 PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)의 10개 파트, [원문 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/PLAN_before_cleanup.md:1), 재작성·검증 메타데이터와 결과 문서다. 다른 담당자의 파일은 수정하지 않았으며 코드·설정·물리·학습·기존 검증을 실행하지 않았다.

## 내용과 보존 대조

- 2,250행 원문 SHA-256 `620d11039d486d9510ee6ce96ef06d51488f5eed86133ed5d57cc9977e2ae45b`가 보존본과 정확히 일치한다. 현재 117행·10파트와 SHA-256 `5ce17c195fef7db312d55e5c68238cdb5c36744e5a4c463fae7b37054d3d324d`를 독립 재계산했다. 사용자 명시적 재작성 승인이 기존 main append 규칙보다 우선한다는 기록도 확인했다.
- [목표·현재 상태](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:6)는 도구/CPU 계약/정적 촬영 완료와 새 초기 배치·범위 판정·실제 연주·학습 미완료를 구별한다. 정적 수평 후보나 작은 후기 drift를 지지·연주 성공으로 확대하지 않는다.
- [모델 비교](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:19)의 기존 기타 고정 root·중력 비활성은 [원 Base 자산 설정](/home/ajou/yigyu/3/tab2body/env/base.py:278)과 일치한다. Fret/Strike 30+30과 Thorax 6 연결은 기존 prior 계약과 일치하며 고정 기타 성능을 자유 기타 성능으로 확대하지 않는다.
- [제어권](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:30)은 root/하체 고정, 몸통 9개 목표 유지와 실제 움직임 측정, Thorax 이하 66개 주요 제어, Neck/Head 유지 및 자유 기타를 보존한다. 목표 유지와 몸통의 물리적 완전 고정을 혼동하지 않는다.
- [범위·초기 배치](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:43)는 actor-root 위치 상자와 extrinsic xyz가 만드는 quaternion 회전 집합을 유지한다. 단일 Euler 축 비교의 특이점 문제와 q 동치, Chest 상한 재확인, 새 후보 미채택이 명시되어 있다.
- [자세·스트랩](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:57)은 왼손 위쪽 반구/지역 지지/연주 공간, 모델 한계와 손가락 분포 선호의 구별, 모든 손가락 강제 접촉 배제를 보존한다. 고정 길이 `1.1018469719600776 m`와 타 환경 출처 확인의 미완료를 구별하며 동적 길이 조절을 제외한다.
- [목표 합성·학습 순서](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:74)는 범위 안 초기점 복원 비용 0, 밖 가까운 허용 상태 복귀, 하나의 최종 PD/중복 평활화 방지, prior 연결 검증 후 residual 설계를 보존한다. 초기점 복원 중심의 과거 미실행 설계보다 최신 사용자 계약이 우선한다.
- [체크리스트·기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:96)는 새 후보 물리/연주/보정 작업을 미완료로 두고, 과거 상세 이력과 옛 줄 번호의 보존본 및 삭제 소스의 ZIP 복원 경로를 안내한다. 중요한 현재 설계의 누락은 발견하지 않았다.
- 현재 PLAN의 10개 절대 파일 링크 및 지정 행 존재를 독립 확인했다. 주변 설계 입력 5개의 현재 SHA가 재작성 전 기록과 일치하며 [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/verification.json)의 7개 판정과 정합한다.

요약 판정: 문제없음. Critical/Warning에 해당하는 설계·내용 문제는 발견하지 않았다. 결과 문서의 작성 대기 문구를 실제 review 링크로 정리한 최종 delta와 root 보존 기록은 후속 확인한다.

## 최종 문서·보존 delta

[README.md:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/README.md:7)와 [CHANGED_FILES.md:3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/CHANGED_FILES.md:3)의 작성 대기 표현이 제거되었고 실제 검수 링크로 정리되었다. 최종 README SHA-256 `4f0e24a065c6189454dd92d8bc404cad2e499ed860f9f6adda67b52d3be65c09`, CHANGED_FILES SHA-256 `492b5cf53b3c0667f757812fec7f1a92161690d2c0a45e7e3f372aacbab7b194` 및 파일·행 링크를 독립 확인했다.

[final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/final_verification.json)의 12개 판정과 새 계획·원문·최종 문서 SHA가 앞선 독립 대조와 일치한다. [source_final/PLAN.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/main_plan_cleanup_v1/source_final/PLAN.md:1)는 현재 계획과 바이트 단위로 일치한다. 구현 파일 118개 불변 및 새 물리·학습 0은 root 보존 검사 범위로 기록되어 있으며, 검수자는 기존 실행이나 광범위한 closure를 재실행하지 않았다.

요약 판정: 문제없음. 미해결 Critical/Warning 없음. 현재 10파트 설계·완료/제안 구별과 원문 복원 경로를 유지한 문서 정리로 판정한다.

최종 판정: PASS
