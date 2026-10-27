# 압현 획득 진단·개선 v1

2026-10-25 진단 도구·조건부 v19 보상 구현과 구동·저장/재개 검증 완료. [구현 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_press_acquisition_20261025.md)에 따라 현재 손가락의 도달·접촉을 진단했다. 자유 기타에서도 실제 연속접촉을 확인해 v19 최초접촉 보상을 적용했다. 장기 성능 개선은 아직 확인하지 않았다.

## 현재 상태

| 작업 | 상태 |
| --- | --- |
| 변경 전 원문 보관 | 474개 원문을 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261025_before_press_acquisition_v1/manifest.json)에 보존 |
| 기존 CPU 회귀 | 관련 278개 검사 통과. 원문은 [기준 검사 로그](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/baseline_cpu.log) 참조 |
| 현행 v18 기준 GPU 실행 | 16환경·H32·65업데이트·33,280전이 완료. 종료 16곡 모두 safe, 평균 달성 0.625/67. [실행 로그](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/baseline_v18_console.log)·[저장 검증](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/baseline_v18_inspection.json) |
| 손가락별 도달·고정/자유 진단 | v2와 feedback v3 대조 완료, 각 조건16목표 모두 안전. 아래 결과 참조 |
| 최초접촉 보상 변경 | v19 구현·관련299CPU·독립검사·16환경실행·65→66재개·large1024 짧은 구동 검증 완료 |
| 보상 구조 문서 갱신 | v19 계약·계산식·관측·로그·실행흐름과 확정 검증 결과 갱신 완료 |

## 범위와 판정 원칙

기본 학습의 자유 기타·중력 ON·스트랩 OFF·035/v14 초기 자세·손가락 전체 가동범위·움직임 비용 0을 유지한다. 고정 기타는 진단 전용이며 현재 단일 강체 기타와 동일한 충돌 자산을 비교한다.

기하 탐색이 찾은 관절 자세는 도달 후보이며, 실제 제어·물리에서 접촉을 유지한 결과와 구분한다. 탐색 실패만으로 도달 불가능을 판정하지 않는다. 몸체 순접촉합력은 해당 패드점의 현 압력·몸체쌍·음향 인증이 아니다.

이 문서의 작은 GPU 실행은 구동·기록·접촉 연결과 저장/복구를 확인하기 위한 검사다. 장기 학습, 곡 연주 수렴, 손 모양의 자연스러움 개선과 구분한다. 이전 v17 장기 결과를 이번 변경의 성과로 상속하지 않는다.

## 진단 중 확인한 사항

첫 고정 pilot은 물리 240Hz의 2,040 step을 재생했으나 보고서를 쓰는 중 중복 키 오류로 종료 코드 1을 반환했다. [첫 실행 로그](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/fixed_console.log)와 원자료는 보존하고 완료된 대조로 세지 않는다.

독립 검수에서 횡오차·높이 분해 기준의 오류를 찾아 현행 `project_press_strings` 투영을 사용하도록 고쳤고 관련 CPU 9개 검사가 통과했다. 첫 nominal source FK와 실제 native 자세 교정 비교 오차는 최대 45.6μm·0.000866rad였다. 이후 v3 전체 재생 표본의 최대치는 고정149.5μm·0.00342rad, 자유190.7μm·0.00439rad다. 이 일치가 접촉 가능성 자체를 인증하지는 않는다.

기존 기하 탐색의 지판면 위 +1mm 목표는 하중 없는 자세를 허용했다. 진단용 후보 목표만 지판면 기준 −0.5mm로 바꿔 [새 기하 탐색](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/geometry_v2_console.log)을 완료했다. 이는 현재 positive 높이 허용대역 [−1,+3]mm 안의 후보 선택이며, 학습의 접촉 판정·모델·보상 기준 변경이 아니다.

## v2 동일 자산 고정/자유 대조

손가락별 4개씩 총 16개 정적 목표를 재생했다. 양쪽 모두 16목표가 안전하게 끝났고 입력 소스는 실행 중 바뀌지 않았다. 단일 강체·89개 충돌 형상의 메타데이터는 요청한 루트 고정 여부만 달랐다.

