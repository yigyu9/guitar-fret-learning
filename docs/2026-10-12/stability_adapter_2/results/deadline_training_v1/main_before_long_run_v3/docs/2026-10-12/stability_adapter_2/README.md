# StabilityAdapter 2 결과·산출물

이 디렉토리에는 검증 결과·분석·로그·영상과 산출물 정리를 저장한다.
메인 계획·구현·설정·구현 설계는 프로젝트의 `stability_adapter_2/`에 둔다.
전체 연구 방향은 [전체 메인 계획](/home/ajou/yigyu/3/master_plan/README.md:14), 이 파트의 실행은 [허용 범위 안에서 자유 기타 연주 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)을 따른다.
이미지·영상과 설명은 [누적 결과 문서](VISUAL_REPORT.md)에 모은다. 작업 단위가 끝날 때마다
새 단계의 이미지 또는 영상·조건·설명·수치·판정·미검증 항목을 추가하며 이전 기록은 보존한다.

## 현재 요약 — 2026-10-10

Root/하체 고정·자유 기타에서 개별 Fret·Strike 체크포인트 연결과 최소2초 준비 후 원본 첫 done까지 native 영상 기록을 완료했다. 양손 통합·학습 보정·지속 연주 성공은 미완료다. 스트랩은 ON/OFF 비교 변수다.

- [Fret 손가락/팔 목표 분리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md:1): 초기 이탈은 줄었으나 압현0%, finger_back 실패.
- [기존 길이 스트랩 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md:1): PLAY 계산 장력0N, 압현0%. 첫 native crash는 보존했으며 원인은 미확정.
- [Strike 2초 전환](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md:1): 적시 타현1회, 잘못된 타현4회로 실패. 완주 결과가 아님.

다음 소단계는 현재 기타 기준 왼손 손목·목표 프렛 오차와 접촉면 시각화, 제한된 팔 보정으로 한 음의 압현·유지 검증이다. 아래 초기 환경·과거 경과는 당시 상태의 기록이며 현재 상태와 구분한다.

## 초기 환경 산출물 — 과거 기록

| 파일 | 내용 | 검증 범위 |
|---|---|---|
| [asset_import_audit.json](analysis/asset_import_audit.json) | 공용 모델 질량·관성·관절 한계의 로더 readback | CPU 자산 로드 |
| [source_comparison.json](analysis/source_comparison.json) | 원본 스트랩 비교·기타 좌표·출처 hash snapshot | 소스 분석·좌표 계산 |
| [asset_import_audit.log](logs/asset_import_audit.log) | 자산 로드 원문 로그 | GPU 미탐지·visual geom 오류 포함 |
| [v1 report](results/initial_environment_v1/report.json) | 초기 준비 단계에서 기타가 0.17mm 이동한 실패 기록 | 초기화 실패; 보존 |
| [v2 report](results/initial_environment_v2/report.json) | 준비 후 1회 초기 pose 복원 | 초기화 검사는 통과했으나 native effort 미적용; 안정성 비교 제외 |
| [v3 report](results/initial_environment_v3/report.json) | CPU native solver PD·COM 기준 점 속도 적용 | 초기화 검사 16개 통과; 안정성 성공 아님 |
| [v3 trace](results/initial_environment_v3/trace.json) | 첫 자유 step 이전부터 0.1초까지 상태·오차·경로 기록 | 60Hz 기록, 240Hz 물리 |
| [v3 run log](results/initial_environment_v3/run.log) | 최신 환경 초기화·짧은 실행 원문 | GPU 미탐지·visual geom 오류·native 경고 포함 |
| [v3 tests log](results/initial_environment_v3/tests.log) | 단위 검사 4개·native 통합 검사 2개 | 총 6개 통과; 실제 관절 응답·COM 속도 확인 |
| [v3 review](results/initial_environment_v3/review.md) | 별도 change-reviewer 최종 검수 | CPU 초기화·계약 범위; Critical/Warning/Suggestion 없음 |
| [VISUAL_REPORT.md](VISUAL_REPORT.md) | v3 기타 오차·몸통 drift·스트랩 그래프 3장과 설명 | 기존 trace 시각화; 실제 장면 렌더 없음 |

기타 로드 질량은 4.6487kg이고 공용 시작 자세의 neck elevation은 22°다.
과거 source hash는 당시 snapshot으로 보존한다.

## 첫 환경 결과: v3

사람 root/Pelvis는 고정, 기타 root는 자유·중력 ON이다. 양쪽 Thorax부터 손가락까지
66관절이 주 제어 대상이며 Torso/Spine/Chest 9관절은 초기 PD 목표를 유지한다.
하체와 Head/Neck도 기준 목표를 유지하되 매 프레임 관절 상태를 덮어쓰지 않는다.
공용 좌식 양손 H0와 preload 없는 S0를 사용했다. 스트랩 rest length는 첫 step 전
native FK 경로의 **1.089185175m**로 고정한다. 동적 길이 조절·양손 안정화 feedback·학습은 없다.

공용 gain/cap 값을 쓰는 **CPU native POS solver PD**로 실행했다. 공용 tensor hybrid PD와
수치적 actuator가 다르며 GPU 환경의 유지 성능으로 일반화하지 않는다.
충돌 readback에서 thumb pad/proxy와 pluck-range의 filter=3을 확인했다.
이는 사람-기타 간 해당 marker 충돌을 제외하는 설정이며 모든 접촉 제거를 뜻하지 않는다.

| 지표 | 첫 자유 step 전 | 0.1초 뒤 |
|---|---:|---:|
| 초기 목표 대비 위치 오차 | 0.000028mm | 65.315mm |
| 초기 목표 대비 회전 오차 | 0.0000145° | 7.318° |
| 기타 COM 선속도 | 0m/s | 1.594m/s |
| 기타 각속도 | 0rad/s | 3.657rad/s |
| 몸통 9관절 최대 절대 drift | 0° | 1.093° |
| 스트랩 경로 길이 | 1.089185m | 1.035838m |
| 마지막 적용 장력 | 0N | 0N |

위 위치는 기타 body-origin 기준이며 선속도는 COM 기준이다. 장력은 마지막 물리 tick에서
적용한 값이다. 기타가 움직이면서 경로가 짧아져 S0 스트랩이 느슨해졌지만,
초기 관통이나 접촉 반발이 원인인지 아직 확인하지 못했다. gain을 바로 키우기보다
초기 장면·접촉·양손 배치를 검토한 뒤 지지 후보와 길이를 비교한다.

native 응답 검사에서 오른쪽 팔꿈치 목표 +0.02rad는 무보정 trial 대비 실제 q를
0.001205rad 증가시켰다(1 control step). offset-COM box 검사에서 API linear velocity=0인데
몸체 원점은 약 -0.199925m/s로 이동했다. 이에 맞춰 점 속도의 회전 레버를 COM에서 계산한다.
v2의 작은 오차(9.438mm·0.485°)는 별도 토크가 적용되지 않은 결과여서 제어 효과로 해석할 수 없다.

검증 범위는 초기 상태·목표 연결·native 계약과 짧은 실행이다. 실제 토크·포화,
초기 배치 렌더·관통/접촉 품질·10초 정지 안정성·작은 손/팔 움직임·연주 호환은 미검증이다.
현재 NVIDIA 드라이버 통신 실패로 영상/렌더 결과는 없다. 몸통의 작은 목표 보정은
사용자 답변에 따라 첫 장면 검토 후 결정한다.

후속 실험은 고유 run ID로 결과를 저장하고, 실행 조건·목표 pose·제어 범위·오차 지표·
실패 원인·영상 경로를 정리한다. 메인 계획서를 이 디렉토리에 중복 저장하지 않는다.

## 이번 구현 파일과 VS Code 확인 위치

링크는 프로젝트의 절대 경로와 실제 1-based 줄 번호다. 첫 CPU 구현에서 추가/갱신한 파일을 정리한다.

