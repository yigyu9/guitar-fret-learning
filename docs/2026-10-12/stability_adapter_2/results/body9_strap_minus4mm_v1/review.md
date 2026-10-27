# 독립 검수 — LA 원본 대비 −4mm 비교

**요약 판정: 문제없음.** 수정된 분석 코드·checkpoint audit v2·최종 그림 v3를 기준으로 남은 Critical/Warning은 없다. 이번 실제 시험은 새 1회·1200 physics step이며 검수 과정에서 재실행하지 않았다. 이 파일 외 코드·원자료·기존 결과는 수정하지 않았다.

## Critical

없음.

## Warning

없음. 아래 발견 사항은 원본을 보존한 후 해결됐으며, 보존된 이전 버전의 오류를 최종 버전의 미해결 문제로 세지 않았다.

## Suggestion

없음.

## 발견 사항과 해결 확인

- [원본 audit:77](/home/ajou/yigyu/3/stability_adapter_2/audit_playing_prior_contracts.py:77)은 Strike 관측 schema도 `payload.observation.schema`에서 읽어 기존 결과가 `null`이었다. [audit v2:59](/home/ajou/yigyu/3/stability_adapter_2/audit_playing_prior_contracts_v2.py:59)에서 Strike의 `config.strike.observation_contract`를 읽고 task별 `*.observation.v2`를 assert하도록 고쳤다. 새 `contract_correction/contract_audit.json`에 Fret/Strike schema가 모두 명시된다. 원본 audit source SHA는 이전 봉인값과 같고, 두 예시의 schema 외 결과 필드는 원본과 같다. 새 감사 입력 SHA 불일치는 0개다. 예시 checkpoint ABI 조사이며 source 선정·모델 inference·학습 실행을 뜻하지 않는다.
- 초기 분석은 원본/−4mm만 동일 조건을 검사하고 −2mm를 집계에만 넣었다. [분석 코드:26](/home/ajou/yigyu/3/stability_adapter_2/analyze_body9_strap_minus4mm.py:26)에 −2mm 공통 11필드·관절 이름·제출 명령·LA −2mm 단일 변경 대조가 추가됐다. 분석 실행 전 보완됐고 최종 13개 check가 모두 참이다.
- 초기 분석의 palm 양λ step 수만으로는 엄지·검지·중지 접촉 변화를 볼 수 없었다. [분석 코드:39](/home/ajou/yigyu/3/stability_adapter_2/analyze_body9_strap_minus4mm.py:39)에 모든 human–guitar 양λ body별 step 수와 최초/마지막 step이 추가됐다. 원자료에서 독립 집계해 최종 출력과 일치했다. raw lambda를 N이나 연속 지지 인증으로 해석하지 않는다.
- 보존된 그림 v1의 중복 범례는 [그림 v2:120](/home/ajou/yigyu/3/stability_adapter_2/make_body9_strap_minus4mm_artifacts_v2.py:120)의 첫 axes handles만 사용하는 방식으로 해결됐다. 실제 v2 PNG에서는 하단 caption과 `Time (s)` 라벨이 겹치는 추가 문제를 확인했다. [그림 v3:107](/home/ajou/yigyu/3/stability_adapter_2/make_body9_strap_minus4mm_artifacts_v3.py:107)의 `bottom=.16`과 새 출력 경로로 해결했다. 실제 v3 PNG를 독립 열람해 범례 3개, 축 단위, caption 분리와 표본 비가림을 확인했다. v1/v2 PNG·manifest는 보존돼 있다.

## 준비·실행·세 조건 수치 확인

- [준비 코드:27](/home/ajou/yigyu/3/stability_adapter_2/prepare_body9_strap_minus4mm_trial.py:27)의 새 trial은 원본과 비교해 `strap_rest_length_m` 한 필드만 다르다. LA는 `1.1018469719600776 → 1.0978469719600776m`이며 준비 입력 SHA 불일치는 0개다. 기존 humanoid pose·기타 p/q·목표·gain·source admission 근거를 바꾸지 않는다.
- 세 조건의 실제 공통 11개 초기 필드와 81개 DOF 이름이 같고 각각 1200개 제출 명령이 같다. 몸통9 stiffness×2/damping×√2, 다른72 PD, 초기81q·기타 상태·기존 절대 목표·손목 파형·물리 조건이 보존된다. root/하체 고정·자기충돌 정책·자유 기타·수동 고정 LA 조건을 유지한다.
- native 실행 exit 0과 완결된 1200step/151frame 기록을 확인했다. 세 조건마다 state/trace 1201행, contact/control 1200행과 step 순서를 대조했다. 분석 봉인 입력 SHA 불일치는 0개다.
- 기타 초기 최대/종료 p/q 오차와 2초 기준 후기 변화, original static baseline을 뺀 scalar 손목의 상수/trend/1Hz fit을 독립 재계산해 일치했다. 손목 진폭은 bone 회전과 구분돼 있고, −2/−4mm의 별도 무동작 정지 실측으로 표현하지 않는다.
- 세 조건 각 1200개 적용 장력을 직전 trace의 route point/velocity와 기존 `k=6000`, `d=120`, cap `300N` 법칙으로 독립 재구성해 오차 <1e−8N을 확인했다. 장력은 저장된 직전 step 적용 법칙값이며 연속 force 센서 실측이 아니다.