| 조건 | 연속접촉 결과 | 원문 |
| --- | --- | --- |
| 고정 | 16목표 모두 연속 candidate 0초 | [fixed_v2 보고서](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/fixed_v2/report.json) |
| 자유 | 검지 row0 최장 7.837초, 검지 row3 최장 0.996초. 나머지 14목표 0초 | [free_v2 보고서](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_v2/report.json) |

자유 기타에서도 기존 판정의 의미 있는 연속접촉을 실제 물리로 만들 수 있음을 확인했다. 모든 손가락·목표의 도달을 확인한 것은 아니다. 이 진단은 곡 시계의 음별 달성 평가가 아니며, 검사하지 않는 다른 손가락은 준비 자세 명령을 유지했다. 이 결과를 도달 불가능의 증명이나 고정 기타의 일반적 열세로 해석하지 않는다.

## v3 추종 오차 보정 대조

초기0.5초 유지·6초 ramp·6초 hold의3,000 물리 step(750제어tick)을 각 조건에서 수행했다. 초기 ramp 뒤 팔12축과 지정손가락4축만 실제 q 오차에 따라 보정했고, gain1.5/초·offset최대0.1rad와 기존 행동/목표 한계를 지켰다. 보정은39차원 행동 역변환 경로만 사용하며 기본 학습 제어·PD·DOF 상태를 바꾸지 않는다.

| 조건 | 연속50ms 이상 | 연속100ms 이상 | 안전 | 원문 |
| --- | ---: | ---: | ---: | --- |
| 고정 feedback | 2/16 | 1/16 | 16/16 | [보고서](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/fixed_feedback_v3/report.json) |
| 자유 feedback | 2/16 | 2/16 | 16/16 | [보고서](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_feedback_v3/report.json) |

접촉한 목표는 둘 다 검지2개다. 고정의 보정 조건에서도 접촉을 확인했지만 보정의 인과 효과는 분리 검증하지 않았다. v3 row0은 보정 시작6.5초 전인 첫 물리step에도 candidate가 있었고, v2와 v3의 hold 길이도2초와6초로 다르다. 다른 세 손가락의 접촉은 확인하지 못했다. 실측오차가 각 조건의 명령에 영향을 주므로 v2의 같은 명목 궤적 대조와 구분한다. 양쪽 소스는 실행 중 불변이고 종료 scene.closed=true를 확인했다. 자산 메타데이터 차이는 요청한 루트 고정 여부뿐이다. [대조 요약](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/diagnostic_comparison.json)을 따른다.

## v19 변경 내용

최초접촉 원시 예산0.5b를 최장 연속접촉의 문턱 진행 증가분으로 분할한다. 문턱 tau=min(50ms,end−press)과 contact_done 판정은 유지한다. 짧은 접촉을 반복해 최장 길이가 늘지 않으면 추가 예산이 없다. 기존 이진 보너스는 중복 지급하지 않는다.

reward.v19·surface_fretting.v8·events.v5·ledger.v7로 구분한다. 음별 best_contact_streak/contact_progress를 기록하고, GPU왼손 일반·우선 토큰12/13은 현재streak/tau와최장streak/tau(scale1)다. 누적held 관측을 교체하되 실제 clean/held 계산·보상·원장·로그와 토큰11clean_streak는 유지한다. contact_progress는 소진한 원시 예산 진행률이며 실패tick 억제·단계 가중 후 실제 받은 금액이 아니다. 실제 지급은 reward_components.song_left_contact에 기록한다.

상태544·토큰24열·우선8·3331단계·Bv3·손가락움직임비용0·035/v14·자유기타·힘/PD·PPO·clean달성을 유지한다. v18 이하 strict resume와 자동 Actor 이전은 허용하지 않는다. [보상 구조 문서](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/README.md)에서 상세 식을 확인한다.

## 구현 검사와 남은 검증