| 파일·확인 위치 | 변경 내용 |
|---|---|
| [PLAN.md:5](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:5) | 현재 상태·몸통 목표 유지·66관절 범위·P1a 체크리스트 |
| [README.md:114](/home/ajou/yigyu/3/stability_adapter_2/README.md:114) | CPU 구현 안내·실행 방법·후속 인계 |
| [__init__.py:1](/home/ajou/yigyu/3/stability_adapter_2/__init__.py:1) | 새 패키지 진입점 |
| [config.json:1](/home/ajou/yigyu/3/stability_adapter_2/config.json:1) | 공용 자산·제어 주기·원본 스트랩 설정 |
| [control.py:11](/home/ajou/yigyu/3/stability_adapter_2/control.py:11) | 이름 기반 66관절 범위·몸통 목표 유지·한계 검사 |
| [environment.py:35](/home/ajou/yigyu/3/stability_adapter_2/environment.py:35) | 자유 기타 초기화·native solver PD·물리 step |
| [strap.py:11](/home/ajou/yigyu/3/stability_adapter_2/strap.py:11) | COM 기준 점 속도·원본 경로 장력/반작용 |
| [run_initialization.py:33](/home/ajou/yigyu/3/stability_adapter_2/run_initialization.py:33) | 초기화 감사·짧은 실행·결과 저장 |
| [test_physics_contract.py:10](/home/ajou/yigyu/3/stability_adapter_2/tests/test_physics_contract.py:10) | 제어 범위·입력·힘/모멘트·장력 단위 검사 |
| [test_native_contract.py:9](/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:9) | 실제 목표 응답·native COM 속도 계약 검사 |
| [결과 README.md:28](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:28) | 실행/실패 이력·수치·한계·변경 파일 정리 |
| [review.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_environment_v3/review.md:1) | 최종 검수 기록 |

새 run별 report.json·trace.json·run.log와 v3 tests.log는 위 산출물 표에 연결했다.
기존 stability_adapter 및 그 보호 대상 계획·결과 87개 파일은 수정하지 않았다.

## 이미지 문서화 단위의 추가·갱신 파일

| 파일·실제 확인 위치 | 내용 |
|---|---|
| [VISUAL_REPORT.md:17](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:17) | 이번 v3 결과 이미지 3장·설명·수치·판정·출처 |
| [plot_initialization.py:13](/home/ajou/yigyu/3/stability_adapter_2/plot_initialization.py:13) | 기존 trace/report로 PNG 생성; 원본 데이터·물리 환경 변경 없음 |
| [PLAN.md:486](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:486) | 이미지 누적 문서화 계획·체크리스트 |
| [작업 README.md:94](/home/ajou/yigyu/3/stability_adapter_2/README.md:94) | 작업마다 이미지와 설명을 누적하는 규칙·후속 인계 |
| [결과 README.md:6](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:6) | 누적 문서 연결·산출물 목록·변경 위치 |

PNG 절대 경로는 누적 문서의 각 이미지에 포함되어 있다. 문법·링크·PNG 파일 검사를 통과했고,
별도 change-reviewer가 3개 이미지를 직접 확인하고 원본 수치와 대조해 문제없음으로 검수했다.

## 핵심 목표 재확인 시 변경 위치

- [PLAN.md:10](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:10): 초기 humanoid·strap 조합 선정 → 같은 초기 조건에서 오차 보정·유지.
- [작업 README.md:3](/home/ajou/yigyu/3/stability_adapter_2/README.md:3): 가장 중요한 목표와 인계 프롬프트 갱신.
- [누적 기록:136](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:136): 핵심 목표·미달성 범위·후속 비교 조건 기록.
- 이 결과 README는 변경 위치와 이동한 줄 번호를 갱신했다. 새 물리 실험·미디어 생성은 없다.

별도 change-reviewer가 초기 자세/길이 비교의 절대 rest length 일치와 feedback OFF/ON 조건을 검토했다.
최종 판정은 Critical/Warning/Suggestion 없음이다.

## 최소 자세 제약 검토 시 변경 위치

| 파일·실제 확인 위치 | 내용 |
|---|---|
| [POSTURE_CONSTRAINTS.md:9](/home/ajou/yigyu/3/stability_adapter_2/POSTURE_CONSTRAINTS.md:9) | 최소 제약 5개·법선 정의·왼손 초기 방향 사용자 확인·적용/검증 순서 |
| [PLAN.md:501](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:501) | 최소 자세 제약 검토 연결과 확인 범위 |
| [작업 README.md:177](/home/ajou/yigyu/3/stability_adapter_2/README.md:177) | 사용자 확인 기준과 나머지 제안의 구분 |
| [누적 기록:150](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:150) | 제안·사용자 선택·runtime 미적용 기록 |
| [결과 README.md:114](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:114) | 이번 변경 위치 정리 |

새 자세 제약의 실제 적용·물리 실험·미디어 생성은 없다. 기존 v3와 보호 대상 실험 파일은 보존한다.
문서 링크·v3 source hash·보호 대상 87개 파일을 확인했고, 별도 change-reviewer의 최종 판정은
Critical/Warning/Suggestion 없음이다.

## 2026-08-19 자료 검토 산출물·변경 위치

| 파일·실제 확인 위치 | 내용 |
|---|---|
| [POSTURE_CONSTRAINTS.md:68](/home/ajou/yigyu/3/stability_adapter_2/POSTURE_CONSTRAINTS.md:68) | 손 분포와 상지 모델 한계의 활용·제약 설계에 주는 의미 |
| [PLAN.md:510](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:510) | 자료 검토 계획·완료 체크리스트 |
| [VISUAL_REPORT.md:161](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:161) | 원본 이미지 사본 3장과 설명·한계·활용 순서 |
| [historical_20260819_review.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/analysis/historical_20260819_review.json:1) | 원본 hash·33관절 한계 비교·렌더 각도 불일치·자료 범위 |

이 결과 README에도 산출물과 변경 위치를 추가했다. PNG 절대 경로는 누적 문서에 포함한다.
원본 49개 자료 파일과 기존 실험 보호 대상 87개 파일은 보존되었다. 새 runtime·물리 실험은 없다.
별도 change-reviewer 최종 판정은 Critical/Warning/Suggestion 없음이다.

## 초기 겹침 진단 산출물·변경 위치

`initial_overlap_v2`에서 전신 54개·기타 26개 활성 형상의 1,404쌍을 검사했다.
R_Hip–G:body 음수 후보 1쌍을 검출했으며 검사 전후 native 상태는 같고 추가 step은 0이다.
음수 크기를 실제 관통 깊이로 해석하지 않는다. PhysX 형상과 대조 전인 CPU 보조 진단이다.

| 파일·실제 확인 위치 | 내용 |
|---|---|
| [INITIAL_STATE_DIAGNOSTICS.md:1](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_STATE_DIAGNOSTICS.md:1) | 반복 실험 계획·검증·판정 한계·다음 단위 |
| [PLAN.md:520](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:520) | 메인 계획에 초기 배치 검사 연결 |
| [작업 README.md:183](/home/ajou/yigyu/3/stability_adapter_2/README.md:183) | 실행 명령·7개 검사 환경·미구현 범위 |
| [initial_overlap.py:9](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:9) | native pose에서 활성 XML 형상 구성 |
| [initial_overlap.py:56](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:56) | 전신–기타 쌍 query·부호·가까운 점 기록 |
| [run_initial_overlap.py:11](/home/ajou/yigyu/3/stability_adapter_2/run_initial_overlap.py:11) | CPU 형상 진단 이미지 생성 |
| [run_initial_overlap.py:64](/home/ajou/yigyu/3/stability_adapter_2/run_initial_overlap.py:64) | native 상태 보존·활성 수 대조·JSON·hash 저장 |
| [test_initial_overlap.py:8](/home/ajou/yigyu/3/stability_adapter_2/tests/test_initial_overlap.py:8) | 상자 분리/접촉/관통/검색 범위 회귀검사 |
| [VISUAL_REPORT.md:248](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:248) | 이미지·설명·결과·해석 한계 누적 |

증거는 [v2 JSON](results/initial_overlap_v2/report.json), [로그](results/initial_overlap_v2/run.log),
[검사 로그](results/initial_overlap_v2/tests.log), [그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/initial_overlap_v2_geometry.png)이다.
v1의 실패 이력은 [이전 검사 로그](results/initial_overlap_v1/tests.log)에 보존한다.
설정별 초기 관절각/길이 입력·runtime gate·자동 reset/controller는 다음 단위로 남겨두었다.

