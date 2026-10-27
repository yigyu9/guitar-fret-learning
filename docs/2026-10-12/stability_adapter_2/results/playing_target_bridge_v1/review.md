# Playing target bridge 독립 사전 검수

요약 판정: **문제없음**. 아래 SHA의 CPU checker 최초 실행을 막는 코드 오류는 발견하지 않았다. 이 기록은 실행 전 코드 검수이며 checker 본체의 통과 또는 실제 연주 성능을 인증하지 않는다.

검수 소유권은 이 `review.md`뿐이다. 다른 소스·계획·checkpoint·이전 결과를 수정하지 않았고 main/checker/actor/native/학습을 실행하지 않았다. 새 세 파일이 git untracked임을 확인하고 전체 새 코드와 직접 의존하는 범위/원본식을 읽었다.

## 고정 검수 대상

- `PLAYING_TARGET_BRIDGE_PLAN.md`: `fe0b0f93b1196e18c1265d9f8ce35a9a9e77ecab8b6286ed11254aedcee68643`
- `playing_target_bridge.py`: `d43ac8bef6270c1c053a456b23fc09c8f066d49e6b0458511e342dbe316f8ad8`
- `check_playing_target_bridge.py`: `97aac8701ccedca78a65ce73327f06f58067c14ec1f21164ab99095544075411`

## 확인 결과

- Bridge 17–39,59–68행: native81/main66 이름 유일성, source30+30 비중복 소유권, 남은 Thorax6, 동일 EMA alpha를 검사한다. Native/source/normalized 표현 범위 교집합과 유효 native hold를 확인한다.
- Bridge 82–122행: 이전 최종 목표를 source normalized history로 역변환하고 source 절대각+66 residual에 EMA를 한 번 적용한다. 최종 clamp 이후 실제 float32 목표에서 history를 다시 계산한다. 이전 목표의 effective range와 held15 exact를 검사하며 residual cap, action 범위 및 유한 float32 입력을 검사한다.
- 실제 선택 checkpoint를 readonly로 읽어 Fret47000 SHA `681e8b6f282f6ac8e02f4959aa225cfa0520deeb6bf8a5b530e8a34663ac99b3`, Strike10000 SHA `9244b33c87426afb28c10a1176b88f23832a50a57605586d4e28084a48160e87`, 양쪽 scale1/alpha0.5를 확인했다. 실제 source 범위로 만든 작은 pure-function 검사에서 66 residual gradient가 모두0.5이고 source history가 유한했다. 별도 작은 합성 입력에서 held15 exact를 확인했다. 유한 극단 scale/range의 float32 overflow/underflow는 ValueError로 중단하여 비유한 target/history를 반환하지 않았다.
- 원본 유지 PDtarget의 source 범위 불일치를 독립 재계산하면 Fret6관절(`LH:thumb1_x`, `LH:thumb1_y`, `LH:thumb3`, `LH:index1_x`, `LH:middle3`, `LH:ring1_x`)이다. Checker 125–141,209행은 이 유지 target을 음성 사례로 거절한다. 136,226행의 초기 q 비교는 유지 PDtarget 비교와 별도 목록이다.
- Checker 45–54,147–167행의 원본 `Base.apply_actions` AST 추출 및 reference 필드는 실제 원본824–860행에 필요한 값과 일치한다. 원본식80step/batch17 비교, native/source 순서 permutation, 66 gradient, 포화 후 history, 9종 거절, 입력 SHA 전후 동일성 검사가 구성되어 있다. **이 checker 본체는 검수자가 실행하지 않았다.** Python AST/compile 구문 검사는 통과했다.
- Checker 98–123행은 Fret 평가의 checkpoint 경로/contract 연결과 평가 당시 checkpoint 파일 SHA 부재를 구분하고, Strike10000 평가 파일 SHA 및 best-full-song 선택 SHA를 현재 파일과 연결한다. 직접 읽은 Fret47000 full-song recall0.05284974/F1 0.10009813과 Strike10000의64episode/single2688건/strum0건은 좁은 진단 후보와 single-pick 상위 후보라는 계획 표현과 맞는다. `strict_G0_qualification`은 원본 qualification 사실로 보존하고 자유 기타 연주 채택은 false로 기록한다.
- 계획7,23–29,39–42행과 checker231–232행은 CPU target/history 부분 계약임을 명시한다. Source stage/synergy/grip 후처리, 전체 observation/normalization/event clock, actor, native backend 및 추가 actuator/task envelope는 구현·인증 범위 밖이다. CPU 통과를 Full G0 적격성이나 자유 기타 안정화/연주 성공으로 확대하지 않는다.