| 항목 | 원본 | −2mm | −4mm |
|---|---:|---:|---:|
| 최대 초기 위치 오차 mm | 14.132608 | 14.010556 | 14.023529 |
| 최대 초기 회전 오차 ° | 2.894328 | 2.607665 | 2.335921 |
| 2초 기준 최대 위치 변화 mm | 0.481766 | 0.363488 | 0.404326 |
| 2초 기준 최대 회전 변화 ° | 0.091929 | 0.070089 | 0.079347 |
| scalar 손목 fit 진폭 ° | 0.146929 | 0.147836 | 0.149523 |
| 최대 법칙 장력 N | 24.129230 | 28.152161 | 28.097309 |
| thumb3 양λ step 수 / 마지막 step | 411 / 1059 | 194 / 1054 | 163 / 1060 |
| middle3 양λ step 수 / 마지막 step | 14 / 42 | 20 / 48 | 28 / 59 |
| index3 양λ step 수 / 마지막 step | 1149 / 1200 | 1155 / 1200 | 1154 / 1200 |

palm 양λ와 human self-contact step은 세 조건 모두 0이고 R_Hip 양λ는 세 조건 모두 1200step이다. 접촉 개수/마지막 표본만으로 연속 지지나 완전한 세 면 grip을 인증하지 않는다.

## 후속 결정·제어권 범위

- [STRAP_MINUS4MM_DECISION.md:3](/home/ajou/yigyu/3/stability_adapter_2/STRAP_MINUS4MM_DECISION.md:3)의 숫자와 판단은 원자료와 일치한다. −4mm는 회전 개선 후보로 보존하고, −2mm는 더 작은 후기 위치·회전 변화의 비교 기준으로 유지한다. 두 조건의 모든 항목이 동시 개선됐다고 주장하지 않으며 추가 길이 단축을 자동 진행하지 않는다.
- [결정:15](/home/ajou/yigyu/3/stability_adapter_2/STRAP_MINUS4MM_DECISION.md:15)의 다음 범위는 −2mm 저장 actual snapshot에서 팔12+검증된 single-hinge finger6의 source identity/차분·whole-shape 검사를 먼저 하는 것이다. 실패한 finger1 FK를 사용하지 않고 source와 native 검증을 구분한다. 이 임시18축 탐색은 최종66 제어권을 제한하거나 신규 물리/학습 실행 완료를 뜻하지 않는다.
- [연주 설계:60](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:60)의 단일81D PD 제출, 이름 기반 source60+Thorax6 매핑, 한 번의 EMA, 최종 실행 목표의 source history 회신, Thorax-local projected gravity와 움직이는 G-frame 상대 속도는 현재 원본 코드 계약과 정합하다. 원래 유지 목표+공동66 residual을 사용하며 actualq로 base를 치환하지 않는다. 실제 관측/제어 연결·잔차0 동등성·actuator 차이 검증·학습은 후속 미완료 범위로 명시돼 있다.

## 그림·영상 색인 검수

- 최종 그림 v3 source SHA는 `1e61386b15c1a610889a1ec1ce8423f52ec8996888eaf1fcc87d46bd6fd239b5`다. v3 manifest의 생성 전후 입력 SHA, 현재 입력 SHA, PNG 출력 SHA가 모두 일치한다. 13개 분석 check와 저장 trace 3×1201행을 사용하며 그림 생성의 native 초기화/physics step은 0이다. 최종 v3 이미지의 시계열·단위·범례는 검수한 원자료와 맞는다.
- [영상 수집 코드:17](/home/ajou/yigyu/3/stability_adapter_2/collect_body9_strap_minus4mm_videos.py:17)는 완료한 두 MP4를 재인코딩 없이 복사하고 새 v4 색인을 만든다. `video_collection_update_v3.json`의 원본/복사 SHA·크기, producer SHA, 이전/새 색인 SHA를 독립 대조해 일치했다. 실제 videos 디렉터리는 126개이며, v4는 v3 내용 전체를 그대로 suffix로 보존한다. 기존 목록/영상 수정은 없다. 영상 본문의 모든 frame을 독립 시청한 검수로 확대하지 않는다.

검수는 코드·계획/결정 문서·출력·SHA 읽기, 저장 자료 수치 재계산, Python AST 문법 확인과 최종 PNG 직접 열람으로 수행했다. Source proxy admission을 PhysX cooked 관통 인증으로, 작은 손목 동작을 실제 fret/strike 연주·초기 p/q 복원·학습 성공으로 표현하지 않는다.
