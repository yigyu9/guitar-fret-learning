# Thumb2 clearance v2 수정 코드·저장 source 결과 검수

요약 판정: **이번 저장 결과 문제없음(PASS)**. 실행을 막는 잔여 오류는 없다. 아래 미실행 후보 분기의 경로는 향후 재사용 전 정정을 권장한다. 검수 시작 시 이미 v2/search_execution.json exit0가 존재했으므로 미소비 사전승인으로 기록하지 않는다. 소유권은 v1 실패 추가 기록과 이 review.md뿐이며 다른 담당자의 파일·소스/결과를 수정하지 않았다. Search/geometry solver/FK/native/분석/렌더 main을 실행하지 않았다.

- [수정:74](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance_v2.py:74)는 source XML thumb2 subtree에서 모든 descendant body를 유도한다. 직접 XML을 읽어 thumb2/3/thumb_pad/thumb_top 네 body와 각각 geom1/1/1/0임을 확인했다. build_probe는 thumb_pad를 의도적으로 제외하므로 실제 collision geom은thumb2/3 둘이며 assertion과 맞는다. Nonmoving pose identity는 네 descendant를 모두 제외하고, [scope:137](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance_v2.py:137)도 충돌 geom2와 따라가는 pad/top pose를 구분한다. v1 identity 오류는 해소됐다.
- [wrapper](/home/ajou/yigyu/3/stability_adapter_2/run_thumb2_clearance_phase_v2.py:24)는 새 module/output/후속 execution leaf를 소비하며 source 단계68입력/68사본의 현재·전후 SHA, 로그 SHA, exit0/terminal completed가 모두 일치한다. Frozen native runtime/inner SHA 강제와 native-only inherited closure 정책은 그대로다. Python3.8 AST 통과, 실행 source SHA는 `e3eb39131b9d7a639dbf2d6144f126795664e373ff73daf067a091603d618eb4`, wrapper SHA는 `c5ad19b43ae13ab3791457ab11394e7baa0f5615fd2cbb03cfe4d1c1fac3d43f`다.
- [search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/search.json:1)은8검사 true/7조건을 보존한다. Zero pose position1.2719202621569003e−16m/rotation3.3207156815710926e−16rad이며 기준 단일thumb2–G LP4.288364821mm를 재현했다. 저장 raw 초기각으로 일곱 float32 angle/actual delta와 source_clear 식을 독립 재계산해 일치했고, 모든rear-patch upper/lower/gap 및 feasible-witness 오차 범위를 확인했다. Solver/FK는 재호출하지 않았으므로 LP/pose 결과 수치의 검수 범위는 저장 결과·코드·기준 재현 검사의 정합성이다.

| 요청 thumb2 delta(rad) | 저장 thumb2–G LP 공통내접반경(mm) | source clear |
|---:|---:|---|
| 0 | 4.288364821 | false |
| −.05 | 3.984985912 | false |
| +.05 | 4.590763189 | false |
| −.10 | 3.679258129 | false |
| +.10 | 4.893354547 | false |
| −.20 | 3.054823670 | false |
| +.20 | 5.500940003 | false |

모든 조건은 bounds/other-pose identity/self1188 및 cross-hands clear를 만족하나 thumb2–G 교차가 남는다. Palm up0.9565471586122466도 동일하다. selected=null/proposal 없음/native 디렉터리·native_execution 없음, native_initializations/physics_steps0을 확인했다. 이번7조건에서 source-clear 후보가 없다는 결과이며, thumb2 전체 가용범위나 다른 관절 조합의 불가능성·cooked 관통깊이·힘·연주/지지 실패 일반론으로 확대하지 않는다.

Warning(미실행 분기): [후보 trial 경로:128](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance_v2.py:128)가 아직 `trials/source_hand_thumb2_clearance_v1`이다. Clear 후보가 생기면 v2 proposal이 v1 이름의 trial 디렉터리를 쓰게 된다. 이번 selected=null로 해당 분기는 실행되지 않아 실제 생성물 영향은 없다. Root에 전달했으며 소비된 v2는 보존하고 향후 후보 준비용 새 버전에서 해당 phase 경로를 정정해야 한다.


## 마감 그림·문서·후속 계획·감사 코드 검수: PASS

요약 판정: **이번 산출물 문제없음(PASS)**. 추가 Critical 사항은 없다. 앞서 기록한 미실행 후보 경로 Warning은 [ROOTnotes:9](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/ROOT_VERIFICATION_NOTES.md:9)에 남았으며 해당 소비 코드를 향후 후보 생성에 재사용하지 않기로 명시했다. 기존 v1 실패/사전 검수 기록은 수정·삭제하지 않았다.

