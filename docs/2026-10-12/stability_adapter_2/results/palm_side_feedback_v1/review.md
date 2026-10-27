# 파란 neck 측면 palm 추적 독립 검수

검수일: 2026-10-07. 소유 범위는 이 새 검수 기록뿐이다.
이번 controller·교정·runner·분석기·그림과 최종 문서를 읽기 검토했다.
검수자는 추가 native 실행, source query, 물리 재생 또는 다른 파일 편집을 하지 않았다.

## 요약 판정

**문제없음.** 미해결 Critical / Warning / Suggestion 없음. 손바닥 지속 지지와 기타 안정화 성공은 아니다.

## 독립 확인

- 기타-frame의 live 목표점, 50 µm 간격, 초기 palm/guitar 상대 회전과 world tangent 오차를 확인했다. 저장 pose에서 세 조건의 모든 task를 재계산한 최대 차이는 1.11e−16 m-scaled-rad다. 주황 추적점은 source facet의 선택점이며 native 접촉점이나 cooked 표면점이 아니다.
- 초기 FK 6×12와 첫-step PD 응답 6×12 행렬을 저장 columns에서 재계산해 차이 0을 확인했다. FK held-out 진단과 startup bias 실제 응답은 별개의 계측이며 장기 구동 모델이 아니다.
- Tracking의 6회 업데이트를 독립 재계산했다. KP2/KI4/s, damping 0.01 m/rad, 회전 scale 0.08 m/rad, residual ±0.15 rad·1 rad/s와 최종 C02/native/초기±0.15 box 및 축별 적분 rollback이 일치한다. float32 제출 목표 최대 차이는 4.31872e−8 rad로 2e−7 rad 허용치 안이다.
- 세 조건의 25 states/trace/tasks, 24 controls/contacts, 240 Hz 시간과 step 1/5/9/13/17/21 업데이트를 확인했다. 보완한 raw guard는 실제 자료를 수용하고 상태 1개 누락·잘못된 업데이트·NaN task를 거절했다(AST 순수 검사, 디스크 fixture 없음).
- OFF의 이전 states/trace/contacts 재현과 bias의 검증 첫-step 일치 계약을 확인했다. 실제 기타 전체 body states·p/q·오차곡선은 세 조건에서 같다. 전체 trace는 route point/velocity, strap 길이, torso drift가 다르다. 나머지 목표·PD·고정 root/lower·자유 기타·절대 LA 보존 계약을 구별했다.
- 추적점 최대 오차는 OFF 71.909699, bias 49.465670, tracking 48.323668 mm다. 기타 최대 오차는 모두 5.107730 mm / 0.969008°다. 첫 step의 palm 접촉 4행은 raw λ=0이며 step 2–24에는 없다. 힘 단위·하중·지지력으로 환산하지 않는다.
- 기록 집계는 FK 14 init/0 step, 응답 14 init/14 step, 짧은 3조건 3 init/72 step, camera 1 init/24 step으로 합계 32 init/110 step이다. 분석 14개 계약과 보존 검사 기록을 확인했다. 새 preflight_v2는 89개 실제 입력 SHA가 일치하며 0 init/0 step이다.
- Calibration provenance의 전체 입력 key/SHA와 역사 helper 사본을 대조했다. 역사 helper의 비-class AST는 현재와 같고 현재에는 SideFeedback만 추가됐다. 원래 native camera runner의 복원 사본도 당시 producer SHA와 같다. 기존 production의 columns SHA 누락을 사후 검사로 소급 인증하지 않는다.
- 두 최종 PNG를 직접 확인했다. 그림 입력 31개·producer·출력 2개의 실제 SHA가 manifest와 같다. Camera 3×2 패널은 각 이미지와 같은 시점의 저장 pose/target을 사용하며, source-derived 표시와 원본 native 이미지·raw 접촉을 분리한다. README·인덱스·누적 보고서의 값·단위·링크 정정도 확인했다.

## 지적 및 해소

- Warning 해소: response/columns.json 및 calibration provenance·resolved source 입력 봉인, 전체 trace exact 표현의 범위 정정, raw 누락/finite/schedule guard, 결과 관측을 분석·plot 정상성 gate로 강제하던 조건 제거.
- Warning 해소: 계획의 ‘하중0’을 첫 접촉 raw λ0와 후기 접촉 없음으로 정정했다.
- Suggestion 해소: 제어 단위 명시, binary PNG의 가짜 줄 번호 제거, analyzer main 실제 32행 링크 반영.

## 검토한 현재 source SHA-256

| 파일 (`stability_adapter_2/`) | SHA-256 |
|---|---|
| palm_side_feedback.py | a7b38d753923f4ac1ef5a89fab1d1f10afc46112c7aa9077f38abeedc0936dfa |
| calibrate_palm_side.py | e3c8a433b4bb337423bc0726a64b5f096579e8b72379a89655571c25fd89051b |
| run_palm_side_feedback.py | da0c95d549b676b94b86e700673a0fa0f595dd27f5c1f5e673b8433f5af22ffe |
| seal_palm_side_calibration.py | d7195c78fc433e429fa6e9068edd314114350c66a26a822564a462aaadb91b69 |
| analyze_palm_side_feedback.py | 1d7237b30b420baf051fb75c7a39e080a8da77798f7e840019a32d670d9cb446 |
| plot_palm_side_feedback.py | 3f94c4f2bd339c6ed0f4dd398ed586d0b7e270662e482dd8cb598e985d73391b |

## 최종 검수

현재 소단계의 코드·저장 결과·산출물·문서에 남은 finding은 없다. 처음 가까이 배치한 손바닥의 첫-step 접촉은 관측됐지만 유지되지 않았고, 추적점 개선이 기타 개선으로 이어지지 않았다. 후속 목표 범위·접촉 추적·손가락 결합은 이번 결과에 포함되지 않는다. 검수 기록을 동결한다.
