# 저장된 팔 목표–응답 분석 독립 검수

검수일: 2026-10-07. 범위는 새 `analyze_palm_target_response.py`, `plot_palm_target_response.py`, 현재 response와 provenance, 계획·결과 안내·누적 보고서다. 원자료와 코드·기존 동결 기록은 수정하지 않았으며 native 실행은 하지 않았다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 이번 결과는 저장 표본의 목표 좌표 차이와 이동 방향 분석이며, 안정화 성공이나 PD·토크 원인 판정이 아니다.

## 계산·입력 검증

- 세 조건의 90개 창에서 step `k=0,4,…,116`→`k+4`, 전달 목표의 네-step 유지, pre/post 실제 좌표 차이, 관절 이름·도 단위 변환을 독립 재계산했다.
- `A(target−actual)` 정적 이동, 실제 source-center 이동, 실제 팔 좌표변화의 선형항과 잔차, 초기 목표 방향 투영을 대조했다. PALM_RATE의 30개 task residual 수식도 일치했다.
- response의 6개 검사, 명시 입력 SHA 154건 및 이전 보관 소스 13건을 확인했다. 기존 0.5초 자료를 읽는 분석이며 새로운 물리 표본을 만들지 않았다.
- 각 조건은 투영 음수 29개·초기 null 1개다. 마지막 PALM_RATE 창의 정적 크기 177.530792582 mm, 실측 이동 0.745714262 mm, 방향 투영 −0.613600483 mm가 일치한다.

## 수정 사항 확인

- 후기 null을 거절하던 plot 조건을 해소했다. 초기 null 계약을 유지하며 이후 null과 양수 관측은 허용하고, 숫자 NaN은 거절한다. v2 producer의 별도 합성 plot fixture에서 후기 null·양수 입력은 exit 0, 숫자 NaN은 exit 1이었다. 이는 소비자 검증용 합성 자료이며 새로운 실측 결과가 아니다.
- 결과 README:31에서 기타 초기 p/q 기준과 LH source-center 위치 task 목표를 구별했다. README:29의 잔차 및 계획:18의 방향 성분 표현도 수정되어 원인·거리 단조 변화를 과장하지 않는다.
- v3는 footer 배치 수정이며 검증 로직은 v2와 같다. 이전 producer·이미지·실행 기록을 보존했고 현재 canonical 경로는 `artifacts_final`과 `plot_execution_v3.json`이다.

## 최종 미디어·문서 검수

지원 CLI를 새로운 `/tmp` 경로에서 실행하여 최종 2212×1434 PNG의 바이트·RGBA 일치, response/입력 154건/producer/output SHA를 확인했다. 그림을 직접 열어 축·단위·범례·초기 null 생략·부호 유지와 데이터 축 밖 footer를 확인했다. README:7·41, CHANGED_FILES:4–6, VISUAL_REPORT:852·858·860 및 PLAN:945의 수치와 링크가 정합하다.

정적 Jacobian 계산에는 응답 시간이 없다. 이를 16.7 ms 예상 이동이나 actuator 토크·PD 부족의 증거로 해석할 수 없다. 실측 이동에는 전체 humanoid 움직임이 포함되며 잔차는 원인을 분리하지 않는다. 부호 있는 방향 성분도 연속시간 거리 단조 변화의 증명이 아니다. source 형상 중심은 해부학적 palm·접촉점·COM·물리 지지 인증을 뜻하지 않는다. gain·PD·초기 q·LA·제어 조건 변경 없이 이 분석 단위의 검수를 완료했으며, 본 리뷰는 동결한다.