- [그림 producer](/home/ajou/yigyu/3/stability_adapter_2/make_thumb2_clearance_artifacts.py:57)는 저장 actual_delta_rad로 정렬한7점과 LP 반경×1000의mm값을 그린다. 실제 PNG를 직접 열어7개 표식/각delta와반경 annotation·단위·범례·세줄 caption의 표시와 겹침/잘림 없음을 확인했다. 연결선은 저장 표본의 정적 도표이며 새로운 Gym 장면/동적 contact나 중간각 조건의 인증이 아니다. [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/README.md:5)의7행 actual delta/initial q/LP mm/thumb3 후면patch witness upper-mm를 저장 search에서 별도로 포맷 계산해 모두 일치했다.
- Artifact ONE 실행의 exit0/terminal completed, 직접5입력 전후·현재 SHA, producer/wrapper 포함7사전 사본, 로그 SHA와 PNG SHA를 독립 확인했다. [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/artifacts/manifest.json:1)의 rows7/all_source_clear=false·native/physics/actor/train0가 실제 저장 결과와 맞는다. 도표 단계의 직접5입력 보존과 원 검색68입력 보존은 구분되며 검색 closure는 앞선 검수에서 직접 대조했다. Producer Python3.8 AST 통과, source SHA `2905668f17c0e0387da74bb1178eeb45e9c6ef4eec42029f058c292a1c679996`, wrapper SHA `5dfea46a0abc653c76c3e80a3d7e37e06c792c1831fc23b08201e5b485334f8b`다.
- 최종 README/CHANGED·[ROOTnotes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/ROOT_VERIFICATION_NOTES.md:3)와 main [README:1153](/home/ajou/yigyu/3/stability_adapter_2/README.md:1153)·[PLAN:1974](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1974)·[VISUAL §113:2058](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2058)은 v1 구현 실패와 v2 완료, 실제geom2/descendant pose4, 7조건 전부HG겹침/후보없음/native0, LP와 cooked침투의 구별, thumb2 전체범위 불가능성 미증명,5초 미측정을 일관되게 설명한다. 재사용 hands 이미지는 직전 실제0step 거절 장면임을 명시한다. Phase문서 링크/실제줄과 현재 main prefix 보존을 확인했다. 영상144개 유지와 기존 원본 보호의 최종 전체 감사는 root 소유다.
- [다음 기저부 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md:7)은 thumb1_x−.05,thumb1_y+.05,thumb1_x−.10,thumb1_y+.10 순으로 한축4후보를 직접 native 초기 형상 검사하고 처음 통과한한후보만 같은 초기화1200step5초를 기록하는 **미실행 계획**이다. Thumb2 초기0.3384127914905548/held0.3474094569683075rad 유지값은 원 native initial 자료와 일치한다. Finger1다축 FK로 pass를 예측하지 않고 source/native/normalized 숫자 조건과 fresh 형상·동적지지 검증을 구분한다. 고정LA/다른80/G/root하체/PD/몸통9/손목/최종66범위가 일치한다. 향후 구현과 실제 gate 승인은 이번 검수 범위가 아니다.
- [root 감사 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/root_final_audit_producer.py:22)는 v1exit1/v2exit0 및 사본·전후/현재SHA·로그/mainprefix·source7조건/no-native·artifact/이전4inventory/144영상·인덱스를 확인하고 모두 통과한 뒤 source_final+inventory를 작성한다. V1 실패 경로도 inventory에 포함하며 append 가능한 main canonical3개는 사본을 남기고 inventory에서 제외한다. AST3.8 통과·SHA `af505ff25563de7ada98e283d9d771d8fe870b91bf426cf057b7aa317f44ff6a`를 확인했다. 이 코드는 읽기만 검수했으며 최종 감사 실행 완료를 인증하지 않는다.

최종 확인 SHA-256:

- PNG: `7baf762c1790606b23444c2f3096e3c673d622728cf0d037460f3f555e1f6145`
- README: `07e57779270ec929c0b825ddfe03a66129801adf21e18c8a6a2d282e822dd3e9`
- CHANGED_FILES: `40dc9fbb19493446e4cfaf58db33949ea4b1bcdbf5e2a8c85a243b223039e25f`
- ROOT_VERIFICATION_NOTES: `a0085472fa10535b3e6e4abdf3695a8748cee368d1d6519e501f274bca9761d1`

이번 마감 검수는 저장 자료 읽기·해시/작은 수치 대조·AST·기존PNG 보기만 수행했다. Root audit/geometry/physics/producer/actor/훈련 재실행0이며 이 review.md 최종 추가 기록을 동결한다.
