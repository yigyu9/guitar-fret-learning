# 양손 음악 연결 범위 요약

최종 환경에는 **Fret(압현)와 Strike(타현)를 모두 연결**합니다. CPU 입력 검사는 `02_Jazz1-200-B_solo`의 canonical 42개 event를 60 fps에서 확인해 통과했습니다. 이는 입력 데이터의 정합성 검사이며, 새 물리 실행·추론·학습 결과는 아닙니다.

실행 시에는 자유 기타 하나가 있는 단일 native 장면과 공통 음악 clock을 사용하고, 공동 정책 하나가 상체 81개 목표의 단일 제출 소유자가 됩니다. 승인된 타현 crossing 시각에 해당 현의 실제 유효 압현 상태와 요구된 유지/dwell 조건을 함께 평가해야 합니다. 압현과 타현을 별도 성공으로만 평가하지 않습니다.

비교 기준은 **동결된 기존 Fret·Strike checkpoint 쌍의 호환성 비교 경로**입니다. 기존 checkpoint는 각자 ABI를 보존한 읽기 전용 추론 후보로 두며, 두 모델의 목표를 한 제출 경계에서 비교·조정합니다. 이는 양손 압현·타현·안정화를 학습하는 **새 공동 상체81 정책**과 역할이 다릅니다. 기존 가중치·critic·optimizer·정규화 통계를 새 정책에 자동으로 이어 붙이지 않습니다.

현재 기본층 runtime에서 양손 연결은 아직 `false`입니다. 이번 확인에서 checkpoint를 로드하거나 추론하지 않았고, 새 물리 실행과 학습도 없었습니다.

## 근거 파일

- [양손 연결 범위 원문](/home/ajou/yigyu/3/stability_adapter_2/DUAL_MUSIC_CONNECTION_SCOPE_V1.md)
- [CPU canonical 입력 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_connection_scope_v1/cpu_input_check.json)
