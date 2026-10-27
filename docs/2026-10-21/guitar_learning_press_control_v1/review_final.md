# 압현 제어 v1 현행 문서·영상 최종 독립 검수

요약 판정: **검수 범위 문제없음. 구현·실행·저장·평가 무결성 PASS이며 연주 성능 개선 판정은 실패다.** 현재 계약의 2,000회 실행은 하지 않았다.

## 범위

이 phase README, `CURRENT_STATUS.md`, `guitar_learning/README.md`, `guitar_learning/AGENTS.md`, `docs/2026-10-26/learning_flow/README.md`와 승인 계획의 현재 설명을 실제 학습·고정평가·재개 증거 및 동결 source 계약에 대조했다. 영상 `video_qa.json`, 두 render report/presentation/pose audit/입력 pins 및 실제 MP4를 읽었다. 최종 정책 진단은 원 NPZ·원장으로 별도 독립 재계산했다.

GPU·native physics·GL·Renderer·기존 분석 main은 실행하지 않았다. CPU에서 원자료 집계·SHA·ffprobe만 수행했다. 영상 미리보기 여섯 장의 시각 판단은 root가 기록한 QA이며, 이 검수에서는 직접 영상 재생/시각 판단 대신 원본·영상·감사 로그의 대응을 검증했다. N4 정책 ablation의 상세 독립 분석은 별도 검수로 인계받을 범위로 남긴다.

## 코드·계약과 문서

- 활성 Python **435개** SHA가 동결 manifest와 일치함을 최종 재확인했다. 기존 **3개 수정 / 5개 추가 / 삭제 0**, protected unchanged의 변경 범위가 앞선 코드 검수와 일치한다. 제어·물리·PPO 변경이나 이전 성공의 암묵 상속은 없다.
- 현재는 GPU 왼손 reward v4 / surface observation v2 / ledger v2이며 상태512·행동39·curriculum3331이 유지된다. 같은 차원과 codec의 이전 v3도 strict resume할 수 없다는 고지가 실제 identity 거부 검사와 맞는다. CPU·오른손의 별도 경로를 구분한다.
- source neck convex hull의 **Gz9.3mm 접근 목표**와 원래 **Gz12.3mm 가상 현 중심 기반 접촉/clean 성공**을 분리했다. Gz 투영·프렛셀 안쪽2mm·실제 선택 표면점 상대속도 및 원 contact/success 문턱 설명이 구현과 같다. source 평면을 PhysX cooked witness·실제 현 압력·음향으로 인증하지 않는다.
- LH21은 행동×4/60 누적·native clamp·zero 목표 유지이며 GPU 위치평활화는 우회한다. CPU의 비례 위치제어 평활화0.45와 구분한다. 240Hz 양성 tracking 적분·요청 크기/속도 의존·최대4/s 및 실패tick 억제 설명도 계약과 일치한다.
- 실제 검증 예산은 **large/N1024/H32/seed7 fresh100회, 3,276,800전이**와 별도100→101재개다. 과거 위치제어·다른 보상 계약의 2,000회 결과 및 과거 절대 제어 8.301음과 현재 결과를 분리했다. H32가 reset 조건이 아니라는 설명과 53.333초/환경 예산도 맞는다.
- CPU **865 unique**는 856개 파일 격리 통과와 최초 실패 legacy 모듈의 9개 GDB 재검사 통과를 합한 커버리지다. 최초 단일프로세스·첫 sweep SIGFPE를 보존하고 `single_process_full_suite_passed=False`, FPU root cause 미해결을 구분한 설명이 정확하다.

검수 중 찾은 flow의 두 잔여 모순은 root가 수정했고 원문을 다시 확인했다. 현재 GPU21의 평활화0.45 표현은 GPU alpha1/CPU0.45 구분으로 교체됐으며, 현행 단계 설명의 옛 v1/현 중심선/±2mm 문단은 v2/press plane/안쪽2mm 및 기존 candidate 분리 설명으로 교체됐다. 계획의 진행 중 CPU 기록과 완료 기록도 시점이 구분됐다.