검증: 7개 테스트·문법·문서 링크·source hash·이미지 일치와 기존 87개/과거 자료 49개 보존 확인.
별도 검수자가 테스트와 query를 독립 재현했다. CPU 정적 보조 진단 범위에서
Critical/Warning/Suggestion 없음이다. [검수 기록](results/initial_overlap_v2/review.md),
[보존·문서 검증](results/initial_overlap_v2/validation.json).

## 넥–손바닥의 국소 높이 이미지·변경 위치

실제 초기 상태 H0의 native pose를 읽어 대응 단면을 표시한 그림과, 같은 기타에서 가상점을
사용한 설명 그림을 분리했다. H0 palm 중심의 대응 중심선 높이 차는 -109.349mm,
중심선까지의 3D 거리는 129.612mm다. 높이 조건만으로 좋은 지지 자세라고 판단하지 않는다.
설명용 가상점의 10mm는 제어 목표/허용치로 채택하지 않았다. 자세·controller·gate는 변경하지 않았다.

| 파일·실제 확인 위치 | 내용 |
|---|---|
| [POSTURE_CONSTRAINTS.md:98](/home/ajou/yigyu/3/stability_adapter_2/POSTURE_CONSTRAINTS.md:98) | 기준점·길이 투영·시각화 계획과 체크리스트 |
| [plot_neck_palm.py:12](/home/ajou/yigyu/3/stability_adapter_2/plot_neck_palm.py:12) | native pose의 원본 충돌 형상 구성 |
| [plot_neck_palm.py:33](/home/ajou/yigyu/3/stability_adapter_2/plot_neck_palm.py:33) | 대응 단면의 convex-hull 교점 |
| [plot_neck_palm.py:49](/home/ajou/yigyu/3/stability_adapter_2/plot_neck_palm.py:49) | 실제 3D 배치·길이/높이 그림 |
| [plot_neck_palm.py:107](/home/ajou/yigyu/3/stability_adapter_2/plot_neck_palm.py:107) | 실제 기타와 별도 가상점의 설명 그림 |
| [plot_neck_palm.py:135](/home/ajou/yigyu/3/stability_adapter_2/plot_neck_palm.py:135) | 초기 상태 읽기·투영·수치·hash 기록 |
| [작업 README.md:206](/home/ajou/yigyu/3/stability_adapter_2/README.md:206) | 실행 명령과 기준 연결 |
| [VISUAL_REPORT.md:310](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:310) | 이미지 2장·수치·범위·해석 |

산출물: [좌표 JSON](results/neck_palm_visual_v2/report.json), [실행 로그](results/neck_palm_visual_v2/run.log),
[실제 배치 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/neck_palm_visual_v2_native.png),
[설명 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/neck_palm_visual_v2_example.png).

문법·단면 계산·native 상태 보존·투영·source hash·문서 링크·이미지 사본·기존 87개/과거 49개 보존을 확인했다.
별도 검수자가 수치·좌표·단면을 독립 재현했고 국소 높이 시각화 범위에서
Critical/Warning/Suggestion 없음으로 판정했다. [검수](results/neck_palm_visual_v2/review.md),
[검증](results/neck_palm_visual_v2/validation.json).

## 실험 역할 문서화

실험 로그의 물리·수치 분석과 다음 후보 결정은 GPT-6.1 Sol 담당으로 기록했다.
승인 brief에 따른 표·그래프·캡션·누적 시각 보고서는 GPT-6 Luna 담당으로 기록했다.
역할과 검수 순서는 [workflow 합의](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:1)와
[프로젝트 README 역할 안내](/home/ajou/yigyu/3/stability_adapter_2/README.md:221)에 추가했다.
이번 문서화에서 새로운 물리 실험이나 이미지는 만들지 않았다.

문서 링크·줄 번호와 기존 실험 87개 및 과거 자료 49개 보존을 확인했다.
별도 change-reviewer 최종 판정: Critical/Warning/Suggestion 없음.

지속 반복 운영은 [workflow 합의의 지속 반복 운영 절](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:71)에 기록했다.
승인된 탐색 범위에서 반복하되, 중요한 조건 변경은 먼저 사용자에게 확인한다.
성공 기준과 중단/계속 선택은 아직 미합의이며, run 입력·batch·checkpoint 구현도 다음 작업으로 남아 있다.
이번 운영 규칙 문서화에서는 새 실험이나 이미지를 만들지 않았다.

## 후속 실행 결과: 입력 batch·접촉·PD·기타 Z 비교

이전 운영 규칙 기록 이후 입력 JSON·batch·checkpoint는 구현하고 검증했다.
[batch 계약 결과](results/batch_contract_v1/README.md),
[240Hz native 접촉 결과](results/physx_contact_v1/README.md),
[하체 PD/solver 14조건 결과](results/lower_body_pd_v1/README.md)를 별도 보존했다.
14조건은 초기 자세 이탈·관통 문제가 남아 안정 후보로 채택하지 않았다.
현재 native 환경의 기본 solver/gain·전신 초기각·기타 초기 목표는 baseline 그대로다.

사용자는 하체 초기각 보정 대신 기타 초기 Z 소폭 상승을 제안했다.
[정적 Z 비교](results/guitar_z_preview_v1/README.md)에서 +5mm가 허벅지/팔꿈치
source gap 3.303/4.208mm로 다음 권고 후보가 됐다. 실제 native 목표 적용은 사용자
확인을 요청했으며 아직 변경하지 않았다. strap route는 5.811mm 짧아지므로 기존
절대 rest length와 분리해 비교한다. 정적 형상 간격은 PhysX clearance 인증이 아니다.

[누적 이미지·설명 06–08](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:408),
[변경 파일의 절대 경로·실제 줄 번호](results/guitar_z_preview_v1/CHANGED_FILES.md),
[검증·원본 보존](results/guitar_z_preview_v1/protected_validation.json)을 따른다.
자유 기타 유지 feedback·작은 손/팔 움직임·연주 성능과 성공 기준은 후속 작업으로 남아 있다.

## 초기 목표 변경 대기 중 독립 hip/PD 진단

[독립 hip drive fixture 24조건](results/hip_drive_probe_v4/README.md)에서 3 hinge·−90°
초기각의 native POS 이탈이 외부 접촉 없이 약 4.2°로 재현됐다. 단일 hinge는 그대로
있었고 drive OFF는 매우 작은 raw 편차였다. 이것만으로 전체 humanoid의 원인을
확정하지 않는다. 실제 환경의 하체 초기각·한계나 기본 controller는 바꾸지 않았다.

[하체 damping-zero 두 조건](results/lower_kd0_v1/README.md)도 큰 하체 이탈이 남아
채택하지 않았다. PGS의 기타 오차가 19.908mm/3.551°로 줄어도 raw 하체 편차
99.455°가 남는 경우이므로 기타 오차만으로 좋은 자세를 고르지 않는다.
계획·구현은 `stability_adapter_2/HIP_DRIVE_PROBE.md`와 `run_hip_drive_probe.py`에,
그림·설명은 [누적 결과 09·10절](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:458)에 있다.

## 승인 후 기타 초기 Z +5mm 실제 비교

사용자가 실제 +5mm 시험을 승인했으며, 위 목표 변경 대기는 해소됐다. 동일 baseline에서
H0/+5mm를 각각 0.1초 실행했다. [실제 결과](results/guitar_z_trial_v1/README.md)와
[전체 비교](results/guitar_z_trial_v1/comparison.json)를 보존한다. source 초기 허벅지
겹침은 해소됐지만 두 조건 모두 0.05초 무릎–넥 접촉이 남아 정지 안정성 성공은 아니다.
올린 목표 기준 위치 오차와 공통 원본 위치 기준 오차를 분리해 기록했다.
그림과 설명은 [누적 결과 11절](VISUAL_REPORT.md)에 추가한다.

## 승인된 하체 초기각 소폭 보정 결과

