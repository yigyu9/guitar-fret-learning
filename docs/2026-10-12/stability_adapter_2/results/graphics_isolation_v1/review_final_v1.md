# 그래픽 분리·첫 복구 저장 최종 독립 검수

요약 판정: **문제없음(아래 유한 검증 범위)**. Critical 및 미해결 기능 오류는 없다. 원자료·체크포인트·소스·문서·그림·보관 영상의 SHA를 읽기 전용으로 대조했다. 진행 중인 장기 학습의 최종 완료·음악 성공·영구적인 무충돌은 인증하지 않는다.

## 완료 범위

- 실제 A 6개 소스와 계획은 [실행 전 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/source_before_native_v1.json:1)과 일치한다. 학습 graphics −1·기록 평가 graphics 0의 분리 외 기존 native81 제어·물리·보상·nominal/residual/rate·고정 하체·스트랩·동결 Fret/Strike 계약은 유지한다. 체크포인트 이관은 기존 ABI core와 source SHA 동일성 및 정확한 6파일 추가만 허용한다.
- [완료 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verification_v1.json:1)의 입력 39개 SHA를 확인했다. probe v2의 60회 reset 후 trace983개·controls982개 전체값과 기존 CP241 자료가 같으며, 새 recorded 초기 평가도 원본과 bytes가 같다. CP241→adopted/initial 체크포인트의 모든 비메타데이터(model/Adam/RMS/RNG/counters 등) exact를 직접 확인했다. 실제 CP242/61,952 전이·추가 1갱신/256전이, Actor/Critic 변경·RMS 불변·KL 0.0199047048을 확인했다.
- 초기·갱신 평가는 각각 16.3667초·982제어/3,928물리 단계, 두 baseline 각862추론, 스트랩 13×3,928호출, 금지 API 0·안전 종료 없음과 각 영상2개를 기록했다. target 한계 및 float32 2ULP를 반영한 rate 검사와 native 상태 검증의 범위를 구분했다. 음악 성공은 양쪽 0/42이며 완주를 연주 성공으로 해석하지 않는다.
- [진행 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/progress_analysis_v1.json:1)의 입력 13개 SHA와 문서 수치를 대조했다. CP241→242의 범위 밖 비율 47.04684→46.63951% 감소와 최대 거리 0.431175→0.471120m·평균 거리 0.086390→0.094476m·최대 초기 대비 SO(3) 90.20247→95.66406° 악화를 함께 설명하는 것이 맞다. 위치는 actor-root world box, 회전은 초기 quaternion 대비 거리이며 바디 중심 자연스러움 인증이나 scalar 관절각이 아니다.
- [v3 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/cp241_cp242_native_frames_v3.png)를 실제로 열어 0·2·16.3667초 전신/손 프레임 12개와 한글 글리프·캡션을 대조했다. 말미 기타 이탈이 드러나며 성능 개선을 주장하지 않는다. [v3 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/provenance_v3.json:1)의 입력/출력 51개 현재 SHA와 기록된 전후 동일성을 확인했다. V4 영상10개·14,685,510bytes의 원본/사본 SHA 및 총량도 일치했다.

## 재개·복구 저장

[재개 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/resume_verification_v1.json:1)의 17검사·입력21개 SHA, CP242 strict resume 초기 checkpoint의 원본 SHA, 초기 full trace/controls 동일성과 자동 보관 영상2개의 SHA를 확인했다. 첫 복구 checkpoint는 **10:52:25 KST의 CP257/65,792 전이**이며 SHA는 `f89c979e834d6a457a919903284f636a3dcb93dd96000a1164fd865d272e2f98`다. ABI/config/RMS 및 저장 counter와 로그의 대응이 맞다. [고정 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/training_prefix_at_recovery_v1.jsonl:1)는 갱신243..258·마지막66,048전이를 포함하고 live 로그의 prefix로 유지된다. 이후 갱신은 이 검수 범위 밖이다.

기존 입력1158개를 직접 SHA 대조했고 허가된 main append 예외는 원문 snapshot prefix로 확인했다. [main4 추가 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/main_append_resume_v1.json:1)의 이전/이후 SHA와 prefix 및 재개 input closure1165개도 일치한다. [보존 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/preservation_verification_v1.json:1)의 범위와 부합한다.

## Warning·보존 예외

- 최초 probe의 잘못된 audit/학습 ABI 혼합과 영상 전용 control 필드 불일치는 별도 진단 및 수정으로 해결했고 원본 실패 자료는 보존했다. render 조회 0회와 graphics device0의 문서 모호함·한글 글리프 실패는 별도 v3에서 정정됐다.
- [v3 producer:68](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/build_assets_v3.py:68)은 기존 V4 manifest를 재기록했다. 이는 기존 파일을 쓰지 않는 소유권 조건의 예외이며 [보존 예외 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/PROVENANCE_NOTE_V1.md:7)에 공개됐다. v2 기록과 현재 SHA `2f1ef5aa65d8bc0b248cdc69bd755e3e6d0800a14bcac4c256d6d9637e7ef741`는 동일하고 영상도 그대로지만, ‘기존 파일에 전혀 쓰지 않았다’는 판정은 하지 않는다. 이 producer를 재실행하지 않고 후속 그림과 보관 작업을 분리한다는 조치가 맞다.
- V4 색인의 이전 v2 링크는 [최신 V6 색인:9](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V6.md:9)에서 v3로 보완됐다. V5의 재생 시간 표현도 [V6:13](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V6.md:13)에서 물리16.366667초/MP4 16.4초로 구분됐다. V5는 보존됐으며 V6 SHA는 `470ca7177340d2c6e51e5f08bd27b3f999a7704f9d4c5909a33e5d722db4ba54`다.
- 5분 복구·30분 공식 저장은 갱신 완료 뒤 수행되는 예정 간격이고 11:40 cutoff는 협조적 검사다. native 호출의 강제 선점·미래 무충돌·향후 음악 성공 또는 전체 영상 재생/학습 품질을 인증하지 않는다.

검수자는 추가 native·정책 학습을 실행하지 않았으며 소유한 이 새 리뷰 외 파일을 변경하지 않았다. source_final·inventory·최종 봉인은 root의 후속 작업이다.
