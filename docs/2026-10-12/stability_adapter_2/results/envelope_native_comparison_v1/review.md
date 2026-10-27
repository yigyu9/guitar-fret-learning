# 범위의 실제 native 장면 비교 독립 검수

검수자는 이 review만 작성하며 구현·계획·원자료·다른 담당자 파일을 수정하지 않았다. 새 `render_envelope_native.py`, `run_envelope_native.sh`, `ENVELOPE_NATIVE_COMPARISON_PLAN.md` 및 해당 결과를 검수했다. **최종 판정: 문제없음.**

## 사전 판정

**문제없음.** 실행을 막는 오류를 발견하지 않았고 아래 결과 검수에서 실제 PNG·metadata·입력 SHA 및 설명 문서도 확인했다. 이 판정은 정적 설명 장면의 구현 정합성에 관한 것으로, 물리 안정성·접촉·전체 회전 집합 인증을 뜻하지 않는다.

- [render_envelope_native.py:96](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:96): world actor-root 위치 box에 각 장면의 실제 회전으로 계산한 `gr*BODY_CENTER_G`를 더하므로 파랑 box는 이 회전을 고정한 body-center 위치 범위다. 노랑 Pelvis RFU box도 world body-center 좌표로 변환하여 두 상자의 좌표 대상이 같으며, 모든 회전에서 하나의 동일한 파랑 box라고 주장하지 않는다.
- [render_envelope_native.py:23](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:23): 현재 수평/보고 기준은 범위 안의 Euler witness와 실제 quaternion의 동치를 확인한다. 중앙은 비특이 조건에서 두 Euler 해 및 360° 이동을 비교한다. 입력 세 조건의 membership만 검사하며 전체 회전 집합의 일반 판정 구현이라고 주장하지 않는다.
- [render_envelope_native.py:40](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:40): 실제 native view/projection/depth에 설명 선을 투영한다. camera Z가 음수인 기존 `project`와 `z>=depth−.002` 깊이 비교 부호가 정합하며 가려진 선을 옅은 점선으로 구분한다. 선·범위·marker는 충돌 형상이 아니다.
- [render_envelope_native.py:91](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:91), [render_envelope_native.py:126](/home/ajou/yigyu/3/stability_adapter_2/render_envelope_native.py:126): 기존 `UnderneckEnvironment(...,static=True)`의 NoPhysicsGym 경로를 사용하고 이전 입력의 native 상태 exact 대조·렌더 전후 상태 보존·0step·금지된 force/write 없음·입력 SHA를 검사한다.
- [계획:5](/home/ajou/yigyu/3/stability_adapter_2/ENVELOPE_NATIVE_COMPARISON_PLAN.md:5): 정면/측면 t0 정적 장면, 두 위치 box, 실제 기타 회전과 새 재구성 가정을 구별한다. 기존 사용자 범위·제어·원본 결과를 변경하는 작업으로 확대하지 않는다.
- [shell:9](/home/ajou/yigyu/3/stability_adapter_2/run_envelope_native.sh:9): 고정 rl38 runtime과 기존 환경 변수 보존, `"$@"` 인자 전달이 적절하다.

## 결과 검수

**실행·좌표·이미지·최종 문서 검수: 문제없음.** 새 물리 실행 없이 저장 결과를 독립 대조했다. 아래 문서 지적 두 건은 수정 확인을 완료했다.