기타 +5mm를 유지한 하체 유효 초기각의 기준 ±0.05rad 탐색을 사용자가 승인했다.
[101개 정적 평가와 3개 native 후보](results/lower_initial_pose_v1/README.md)를
보존했다. C02는 0.1초 기타 오차 7.174mm/1.591°와 무릎–넥 접촉 없음으로
개선됐지만, source 발 음수 gap 2개·실제 leg body 구간 최대 편차 116.689°가
남아 안정 자세로 채택하지 않는다. 그림·설명은 [누적 결과 12절](VISUAL_REPORT.md:498)에 있다.
원본 공용 자산·기존 결과는 보존하며 학습/feedback 설계보다 하체 자세 유지 문제를
우선 다룬다. 초기각 변경은 하체 연주 action 추가를 의미하지 않는다.

## 현재 방향: 하체 진단 보류, 초기 상체 자세와 스트랩 조합

위 하체 우선 후속 방향은 사용자의 새 지시로 보류했다. C02 하체 초기각과 실제 하체
물리는 유지하고, 기타 +5mm 목표·몸통9 PD를 유지한 상체·손/고정 초기 LA를 비교했다.
[33회 초기 조합 결과](results/pose_strap_v1/README.md)는 짧은 개선이 1초 유지로
이어지지 않았음을 보여준다. [누적 이미지·설명 13절](VISUAL_REPORT.md:514)에 그림을 추가했다.

사용자가 팔 초기각 ±0.3rad 확대를 승인한 뒤 source 손–넥 접근 159개와 10회 native
trial을 비교했다. 초기 근접과 경로에 맞춘 LA만으로 손 지지는 유지되지 않았다.
원거리 source query의 잘못된 부호를 사용한 첫 검색은 제외하고 실패 기록도 보존했다.
결과와 그림은 [손 지지점 접근 결과](results/hand_support_v1/README.md)에 누적한다.
메인 계획·구현은 프로젝트의 stability_adapter_2에 있으며, 다음
[관절 자세 유지 보정 설계](/home/ajou/yigyu/3/stability_adapter_2/JOINT_HOLD_RESIDUAL_PROPOSAL.md:1)는
아직 사용자 확인 전 제안이다. 능동 스트랩·기타 pose 덮어쓰기·학습을 추가하지 않았다.

위 제어 제안을 사용자가 승인했다. [관절 목표 보정 결과](results/joint_hold_v1/README.md)에
0.1/0.5/1초 OFF/ON을 기록한다. 1초 기타 오차264.207mm/48.065°→
196.035mm/33.994°와 팔 편차20.997→14.314°로 개선됐지만 LH 접촉0·큰
이탈·포화가 남아 안정 유지로 채택하지 않는다. 현재 joint-error 보정만 구현했으며
guitar-error feedback/FK 작업조건 rejection/변화율 제한/학습은 아직 없다.


## 하체 완전 고정 조건 — lower_body_fixed_v1

사용자 요청에 따라 기존 H0의 양쪽 Hip/Knee/Ankle/Toe를 물리적으로 고정한 별도 모델과
환경을 만들었다. 0.1초와 1초 실행에서 하체 8개 링크의 전체 pose/velocity 구조체가
모든 step에서 초기와 같았다. 기타는 자유이며 기존 상체 제어는 유지한다.
기타1초 최대 오차는149.372986mm/62.331933°로 이전 동적 하체보다 커졌으며,
이후 자세·strap 조정은 고정 하체 조건에서 진행한다.

[영상·이미지와 측정 설명](results/lower_body_fixed_v1/README.md),
[변경 파일과 실제 줄 번호](results/lower_body_fixed_v1/CHANGED_FILES.md),
[하체 고정 구현·검증 계획](../../../stability_adapter_2/LOWER_BODY_FIXED_PLAN.md),
[원본 보존 검사](results/lower_body_fixed_v1/preservation_verification.json)를 따른다.


## 양손 겹침 확인 — hand_hand_collision_audit_v1

대표0.5/0.670833/1초에 LH–RH source convex hull 교차가 확인됐다. 현재 양손은
공통 collision-filter bit로 native 충돌 처리에서 제외된다. 이 감사는 설정을 바꾸지 않았다.
[이미지와 검사 설명](results/hand_hand_collision_audit_v1/README.md),
[실제 변경 파일·줄 번호](results/hand_hand_collision_audit_v1/CHANGED_FILES.md)를 따른다.

## 오른쪽 허벅지·왼손 손바닥 초기 지지 접근 — thigh_palm_support_v1

하체 고정 상태에서 왼쪽 Wrist3+Elbow_x와 기타 생성 위치 약1.1mm를 조정한5회
짧은 비교를 기록했다. 후보의 오른쪽 허벅지 접촉은 첫 step부터 생겼지만 왼손
손바닥 접촉은 없고 초기 약2µm의 source 간격이 실행 중 벌어진다. 안정 자세로
채택하지 않는다. [초기·종료 이미지와 전체 짧은 영상](results/thigh_palm_support_v1/README.md),
[변경 파일·실제 줄 번호](results/thigh_palm_support_v1/CHANGED_FILES.md)를 따른다.

## Humanoid 내부 충돌 — self_collision_v1

양손/팔–몸통의 self-collision을 활성화하고 같은 손·연결부의 importer 제외를 유지했다.
동일0.1초 비교에서 native 사람 내부 접촉은0→9행(LH:palm–RH:index1), 양의 rawlambda는
6행이었다. 하체/root 고정과 기존 PD/PI·자유 기타·strap 조건은 유지했다.
[결과 이미지·영상](results/self_collision_v1/README.md),
[변경 파일·줄 번호](results/self_collision_v1/CHANGED_FILES.md)를 따른다.

## Isaac Gym native camera 초기 장면 — isaac_gym_camera_v1

사용자 요청에 따라 physics step 0의 초기 장면을 Isaac Gym native camera sensor로 저장했다. 앞선 MuJoCo source-geometry replay와 renderer를 구별한다. 전신과 손 visual image, 캡처 SHA는 [결과 안내](results/isaac_gym_camera_v1/README.md), [변경 파일 인덱스](results/isaac_gym_camera_v1/CHANGED_FILES.md)에 있다. 초기 이미지는 충돌 성공이나 안정성 인증이 아니며 strap은 화면에 나타나지 않는다.

## 왼손 finger seed·preload·palm feedback와 native camera — finger_grip_hold_v1

저장 trace 비교에서 0.5초 palm-feedback `v2` 기타 오차는 baseline보다 작았지만, 1초에도 오차가 남고 LH contact 기록은 0.545833초 이후 사라졌다. 0.30-rad cap은 최대오차 개선 없이 종료값만 조금 낮춰 채택하지 않았다. 안정화·연주 성공은 아니다. 실제 Isaac Gym native camera의 1초 전신·손 영상은 [0.2× 재생 영상과 비교표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/README.md), [변경 파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/CHANGED_FILES.md)에 있다. 이미지·영상 후처리는 저장된 카메라 frame만 사용했으며 native 실행을 추가하지 않았다.

## 파란 기타 neck 측면의 왼손 palm — palm_neck_side_v1

사용자가 요청한 neck 아래 측면 접근을 저장 native camera frame으로 비교했다. face-used neck facet을 향해 배치한 결과 첫 step에 LH:palm–guitar 네 contact point가 기록됐으나 raw lambda는 0이고 0.1초에는 접촉이 사라졌다. 안정적 지지 성공은 아니다. cyan target polygon은 저장 camera 이미지에 투영한 설명 overlay다. [비교 결과·제한](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/README.md), [산출물·source 경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/CHANGED_FILES.md:1).

## 파란 기타 측면 palm 추적 — palm_side_feedback_v1

OFF, startup bias, bounded palm-task tracking을 같은 짧은 조건에서 비교했다. 추적점 오차는 최대 71.910→49.466→48.324 mm로 줄었지만 첫 step의 네 palm 접촉행은 raw lambda 0이고 step 2–24에는 접촉이 없으며, 기타 최대 오차도 5.108 mm / 0.969°로 남는다. 손 추적 개선은 지속 지지나 기타 안정화 성공이 아니다. 저장 trace와 native camera 비교는 [phase 결과 및 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/README.md), 입력·출력 SHA와 실제 경로는 [파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/CHANGED_FILES.md)에 있다.

## 손바닥·파란 측면의 source 평면 정렬 — palm_plane_alignment_v1

