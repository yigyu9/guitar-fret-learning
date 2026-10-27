# stability_adapter_2 작업 디렉터리 정리 사전 검수

요약 판정: **문제없음(PASS, cleanup_manifest_v3 삭제 전 preflight 범위)**. 현재 사용자 요청에 따라 과거 단독 작업 파일을 정리하되 실행 중 필요한 파일과 원본 복구 가능성을 확인했다. 과거 실험의 과학적 실패·무가치성을 판정한 것이 아니다. 삭제·ZIP 추출·코드/원자료 변경·native/physics/테스트 main 실행은 하지 않았으며 소유 review.md만 작성했다. 최종 삭제·검증 결과는 후속 검수 대상이다.

## 최초 후보의 blocker와 해소

최초 [cleanup_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/cleanup_manifest.json:1)은 keep118/remove566이었다. **Critical(해소):** [run_recorded_trial.py:24](/home/ajou/yigyu/3/stability_adapter_2/run_recorded_trial.py:24)와 [run_strap_recorded_trial.py:24](/home/ajou/yigyu/3/stability_adapter_2/run_strap_recorded_trial.py:24)는 `palm_hold_pd_v2/analysis.json`의 input_sha256 전체를 실제 해시한다. 삭제후보와 canonical 소스/계획23개가 겹쳐 그대로 삭제하면 native 초기화 전 FileNotFoundError가 발생한다. 예시는 run_palm_hold_pd.py/analyze_palm_hold_pd.py/PALM_HOLD_PD_PLAN.md/finger_grip_control.py다. JSON이나 ZIP을 docs에 보존하는 것만으로 canonical live 경로 읽기가 해결되지는 않는다. 실제 해시 의존성을 유지하도록 root에 전달했다.

또 [self_collision_probe.py:42](/home/ajou/yigyu/3/stability_adapter_2/self_collision_probe.py:42)는 search_near_touch.json의 input_sha256을 읽어 해시하므로 run_fixed_lower.py가 필요하다. [진단 proposal 해시:29](/home/ajou/yigyu/3/stability_adapter_2/run_strap_recorded_diagnostic.py:29) 및 [small-wrist proposal 해시:29](/home/ajou/yigyu/3/stability_adapter_2/run_small_wrist_recorded_diagnostic.py:29)는 CLI proposal별 canonical closure를 요구한다. 현재 지원 proposal은 three_face_initial_same_target_v1/proposal.json으로 한정하고, 다른 과거 proposal은 원래 closure 복원이 필요하다는 root 지원 범위를 적용했다. 이 조건은 최종 안내에도 유지해야 한다. Data-only initial-values의 모든 과거 해시 경로를 live 실행 의존성으로 간주하지 않았다.

root는 v1/v2 manifest를 수정하지 않고 별도 **v3**를 작성했다. v2 keep242/remove442는 미실행 중간 초안이며 이번 삭제 대상으로 승인한 manifest가 아니다. [최종 v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/cleanup_manifest_v3.json:1)는 keep176/remove508, SHA `7e0cdc2fcc4ffdbd58121c2cc4c5cf59f2df1b157fb768e2468c130c7d90ccd5`다. 최초 blocker는 해소됐다.

## v3 독립 preflight

필수 metadata 세 개를 실제 읽어 삭제 목록과 교차하고 모든 현재 경로의 SHA를 대조했다. palm_hold_pd_v2/analysis.json **466**경로, thigh_palm_support_v1/search_near_touch.json **77**경로, three_face_initial_same_target_v1/proposal.json **8748**경로가 모두 현재 SHA exact이며 삭제와 겹치는 경로0이다. 일부 과거 helper의 standalone main은 임의 과거 JSON manifest를 다시 해시하므로 현재 지원 외 과거 실행은 압축본 복원 후 사용할 수 있다. Quiet YZ compact wrapper의 현재 직접 의존성과 읽기 전용 baseline 데이터는 유지되며, 데이터에만 기록된 14k 조상 전체를 다시 해시하는 구현으로 설명하지 않는다.