Critical: 없음. Warning: 실행을 막는 미해결 사항 없음. Suggestion: 없음.

## 최초 CPU 실행 출력 검수

요약 판정: **문제없음**. Root의 최초 checker 실행 exit0 뒤 저장된 결과를 독립 대조했다. 검수자는 checker/main을 재실행하지 않았다. 다른 소스·입력·출력을 수정하지 않았다.

- `contract.json` SHA는 `c4ae203993b9994c1db19598c5fb82d5e15eff0bbb25b071551ddb9dfeefc645`이다. `execution.json`의 exit0, 실행 전후 source3 SHA와 원본/phase복사본, execution.log SHA 및 로그의 checks/mismatches/AST최대차가 contract와 exact 일치한다. Contract의30개 input SHA는 before=after=현재 파일과 모두 일치한다. Native initialization/physics step/actor inference/training update는 실행 기록과 contract 모두0이다.
- 저장 결과10checks가 모두true이며 9종 거절 목록이 소비 checker의 호출과 일치한다. 원본 Base AST80step×batch17 최대차는 `2.384185791015625e−7rad`, 포화 후 history decode 최대차는 `1.1920928955078125e−7rad`이다. 이 두 값은 저장 실행/로그와 소비 코드의 검사식·허용값을 대조한 결과이며 전체 checker 반복 실행으로 재측정한 값은 아니다.
- 실제 checkpoint/profile/native 범위에서 source mapping30+30의 이름·native index·mid·half를 다시 계산하여 contract와 exact 대조했다. 유지 PDtarget 및 초기 q 비교 목록도 별도 재계산하여 각각 Fret6관절, 최대 최소 변경폭 `0.6176479458808899rad`와 `0.6612687706947327rad`로 exact 일치했다. 초기 q 원자료는 이 실험의 `initial_PD_target_rad`(시작 q와 같은 초기 target)이고, 유지 target은 `preserved_absolute_targets_rad`로 구분한다.
- 독립 batch3/단일 pure-function 표본에서 source 절대각+EMA 식과 bridge의 차이0, 전체66 residual gradient0.5, held15 exact, 이전 target 불변, 최종 target→history→target 복원을 확인했다. 두 이름순서 permutation 및80step 전체 결과는 저장 checker 통과 기록으로 확인했다.
- 4checkpoint의 검증된 contract와 qualification/execution metadata를 readonly로 다시 읽어 저장값과 exact 대조했다. Strict G0 qualification은4개 모두false이다. Fret47000/47500은 goal_pair이며 full-song 평가 성능이 낮다. Fret의 평가 연결은 checkpoint 경로+contract SHA이며 평가 당시 checkpoint 파일 SHA 부재를 명시한다. Fret47000의 변경된 implementation 파일 및 event34가 full-song 내부 관측이고 독립 single-event 검증이 아님을 보존한다.
- 3평가 원파일의 metrics, Fret event34, Strike64episode/quality eligibility를 exact 대조했다. Strike10000은 평가 당시 checkpoint SHA가 현재 파일과 같고 best-full-song 선택 SHA도 맞는다. Single2688/strum0 평가이며 wrong-crossing termination suppression 사실을 보존한다. 이 근거를 free-guitar/strum/FullG0 인증으로 확대하지 않는다. Strike10708은 별도 중단 checkpoint이며 이 출력에는 직접 평가가null이다.
- 후처리된 source action의 target/history 부분 계약만 통과했다. Stage mask/synergy/pick-grip 후처리, 전체 observation/normalization/event clock, actor, 추가 task envelope/actuator/COM 관측, native 제어·접촉·자유 기타 성능은 여전히 미구현 또는 미검증이다. 현재 유지 target을 숨겨 clip해 정책을 붙이는 동작은 거절된다.

Critical: 없음. Warning: 현재 CPU 출력에서 미해결 수치·closure 문제 없음. 그림·최종 문서 검수는 이 출력 검수에 포함하지 않았다.

## 최종 그림·문서 추가 검수

요약 판정: **문제없음**. 이번 추가 검수는 새 artifact와 최종 문서에 한정했다. 앞선 bridge/checker 코드 검수를 반복하거나 producer/checker/actor/native/학습을 재실행하지 않았다. 수정한 파일은 이 검수 기록뿐이다.