- 검수자가 세 조건의 정면/측면 annotated PNG **6개 모두 실제 열람**했다. 전신·기타·두 상자·actual body center와 origin·넥 방향·한국어 범례가 이미지 안에서 읽힌다. native 장면과 투영 설명 표시, t=0/물리 OFF와 회전별 파랑 box의 의미가 분명하다.
- 각 case의 report **9개 검사 모두 true**, native 초기화 1/physics step 0/learning 0이다. 이전 배치의 humanoid DOF·body pose·기타 pose exact 대조와 렌더 전후 불변이 통과했다. 세 결과는 동적 유지 시험이 아니다.
- attempt/report의 입력 **각 324파일 SHA**가 동일하며 현재 원문 SHA도 exact다. raw PNG 1280×720, annotated PNG 1280×875, depth 배열 720×1280 및 보고된 6개 raw/6개 annotated SHA를 독립 확인했다. 이전 소단계 보호 **975파일 SHA**도 그대로다.
- 실제 quaternion에서 body offset과 실제 바디 중심을 다시 계산하여 파랑 box/center metadata와 대조했다. 파랑 box 폭은 world X/Y/Z 약 **0.35/0.30/0.2337384m**로 원점 box의 폭을 유지하고 조건별 offset만 달라진다. 팀원 RFU box는 Pelvis 기준 변환을 사용하며 둘 모두 최종 world body-center 좌표다.
- 회전은 현재 수평 `[67.5,90,157.5]°` 및 보고 기준 `[90,68,180]°` witness와 각각 약 2.88444e−16/2.33212e−7 rad 이내 동치다. 중앙의 비특이 두 해는 `[116.1218,68.1745,−152.1556]°`, `[296.1218,111.8255,27.8444]°`이며 360° 이동을 포함한 사용자 box 검사에서 밖이다. 세 실제 후보에 관한 판정이며 전체 회전 집합 인증이 아니다.

## 문서 보완 전달

Critical 없음. 결과 수치나 renderer 변경은 요구하지 않는다.

- **Warning — [README:21](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/README.md:21), [README:41](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/README.md:41):** ‘좌표 정의가 달라 비교할 수 없다’는 설명은 이미 같은 world body-center로 옮긴 구현과 혼동을 만든다. 같은 좌표에서 비교하되 파랑이 각 회전 조건부여서 전체 6축 범위의 포함관계가 아니라는 설명으로 보완한다.
- **Warning — [PLAN:634](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:634), [validation_record:23](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/validation_record.json:23):** 소비된 leaf 계획의 마지막 ‘saved-data postprocessing’ 표현을 참조하지만 실제 원문/보존본 10줄에는 그 표현이 없다. 이 참조를 제거하고 새 native 초기화 3회/렌더 후 overlay/physics 적분 0이라는 실제 범위만 기록한다. 소비된 leaf/renderer는 보존한다.

두 지적의 해소를 확인했다. 최종 README:21/41은 두 box가 같은 world body-center로 변환되어 비교 가능하며 파랑이 회전 조건부임을 명시한다. PLAN과 validation_record의 실제로 존재하지 않는 과거 leaf 표현 참조는 제거됐다. 소비된 leaf/renderer와 source_final은 보존됐다.

## 최종 문서·보존 확인

최종 README/FILE_INDEX의 **60개 절대경로 링크·실제 줄**이 존재하는 파일과 범위에 맞는다. before PLAN·누적 README·VISUAL_REPORT의 본문 전체가 새 파일의 exact prefix로 보존됐다. 이번 append는 새 native 초기화 3회/physics 0step과 기존 범위·제어 보존, 세 회전 점의 한정 판정, source 재현 및 동적 안정성 미인증을 구분한다. source_final 계획/renderer/shell **3파일**은 소비된 입력 SHA의 현재 원문과 exact 일치한다.

[최종 root 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/final_verification.json:1)은 실제 존재하며 status=pass다. 3초기화/physics 0/학습 0, raw·annotated·depth 각6개, 이전 보호975파일의 수치가 독립 확인 결과와 일치한다. final inventory는 예정 경로로만 안내되어 있으며 현시점 생성 완료라고 주장하지 않는다. 최종 생성·봉인은 root 담당이다.

경계 회전의 float32 readback 수치와 witness의 차이는 코드의 **1e−5 rad 미만 quaternion 동치 허용** 안이다. 보고 기준 witness 오차는 2.33212e−7 rad이며 exact 무오차 경계 판정이라고 해석하지 않는다. 최종 README:21도 허용치·실제 오차·float32 경계 정밀도를 명시하도록 보완됐음을 확인했다. 소스나 물리를 다시 실행할 사항은 아니다. PLAN:632의 완료 체크와 최종 footer도 확인했다.

**최종 검수 완료. 미해결 Critical·Warning 없음.** 이 review 외 코드·계획·다른 문서는 수정하지 않았다.
