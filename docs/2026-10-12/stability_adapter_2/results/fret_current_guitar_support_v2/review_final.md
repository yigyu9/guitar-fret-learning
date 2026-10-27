# 현재 기타 지지 관계 추종 v2 최종 검수

**요약 판정: 문제없음.** Critical·Warning 코드/결과 오류는 확인하지 못했다. 목표 기준 문구 보완도 반영됐다. 실제 실험은 원본 wrong-press 실패로 끝났으며 안정화·압현·연주 성공은 아니다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음. 발견했던 준비 목표 기준의 모호한 문구는 마지막 제출 PD 목표 기준으로 수정 완료됐다.

이 검수 문서만 생성했다. A·raw·analysis·기존 결과를 수정하지 않았으며 native trial을 실행하지 않았다.

## 제어와 원본 종료

- [run_fret_current_guitar_support_v2.py:125](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:125): actual wrist-G 지지 관계를 left9 solver에 사용하고 source wrist anchor는 별도 측정만 한다. 모든 finger21 요청이 source 정책 해당 slot과 exact 같으며, 제출 속도·native bounds·prepared ±0.1/initial ±0.3 envelope를 raw 목표 전체에서 대조했다. prepared 대비 최대 목표 변화0.10000002384rad는 float32 제출 정밀도 범위에 있다.
- [run_fret_current_guitar_support_v2.py:142](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:142): 다음 actor observation의 O_history는 직전 executed_history와 exact 같다. trace가 존재하는 control timestamp의 actual wrist 및 지지 world 목표가 같은 시점 native state와 일치한다. root/하체도 raw trace에서 고정돼 있다. 최대 FK/native 위치 오차3.114e-7m·회전 오차6.008e-7rad이며548개 fit 모두 수렴 판정을 받았다.
- [run_fret_current_guitar_support_v2.py:160](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:160): 이전 PLAY 행은 모두 source_done=false, 마지막만 true다. 마지막 control 뒤4 physics step에서2672 step·11.1333333초로 종료되며 마지막 source_info와 terminal_info는 exact 같다. 원본 wrong_press_termination/failure_termination만 해당 실패로 true이며 goal_finished·success는 false다. actor548회, 학습 업데이트0회다.
- [ON/data/terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/terminal_info.json): physical_press_rate·stable_press_success_rate는0, sustain_event_success_count/event_count는0/21이다. 녹화 완료와 물리적 성공을 구분한다.

## 공정한 비교와 지표 구분

- [analyze_fret_current_guitar_support_v2_verified.py:33](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_support_v2_verified.py:33): raw ON의 wrist_error_m는 지지 관계 오차다. analyzer는 메모리 안에서 source_wrist_error_m를 source 목표 비교용으로 분리하며 raw 파일을 수정하지 않는다. observation의 source wrist vector norm과 별도 source_wrist_error_m가 일치함을 확인했다.
- [analyze_fret_current_guitar_support_v2_verified.py:65](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_support_v2_verified.py:65): timestamp와 source_frame_before가 같은548개 control(2.0000000~11.1166667초)을 독립 대조했다. 평균 source wrist ON−OFF는+3.3539976974mm로, 지지 오차 개선과 별개로 source 목표 오차가 악화됐다. 같은 goal/time/finger646개 표식 평균 ON−OFF는+32.4804323741mm다. 표식 norm은 압력·접촉 증거가 아니다.
- [interpretation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/interpretation.json): 공통0~11.1333333초 기타 최대 root 이동은73.190→126.888mm, 최대 회전 변화는47.863→19.408°다. ON 위치box 최대 초과68.363mm도 독립 raw 계산과 일치한다. 상대 손목 지지 오차는 같은2~11.1333333초의30fps trace275개(준비 완료/terminal 포함)에서 평균52.902→49.746mm, 최대62.413→55.841mm다. source 손목 비교의60Hz control548개와 표본 기준이 다르다.
- [analysis_verified/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/summary.json)의 OFF 전체 episode 지지오차 평균54.504mm와 최종82.234mm는 OFF가 더 길게 진행된 값이다. 공통 구간 비교에는 interpretation.json의52.902mm 및59.883mm를 사용해야 하며 결과 README는 이를 정확히 구분한다.
- v1 OFF와 v2 ON의 native 초기 상태 및 준비2초 trace는 exact 같다. mode metadata를 제외한 준비 control도 exact 같다. 기존 OFF는 재실행한 v2 trial로 세지 않고 v1 보존 기준을 재사용한다.

## native 영상과 분석 봉인

ON raw PNG 전체 SHA, 두 MP4 SHA와 독립 ffprobe 결과, capture/trace step 목록을 대조했다. 전신·손 각각1280×720·30fps·335 frame이며 t0~11.1333333초의 첫 원본 done까지 포함한다. MP4 재생 길이는11.166667초로 실제 physics duration과 다르다. 선택된 native 나란히 패널과 timeline을 열어 시각·범례·축 범위를 확인했다. 압력/접촉 overlay가 추가된 화면으로 설명하지 않는다.

[fret_arm_analysis_preserved.py:20](/home/ajou/yigyu/3/stability_adapter_2/fret_arm_analysis_preserved.py:20)은 analyzer import 전에 source/helper·ABI·font·BASE·기존 baseline·raw JSON/PNG를 봉인했다. 감사 실행의2229개 before/after SHA는 변경0이며 소비 source snapshot도 before SHA와 일치한다. 직접 raw 입력·코드·검증 analyzer는 현재도 일치한다.

검수 시 현재 작업본에서 A/PLAN.md 및 A/README.md만 감사 실행 후 진행 갱신으로 달라졌다. 두 문서의 당시 소비본은 analysis_verified_audit/source_before에 before SHA와 exact로 남아 있다. 따라서 “감사 실행 중2229입력 변경0”과 “현재 작업본의 모든2229입력이 동일”을 구분한다. root 최종 봉인은 소비 스냅샷 및 이후 갱신 문서를 각각 식별해야 한다.

## 결과 문서

README/FILE_INDEX의 source goal·지지 관계 목표 구분, frozen checkpoint와 동작하는 finger21 정책, 작은 목표 envelope/변화율, 실패·press/sustain 지표, 보존된 v1 OFF 재사용, no-overlay native 패널 설명을 대조했다. 기존 artifact 링크가 존재하며 최종 감사/봉인 산출물은 작성 예정으로 명시돼 있다. 다음 방향은 구현된 안정화 성공으로 설명하지 않는다. source 운지 오차와 위치 범위 악화가 남으므로 회전 개선만으로 실제 연주 성공을 주장할 근거는 없다.

마지막 수정본의 README5·FILE_INDEX8은 ±0.1rad의 기준을 준비 마지막 제출 PD 목표로 명시한다. README11은 실제 physics 종료11.133333초와 MP4 재생11.166667초를 구분하고, README41은 timeline 위 패널이 source wrist anchor 오차이며 상대 지지 오차가 아님을 설명한다. 이 문구들을 확인해 미해결 Suggestion을 닫았다.