유지 Python과 테스트 **123파일(9개 test 포함)**을 Python3.8 AST로 읽어 상대/절대 local import·literal filename/module string을 교차했다. 삭제될 module import·직접 파일명 참조는0이다. 현재3 static launcher가 지칭하는 Python entry도 유지된다. 이 검사는 실행하지 않는 AST/문자열 의존성 검수이며 동적 사용자 입력의 임의 과거 경로까지 인증하지 않는다. Root의 사전 CPU 테스트 결과와 삭제 후 CPU/native 검증을 대신한다고 주장하지 않는다.

v3 keep/remove 전체 **684개 root 파일**의 경로가 패키지 root 안에 있고 상대 filename/현재SHA/size와 exact, 중복·교집합0을 확인했다. assets/trials/tests 하위디렉터리와 docs/공유 stability_adapter는 삭제 범위 밖이다. __pycache__/pyc 제거는 재생성 가능한 캐시 범위이며 과거 소스는 ZIP에서 복구할 수 있다.

[원본 ZIP 보존 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/backup_verification.json:1)의 archive SHA `8c2104db1c7bbf6974805d2c683bb47c68812c5a9628831d7787742ea4faf152`를 독립 확인했다. ZIP **1003항목**의 내부 bytes SHA와 현재 비캐시 파일이 exact이고 ZIP CRC 검사도 통과했다. trial references의 **15개 심볼릭 링크**는 타깃 파일 내용을 복사하지 않고 원래 link target 문자열과 symlink 형태를 보존한다. 압축은 읽기만 했고 추출하거나 원본을 수정하지 않았다. 따라서 삭제된 옛 문서 링크/재현 명령은 원본 복원 뒤 사용할 수 있다는 계획이 타당하다.

사전 판정: PASS — **v3 manifest에만 적용**. v1/v2 삭제 목록으로 실행하면 안 되며, 현재 지원 외 과거 proposal·standalone main은 원래 closure 복원이 필요하다. 삭제/캐시 정리/사후 검증은 root의 후속 실행이며 이번 review가 이미 삭제 성공을 선언하지 않는다.


## 실제 삭제 및 사후 저장 검증 delta

요약 판정: **문제없음(PASS, 실제 정리/저장검증 범위)**. v3 SHA와 [deletion_report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/deletion_report.json:1)의 manifest SHA/삭제명508이 exact이고, 현재 트리에서 해당508파일은 모두 없다. root 파일 집합은 유지176개에 신규 CURRENT_FILES.md 한 개만 더한 **177개**와 일치한다. 유지 코드/문서는 사전 SHA exact이며 append 가능한 README/PLAN은 원본 길이 prefix SHA exact다. 현재 cache 디렉터리/pyc는 없다. report의 삭제된 캐시는 두 디렉터리이며 source508삭제와 구분한다.

삭제508파일의 원본 bytes가 ZIP 안에서 manifest SHA와 일치하고 archive SHA는 사전검수 값 그대로다. 자산·trial·test **319항목**은 현재 트리와 ZIP의 원본 SHA가 exact이며 symlink15는 target 문자열을 그대로 비교했다. 압축본의 링크를 역참조하여 원래 docs 타깃을 수정하거나 현재 패키지 전체에 덮어쓰기 복원을 수행하지 않았다. docs 결과/영상/공유 stability_adapter 비변경은 root 삭제 scope와 기록에 명시되어 있으며 이번 검수에서 무관한 외부 디렉터리 전체를 재감사했다고 주장하지 않는다.

