# Index/middle wrist candidate v3 precheck 준비

상태: v3활성구현 동결 인계 뒤 최종CPU 준비를 통과했고 독립prep검수 대기다. GPU/native 실행은 하지 않았다.

표준 `-m guitar_learning.tool.experiments.short_finger_learning`을 그대로 쓴다. index(row1)와middle(row8) 각각 freshbootstrap1update 뒤 owninitial만reference/zero/random 각4첫시도를 평가한다. 총8stage·평가24시도이며 실패도 포함한다. 새child·runtime monkeypatch·추가학습300·선별reset은없다.

`run_precheck.py`는 직전검수된 other_finger_regression driver의 validate/model hash/출력보호/run_child를 유지하고 jobs만index+middle8개로바꿨다. index는원래 other_finger_precheck jobs[:4],middle은직전regression jobs[:4]를복사하며 run경로만새폴더로바꾼다. teacher/reference 원본 경로/bytes는동일하다. .5cap/2sramp/3sonset/PD/범위/codec/보상은기존조건이다.

기본 실행은 dry plan이며 simulator를 만들지 않는다:

```bash
/home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/wrist_position_candidate_v3/native_precheck/run_precheck.py
```

최종봉인 전 `--execute`는 사용할 수 없다. CPU초기73모델hash/현재settings/4환경전체quota/nativefixedscene·closed/inputbeforeafter를검사하고,실제초기모델불일치면기존보고서를보존한채후속단계를중단한다. output기존폴더/깨진symlink를거부한다. oldv2source의checkpoint strict load는정상적으로거부되어야한다.

이번준비는기존원자료·active소스를바꾸지않으며도달/학습/자유손압현/하중개선을가정하지않는다. 원래trace는env0/60Hz다.

final CPU는부모shortschema2/WRIST_CONTROL3, index/middle각seed7초기73모델값의v2저장본일치,oldv2source strict거부,settings변경이wrist계약뿐임을확인했다. .5cap/2sramp/3sonset/Jacobian수학계약·PD/범위/codec/보상 settings는보존됐다. 현재기존CPU2검사로candidate12float의원evaltrace/metadata저장과v1/v2↔v3contract strict거부를확인했다(실제 native동작 검증아님). 실제eval후에도fieldshape/finite/scope를검사한다.

실제73모델은각freshinitial에서CPUhash와비교하고불일치시원래CP/보고서보존후후속평가를중단한다. bootstrap final은미사용이다. 기존43CPU source검수는상위별도code_review기록이며 여기서43개를다시실행했다고주장하지않는다. compactnativefixture와실행가이드README/AGENTS를명시prep입력으로pin했고 root의결과analysis는runtime입력외다.