저장 native pose에서 source facet의 법선각, signed normal gap, patch 중심까지의 접선 거리를 OFF/bias/tracking 0.1초에 걸쳐 기록했다. Tracking의 종료 측정은 4.750409°, 40.495078 mm, 26.445653 mm로, 작은 시작 간격만으로 유지 접촉을 말할 수 없다. normal-only controller는 구현·시험하지 않았다. [세 지표 그림과 측정 한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/README.md), [artifact 경로·SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/CHANGED_FILES.md)에 있다.

## 손바닥 법선 방향 제어 비교 — palm_normal_control_v1

0.1초 trace에서 normal-only 0.30 조건은 법선각·접선 거리, 0.50 조건은 추적점 최대오차가 상대적으로 작았지만 접촉 lambda는 모두 0이고 기타 오차도 동일했다. 유지 지지나 안정화 성공은 아니다. 기존 native camera frame과 저장 곡선은 [phase 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/README.md), [파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/CHANGED_FILES.md)에 정리했다.

## Palm support-weight 비교 — palm_support_weight_v1

0.08, 0.02, 0 m/rad의 저장 trace에서 낮은/0 orientation scale은 기타 오차를 낮추지 못했고, contact 행은 모두 raw lambda 0이었다. 0.08은 계속 사용할 진단 기준이지 최종 weight나 지지 성공 판정이 아니다. [비교 곡선과 측정 한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/README.md), [실제 파일·SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/CHANGED_FILES.md)에 있다.

## Palm-side strap 길이·초기 tension-law 비교 — palm_side_strap_v1

네 0.1초 저장 실행에서 rest length와 초기 law를 비교했다. 10 N 조건의 기타 최대 p/q 오차는 가장 작았지만 첫 step 오차는 더 컸고, 손 접촉 행의 raw lambda는 거의 모두 0이며 지속 지지를 보이지 않았다. 10 N은 채택하지 않았고 안정화·연주 성공을 뜻하지 않는다. [비교표와 두 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/README.md), [파일·SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/CHANGED_FILES.md).

## Palm-side strap 0.5초 저장 비교 — palm_side_strap_long_v1

rest length/초기 law 네 조건 모두 0.5초까지 기타 오차가 커져, 짧은 0.1초에서의 작은 오차가 유지되지 않았다. palm 접촉행은 초기 step에만 있고 지속 지지나 안정화·연주 성공은 확인되지 않았다. 이번 비교에서 길이를 채택하지 않았다. [곡선·camera 그림과 저장 frame 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/README.md), [파일·SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/CHANGED_FILES.md).

## 손바닥 지지의 유한시간 팔 응답 — palm_finite_response_v1

기존 초기각/LA/PD의0.1초 응답교정은작은heldout에서맞았으나 전체보정은손위치오차를줄이며
기타오차를키웠다. 1/4보정+기존tracking도손바닥rawlambda0/후기소실이남아지지성공은아니다.
평행성은필수조건이아니며 실제지지와기타초기p/q유지를우선한다.
[계산·표·실제Isaac Gym 비교이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/README.md),
[변경파일·원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/CHANGED_FILES.md)를 따른다.

## 접촉 경계와 손·기타 결합 응답

새 경계4조건에서 .40은 양의 palm raw lambda가 없고 .45는 step2 두 행만 있다.
.45에서 기타 오차도 커져 접촉만으로 보정을 채택하지 않았다.
[경계 표·그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/README.md),
[변경 경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/CHANGED_FILES.md)를 따른다.
이어 .45 주변12관절 응답과 독립 조합을 측정했다. 14init336steps, 기준5배열 반복exact,
손·기타12×12 유한시간 응답을 얻었다. 양의 palm raw lambda는 지속되지 않으며
새 행렬을 feedback으로 사용하거나 기타 안정화 성공으로 판정하지 않는다.
[결합 응답 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/README.md),
[다음 보정 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md:1)을 따른다.

## 작은 손·기타 결합 보정 실제 비교

초기 q/기타/절대 LA/PD를 유지하고 ±.001rad PD 목표 보정을 3배율로 비교했다. 전체 보정은
기타 5.341mm/1.006°→5.099mm/.973°와 손 추적점 9.289→9.113mm로 줄지만,
양의 palm raw lambda는 step2 한 행뿐이라 지속 지지는 아니다. 3init/72steps이며
후처리 refit은 추가 물리 실행 없이 원 fit의 11개 결과 필드 exact를 확인했다.
[비교표·그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/README.md),
[절대 경로·실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/CHANGED_FILES.md)를 따른다.
다음은 native 질량·drive property·total DOF force의 관절 유지 관측이며 gain 변경은 미실행이다.

## 관절 유지 관측·왼팔 PD 비교 완료

질량·PD property·total DOF force 관측은 2init/48step이며 각 목표각 조건의 이전 raw
5배열과 exact다. baseline/full은 서로 다른 목표각 조건이며 둘 다 sensor를 추가했다.
[관측표·그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/README.md)을 따른다.

같은 초기 자세/기타/LA/목표에서 왼팔12 kp와 kd를 함께 1/1.5/2배로 높인 v2의 기타
최대 이동은 5.099/5.631/6.145mm, 회전은 0.973/1.039/1.100°다. 증가 조건은 채택하지 않는다.
손 추적점 오차는 9.113/9.025/9.336mm이며 양의 palm raw lambda는 step2 이후 없다.
첫 v1 3init/72step의 setter 반환값 검사 누락을 보존하고, v2 3init/72step으로 보완했다.
보완은 각 조건의 원자료5배열을 exact 재현하며 import 실패 후처리는 추가 물리 실행이 아니다.
[PD 결과·그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/README.md),
[다음 강성 분리 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1)을 따른다.

## 앞으로 매 실험 초기 값·실제 Gym5초 녹화

새 기본 실행은 초기 값 JSON과 실제 Isaac Gym 전신·손 근접 영상을 함께 저장한다.
기준 한 조건의 시뮬레이션0~5초1200step, t0 포함151frame/30fps 두 MP4를 검증했다.
영상 길이는5.033333초이며 처음24step 원자료5배열은 이전 기준과 exact다.
별도 SIGTERM 시험은1init28step에서 중단 사유·4frame 부분 영상과 completed=false를 저장했다.
전체 신규 물리 집계는2init1228step이고 postprocessing은 신규 물리 실행이 아니다.
기타 최대 오차82.047mm/10.831°로 녹화 완료를 안정화 성공으로 판단하지 않는다.
[초기 값·영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/README.md:1),
[실험 기본 기록 규칙](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:107)을 따른다.

## 왼팔 stiffness-only 5초 비교

초기 자세·기타 p/q·LA·상수 목표를 유지하고 왼팔 kp만1/1.5/2배, kd1배로 각각5초
실행했다(3init/3600step). 실제 초기값,각전신·손151frame/30fps 영상과 연속 로그를 보존했다.
5초 최대 기타 오차는82.047/246.612/241.007mm,10.831/76.100/74.383°로 상향kp는 채택하지 않는다.
양의 palm raw lambda는 초기step2/1–3/1–4에만 관측되어 지속 지지가 없다.
몸통9목표는 유지했지만 실제 최대 좌표변화는4.227/4.400/4.457°였다.
[결과와 실제 영상](results/palm_stiffness_only_v1/README.md),
[다음 초기 strap 길이 비교 계획](../../../stability_adapter_2/STRAP_FIVE_SECOND_PLAN.md)을 따른다.

## 다면 그립 실제 5초 비교 — multi_face_grip_v3

왼엄지 후면·나머지 손가락 전면·손바닥 측면의 초기 접근을 겨냥한 baseline 및 두 초기각 seed를 각각 5초 실행했다(3 init/3600 step). 세 조건 모두 세 면 초기 source 접근 기준을 만족하지 않았고, 완료된 seed 2도 안정성 성공으로 판정하지 않는다. 기타 최대 위치/회전 오차는 baseline 82.047 mm/10.831°, seed 1 47.437 mm/12.769°, seed 2 26.773 mm/8.323°다. 실제 손 접촉 기록만으로 넥의 면이나 지속 지지를 인증하지 않는다.

### 그림 96 — 세 조건의 5초 기타 오차

![다면 그립 조건의 기타 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/multi_face_grip_curves.png)

### 그림 97 — 실제 Gym 손 카메라의 초기·종료 프레임

