# 초기 자세 적격성 자료 — 준비 브리프

이 문서는 완료된 baseline, static, strike 자료로 만든 준비용 브리프다. 왼손 사이클과 z+3 mm 실행은 아직 최종 확인 전이므로 결과값, 순위, 결론에 포함하지 않는다. 최종 문서, 비교 그래프, 복사 manifest 및 영상 복사는 root의 최종 브리프를 받은 뒤 진행한다.

## 닫힌 조건과 현재 승인 수치

| 조건 | 실행 | 최대 기타 BB 중심 변위 | 최대 SO(3) 회전 | 왼팔·손 접촉 |
|---|---|---:|---:|---|
| 기준 자세 | `native_baseline_v2` | 2.81097 mm | 0.69288° | 2,255/2,400 표본 |
| 정적 왼손 분리 | `native_static_v3` | 2.71887 mm | 0.82645° | 0/2,400, 즉 전 구간 접촉 없음 |
| EW6 타현 | `native_strike_v2` | 6.14502 mm | 4.23678° | 짧은 접촉 41/1,200; 엄지+다른 손가락 동시 양의 표본은 0 |

Strike는 EW6 타현만 사용했고 나머지 75개 목표를 유지했다. down/up 실제 창은 `strike_actual_windows_v1.json`의 V7 집계를 따른다. 기존 raw detector는 보존하고, 오래된 상향 창 경계(3.95초 이후)로 누락된 합계를 유효 창으로 취급하지 않는다. 전체 6줄 하향·상향 통과는 원시 시퀀스에서 확인된 범위이며 학습된 노래 연주나 음악 성공을 뜻하지 않는다.

Static 결과는 `native_static_v3`만 사용한다. `native_static_v2` 전역 guard는 실패했지만, v3는 guard를 통과했고 `static_reproduction_v1.json`에 원자료 일치를 기록했다. v2가 전역 guard를 통과했다고 쓰지 않는다. 재현된 static 마지막 2초 최대 변화는 0.01591 mm / 0.006185°다.

## 최종 산출물 계획

최종 묶음은 아래 다섯 조건 각각에 대해 front, right-side, top, front-side-top 4개 기존 annotated MP4와 visual report에 지정된 3-up PNG들을 그대로 복사한다. 스냅샷은 initial/final 및 LH hold/free/peak 역할로 골라 실제 프레임 시간과 해시를 확인한다. 비교 그림은 표준 Matplotlib에서 기타 BB 중심 변위(mm)와 회전(deg)을 **별도 축**으로 그린다.

| 최종 조건 | Native 원본 | Annotated visual 원본 |
|---|---|---|
| 기준 자세 | `native_baseline_v2` | `visual_baseline_v1` |
| 정적 왼손 분리 | `native_static_v3` | `visual_static_v1` |
| EW6 타현 | `native_strike_v2` | `visual_strike_v1` |
| 왼손 사이클 | `native_left_cycle_v2` | `visual_left_cycle_v1` |
| z+3 mm 변형 | `native_z_plus3mm_v2` | `visual_z_plus3mm_v1` |

왼손 사이클·z+3 mm의 확정 상태와 수치는 최종 브리프 전까지 미정으로 둔다. 최종 산출 전 실제 raw/helper/font/copied source를 새 pre-pin에 기록하며, 이 준비 브리프만으로 최종 manifest를 만들지 않는다.

## 해석 범위와 보류

- 이 자료는 자유 기타, 끈/인위적 기타 힘 없음, root·하체 고정과 유한 human support가 있는 native 실행의 관측이다. passive equilibrium, force closure, 강건성, 학습 checkpoint 또는 music-ready를 주장하지 않는다.
- 팔 관절 scalar limit 여유는 자세 가능 범위 지표이지 해부학적·사용성 인증이 아니다. 현재 여유는 L_Wrist Y 0°, R_Thorax X 0.000046°, L_Thorax Z 0.0012°로 limit에 가깝다. 따라서 final music-ready default를 선언하지 않는다.
- 호환성 목적으로 상속된 `left_neck_near`/`body_side_lean_axilla` 이름을 가진 후보 metadata는 새로운 다면 접촉 또는 LH-near 인증이 아니다. 현재 주장은 `source_v4/proposal_audit`, 실제 native 실행 및 분석으로 제한한다.
- Q14 LH는 시작 시 분리/후퇴하며 고정 palm 접촉을 요구하지 않는다. 단일 접촉 프레임이나 목표값만으로 연속 그립을 주장하지 않는다.

## 준비용 preflight

`artifact_producer_v1.py`는 현재 닫힌 세 조건의 분석·visual 파일 존재와 주요 캡처 구성을 읽기 전용으로 확인한다. 복사, 렌더, 문서 생성, hash manifest 생성은 하지 않는다. 최종 브리프와 두 pending 조건이 확정된 뒤 소유 경로 안에서 production 단계를 추가한다.
