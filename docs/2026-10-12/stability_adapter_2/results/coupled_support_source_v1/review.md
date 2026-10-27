# 독립 검수 — 팔12·손가락6 conditional source 모델과 검색 v3

**요약 판정: 문제없음.** 최종 검수 대상은 소비·보존된 helper/model, `search_coupled_support_source_v3.py`와 `search_v3.json`, 새 `PLAYING_RESIDUAL_EVALUATION.md`다. 이전 v1/v2의 문제는 원본 보존 후 v3에서 해결됐다. 이번 검수는 이 파일만 새로 작성했으며 기존 코드·원자료·계획을 수정하거나 검색/물리를 재실행하지 않았다.

## Critical

없음.

## Warning

없음. 아래 기록은 해결된 이전 버전의 문제이며 v3의 미해결 항목이 아니다.

## Suggestion

없음. 실제 후속 PD 실행 전에 필요한 native float32 제출·응답 검증은 이번 source-only 범위 밖이다.

## 이전 문제와 해결 확인

- [검색 v1:75](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source.py:75)은 t0 base를 실제 초기각인 `initial_PD_target_rad`로 치환했다. 실제 첫 제출 유지 목표와 33개 관절이 달랐다. [v3:87](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v3.py:87)은 모든 시점에 저장 control의 최종 목표를 사용하며 t0가 `preserved_absolute_targets_rad`와 같음을 assert한다. [v3:137](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v3.py:137)은 선택18 밖의 63개 목표를 그대로 유지한다. 16개 행 모두 원 control·base·held63·delta를 독립 대조해 일치했다.
- v1의 5초 quarter는 대표점 오차만 줄고 whole-palm–patch 간격은 늘었는데도 방향 screen을 통과했다. [v3:134](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v3.py:134)은 후보 whole-palm 거리 상한이 기준 거리 하한보다 작아야 하는 조건을 유지한다. 실제 5초 quarter의 `8.91292275 → 9.18308764mm` 간격 증가는 이제 거절된다.
- [검색 v2:63](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v2.py:63)의 native filter 적용은 같은 왼손 mask128 쌍을 제외했다. [v3:67](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v3.py:67)은 LH/Wrist/Elbow source geom을 별도로 열거해 graph>2 쌍을 모두 포함한다. 실행 전 활성 source geom 기준 정적 pair 생성을 검사해 예상 비인접110쌍=실제 포함110쌍, 추가 중복0을 확인했다. 연결부 진단51쌍은 모두 graph≤2였다. [v3:126](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_support_source_v3.py:126)은 연결부 진단만 blocking에서 제외한다. Native collision filter 자체는 바꾸지 않는다.

## helper와 모델 검증 범위

- `model.json`의 24시점×11body=264개 위치/회전 오차를 저장 native pose와 독립 재계산해 일치했다. 최대 위치 오차는 `0.0002627014737mm`, 회전 오차는 `7.58811721e−7rad`다. 모델 입력 SHA 불일치는 0개다.
- 네 시점의 zero-delta pose identity와 18축 중앙차분 Jacobian을 독립 재계산해 기록과 일치했다. helper/model의 5개 check가 모두 참이다. 선택축은 팔12와 thumb2/3·index2/3·middle2/3의 단일축6개뿐이다.
- [helper:64](/home/ajou/yigyu/3/stability_adapter_2/coupled_support_source.py:64)의 finger relative pose는 각 저장 snapshot의 실제 부모·자식 관계다. 실패한 finger1의 다축 q→pose 예측을 사용하지 않고 measured relative를 유지한다. hinge 검증은 실제 부모 pose를 공급하는 조건부 검증이며 전역 finger FK·미래 PD 응답·접촉 예측 정확성을 인증하지 않는다.
- Chest 이동/회전 lift와 arm calibration, source pose/mesh의 읽기 전용 delta 합성만 수행한다. Root/하체·torso·G·LA·비선택 관절의 실제 simulator state를 덮어쓰지 않는다. 임시18축 탐색은 최종66 제어권을 제한하지 않는다.

## v3 결과 독립 대조

