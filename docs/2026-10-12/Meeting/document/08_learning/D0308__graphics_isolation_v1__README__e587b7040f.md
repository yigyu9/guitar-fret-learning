# 학습 그래픽 분리와 오류 예방

기존 long_on_v1은 NVIDIA EGL 라이브러리 내부 SIGSEGV(-11)로 종료됐다. 카메라 없는 학습에서도 wrapper가 graphics0을 강제했던 경로를 확인했다. 이 위치만으로 드라이버 자체 결함을 확정하지 않는다. 새 학습은 graphics−1, 영상 평가는 별도 프로세스의 graphics0을 사용한다. 기존 물리·제어·보상·스트랩·두 baseline과 checkpoint의 수치는 유지한다.

[구현 계획](/home/ajou/yigyu/3/stability_adapter_2/GRAPHICS_ISOLATION_PLAN_V1.md:1) · [사전 코드 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/review_preflight_v1.md:1) · [진단 v2 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/review_probe_v2.md:1).

## 완료한 검증

- CPU9검사: 학습−1/평가0의 실제 인자 전달, 학습 렌더 조회 차단, ABI·기존 source·PPO 설정 변경 거절, checkpoint 수치 보존.
- 첫 진단은60회 초기화에 성공했으나 비교용 reference JSON을 학습 ABI 목록에 포함해 checkpoint 이행 단계에서 거절됐다. 물리 진행·PPO 갱신은0회이며 원본 실패 자료를 보존한다.
- 새 진단은 학습 ABI와 감사 입력을 분리했다. 60회 graphics−1 초기화 모두 기준 초기 상태와 PD가 exact 일치했다. 이어서 같은 CP241의16.3667초 전체 에피소드에서 기존 graphics0 평가와 trace983개·controls982개가 exact 일치했다. 기타 위치/xyzw quaternion·관절각·속도 최대 기록 차이는 모두0이었다. 입력 SHA와 종료코드0을 확인했다.

[첫 진단 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/reset_probe_v1/report.json:1) · [새 진단 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/reset_probe_v2/report.json:1) · [전체 궤적 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/reset_probe_v2/comparison.json:1).

## 저장과 한계

공식 checkpoint/전체 영상은30분 간격을 유지하고, 별도 복구용 checkpoint는5분마다 model/Adam/RMS/RNG/counters를 저장하도록 구현했다. 복구용에는 영상 평가를 붙이지 않는다. 저장은 rollout 완료 뒤 이루어지므로 동기식 평가 등의 대기로 예정 간격보다 늦을 수 있다. 새 학습 진입은11:40에 협조적으로 차단하며 native 호출의 강제 선점은 아니다.

SIGSEGV는 Python 예외로 복구할 수 없다. 이번 분리는 학습의 불필요한 그래픽 컨텍스트 경로를 제거하고, 영상 평가 오류로부터 저장된 학습 결과를 보존하는 예방책이다. 유한 반복 검사이며 모든 드라이버/native 오류의 재발 방지를 보장하지 않는다. 학습 품질과 음악 성공은 별도의 평가 항목이다. 최종 CUDA/영상/복구 저장 결과는 이후 항목으로 추가한다.


## CUDA 및 전체 영상 검증

CP241→242 실제1갱신/256transition을완료했다. 이행 checkpoint와초기재저장의모델·Adam·RMS·RNG·counter가원본과exact일치했다. 정책KL은0.01990470476448536으로0.02이하이며RMS는고정됐다. 초기·갱신평가는각982제어/3928물리step/16.3667초를완주했고각2개492frame영상(16.4초)을만들었다. 두baseline의동결과각862실제추론,13×3928strap호출,nominal/residual/rate/모델한계,금지API0과초기/종료프레임을확인했다. [검증원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verification_v1.json:1).

음악성공은0/42이며CP242 위치box밖46.64%·최대47.11cm·평균9.45cm,초기기타대비최대SO(3)95.66°다. CP241은각47.05%·43.12cm·8.64cm·90.20°였다. 밖에머문시간비율은소폭줄었으나최대이탈은커져일관된개선을확인하지못했다. 위치는현재actor-root box판정,회전은초기자세대비거리이며바디중심자연스러움인증이아니다. [CP86/241/242분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/progress_analysis_v1.json:1).


## 이미지·영상 보관

초기·2초 준비·전체 종료 장면의 실제 Isaac Gym 프레임과 설명은 최신 그림 정정이 끝난 뒤 아래에 연결한다. 기존 그림 v2의 한글 캡션 글리프 누락을 확인하여 원본은 보존하고 한글 폰트로 새 v3를 만들고 있다. v2 README의 render0 및 probe순서 표현도 원문을 보존한 별도 정정본으로 명확히 했다.

이전CP157·CP241과이번초기/CP242의완료영상10개는원본SHA와대조해 [영상모음V4](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V4.md:1)에보존했다. 새로운 장기 실행의 영상은별도 `video/graphics_long_v1/<평가label>/`에자동복사하며manifest에원본/보관SHA와완주/부분종료를명시한다. 실행중소스·입력자료는동결한다.


최신 [한글 이미지·영상 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v3/README.md:1)에서 초기·2초·종료 장면을 함께 볼 수 있다. 실제 native 프레임의 같은 시점이며 인공지능으로 생성한 장면이 아니다. [보존 예외·정정 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/PROVENANCE_NOTE_V1.md:1)에 probe·한글 글리프·표현 정정과 동일 바이트의 매니페스트 재기록을 공개했다.


## 최종 확인 상태 — 2026-10-12 10:52–10:53 KST

CP242 strict resume의 초기model/Adam/RMS/RNG/counter가원본과exact일치했고초기전체평가의trace/controls도직전CP242와exact일치했다. 실제전체영상2개가 [자동보관초기평가](/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/initial_000000/README.md:1)에복사됐으며SHA가일치한다. 첫5분복구용CP257/65792transition은10:52:25에실제저장됐고로그counter·ABI/PPO설정·RMS불변을확인했다. 10:52:56스냅샷은CP258/66048transition까지완료한행을포함한다. [재개·복구검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/resume_verification_v1.json:1).

이 항목이 이번 작업의 최신 확인 상태다. 위의준비문단과영상색인의복구확인중표시는각문서작성시점의기록이다. 최신 [영상색인V5](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V5.md:1)는V4영상10개+새초기영상2개를연결하고이전V1–V3도보존한다. [변경파일·실제줄번호V1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/CHANGED_FILES_V1.md:1)의SHA는색인작성시점값이며최종파일SHA는root최종감사에고정한다.

그래픽없는학습은계속실행중이며5분복구저장·30분공식checkpoint/전체영상·11:40학습cutoff를유지한다. 장기학습로그는계속증가하므로최종감사는완료된prefix/첫복구checkpoint/첫영상만봉인하고이후결과나마감완료를선언하지않는다. 오류예방은확인했지만향후SIGSEGV완전방지와음악성공은인증하지않는다.


영상 목록의 최신본은 [V6](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V6.md:1)이다. 물리 구간16.366667초와492frame/30fps의영상재생16.4초를구분하며첫복구검증기록을연결한다. 루트의최종보존감사는완료자료와고정로그prefix만봉인한다. 실행중 `long_on_v1.log`·`supervisor_long_v1.log`·장기출력디렉토리전체는변경가능한운영자료로봉인목록에서제외한다.