- `playing_bridge_summary.png`를 실제 열어 확인했다. SHA는 `0cb2d85afa5102ed115412cf1a68228ed51103db6dc58d8772d8a602daf9a690`이다. 왼쪽 Fret 두 F1(.100098/.073486)과 오른쪽6관절×PD/initialq의12막대는 contract 및 producer85–119행과 맞는다. 오른쪽 단위는degree이고 unsigned profile 최소거리임을 축·캡션에서 명시한다. 범례·축·하단 캡션이 막대와 겹치지 않고 수치가 판독된다. Strike와 Fret 지표를 한 값으로 합치지 않았다.
- Degree 재계산 결과 PD6값은5.4300448/35.3886205/28.8655440/11.7291253/5.2835304/11.8232726°, 초기q6값은9.5801360/37.8879097/34.4371479/9.6777360/4.7450588/8.1073355°이다. PNG와 README 반올림 표 및 최대값이 일치한다. 이 값은 선택된 보정각·안정 자세·물리 반응이 아니다.
- Artifact manifest의50입력 SHA는 before=after=현재 exact이며4출력 상대경로 SHA도 artifacts 기준으로 exact이다. Producer source SHA `4192ff9cfcdecfbdd36787e2dabdc172c0a09334341c74808d6095003846e5ef`, producer execution 전후 SHA/exit0/log SHA, source snapshot5개의 원본·복사본 SHA가 모두 일치한다. Producer85–87행의 수치 출처와 manifest/source-only 범위가 맞는다. 추가 artifact native/physics/actor/training은0이다.
- 결과 README/CHANGED_FILES/SUPPLEMENT/ROOT_VERIFICATION_NOTES와 결정/후속 계획의33개 절대 링크는 존재하고 줄번호가 유효하다. Main README985/PLAN1772/VISUAL_REPORT1841의 추가분을 읽었고 `journal_before.json`의3문서 byte prefix SHA가 현재 그대로 보존됨을 확인했다.
- 결과 README29–37행, 결정문 및 main 추가분은4source strictG0=false, Fret 평가 시 파일 SHA 부재, Strike10000 single-pick64episode 평가와 자유 기타/strum 자격의 차이, 전체 observation/후처리/actor/backend 미구현을 일관되게 설명한다. 원본 qualification을 바꾸거나 현재 warmstart를 숨겨 clip하지 않는다.
- 이전−2mm hands 초기PNG를 실제 열어 보았으며 manifest가 이 PNG와 두 원본MP4 SHA를 그대로 참조한다. README39–47행/VISUAL_REPORT는 이전 actual Isaac Gym 캡처 재사용과 이번 CPU phase 새렌더·새영상0을 명확히 구분한다. 공유 videos 폴더의MP4는 현재128개이며 새 collection을 만들지 않았다.
- 후속 `SOURCE_PROFILE_INITIAL_POSE_PLAN.md`13–31행은 손6 초기각/유지목표만 변경,75각/목표 exact 보존, 초기값 설정은 초기화에만 수행, 현재 PhysX limit을 source profile로 교체하지 않음, fresh native actual pose/readback/filters/PD 및 전체 source self admission을 별도 구현·코드 검수하도록 명시한다. 기존18변수 FK 인증을 finger1 변경에 확대하지 않는다. Root가 미실행 계획의 부정확한 ‘두 finger1’ 표현을 ‘finger1의 여러 축 관절’로 정정한 최종본을 확인했다. 손6 중 thumb1_x/y·index1_x·ring1_x의4 DOF가 해당한다. 이 후속 계획의 geometry admission은 향후 PD/contact·cooked mesh·연속 지지 성공 인증을 대신하지 않는다.

최종 검수 시 결과 README SHA `eccbae6afdb6f261e2aa60ce86e9decf3f19fa90d1e5319eb6dc5514904935e3`, 결정문 SHA `4dd170069f27b27f94f3fa675c8a35a08c52e76c6a3c82f0ff0fca7f0db07c45`였다. 후속 계획 최종 SHA는 아래와 같다.
`6b7099c9f8b3c4ceb6c3a3f85a603860be26713d465d05fe08ec156af2a00798`

Critical: 없음. Warning: 미해결 그림·수치·문서 범위 문제 없음. 최종 보존 audit/seal은 root의 별도 책임이다.
