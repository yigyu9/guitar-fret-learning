# 프로젝트 현재 상태 — 2026-10-31 확인

## 현행 기본 구현

GPU 왼손 finger-skill v3의 J33 공동 학습을 사용한다. GPU 왼손의 초기 자세는 내부 자산 `guitar_learning/assets/prepared_reset_v1/left_standby_v9.json`이며, 왼팔·손목·손가락33축을 첫 tick부터 함께 학습한다. LH21은 목표각 직접 지정(position), 물리240Hz·정책60Hz·K1이다. R/F 단계·자동 단계 전환·누적 손가락 제어는 현행 기본에서 제거했다.

실행 기본값·관측·재개 계약·보상·종료·저장 방식은 [현행 학습 안내](guitar_learning/README.md)를 기준으로 한다. CPU·오른손 및 과거 song 재현은 별도 도구다. v9와 B 대기 권고는 구분한다. v9는 reset/행동0 기준이고, B는 해당 손가락이 준비·접촉하지 않는 구간에서만 주는 약한 자세 선호다. B 허용대는 MCP±30°, PIP/DIP±15°다.

## 현재 압현 실험

현재 [목표 전환 v2](docs/2026-11-02/압현성공/experiments/target_transition_v2/README.md)를 실행 중이다. 같은 중지의6·7프렛 동시 성공을 허용하던 판정을 `wrong_press_sources.v3`으로 보정했다. 같은 학습 초기 상태·자유 기타·기존 제어기의 참조 동작은 휴지0.75/1초에서6→7→6 각1.5초 유지와 정시 시작을 통과했다.0.5초는 현재 참조 경로에서 실패했다. [구현 검증](docs/2026-11-02/압현성공/experiments/target_transition_v2/validation/IMPLEMENTATION.md). 학습 정책 성과와는 구분하며, 현재 fresh E4·large64·H32·팔12+중지4축·휴지0.75초의 A→B 두 음을 seed7/17 각300회 학습하고100회마다 평균/확률 각32환경을 평가한다. [자동 진행](docs/2026-11-02/압현성공/experiments/target_transition_v2/runs/comparison_v1/진행상황.md) · [결과](docs/2026-11-02/압현성공/experiments/target_transition_v2/runs/comparison_v1/RESULTS.md).

[구조 v2](docs/2026-11-02/압현성공/experiments/structured_press_v2/README.md)는 별도 사본에서 구현·소규모 GPU 실행 검증을 완료했다. A 정렬 시작의 손가락4축 → B 팔12+손가락4축 → C v9 분포·전체33축으로 확장하며 목표 손가락은 모든 구간에서 자유롭다. 초기 자세4목표×6환경 검증, CPU16검사, GPU 학습·저장·재개·이전·지원 제거 평가·렌더를 통과했다. [구현 검증](docs/2026-11-02/압현성공/experiments/structured_press_v2/analysis/IMPLEMENTATION.md).

직전 단독 검증에서는 사용자 요청대로 **검지3번 줄·4프렛 한 목표 A를200회** 학습했다.100회·200회 각각 안전 달성32/32, 물리·손목 종료0이었다. 평균 압현 유지97.6%로 더 좋은100회 모델의 실제 정책 영상을 제공한다. 이는 팔을 정렬 위치에 유지하는 지원 조건이었다. 후속 확장은 아래7시간 연구에서 별도로 평가하며 생산 기본값은 유지한다. [결과·영상·관절 기록](docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/index_s3_f4_A_v1/RESULTS.md).

사용자 승인에 따라 약7시간 예산의 자율 연구를 수행했고 GPU 실험·집계·영상 생성을 마쳤다. [최종 연구 보고서](docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/RESEARCH_REPORT.md): 추가 학습2,408업데이트, 네 손가락 대표 목표의 A학습/자유 평균 평가32/32. 고정 IK 팔 명령을 사용하므로 팔 정렬을 학습한 성과는 아니다. full33의 두 난수 모두 기본 평균은100회32/32→200회0/32였다. 요청관절각 기댓값은seed7 마지막 모델을32/32로 회복했지만seed17은0/32였고, 탐색0.1배도seed17 마지막 실패를 해결하지 못했다. 그룹별 탐색 진단에서는 목표 손가락·팔 표본 실행의 결과가 학습 난수에 따라 달라 어느 설정도 일괄 교체하지 않았다. 실행 방식별 실제 손·전신을 포함해 공개영상17개를 검수했다. [선택 모델·영상](docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/SELECTED_MODELS.md), [완료/검수 상태](docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1/progress.json). 기존 최고 모델과 생산557열 전곡 기본값은 보존했으며 자연스러운 관절 협응·엄지 지지·새 목표 일반화는 남은 과제다.

