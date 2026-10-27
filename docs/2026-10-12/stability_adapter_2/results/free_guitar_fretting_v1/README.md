# 자유 기타 학습 환경 2단계 — 압현 접촉 후보 측정

기존 Fret의 목표 줄·프렛, 유지 시간이라는 구분을 참고해 자유 기타 환경에 **실제 손가락–기타 접촉과 현재 기타 좌표를 함께 사용하는 단일 목표 측정**을 연결했다. 넥을 잡았다는 사실과 목표 줄을 누를 수 있는 위치에 접촉했다는 사실을 구분한다. 실제 현 압력·진동·음향, 학습된 압현이나 곡 연주를 검증한 결과는 아니다.

## 구현과 유지 조건

- [코드 안내](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/README_v2.md): 측정기, 환경 연결부, 실행기와 검사 위치.
- [측정기](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/fretting_v1.py): 지정 손가락의 실제 양성 접촉, 양측 접촉점 일치, 현재 기타 좌표에서 목표 현·프렛 구간을 확인한다. 다른 손가락이나 다른 현의 접촉은 제외한다.
- [환경 연결](/home/ajou/yigyu/3/stability_adapter_2/free_guitar_learning_v1/fretting_environment_v1.py): 준비 22초 후 실제 상태와 접촉을 240Hz로 함께 읽고 연속 유지 시간과 목표 접촉 소실을 기록한다. 접촉 조회가 실제 상태를 바꾸지 않았는지도 검사한다.

Root 고정, 하체 유한 제어, 전체 105채널·비영범위 97축·원래 영범위 8축, 기타 자유 강체·중력 ON·스트랩 OFF 조건을 유지했다. 이전 고정 기타 환경의 중력 해제나 매 단계 기타 상태 주입을 가져오지 않았다. 이번 시험은 39개 정책 행동 입력에 모두 0을 주었다. 정책 행동 0은 유지 제어의 힘 0이라는 뜻이 아니다.

진단 목표는 **물리 현 1번(high-E), 5프렛, 검지**다. 현재 준비 자세에 이미 존재하는 검지 접촉을 확인해 선택했으므로, 곡이 독립적으로 요구한 목표에 도달한 성과로 해석하지 않는다. 기존 Fret의 0=DONT_CARE 표현과 달리 새 목표의 fret 0은 개방현이다.

계약은 분석·실행 전에 고정했다. 현 옆 거리 3mm, 높이 차 3mm, 프렛 구간 여유 2mm, 양측 접촉점 차 0.1mm, 접근 진단 거리 15mm다. 접근 거리는 손가락 강체 원점 기준이며 보정된 손끝 패드가 아니다. 원 접촉 lambda의 양성 여부를 사용하며 뉴턴 단위 현 압력으로 환산하지 않는다. 이 기준들은 시작용 진단 계약이며 실제 연주 정확도를 보정한 문턱값은 아니다.

## 검증 결과

측정기 9개와 연결부 3개, 합계 **CPU 검사 12개 통과**. 누락 표본, 중복·역순, 짧은 음, 목표 변경, 다른 현 접촉 및 환경 초기화 등을 확인했다. 고정 50ms의 접촉 획득 진단과 실제 노트 구간의 접촉 유지율은 분리했다. 50ms보다 짧은 음도 관측한 실제 구간으로 유지율을 계산한다.

| 자료 | 평가 구간 | 목표 접촉 후보 / 표본 | 의미 |
| --- | --- | ---: | --- |
| 기존 free_strike_v14 기록 | 준비 유지 17–22초 | 1,201 / 1,201 | 선택한 진단 목표 접촉 유지 |
| 같은 기록 | 왼손 완전 해제 25–40초 | 0 / 3,601 | 목표 후보 없음 |
| 기존 regrasp_v14 기록 | 준비 복귀 후 44–49초 | 0 / 1,201 | 넥 접촉은 있어도 선택 목표와 불일치 |
| 새 native_probe_v1 | 준비 후 22–23초 | 241 / 241 | 새 환경의 실제 접촉·시간 측정 연결 확인 |

기존 기록은 [읽기 전용 재분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/replay_v1/result.json)이며 과거 물리 실험을 다시 실행하지 않았다. 목표 후보는 약 22.304초에 소실됐다. 당시 다른 왼손 접촉은 남아 있었으므로 이를 왼손 전체 해제 시점으로 부르지 않는다.

재접촉 시험의 원래 44–49초 손가락–넥 접촉률 100%와 이번 목표 후보 0%는 서로 다른 지표다. 검사한 44초·49초 검지 접촉점은 물리 현 4번에 더 가까웠고, 목표 현 1번까지 옆 거리는 약 20.089mm·19.873mm였다. 준비 자세로 돌아와 넥을 잡는 것만으로 지정한 줄의 압현 성공이 되지 않는다는 한계를 드러낸다. 이를 통과시키려고 목표나 문턱값을 바꾸지 않았다.

새 실제 시험은 **준비 22초 + 행동 0 유지 1초**, 총 물리 시간 23초다. 241개 연속 표본에서 목표 후보 유지율 1.0, 연속 관측 유지 시간 1.0초였다. 준비 완료 상태 대비 기타 원점의 최대 이동은 0.004004mm, 회전은 0.000481°였다. 이는 이 짧은 유지 구간의 변화량이며 장기 안정성·새 압현 동작의 성능 지표가 아니다.

[실행 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/report.json)는 정상 종료, 사전 입력 1,510개 불변, 실제 import 소스 누락 0개와 원본 소스 대조 오류 0개를 기록한다. [원자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_analysis_v1/result.json)에 표본 정렬·접촉 조회 전후 상태 불변·영상 해시 검사를 남겼다. 새 PPO 업데이트는 0이다.

## 원자료와 영상

- [초기 전체 값·모델·제어 설정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/initial_values.json)
- [준비 완료 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/prepared.json) · [최종 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/final.json)
- [240Hz 상태·접촉·판정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/measurements240.json.gz)
- [영상 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/media/videos.json): 원 native 카메라 각 116프레임, 5fps. 물리 시간 23초에 시작·끝 표본이 포함되어 파일 길이는 23.2초다. `hands` 카메라는 측면 보조 시점이며 손가락 확대 영상이 아니다.

![실제 준비와 1초 유지: 정면 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/media/whole_body.mp4)

![실제 준비와 1초 유지: 측면 보조 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/media/hands.mp4)

## 남은 연결

다음 단위는 움직이는 기타 기준으로 피크의 240Hz 통과, 방향·재무장·목표 시각 매칭을 처리하는 Strike 측정이다. 이후 여러 음의 목표 변환, 관측 벡터, 음악 보상과 안정성 비용, PPO 수집을 연결한다. 재접촉 후 목표 줄로 이동하는 제어와 하체 16축을 포함한 55행동 정책 연결도 아직 완료하지 않았다.

현재의 `measured_contact_release`는 같은 목표 후보의 소실만 뜻한다. 음악적으로 의도한 최종 해제, 왼손 전체 무접촉, 손가락의 실제 현 압력은 별도 판단이 필요하다. 기존 초기 자세 V3의 미완료 검증과 단계1의 과거 보고 오류도 그대로 보존했다.