![baseline, seed 1, seed 2의 t=0 및 t=5초 손 카메라 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/multi_face_grip_hands_camera.png)

위 행은 실제 Gym 손 카메라 t=0, 아래 행은 같은 실행의 t=5초 저장 프레임이다. [세부 측정표·영상·제약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/README.md) 및 [프레임·입력 SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/artifact_manifest.json)를 확인한다.


## 손바닥 여유 refinement 비교 — grip_palm_refinement_v1

기존 seed 2 저장 결과와 새 α=0.5/0.25 refinement 실행을 비교했다. 둘 다 기존 기준보다 5초 기타 최대·종료 오차가 커 채택하지 않았다. 세 면 초기 source 접근 기준은 α=0.5만 통과했으며, 이는 cooked clearance나 지지 성공을 인증하지 않는다.

![기타 위치·회전 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_curves.png)

![기존 seed 2와 두 새 실행의 t=0 및 t=5초 실제 Gym 손 카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_hands_camera.png)

[결과표·영상·입력 한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/README.md), [v4 producer/input/output SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/artifact_manifest.json)를 확인한다.

## Seed 2 strap 초기길이 5초 비교 — seed2_strap_initial_v1

current, taut, 초기 law 5 N 세 조건을 각각 새로 5초 실행했다(3 init/3600 step). 처음 0.1초의 기타 오차는 taut와 5 N에서 더 작았지만, 5초 최대 위치 오차는 current 26.773 mm, taut 35.020 mm, 5 N 35.293 mm였고 종료 위치/회전 오차는 각각 23.189 mm/7.413°, 35.020 mm/7.542°, 35.292 mm/7.516°였다. 최대 회전 오차는 taut와 5 N이 current보다 조금 낮았다. 이 비교는 안정화 성공이나 최종 길이 채택을 뜻하지 않는다. current run의 다섯 저장 배열은 이전 Seed 2 기준과 exact이며 별도 추가 실행으로 세지 않았다. 초기 pose와 route 길이는 세 조건에서 같고 absolute rest length만 다르며, strap mesh는 camera render에 나타나지 않는다.

[결과표·제약·실제 Gym 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/README.md)에는 strap law 제출 scalar 곡선과 실제 카메라 저장 프레임을 함께 정리했다. 아래 이미지는 해당 결과에서 생성한 그림이다.

![세 조건의 기타 오차와 strap law 제출 scalar](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_curves.png)

![실제 Gym 손 카메라의 시작·종료 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_hands_camera.png)

## Seed 2 왼팔 초기 목표 편차 비교 — seed2_startup_target_v1

세 조건을 각각 새로 5초 실행했다(3 init/3600 physics steps). 왼팔 12축 시작 목표 편차는 0/8.505/17.010°였고, 동일한 기타 초기값과 절대 strap rest length를 사용했다. 1×는 세 조건 중 5초 기타 최대 오차가 가장 작았지만 기타 이탈이 남아 안정화 성공은 아니다.

![초기 목표 편차별 기타 오차와 왼팔 좌표 드리프트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/seed2_startup_target_curves.png)

![실제 Gym 손 카메라 t=0 및 t=5초 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/seed2_startup_target_hands_camera.png)

초기 목표 편차와 실제 좌표 드리프트는 별도 지표다. 초기 여섯 부위의 통합 source 접근 조건은 세 조건 모두 충족하지 않았으며, contact 기록은 cooked clearance나 지속 지지를 인증하지 않는다. [결과·초기값·영상·제약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/README.md).


## 감싸기 자세의 작은 목표 응답과 결합 검증

[8개실제5초 결과·초기값·영상](results/seed2_guitar_response_v1/README.md)에서
같은초기q/G/LA/PD의 기준+어깨/손목6probe+결합heldout을 비교했다(8init/9600step).
heldout 최대p/q26.774777mm/8.124454°: 기준26.772807mm/8.323296°와
최대이동의미세증가/회전의소폭감소를구분한다. 선형예측의큰잔차와손바닥접촉소실이남아
runtime역행렬보정이나안정화성공으로선언하지않는다. 원자료/두뷰영상/그림설명/실제파일줄을남긴다.
[후속3조건계획](../../../stability_adapter_2/SEED2_RESPONSE_LOCALITY_PLAN.md)은아직미실행이다.


## 작은 기타응답의 음의방향·결합0.5배

[새3회 실제5초·초기값·영상·그림](results/seed2_response_locality_v1/README.md)에서 같은초기조건의
negativeShoulder_y/negativeWrist_z -.002와heldout0.5배를비교했다(3init/3600step).
음의Y최대p/q26.684900mm/8.116260°는기준보다모두줄었지만 palm지속지지와G초기복원은아직남는다.
과거saved기준/positive2probe/fullheldout과새3실행의집계를구분한다.
[상수/실제G오차feedback계획](../../../stability_adapter_2/SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN.md)은이후아래단계에서실행했다. 원leaf계획은당시기록으로보존한다.

## 어깨 보정 크기와 실제 기타 오차 feedback

[새3회 실제5초·초기값·이미지와영상](results/seed2_guitar_feedback_v1/README.md)에서
상수-.008/-.016rad와실제G오차목표보정을비교했다. -.016최대25.280921mm/7.753357°는줄었지만,
feedback최대이동26.950260mm는기준보다컸다. 검지와손바닥접촉도지속되지않아성공으로표시하지않는다.
속도제한후요청rate≤.008과실제float32targetrate.008003711700439453rad/s를구별해원자료로대조했다.
[다음실제지지자세초기값비교](../../../stability_adapter_2/SEED2_SUPPORT_POSE_WARMSTART_PLAN.md)는아직미실행이다.


## 세 면 접근 초기값과 동일 PD 목표

[새3회 실제5초 결과·초기값·이미지·영상](results/three_face_initial_same_target_v1/README.md)에서 엄지후면/손가락전면/손바닥옆면 접근 자세를 비교했다. half는 초기source6거리≤3mm이나 최대25.229274mm/7.770624°로 기준보다 이동이 아주 조금 작고 회전은 커졌다. 검지/손바닥 접촉 소실이 남아 안정화 성공은 아니다. 직접보간/투영 거절은 native0으로 보존했다. [다음손가락목표 비교](../../../stability_adapter_2/THREE_FACE_FINGER_TARGET_HOLD_PLAN.md)는 아직 미실행이다.


## 같은 half 초기값의 손가락 목표 비교

[새2회 실제5초 결과·초기값·이미지·영상](results/three_face_finger_target_hold_v1/README.md)에서 finger21 목표만 비교했다. 새초기값 유지 목표는 첫.1초3.934mm/.872°로 줄었지만 최대이동26.112mm와 종료26.047mm/7.715°는 커져 채택하지 않는다. 검지/손바닥 지지 소실도 남는다. 저장목표 반복5원자료배열·두영상exact는 관측이다. [다음 지지소실/물성 진단](../../../stability_adapter_2/THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN.md)은 아직 미실행이다.


## 세 면 지지 소실과 native shape 물성 진단

[three_face_support_loss_v1](results/three_face_support_loss_v1/README.md)에 같은설정 새1회5초 초기값/실제Gym영상과 저장12자세의 source면간격·facet방향·scalar목표오차를 정리한다. Native material friction은 두actor 모두1.0이다. 손바닥 방향은 가까워도 source간격이벌어지고 초기 팔절대목표가 배치와 달랐다. [다음팔초기목표 일치비교](../../../stability_adapter_2/THREE_FACE_ARM_INITIAL_TARGET_PLAN.md)는 아직 미실행이다. 기타자유/고정root하체/몸통9목표/최종66/selfcollision 조건을 유지하며 초기복원·연주안정화 성공은 아니다.


## 초기 팔 목표 일치 두 조건 — three_face_arm_initial_target_v1

[초기값·비교 결과·Gym 5초 영상과 설명](results/three_face_arm_initial_target_v1/README.md), [실제 변경파일/줄](results/three_face_arm_initial_target_v1/CHANGED_FILES.md), [독립 검수](results/three_face_arm_initial_target_v1/review.md), [최종 보존검사](results/three_face_arm_initial_target_v1/final_verification.json)를 모았다. 새2실행/2400step의 종료이동159.795174/157.510653mm는 저장기준21.912505mm보다 커 두 조건은 채택하지 않는다. 초기팔 목표 일치만으로 지지유지가 되지 않았으며 단독 원인이나 PD결함은 단정하지 않는다. 원자료7계약과 각 초기값/전신·손151frame영상은 보존한다. 다음계획/구현은 [half 스트랩 여유 비교](../../../stability_adapter_2/THREE_FACE_HALF_STRAP_SLACK_PLAN.md)에 둔다. 전체 기타복원·유지·연주중안정화는 미완료다.