459개 현행 Python AST 검사와 GPU 관련·진단 29모듈299개 CPU 검사가 통과했다. [CPU 결과](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/cpu_validation.json)·[최종 로그](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/cpu_regression_final.log)를 따른다. 독립 검수에서57개 관련 검사를 재실행하고7개 scalar case·532표본·H32 경계를 대조했으며 최대오차1.49e−8을 확인했다. [독립 보상 검수](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/independent_reward_review.json)를 따른다.

별도 확장48개 CPU 검사에서는47개가 통과했고 기본GPU544를 CPU512로 가정하는 기존 검사1개가 실패했다. 해당 검사의 원문 SHA는 변경 전과 같고 명시적 CPU왼손512/오른손500은 확인했다. [기존 검사 실패 구분](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/known_test_failure.json)을 따른다.

## 실제 GPU 구동·재개 검증

| 조건 | 전이 | 종료곡 | 안전 | 평균 달성음 |
| --- | ---: | ---: | ---: | ---: |
| 기준 v18·16환경/H32/65업데이트 | 33,280 | 16 | 16 | 0.625/67 |
| 변경 v19·같은 조건 | 33,280 | 16 | 15 | 0.5625/67 |

v19의1회 실패는 env9의28.15초 기타 변위 종료다. 초기 v18/v19 모델은 정확히 같았고 물리·제어·안전·태스크·B·PPO 계약이 같음을 확인했다. 이 작은 검사는 성능 향상을 보이지 않았으며 수렴·다중seed 인과 비교로 해석하지 않는다.

GPU 원장에서 문턱 전 부분접촉음10개와 최초접촉 완료18개를 확인했다. 단계 가중 후 실제 지급과 예산 계산의 최대오차는9.27e−8이었다. [v19 저장 검증](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/gpu_v19_inspection.json)과 [GPU 검증 원문](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/gpu_verification.json)을 따른다.

실제65→66 재개에서 모델·양optimizer·CPU/CUDA/NumPy/Python RNG·3331단계를 포함한 metadata 이외10개 필드를 정확히 복원했고 이후 모델·양Adam이 갱신됐다. 곡 중간의 물리 상태 복원이 아니라035/v14에서 시작하는 새 에피소드다. 실제v18 final은 상태를 바꾸지 않고 strict load에서 거부했다.

large1024·H32·12업데이트·393,216전이도 정상 종료했다. 원시 CRC·회계·실행 중 소스 불변·scene.closed=true를 확인했고 OOM은 없었다. CUDA 전체 표본의 최소 여유는6.47754GiB, cache 반환 뒤 guard의 최소 여유는6.69238GiB다. 두 값은 측정 시점이 다르다.

다만 **1.067~6.267초에 물리 종료33회가 발생했다. 모두 기타 변위이며1회는 회전 조건도 겹쳤다.** 환경별 구동 길이가6.4초라32.8167초 전곡을 완료할 수 없었고, 기록된 종료곡33개는 모두 물리실패다. 이 실행을 안정적인 전곡 학습이나 무실패 검사로 해석하지 않는다. [1024 검증](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/large1024_verification.json)·[실행 보고서](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/gpu_v19_large1024/report.json)·[로그 검사](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/gpu_v19_large1024_inspection.json)를 따른다.

이번 완료 범위는 진단 도구·v19 구현·구동/원장/저장/재개 검증이다. 200회 보상 전후 학습 대조·고정정책 평가·장기 성능 평가는 후속 실험으로 남긴다. 균형 곡 구간·손가락별 단계·제어 변경도 이번에 적용하지 않았다.

## 실제 진단 자세 영상

- 자유 기타 검지 row0: [전신](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_index_front_video/full.mp4)·[손 확대](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_index_front_video/hand.mp4).
- 자유 기타 중지 row4의 미접촉 사례: [전신](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_middle_front_video/full.mp4)·[손 확대](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/free_middle_front_video/hand.mp4). 각751프레임 출력 검증을 통과했다.

저장된 실제 물리 진단 자세를 렌더한 영상이며 ffprobe로 출력 형식을 확인했다. 학습한 정책의 평가 영상이나 곡 연주 성공 영상이 아니다.