앞선 [실제 PPO 단일음 실험](docs/2026-11-02/압현성공/README.md)은 검지·중지·약지·소지마다4개, 총16개 목표를 large·64환경·H32·100회·seed7로 독립 학습했다. 최종256평가의 접촉·clean·달성은0이었다. 이후 탐색·학습률·순차 구조 비교도 최종0/640이었으며, 이전 정렬 gate가 손가락 굽힘을 차단한 결과를 근거로 구조 v2를 구현했다.

- 변하는 진행 단계와 완료 수: [실시간 진행](docs/2026-11-02/압현성공/process/learning/progress.md)
- 초기/최종 모델의 동일16환경 평가: [누적 평가](docs/2026-11-02/압현성공/analysis/learning/summary.json)
- 완료 결과는 `analysis/learning/RESULTS.md`, 영상은 `video/learning/`에 저장했다. 새 구조의 결과와 구분한다.

앞서 완료한 기하 후보 재생의5/16 성공은 이 PPO 학습 성과가 아니다. 짧은 학습의 실패도 물리적 도달 불가능의 증거로 단정하지 않는다.

## 검증과 성과의 범위

현재 단일음 경로는 GPU8환경·2회 소규모 학습과 실제 정책의 native 손·전신180프레임 영상 저장을 확인했다. [학습 보고서](docs/2026-11-02/압현성공/process/learning/smoke/report.json) · [렌더 보고서](docs/2026-11-02/압현성공/process/learning/smoke_native_render/report.json). 실행 완료는 압현 성공이나 장기 수렴을 뜻하지 않는다.

UTF-8/시각 현 로딩 수정의 GPU 학습·strict 재개 검증은 [당시 검증](docs/2026-10-29/utf8_visual_load_v1/README.md)에 있다. 이식성 작업 당시의 드라이버 제약은 [당시 이식성 검증](docs/2026-10-29/portability_v1/README.md)에 남긴다. 현재 GPU 실행 확인을 다른 PC·SSHFS 이동 및 모든 계약의 재검증으로 확대하지 않는다.

이전 직접 위치제어8시간 학습은1626회·53,280,768전이를 실행했고 최종128환경 평균7.9297/67음, 전곡 달성0/128이었다. [당시 결과](docs/2026-10-29/direct_position_8h_v1/README.md). 초기 자세 변경 전의 결과이므로 현재 v9 정책 성과가 아니다.

별도 비교 연구의 완료·선정 결과는 [개별비교 연구](docs/2026-11-02/수정사항/개별비교연구/README.md), [무접촉 종료 연구](docs/2026-11-02/수정사항/무접촉종료실험/RESULTS.md), [효율 검증](docs/2026-11-02/수정사항/연구환경효율검증/RESULTS.md)에서 확인한다. 연구 결과를 현행 기본에 자동 채택한 것으로 해석하지 않는다.

## 정리·역사 기록

사용자 승인으로 이전8시간 학습의 원시 로그3개(6.10GiB)를 삭제했다. 모델·요약·그래프·영상은 보존했으며 삭제 원시 로그를 사용하는 상세 재분석은 불가능하다. [정리 내역](docs/maintenance/storage_cleanup_20261030/result.json).

과거 버전별 장문의 상태·검증 기록은 [정리 전 상태 기록](docs/archive/document_cleanup_20261030/before/CURRENT_STATUS.md)에 보존했다. 그 문서의 ‘현재’·‘최신’은 각 기록 당시를 뜻한다. 더 많은 자료는 [문서 색인](docs/DOCUMENT_INDEX.md)을 따른다.
