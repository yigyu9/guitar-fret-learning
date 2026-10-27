# 병렬 수집 완료 독립 검수

요약 판정: **문제없음(유한 실행·표기 정정 완료 범위)**. Critical·미해결 기능 오류 없음. 추가 native·학습 실행 없이 코드·체크포인트·로그·문서·실제 PNG·영상 SHA를 읽기 전용으로 대조했다.

## 확인 결과

- [소스 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/source_before_native_v1.json:1)의 신규6파일+계획 SHA는 현재와 일치한다. spawn worker의 Isaac→Torch import, 프로세스별 native/전역 patch 격리, 생성 실패 정리·EOF/timeout 시 불완전 rollout 거절, final observation critic 이후 done worker만 reset하는 계약을 확인했다. 기존 물리·native81·PD·보상·스트랩·두 동결 baseline 및 `[T,N]` GAE/latent log_prob·RMS 고정·전체 rollout KL guard를 유지한다. 실제 worker 강제 장애 복구를 별도 시험한 것으로 해석하지 않는다.
- [검증 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/verification_v1.json:1)의 22검사·입력24개 SHA를 확인했다. N2는 초기 native exact·실제 scalar q 차이·각5초/1200물리·금지0·원본 스트랩 호출을 검증했다. CP315→316의 N4/T64 실제 CUDA1갱신은 256표본·KL0.01990500465·RMS 고정이며 모델/Adam/RMS/RNG/counter 이관을 보존했다. 초기 물리 노이즈 false와 무차원 latent std(몸통/머리 약0.006738, 팔/손가락 약0.018315)는 서로 다른 양이다.
- [완료 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/completion_verification_v1.json:1)의 14검사·입력26개 SHA가 일치한다. CP316 strict 초기 checkpoint의 비메타데이터 exact와 최종 ABI/config/RMS 및 CP320/84,992전이를 직접 확인했다. 종료 코드0·보관 오류0이다. production 로그는 갱신317..320의 4×1024=4096표본으로 최종 로그와 고정 prefix bytes가 같고, KL은 모두0.02 이하다. 네 worker의 982제어 full horizon 종료/음악0과 reset 경계가 로그에 있다.
- 생산 평균 수집+최적화 처리량36.5024표본/초와 첫 수집44.1943표본/초는 실측값이다. PREP 전용 smoke의57.5069 및 다른 CP·데이터의 단일 환경14.8839와 통제된 속도 개선으로 비교하지 않는다. 짧은 실행에서 생산 복구 checkpoint는0개였고 최종 CP320은 보존됐다.

## 품질·산출물

대표 단일 환경의 CP316/320 초기·마감 평가는 각각16.3667물리초·982제어/3928물리 단계·492프레임이며 MP4는16.4초다. 각 스트랩 호출은51,064=13×3928, 금지 API0·baseline 동결·안전 위반 없음, 음악 성공0/42다. 재계산한 위치 상자 밖 비율59.77597→55.19348%와 최대 초기 대비 SO(3)93.93445→91.21340°는 줄었으나 최대 외부 거리0.304489→0.339885m·평균0.058226→0.084887m는 커졌다. 안정화·음악 성공·일반화 개선으로 판정하지 않는다. 위치는 actor-root world box이고 회전은 초기 기타 quaternion 대비 거리다.

CP315/316 및 CP316/320 PNG 두 개를 실제 열어 한글·0/2/끝시점·전신/손·대표1환경 범위와 말미 기타 이탈을 대조했다. 두 provenance의 입력/출력 각50개 SHA·기록된 전후 불변을 확인했다. validation 영상4개/5,985,463bytes와 production 자동 보관2쌍의 원본/사본 SHA가 일치한다. main4의 세 단계 snapshot prefix 보존과 최종 변경 색인의 절대 링크·실제 행을 확인했다. 과거 미저장316..319를 새 병렬 갱신316으로 복원했다는 주장은 하지 않는다.

## Warning — 해결 기록·범위

원본 산출물의 GPU번호/스트랩13회·물리0회/마감 update1140 표현은 [초기 설명 정정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v1/README_V2.md:1)과 [최종 설명 정정본:16](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v2/README_V3.md:16)에서 원문 보존 후 바로잡았다. V7의 이전 설명 링크는 [최신 V8](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V8.md:1)에서 정정본으로 연결한다. V8 SHA는 `653e37fb5872dc4a8a96b7fe605e23e3ceb5afb100b7b7f5e738aa348faa8ec4`, 최종 PNG SHA는 `b49d9bc0f321d100595369e128da6d33953e144fc46448fd8d4961234e56c141`다.

11:40은 협조적 학습 cutoff이며 강제 선점이 아니다. 이번 판정은 설정된 실행과 후속 전체 영상 평가 완료에 한정한다. 장기 목표 달성·미래 무충돌·음악 성공을 인증하지 않는다. 소유한 이 새 리뷰 외 파일을 수정하지 않았으며 최종 source_final/inventory/봉인은 root의 후속 작업이다.