## half 초기 자세 스트랩 여유 — three_face_half_strap_slack_v1

[초기값·결과·이미지설명·Gym5초영상4개](results/three_face_half_strap_slack_v1/README.md), [변경파일 실제줄](results/three_face_half_strap_slack_v1/CHANGED_FILES.md), [독립검수](results/three_face_half_strap_slack_v1/review.md), [보존봉인](results/three_face_half_strap_slack_v1/final_verification.json)을모았다. 새2실행/2400step·7분석계약에서두길이는기존저장기준보다종료이동/회전이커채택하지않는다. 손바닥양λ는후기까지이어졌으나엄지끝마디기록이초기에끝난 tradeoff다. Body기록은면별·연속지지나뉴턴접촉력인증이아니다. 다음 [native feature 위치계획](../../../stability_adapter_2/THREE_FACE_NATIVE_FEATURE_MAP_PLAN.md)은저장3조건의좌표/면근접을검토하는미실행offline진단이며원자료/소스/영상은보존한다.


## 저장 접촉feature로 세 면 지지 위치 확인

[결과·그림3개·기존5초영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/README.md)와 [시각보고서83](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1581)를추가했다. 새native/physics0이고저장3조건3600records/15511LH기타feature행의offline분석이다. Palm은요청옆면영역21~30mm밖, thumb는후면경계, index/middle은주로fret4/5였다. Sourceproxy와실제cooked면인증을구분한다. 다음 [접촉footprint계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_CONTACT_FOOTPRINT_PLAN.md:1)은미실행이며독립최종검수는도구thread limit오류로보류다.


## 네 초기 접촉 footprint source 후보

[결과·source비교그림·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/README.md)을추가했다. 네source후보가초기배치조건미달로거절돼새물리실행은0이다. V1 source교차를V2에서없앴으나엄지후면내부여유2mm가미달했다. 이전feature-mapv2/그림3개와이번source검색독립검수는완료했다. 새source그림은Gym렌더가아니며이전영상은재사용출처로명시했다. [다음후면면선택](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md:13)은미실행이다.


## 후면지향 엄지 면: 네 초기 자세 source 검사

[결과/초기조건/그림/실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/README.md:1). 엄지±.10/.20rad의네후보는patch이탈과source교차로제외해새native/step0이다. 거리QP의중단/복구와원본보존을구분했고이번source비교를새실제Gym영상으로표현하지않는다. 다음catalog계획은미실행이다.

## 2026-10-10 연주 자세·현재 프렛 목표 진단

[실제 Isaac Gym 화면과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/README.md:1)에 초기·2초 전환·3초·종료 이미지와113표본 추세를 추가했다. 기존 스트랩 ON 실행의 저장 자료 후처리이며 새 물리 실행·학습은0회다. 넥과 앞판 방향, 몸통 상대 배치, 모델 관절 여유와 현재 프렛 목표를 함께 본다. 넓은 허용 범위를 유지하며 자연스러움 문턱과 전체 회전 집합 인증은 미구현이다.

## 2026-10-10 팀원 자세 허용 후보 시각화

[위치·회전 개념도와96개 판정 표본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/README.md:1)을 추가했다. 팀원 fret_041000 기준의 골반 상대 바디 중심과 축별 후보를 그린 설명도이며 Isaac Gym 장면이나6축 조합 안전 인증이 아니다. 현재 허용범위/초기각/제어는 유지하고 새 물리 실행·학습은0회다. 원본 CSV와 이미지를 보존하며 눈 판정39/미기록57, dy+2cm 이상치와 방위±2° 미검증을 구분한다.

## 2026-10-10 팀원 자세 후보의 현재 환경 적용 진단

[세 조건의 native 비교·초기값·5초영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/README.md:1)을 기록했다. 같은 humanoid 초기각·무스트랩·팔24 PI에서 수평 대조는 2초 대비 후기 최대 1.852mm/0.298° 변화였다. 보고 기준·중앙 재구성은 왼손 접촉 관측0, 각각 0.8833/0.5875초에 기타 바디–ground 접촉 후 낙하했다. 각 실행은 5초/1,200 step, 두 카메라 각각151 frame이며 전체 3초기화/3,600 step·새학습0이다. 초기 source 기타–인체/의자 교집합0과 실제 native q/Pelvis/한계 대조를 통과했다. 원 팀의 정확한 초기각·pivot·checkpoint run이 없어 원 실험 재현이나 전체 범위 인증이 아니며 기존 허용범위는 유지한다. 기타 후보와 손 초기각을 함께 검증해야 한다.


## 2026-10-10 사용자·팀원 범위의 Isaac Gym 장면 비교

[현재 수평·보고 기준·중앙 후보의 정면/측면 이미지와 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/README.md:1)을 추가했다. 같은 humanoid 초기각을 새 native 정적 환경3개에 넣고 physics0step/학습0으로 촬영했다. 파랑 사용자 actor-root 위치범위는 각 실제 회전에서의 바디 중심 범위로 변환했고, 노랑 팀원 골반 상대 바디 중심 후보와 같은 좌표에서 비교한다. 두 상자는 단순 포함 관계가 아니다. 회전은 현재/보고 기준이 기존 범위 안이고 중앙 조합은 밖인 세 점 판정이다. 6annotated PNG·6raw native PNG·6depth와 카메라 행렬을 저장했다. 기존 범위·제어·원본 실험은 보존했으며 접촉·동적 안정성을 인증하는 장면이 아니다.


## 2026-10-11 바디 중심으로 사용자 범위 보기

[바디 중심 기준 화면·세 자세 수치표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/README.md:1)를 추가했다. 분홍 marker/좌표는 표시용 기타 바디 중심, 하늘색은 기존 사용자 위치box를 각 실제 q로 변환한 조건부 body-center 범위다. 현재 수평 배치의 골반 상대 범위는 오른쪽−10..25cm/앞0.83..30.83cm/위5.80..29.17cm이고 팀원 후보는17..23/24.5..34.5/8..10cm다. 같은 body-center 기준으로 비교하지만 단순 포함관계가 아니다. 세 자세의6그림/CSV/JSON은 기존 native 프레임 후처리로 새native/physics/학습0회다. 양방향 좌표 helper를 추가했고 기존 runner 연결·제어 경계 변경은 없다.


## 2026-10-11 사용자·팀원 범위 나란히 비교

[정면·측면 두panel 비교와 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/README.md:1)를 추가했다. 왼쪽은 사용자 위치범위, 오른쪽은 팀원 후보이며 같은 native수평기타프레임/카메라/crop/배율에서 표시용 바디중심을 비교한다. 분홍 실제중심은 양쪽 동일하다. 이회전에서만유효한 위치비교이고 새native/physics/학습0회다.

## 현재 기타 기준 Fret 진단 — 저장 전체 실행 (2026-10-11)

기존완료된Isaac Gym389frame/12.916667초를바디중심/RFU·현재회전조건부위치box·checkpoint손끝목표·실제접촉body표시로후처리했다. 새physics0회다. fresh진단3회는0.87/0.83/1.0초카메라API crash로중단했고부분영상을보존했다. full live 관측성공으로부르지않는다.

2초손목벡터155.2mm·약지목표87.6mm,8초다른goal약지46.7mm다. 사용자위치box밖53/389표본/최대15.0mm,초기회전최대50.25°이며원본운지지속0/27·검지finger_back실패다. 다음은왼팔9의현재기타기준접근보정과손가락21정책제어권분리를검토한다. 투시설명선은접촉/깊이증명이아니며준비목표/마지막접촉은미측정이다. [전신·양손전체영상·이미지·검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md:1).


## 현재 기타 기준 왼팔 추종 — 2026-10-11