- 실행 source SHA는 `c04f312a579dccc525f30734b2ef5b8ab0de561e26d73eb92756a1882aee9113`이고 실행 전후 및 source 복사본이 같다. 실행 exit 0, 출력 7개 check가 모두 참이다. 출력 입력 SHA 불일치는 0개이며 native 초기화/physics step은 0이다. v1/v2 출력과 보존 복사본도 동일하다.
- 네 시점의 18축 bounds를 native limit, 선택 finger의 Aug19 limit, 현재 actualq 변화 폭(팔±0.05/finger±0.10rad), 원래 PD base의 native/손 한계, 초기q 기준 최종 PD offset ±0.3rad에서 독립 계산해 exact 일치를 확인했다. 최종 16행의 PD base+delta·held63·actualq+delta 범위도 맞는다. 한계 clipping으로 통과시키지 않는다.
- 16행×왼손 비인접110쌍=1760개 source LP 교차를 독립 재계산해 저장된 존재/반경과 일치했다. 전 행에서 같은 왼손 비인접 pair count는110이다. v2 대비 solve·비pair 수치와 blocking 판정은 그대로이고 same-left 검사 범위가 추가됐다.
- 16행×4body=64개 유한 patch 거리 certificate의 source-hull witness feasibility, polygon witness coplanarity/내부 여부, witness 거리 상한과 support-plane 하한을 독립 확인했다. 저장값과의 최대 차이는 `1.28e−14m`다. 모든 whole-palm 접근 boolean이 상한/기준 하한 판정과 일치했다.
- Screen 통과는 **0.5초 fraction0.25 한 행**이다. 기준 palm 간격은 `[9.994144830, 9.994144851]mm`, 후보는 `[9.972901650, 9.972901669]mm`로 source 접근은 약 `0.021243mm`다. 대표점 목표 오차는 `15.103434 → 14.605062mm`다. 이는 원하는 접촉 달성이나 실물 안정화 성공이 아니다.
- t0/0.1초의 후보들은 whole-palm/대표점 접근 조건을 충족하지 않고, 더 큰 0.5초/5초 변화에는 finger–G source 교차 증가가 남는다. 5초 quarter도 whole-palm 간격 악화로 거절된다. 특정 한 snapshot의 source 방향을 연속 제어 정책·안전한 grip·초기 world p/q 복원으로 확대하지 않는다. 기존10µm source 반경 증가 screen도 물리 관통 허용 기준이 아니다.

## 연주 residual 평가 계획

- [PLAYING_RESIDUAL_EVALUATION.md:19](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:19)의 **현재 G frame 연주 오차**와 **초기 world p/q 유지 오차** 분리는 사용자 목표와 기존 관측 계약에 맞다. 움직이는 G의 상대 속도/회전 정의를 재사용하고, 좌표 변환만으로 자유 기타 적응이 완료됐다고 주장하지 않는다.
- [계획:33](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:33)은 source 가중치·정규화를 동결하고 source60+Thorax6에 공동 residual 하나를 합성한다. 단일81D PD 제출·한 번의 평활화·실제 적용 목표의 history 회신·몸통9 목표 유지와 최종66 권한이 기존 설계와 정합하다. 별도 PI 작성자를 병렬로 두지 않는다.
- [계획:50](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:50)의 checkpoint 평가→잔차0 연결 계약→무학습 자유 기타 연주 baseline→residual 학습→held-out 이벤트/초기조건 비교 순서는 타당하다. Fret/Strike detector 성능과 기타 유지 지표를 나누고 단일 reward 증가만으로 성공을 판정하지 않는다.
- 실제 checkpoint 선정·관측/action/history 연결·학습은 미완료로 명시된다. 작은 손목 시험이나 source 방향 탐색을 실제 연주 학습 결과로 표현하지 않는다. 기타 고정·지속 state overwrite·episode 중 LA 변경·필수 WAIT를 도입하지 않는다.

- [COUPLED_SUPPORT_SOURCE_DECISION.md:16](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_SUPPORT_SOURCE_DECISION.md:16)의 약21.243µm 접근·약10mm 잔여 간격은 v3 수치와 일치한다. [결정:25](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_SUPPORT_SOURCE_DECISION.md:25)은 다음 palm 우선 검토를 같은 저장 상태의 source 단계로 제한하고, 실제 PD 실행 전 float32 목표 재검사를 요구한다. 한 snapshot의 통과를 실제5초 제어 채택으로 승급하지 않는 결정과 연주 평가 계획 연결에 문제없다.

## 최종 그림·manifest QA