## 실제 결과와 주장 범위

학습100회·고정평가0/100·재개의 완료와 유한 저장본/입력 무결성은 앞선 독립 검수와 일치한다. 고정 전체 첫 곡 평균은 **3.8046875→0/67**, 안전은 **1024→1021/1024**, 전곡67음 성공은 둘 다0, 단계는0이다. 공통 안전1021개에서도 **3.800195886→0**이다. 세 물리 종료만으로 성과0을 설명하지 않으며 구현 완료·안전 완주를 연주 개선으로 표현하지 않는다.

`final_policy_diagnosis.json/md`의 입력21개 SHA와 new env0..7 및 old env0의 actual NPZ를 독립 재계산했다. strict 한 부호 LH21축 18/21 대 이전16/21, native outward/endpoint bound 비율, pooled target−q RMS, 10초 이후 target/q 범위, 누적 제어 recurrence, 팔12축 범위와 moving guitar 역회전 G-frame 마커 변위가 일치한다. 실제 float32 누적식 재대입 오차는 0으로 문서 허용오차 안이다.

새 캡처 8개에서 geometry/loaded-target/contact/clean/near의 해당 원장 시간은 모두0이며 순간 candidate는 첫 준비창1.5185초보다 앞선 endpoint에만 있다. selected body load가 있다는 사실과 목표에 대한 접촉 기하 부재를 구분한다. 손목 약1cm·손가락 마커 약12.8/17.0cm 변위는 body 원점의 기타 상대 이동이며 접촉점/압현 깊이가 아니다. 8개 표본을 전체1,024개의 움직임으로 일반화하거나 특정 보상 항을 회귀 원인으로 확정하지 않는다.

## 전신·손 영상

두 보고서 모두 실제 final100, 사전지정0..7의 가장 낮은 안전 ID **env0**, 안전 완주/0음을 가리킨다. 점수로 좋은 환경을 고른 영상이 아니며 전체 성과를 대표한다고 주장하지 않는다.

- 각 영상의 **593개 입력 SHA**, 실제 MP4 SHA와 보고서/QA 기록이 일치한다.
- 독립 CPU ffprobe로 두 MP4 모두 **H.264 / 1280×720 / 60fps / 1,969프레임 / 32.816667초**임을 다시 확인했다.
- raw source 1,970프레임(t0 포함)에서 끝점1..1969를 그대로 사용한다. 각 pose audit의 전체1,969행에서 frame 순서·정책 시간·4배 물리 clock·106body/105joint·새 물리0을 확인했다. 저장된 position error는0이고 최대 rotation error는 약7.78e-16rad이며 감사의 모든 projection 값은 지정 화면 범위 안이다.
- 원본 자세를 새 물리 적분·정책 실행·보간 없이 설치하는 영상이라는 설명이 맞는다. MP4·감사 자료 검증은 렌더된 모습의 물리 접촉/압력/음향 인증을 뜻하지 않는다.

## 결론과 종료

Critical / 수정이 필요한 Warning: 없음. 현재 문서는 성능 미달·한 방향 출력 잔존·기존 x87/legacy SIGFPE 미해결·장기 실행 미수행을 숨기지 않는다. 독립 정지 보상 등 후속 가설을 구현되거나 효과가 검증된 개선으로 말하지 않는다.

범위별 상세 결과는 `review_preflight.md`, `review_tools.md`, `review_contact_probe.md`, `review_training100.md`, `review_evaluation.md`, `review_resume.md`에 보존돼 있다. N4 상세 분석의 별도 독립 검수와 root의 최종 결과 manifest 봉인은 이 문서 이후 별도 단계다.

이 문서만 새로 작성했으며 작성 종료했다. 다른 source·도구·문서·원자료·과거 봉인 파일은 변경하지 않았다.