OFF baseline을실제native상태/명령exact로전체재녹화하고직접손목목표추종(v1)과준비지지관계추종(v2)을검증했다. v2는공통구간기타회전을줄였지만이동·운지는악화했고wrong_press로종료했다. 기타고정/강제손부착/상태덮어쓰기/학습은없다. 각조건은시작~첫원본done전체영상과초기값을보존한다.

[직접 접근 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/README.md:1) · [지지 관계 추종·비교그림·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/README.md:1).


## 손바닥·엄지 지지 5초 비교 — 2026-10-11

왼손 초기각을 작게 바꿔 손바닥/엄지의 동시 solver 응답은 늘렸지만 자유기타 흔들림 감소는 확인되지 않았다. 기존62.96mm/13.63° 대비 초기자세만62.80mm/13.70°,접촉추종96.22mm/16.24°,자세유지 결합63.30mm/13.76°였다(30Hz표본 최대). 각 정식 조건은 실제Isaac Gym1200step/5초·양손/전신151frame,60Hz접촉300표본과입력불변 검사를 완료했다. Fret/학습0이며 카메라중단3회 및SHA실패로제외한1회도보존한다.

[네 조건 표·설명·초기값·영상·변경색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/README.md:1). 지지 접촉 형성과 기타 허용범위 유지/연주 성공을 구분하며, 다음 설계에서는 기타추종/범위복원 목표와 손가락정책 제어권을 함께 다룬다.


## 왼손 공동 학습 정책 설계 — 2026-10-11

왼손 지지와 압현을 한 정책에서 학습하는 후보를 관측·행동·네트워크·단일 PD 제어권·평가·기존 체크포인트 활용 조건으로 정리했다. 새 그림은 제안 구조의 설명이며 Isaac Gym 실행 화면이나 학습 결과가 아니다. 환경과 기존 실험은 변경하지 않았다.

[설계 그림과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/README.md:1) · [주 설계 원문](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:1) · [변경 파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/CHANGED_FILES.md:1).


## 전체 상체 공동 정책 설계v2 — 2026-10-11

하체 제외 상체81관절을 제어하고 Actor/Critic 은닉층512→256을 사용하는 설계로 정정했다. 이전33관절 초안과 결과는 보존한다. 새 그림은 설계 설명이며 native 실행/학습 결과가 아니다. [v2 그림·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/README.md:1) · [설계 원문](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:1) · [변경 파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/CHANGED_FILES.md:1).


## 부위별 움직임·보상 설계 v3.1 — 2026-10-11

전체81 제어를유지하며 몸통의작은움직임·약한머리시선·자유로운팔/손동작과 음악/기타안정성보상후보를정리했다. 함수그래프와26개합성수식/계약검사는실제시뮬레이션/학습결과가아니다. 기존v1/v2/실험보존, 새환경/물리/학습0이다. [그림·설명·검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/README.md:1) · [보상원문](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:29).


## 프로젝트 계획 기반 보상 정리 v4 — 2026-10-11

메인 설계는 [UPPER_BODY_REWARD_DESIGN_V4.md](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:30)다. 1차 음악 결과,2차 유지/전환/timing,3차 접근/자세 예산을 구분하고 기타 허용범위 유지와 별도 평가한다. 42합성 산술 검사 pass, 환경/물리/학습 변경0이다. 설명·수식 비교 그림·변경 색인·검수는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/`에 모은다.


[보상v4 설명·이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/README.md:1)와 [검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/review.md:1)를 마감했다. [변경 파일/실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/CHANGED_FILES.md:1). 새 physics/PPO는0이다.


### 보상 v4 학습 유인 감사

[결과·세 패널 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/README.md:1) · [상세 감사](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:1). 합성 계산+원본 CPU 유지 tracker 검증이며 실제 환경/학습 실행0. 구조는 좋지만 유지 실패 구별/계층 거래/긴 곡의 희석/할인·ledger/실제 신호 연결은 미완료다. 기존 보상이나 환경은 변경하지 않았다.


### 환경 기본층 v1 — 실제 Isaac Gym 초기·5초 비교

[설명·시작/종료 이미지·전신/손 영상4개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:1). 스트랩OFF/자유기타/root·하체fixed/상체81,548D 물리관측과60/240Hz 단일목표 경로를 구현했다. CPU9 통과, 두 조건 각5초/1200physics/300control/151frames×2view. 초기 상태·목표 readback·관측·고정 부위 보존은 통과했지만 기타 max111.790/113.778mm와19.486/19.888° 이탈해 초기 안정성은 실패다. 음악보상/정책/학습/GPU벡터reset은 아직 연결하지 않았다. 메인 설계·구현은 stability_adapter_2에 있고 원자료·영상은 이 새phase에 보존한다.


### 양손 음악 runtime 1차 구현 (2026-10-12)

[초기 지지목표 비교와 실제 Fret+Strike 동결쌍 연결](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:1)을 추가했다. 초기상태/gain/자유기타 조건을유지한 preload1.0의5초 최대이동46.306mm/9.179°로개선됐지만, 동시연주에서403.605mm/63.992°로지지를잃었다. 환경3.85초에Fret 기타-local 손목X위치안전조건으로종료, 공동4event 성공0이다. 12CPU검사와새native3회/3324step·전체6영상(준비/종료포함), 초기값·source계약·240Hz음악진단로그를저장했다. 학습/성공인증0이다.


#### 입력 계약 검증 마감 — 2026-10-12

현재 entry는 [run_dual_music_v5.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v5.py:26)이다. Strike checkpoint document/goal·grip SHA 및 원본 action/observation 순서 검사를 추가했다. 추가4CPU검사와같은조건native재실행에서v4/v5 controls·trace·초기값·240Hz음악판정이exact일치해같은3.85초Fret 실패를재현했다. 이전v4도실제입력SHA가일치했으며원본은보존한다. 마감집계는고유CPU16검사/새native4회/4248물리step/8영상/두pair각111추론tick/학습0이다. [집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v2.json:1) · [guard검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json:1) · [후처리보존예외공개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE_V2.md:1).


### 상체 공동 학습 구조 1차 구현 — 2026-10-12

Actor739→512→256→81과 별도 Critic739→512→256→1, 원 latent 행동을 기록하는 tanh Gaussian/PPO, terminated·truncated를 분리한 GAE, rollout 곡 진행 연결, model/Adam/RMS/RNG/ABI 불변 저장을 구현했다. body9/head6/arm24/finger42 모두 출력하며 기존 PD와 목표 변화율/몸통±5°/root·하체 고정/기타 자유/strapOFF를 유지한다. 평균0 행동을 검증된 preload1.0 절대 목표에 대응하는 anchor codec으로 초기화했다. 기존 Actor 가중치/행동 복사는 없다. 관측에는 현재 기타 기준 손 상태, 원본 압현 셀, pick detector/rearm 메모리와 양손 음악 목표를 넣는다.

- [x] CPU22반례: Actor/Critic 실제 갱신, 끝점·경계 codec, 포화 likelihood, 종료/절단 bootstrap, checkpoint 복원/덮어쓰기 거절, 재무장0/7frame과 미종료 rollout 연결 검증.
- [x] native 평균5초+같은checkpoint복원·탐색5초, 총2400physics/4영상. 평균 trace는 preload100_v2와 exact, 최대46.306mm/9.179°. 탐색81전채널 표본, 최대57.114mm/9.960°. 각9event 성공0이며 학습·연주 성공이 아니다.
- [x] 실제 초기상태·고정 하체·관측·목표/rate·금지 API0·SHA 보존 대조와 독립 코드 검수.
- [ ] 실환경 PPO 최적화는0회. SO(3)허용집합, 연속 유지/dropout, fatal 일정 정산/할인, distal press pad, reward v5 측정/mask를 닫은 뒤 scalar reward 환경 API를 연결한다. 현재 --train은 장면 생성 전에 막는다. 739D는 이번 버전의 계약이며 보상 ledger 추가 때 새 ABI가 필요하다.

[이번 계획](/home/ajou/yigyu/3/stability_adapter_2/JOINT_LEARNING_IMPLEMENTATION_V1.md:1) · [정책](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py:50) · [PPO](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:60) · [실제 entry](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:18) · [이미지·영상·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/README.md:1).

실제 정의 위치: [JointPPO](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:64), [native main](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:17).
