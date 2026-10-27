# 손바닥 옆면을 우선한 초기 자세 검색

두 초기 추정값에서 왼팔12·손가락21의 초기각을 검색했다. 두 후보 모두 기존 세 면 지지 기준에는 미달했다. source 검색만으로 실제 접촉·기타 안정성을 인증하지 않는다. 겹침 없는 wide_near17만 별도 실제 진단으로 넘겼다.

| 후보 | 손바닥 대표점 목표 오차 | 엄지 대표점 목표 오차 | 손바닥 유한 패치 source 거리 상한 | 기타와 source 교차 |
|---|---:|---:|---:|---:|
| wide_near17 | 0.541139mm | 13.400149mm | 0.421639mm | 0 |
| support_near17 | 0.011668mm | 4.106283mm | proposal 원자료 참조 | 1 |

후자의 작은 대표점 오차를 채택 근거로 삼지 않았다. 전자의 손바닥 투영은 패치 안이지만 경계 여유2.901478mm로3mm 기준에 미달한다. 엄지 거리·후면 witness 조건 등도 미달했다. 동적 목표의0.3mm는 GX 축 오프셋이며 정확한 법선거리와 같지 않다. optimizer 성공 플래그나 source 간격만으로 지지 성공을 표시하지 않는다.

팔±0.15rad·손가락±0.30rad와 native/Aug19/C02/기존81목표 차이의 교집합을 유지했다. 나머지48 초기값, 기존 절대81 PD목표, 기타 초기 p/q, LA1.1018469719600776m와 gain/solver는 같다. 왼손33은 이번 초기 탐색 범위이며 최종 양쪽 Thorax 이하66 제어권 제한이 아니다. Palm world +Z 반구 조건과 전체 source 교차 하드검사는 유지했다.

분리 soft 항의 빠른 종료는 같은 hull face plane의 부분집합에서 충분한 간격을 확인할 때만 벌점0을 반환한다. 그 외에는 기존 dense 계산을 한다. 실제 source 형상의150쌍·간격 조건에서 값이 같았으며 dense0.589659초/shortcut0.230226초였다. 이 시간은 벌점 평가만의 측정이며 전체 검색 속도의 인과 비교가 아니다. 새 두 후보 검색185.983839초, native/physics0이다.

[검색 계약](/home/ajou/yigyu/3/stability_adapter_2/PALM_PATCH_PRIORITY_EXECUTION.md:1), [후보·초기각 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_initial_v1/proposal.json), [150개 벌점 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_initial_v1/separation_benchmark.json), [12개 재계산 검사·4거리 witness](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_initial_v1/interval_data_verification.json)에 저장했다. Solver false2개도 feasible witness 상한과 support plane 하한을 확인했으며 최적해 인증으로 바꾸지 않았다.

[실제5초 영상·두 그림과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/README.md:1), [변경 파일 실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_initial_v1/CHANGED_FILES.md:1)을 따른다. Root의 수치 재계산·그림 QA를 완료했다. Luna 산출물/독립 검수 도구의 thread limit으로 root가 작성했으며 독립 승인 완료를 주장하지 않는다. 기타 초기복원·지속 세 면 지지·연주 안정화는 미완료다.
