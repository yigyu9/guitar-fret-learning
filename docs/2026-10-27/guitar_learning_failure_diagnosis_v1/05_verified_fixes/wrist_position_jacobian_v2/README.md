# 진단용 손목 위치 미분 보정 v2

고정 기타·팔 안내를 사용하는 짧은 압현 진단의 손목 계산을 교정했다. native Jacobian은 native 관절 속도 기준인데 이전 helper는 계산한 증분을 회전벡터 관절 위치에 직접 더했다. 동일 순간16표본과 독립 FK 미분으로 좌표 차이를 확인하고 별도 검수 PASS 이후 수정했다. 이는 기본 raw J33 정책의 직접 계산 경로가 아니므로 원래 전곡 실패의 확정 원인으로 확대하지 않는다.

수정은 팔4개 full3축의 source 이름/XML/실제 열순서를 검증해 위치 미분 Jacobian으로 변환하는 것이다. `M=Rparent Jleft(Aq) A`, ownbody native angular block `S`, `T=solve(S,M)`, `Jposition=Jnative T`를 쓴다. T는 q-position differential에서 native velocity 좌표로 가는 국소 변환이다. 초기화 직후 stale/비유한 행은 solve 전에 제외한다. 속도와 힘에 사용하는 native Jacobian은 그대로다.

.5도 보정 cap·damping·2초 ramp·3초 음 시작·유한 target 범위/속도·PD·접촉 판정·보상은 유지했다. MCP2축·발IK·엄지 helper·과거 filter 진단은 이번 수정 대상이 아니다. 실제 GPU 비교에서 검지 reference/zero/random은 모두0/4로 남았다. 좌표 수정만으로 압현은 해결되지 않았고 팔 추종 지연이 남아 있다.

- [계획과 체크리스트](PLAN.md)
- [실제 좌표 감사](../jacobian_position_coordinate_audit/analysis/results_v2/RESULTS.md)
- [수정 전519원문 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261027_before_wrist_position_jacobian_v2/manifest.json)
- [구현 및 CPU 검증 기록](implementation_verification.json): 작업자 CPU4모듈38검사 PASS, 실제16표본 float32 독립FK미분과 위치 최대3.83e−7m/rad·각도5.15e−7 차이. 독립 코드검수도 통과했다.
- [실제 환경 재검사 준비](native_precheck/README.md): 새 initial만 사용해 검지 reference/zero/random 각4첫시도. 이전 checkpoint source/contract 검증을 완화하지 않는다.

검지 회귀 결과를 확인한 뒤 다른 손가락과 짧은 학습·전환·자유 기타·원곡67음 평가로 돌아간다. 고정 기타/팔 안내/scripted reference의 성공을 자유 기타 학습 성과로 보고하지 않는다. 원자료·기존 봉인·현재 진단 자료는 정리 대상에서 제외하며 공간 정리는 중단 상태다.

[실제 검지 비교 결과·그래프](analysis/results_v1/RESULTS.md): 종료0/103.875초·새initial73tensor동일·686입력/전scene검증. reference env0 음 구간 손목 오차 중앙25.10mm/8.14도, 목표 패드 거리13.97mm, position/loaded/positive0이다. 2초 뒤 말미 손목오차 최대72.26mm가 남는다. 실제 분석 독립검수와 중지/약지/소지 회귀를 진행하고, 새 gain 탐색 대신 요청각 기준FK와 실제 추종을 분리한다.