- 실제 [PNG](artifacts/coupled_support_palm_gap_by_fraction.png)를 열어 확인했다. 4개 이산 시점마다 4개 fraction의 총16점을 모두 표시하며 연결선이 없다. 범례는 fraction별4개이고 유일한 통과인 0.5초 quarter에만 별표와 설명 화살표가 있다. 축·범례·캡션 겹침이나 잘림은 없고 mm 단위와 CPU source-only 범위, cooked clearance/물리 PD 결과가 아니라는 제한을 명시한다.
- [producer:110](/home/ajou/yigyu/3/stability_adapter_2/make_coupled_support_artifacts.py:110)은 각 행의 전체 palm hull–유한 patch 거리 상한 중 최소값을 m→mm로1000배 변환한다. 원 `search_v3.json`에서 독립 계산한 표시값은 아래와 같으며 실제 점 위치/별표와 맞는다. 작은21.243µm 차이를 그림 해상도로 정량 인증하지 않고 위 수치 검수 결과를 사용한다.

| 저장 시점(s) | fraction0 | fraction1 | fraction0.5 | fraction0.25 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 0.421670 | 2.786123 | 1.618719 | 1.036817 |
| 0.1 | 5.259589 | 5.486956 | 5.357960 | 5.305944 |
| 0.5 | 9.994145 | 9.807718 | 10.016362 | 9.972902 |
| 5 | 8.912923 | 9.919493 | 9.543423 | 9.183088 |

- Manifest의57개 입력 SHA를 실제 파일과 대조해 불일치0, before/after 동일을 확인했다. 출력 PNG SHA `4a3086790f7b87a57e8b643f9f6f0d8487b4885a9a2357f86621af6a130676f9`도 맞는다. producer SHA `84bde099d6638367a2f7899eb39abc48e3dd24cd8fcc1fdc3753b348ad350bf3`, execution 전후 SHA, manifest/log SHA와 exit0 기록이 모두 일치한다.
- Producer AST 검사 통과. 원자료/기존 출력 수정 없이 비어 있는 새 출력 경로에만 쓰는 guard가 있으며, 생성기 자체는 JSON/SHA/Matplotlib만 사용한다. manifest의16 placements·통과1·source-only 및 native/physics/inference/training0 기록이 실행 코드 범위와 맞는다. 그림을 재생성하지 않았다.

## 최종 README·변경 색인·root 기록 대조

- [결과 README:18](README.md:18)의16행을 원 JSON과 독립 대조해 전부 표시 자릿수까지 일치하고 통과 표기도 맞았다. [README:45](README.md:45)는 저장 실제 baseline과 가상18D delta 인체 source 재배치·저장 G pose를 구분한다. 유한 patch 거리 certificate와 별도 LP 공통구 교차 검사도 구분하며 실제 cooked 접촉/PD 결과로 확대하지 않는다.
- [README:60](README.md:60)의 도식은 frozen fret/strike 기준 목표와 공동 residual 하나를 동일 합성 노드에 공급한다. 현재 G의 연주 정확도와 초기 world p/q 유지의 분리, 미구현 residual·미실행 inference/학습, 이전 LA−2mm 영상의 참고 범위가 평가 계획과 맞는다.
- `CHANGED_FILES.md`, `CHANGED_FILES_SUPPLEMENT.md`, `ROOT_VERIFICATION_NOTES.md`와 메인 [README:969](/home/ajou/yigyu/3/stability_adapter_2/README.md:969), [PLAN:1745](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1745), [VISUAL_REPORT:1813](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1813)을 대조했다. 조건부264검증·same-left110·통과1/16·21.243µm·실제 PD 미채택·최종66 residual 설계가 일치한다. Model stdout 전체 미보존 한계와 search 로그 보존 설명도 실행 기록과 맞는다.
- 위7문서의 이번 범위에서 로컬 링크58개를 검사해 파일 누락/줄 번호 범위 초과0이다. 최종 문서 대조 뒤에도 manifest 입력57개와 PNG 출력 SHA 불일치0을 확인했다. 검수한 결과 README SHA는 `d1f9338465e4bdf16749a6074785e76fc8335a2fc07172ac11210126116829a1`, CHANGED_FILES SHA는 `8000cf95aa76c45c5a6c880df5f9cb2a6a0845f18d4402e470adde504602fa06`이다.

최종 판정은 **문제없음**, Critical/Warning/Suggestion은 모두 없다. 검수는 원본 읽기·SHA·AST·저장 자료 재계산과 offline source geometry/LP certificate 대조, 실제 PNG 열람으로 수행했다. 실제 Gym scene 생성·physics step·정책 inference·학습·그림 재생성은 실행하지 않았다. 검수자가 수정한 파일은 이 `review.md`뿐이다.