[verification_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/verification_after.json:1)의 11checks 全True, structure 숫자177/AST123/local-import누락0/launcher3/physics0/training0 및 로그3 SHA current exact를 확인했다. 사전·사후 저장 pytest 로그는 각각 **32 passed in 1.88s / 32 passed in 1.83s**, 기존 Gym articulation 경고를 보존한다. CLI 로그의 현재 help6은 각 exit0이며 command help/import 통과 범위다. 이것을 신규 native 장면·5초 물리 실행 또는 그래픽 자원 인증으로 확대하지 않는다. 검수자가 pytest/CLI/native/render를 다시 실행하지 않았다.

실제로 재해시하는 지원3 metadata 경로의 합집합 **8760개**를 삭제 후 읽어 기대 SHA와 current exact를 독립 확인했다. [CURRENT_FILES.md:31](/home/ajou/yigyu/3/stability_adapter_2/CURRENT_FILES.md:31)는 기존 diagnostic의 현재 지원 proposal=three_face_initial_same_target_v1/proposal.json이며 임의 과거 proposal·유지 helper의 과거 standalone main은 원래 closure 복원 후 사용할 수 있다고 명시한다. 일반적인 현재5초 기록 코드는 필수 과거 hash sources를 그대로 사용한다. 모든 과거 명령이 새 트리에서 그대로 작동한다는 주장은 없다.

[현재 안내](/home/ajou/yigyu/3/stability_adapter_2/CURRENT_FILES.md:1), [main README:1411](/home/ajou/yigyu/3/stability_adapter_2/README.md:1411), [PLAN:2243](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2243)의 삭제508/유지177/ZIP1003/32tests/CLI6/123syntax/8760경로·지원 범위 표현은 저장 결과와 맞다. 현재 source/physics/학습을 바꾸거나 과거 실험을 과학적으로 무의미하다고 판정하지 않는다. 최종 결과 README/CHANGED의 중립 검수 링크와 root 최종 보존 기록은 후속 delta에서 대조한다.


## 최종 결과 문서·root 보존 기록 검수 및 동결

요약 판정: **문제없음**. [README:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/README.md:5)와 [CHANGED_FILES:3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/CHANGED_FILES.md:3)은 시간에 따라 모순되는 pending 문구 대신 실제 review 기록으로 연결한다. [색인:14](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/CHANGED_FILES.md:14)의 main README1411/PLAN2243 줄도 실제 정리 추가분을 가리킨다. 현재 안내와 결과문서·색인의 39개 링크 파일/줄 존재를 확인했다. 삭제508/캐시2·유지176+guide=177·원본ZIP1003/symlink15·사전사후32tests/CLIhelp6·지원8760경로의 수치와 삭제/복원 및 현재 지원 범위는 위 독립 검수 결과와 일치한다. 과거 실험의 가치 판정이나 모든 옛 CLI 지원을 선언하지 않는다.

[final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/final_verification.json:1)의 14checks 全True, root177/삭제508/cache2와 saved_verification/manifest/archive SHA, 최종문서2·source_final2 SHA current exact를 확인했다. CLEANUP_PLAN/CURRENT_FILES 사본은 canonical과 byte exact다. 신규 구현·물리·연주·학습 실험을 인증하는 보존 감사가 아니라 이번 파일 정리의 보존 기록이다. 기존 검수 이후 코드·데이터 검증을 재실행하지 않았다.

최종 SHA-256:

- README.md: `f53d086e929862891baf28e7993c5157d620a94eccf4fe053e0c197928783d64`
- CHANGED_FILES.md: `2e280148436285ab996ee3bd8567375c3438a844bcf72f0c36f3d9bdeaa5a67d`
- cleanup_manifest_v3.json: `7e0cdc2fcc4ffdbd58121c2cc4c5cf59f2df1b157fb768e2468c130c7d90ccd5`
- final_verification.json: `6c1237c85613e3a47fa6ff23929a1d85d5fc43a66c13796837affb6d21f8b930`

미해결 Critical/Warning은 없다. 검수 소유 파일만 기록했으며 이 review를 동결한다.

최종 판정: PASS
