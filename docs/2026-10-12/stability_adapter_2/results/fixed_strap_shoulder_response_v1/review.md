# Fixed-strap shoulder response 독립 사전 검수

요약 판정: **문제없음**. 현재 준비/native/분석 코드에서 최초 실행을 막는 오류는 발견하지 않았다. 검수자는 prepare/wrapper/analyzer main·checker·native·actor·학습을 실행하지 않았고 이 기록 외 파일을 수정하지 않았다. Git상 네 대상이 새 untracked 파일임을 확인하고 새 전체 코드와 재사용 runner 관련 계약만 읽었다.

## 고정 검수 대상

- `FIXED_STRAP_SHOULDER_RESPONSE_PLAN.md`: `be7a741eeb4a932914ac364b794bdafa21788defa72d9a06fc4f6f8abffe0c85`
- `prepare_fixed_strap_shoulder_response.py`: `b33422946668d41c4fdfa39a517843c842f2b5eb8b57639acfc53c0951b7b725`
- `run_fixed_strap_shoulder_phase.py`: `cb570f60b594c22f83dc83c9141675d718ed25147466f0596ecd8afc0b33fa3a`
- `analyze_fixed_strap_shoulder_response.py`: `2a518e81b1fbd0a4e5d323ccbf94977d69e7b60c57301d8e5865456502c33a72`

## 확인 결과

- Prepare11–17행은 기존 joint-only proposal의 checks/전체11460 input SHA와 trial SHA를 먼저 검증하고 덮어쓸 기존 SHA가 같은지도 확인한다. 새로운 두 row는 초기81q/source_state/G/LA/gain/geometry admission 정보를 유지하고 `L_Shoulder_y`의 유지offset만±.008rad 바꾼다. 25–31행의 other80 exact/native bound/offset±.3/손목±.005극값 gate가 목적과 맞는다. 33행의 finger_target_policy도 shoulder offset probe 예외를 명시한다.
- 현재 baseline 원자료에서 독립 pure float64합성→float32 target 조립으로 확인한 실제 목표delta는−0.008000016212463379/+0.008000016212463379rad이다. Shoulder_y 목표는−0.9194518327713013/−0.9034518003463745rad이고 other80은 exact이다. Native bounds/offset±.3/wrist두극값을 모두 만족한다. 초기81각을 바꾸거나 source geometry FK 인증을 다른 자세로 전이하지 않는다.
- Frozen native entrypoint와 runner SHA가 기존 봉인값이고 wrapper14행에서 exact 강제된다. Runner는 각 row의 trial SHA와 proposalclosure/미인증support 이유를 검증하고 fresh14/q/FK/LA gate 뒤1200step을 진행한다. Command의 shoulder 축은 해당 row baseline목표이고 손목 파형만 주기적으로 더해진다. 두 trial을 각1init/1200step으로 집계하고 partial을 성공으로 표시하지 않는다.
- Wrapper11–25행은 각 stage별 no-overwrite, 순수입력 SHA 전후와 R-relative 사전복사/manifest/복사SHA를 유지한다. 이전 basename충돌 방식으로 돌아가지 않았다. Analysis wrapper는 두 initial-audit까지 포함한 현재39개 직접 입력 경로를 사전해시하고 helper/source를 보존한다. Analyzer 자체 맵은 wrapper자신을 제외한 예상38개다. 첫 준비 wrapper소비와 native/analysis소비를 구분해야 한다.
- Analyzer14–19행의6D world error는 `p−p_goal`, `Log(R_current R_goal^-1)`이다. 함수만 AST로 compile하여 저장 baseline1201states에 적용한 작은 pure 검사에서 shape1201×6/finite이며 기존 trace 위치norm과≤1.74e−18m, 회전norm과≤2.04e−8° 차이로 맞는다. 이것은 새 물리 또는 분석 main 실행이 아니다.
- Analyzer27–51행은 양끝 포함4평균window(0~.1/.1~.5/2~5/4~5s), 동일13개 초기필드, shoulder offset외 trial불변, other80의1200목표/clock/waveform, shoulder 실제float32 constantdelta, 모든1200target 재구성, fresh14/self1188,151frame readonly/604PNG,1201/1200coverage/rootlower를 검사한다. 접촉rawλ·body9/nativebound·strap law/초기·late metrics를 별도 요약한다.
- Analyzer60–65행은 실제delta로 forward/backward/central secant를 계산하고 W=diag(1,1,1,.1,.1,.1)를 norm/LS 분석에만 사용한다. Central secant 자체는 unweighted world6D 열이다. 중앙과양·음 응답 불일치/국소prediction잔차를 기록한다. 계획의 rank명시와 맞추어 root가 미소비 analyzer에 sampled-column rank0/1 및 upperbound1을 추가한 최종본을 확인했다. 이 단일축 rank는66rank/접촉력/순간Jacobian 인증이 아니다. Unbounded1D LS delta는 진단값이며 새offset/gain/box 또는feedback 채택값으로 자동 사용하지 않는다.
- 계획은 이전 seed2 응답 전이, 특정palm접촉/WAIT의 강제선행, 기타목표 외력/지속pose덮어쓰기를 도입하지 않는다. 현재G오차를 읽는 feedback 이전의 두 정적 목표probe이며 초기worldG 복원/연주성공/66제어가능성/반복재현은 아직 검증하지 않았다. Source LP/cooked contact/λ N의 구분을 유지한다.

Critical: 없음. Warning: 미해결 사전 실행 blocker 없음. 이 검수는 실행코드·현재입력의 사전계약 검수이며 새 두actual결과·secant 숫자·영상은 완료 후 별도 원자료 검수가 필요하다.

## 네 영상 collector 사전 검수

요약 판정: **수정 권장**. Native 실행 blocker는 아니며 정상 완료된 두 frozen report를 받은 조건에서는 원본보존·130→134 수집 논리가 맞다. Collector main을 실행하지 않았다.

대상 `collect_fixed_strap_shoulder_videos.py` SHA `c34dffb95309fc3a04b0728f722778d07a8ba7070ae084db607b21defbcd952f`. Git상 새 파일이며 AST compile 통과했다. 7–8행은 새index/update 부재와 기존130개를 검사하고14–15행은 새목적지 부재 및 source/copy SHA를 대조한다. 17–20행의v7 제목/설명·v6전체 suffix보존·134개 확인·update-v6 기록이 계획과 맞다.

Critical: 없음.

Warning: `collect_fixed_strap_shoulder_videos.py:11–15` — minus report 검증 직후 두 영상을 복사하고 그 다음 plus report 완료를 확인한다. Plus가누락/partial이면 두복사본만 남고index/update 없이 실패하며 동일실행재시도는130개 조건 또는dest부재 조건에서 중단한다. 두report 완료·각views={hands,whole_body}·네sourceSHA·네dest부재를 mutation 전에 모두검사하고 이후copy를 시작하도록 보완권장했다. 이 지적은 미래source읽기/preflight 실패에서 partial수집이생기는 범위에 한정하며 현재실제physics결과 실패를 주장하지 않는다.

실제 네 MP4·134개 collection·새index/update 출력 검수는 collector 완료 후 별도 범위이다.

### Collector 미소비 최종 보완 확인

요약 판정: **문제없음**. Root가 최초 실행 전에 같은 미소비 collector를 보완했다. 최종 SHA `0bccf1019da08c1570213ae55b4b9b592bb9614bd95d259abe2f949d3b75206c`, AST compile 통과. 10–15행에서 두 report 완료/각2view/네sourceSHA/네dest부재를 모두 검사해 pending에 모은 뒤16–18행부터copy하므로 위 Warning의 source/preflight 실패 시 부분수집 문제는 해소됐다. 미해결 실행 blocker 없음. Collector main은 실행하지 않았고 실제 출력은 후속 검수한다.

## Artifact producer 미실행 사전 검수

요약 판정: **문제없음**. Root/Luna의 미소비 보완 후 `make_fixed_strap_shoulder_artifacts.py` SHA `04e4343b3e7397ddc59c1f1da75f3637b14e0648b0a4178e8748f0d4eaac0cbe`를 읽었다. Python3.8 AST compile 통과, artifacts 출력 폴더는 아직 없다. 검수자는 producer/분석/native를 실행하지 않았다.

- 24–35,83–99행의 SOURCE_FILES에는 producer자신이 포함되고 input_paths가그전체를추가한다. 따라서127행 self-SHA 조회KeyError가생기던 미완성입력목록 문제가 해소됐다. 131–138행의baseline label은실제analysis의 `baseline`과일치하며 잘못된`current18_baseline`을조회하지않는다.
- 55–71행은첫실행의 producer/helper/source를R상대경로로복사하고copy SHA를확인한다. 122–130행은 analysis input SHA를대조한뒤보존된원metrics helper를로드한다. 102–108행은3조건각1201trace/0~5초및원metric요약을검산한다. 앞단계의잘못된scalar차이 late공식을재도입하지않았다.
- 149–167행의 두panel은초기world위치오차×1000mm와회전오차degree,시간0~5초·2~5초음영이다. 네범례항목(음영+3조건)을데이터바깥아래에두도록구성한다. 곡선의initialworld오차와2초pose기준late변위는캡션에서구분한다. Actual PNG의겹침/가독성·수치는최초생성뒤독립QA가필요하며코드만으로통과를인증하지않는다.
- 172–190행은 input전후/self SHA를비교하고 rootaudit가예상한 `producer_sha256_before`/`producer_sha256_after`를manifest에저장한다. No-overwrite 및native/physics/actor/training0의saved-data범위가맞다. 실행command/exit/log metadata와실제manifest/outputSHA는생성후별도대조해야한다.

Critical: 없음. Warning: 미해결 producer 사전 실행 blocker 없음. 아직actual 분석출력/최종그림/실행closure를검수한단계는아니다.


## 완료된 native·분석·수집·그림·최종 문서 독립 검수

요약 판정: **문제없음**. 검수자는 저장 원자료 읽기와 별도 NumPy/SciPy 계산, MP4 ffprobe 및 실제 PNG 열람만 했다. 준비/runner/analyzer/checker/producer main·actor·학습·물리를 재실행하지 않았고 이 review 이외 파일을 수정하지 않았다. 기존 사전 검수와 구분하여 아래 실제 완료 범위를 추가한다. 최종 보존 감사/봉인은 root의 별도 후속 작업이다.

### 실행 계약과 원자료

- 두 report의 completed/failure 없음/1attempt·1init·1200step·constraint_violations 빈 목록, 모든 native checks를 확인했다. 세 조건 각각 states/trace1201행 및 controls/contacts1200행의 전체 step/time coverage를 직접 대조했다. 두 새 fresh audit는14checks/1188 source self쌍/교차 없음이며 기준선 audit와 원문 내용이 exact다. 새 초기 q/G/source 형상은 기준선과 같고 지원완료 source_support_search_passed=false를 유지한다.
- `analyze_fixed_strap_shoulder_response.py:28`의13공통 초기필드 및 t0 전체 human/G state가 세 조건 exact다. 입력 trial에서 shoulder offset을 복원하면 기준선 trial과 exact다. 각 probe의1200 command 모두 나머지80target·clock·updated_before_step·wrist waveform이 기준선과 exact이며 실제 shoulder target차는−/+0.008000016212463379rad다. float64 offset합성 후 float32 target을 독립 재구성하여1200개 모두 exact, native target경계/±.3offset을 확인했다. 손목은 공통±.005rad·1Hz이고 초기18 후보와 held63의 기존 상태 관계는 유지된다. 이번 변경은 초기18을 다시 바꾸는 시험이 아니다.
- 모든1201state에서 root/Pelvis·하체 링크가 t0와 exact다. 몸통9 목표·PD2 유지와 실제 coordinate drift 약3.533~3.549°를 구분한다. 실제 q의 최대 native bound초과 약9.98~9.99e−5rad도 분석 원자료와 맞으며 목표 clipping이나 강제 상태 고정으로 숨기지 않았다.
- 분석29checks/38입력 SHA 및5stage execution의 input전후/current SHA·exit0·로그 SHA를 확인했다. Wrapper 입력 수는 preparation3, minus/plus 각11469, analysis39, collection8이다. 원문 사전복사 manifest의 preparation3/minus128/plus128/analysis9개 original→R-relative snapshot SHA가 모두 exact다. Analyzer38과 wrapper39 차이는 wrapper 자신 포함 여부로 설명된다.
- 두 capture는각151frame, step=8j/time=j/30/render_preserves_states=true이고 overlay+raw604PNG씩 총1208개의 저장 SHA를 전수 대조했다. 각4MP4를 ffprobe로 읽어1280×720/30fps/151frame/5.033333초 및 원본 SHA를 확인했다. Collector4복사 SHA/size·indexv6 SHA불변·v7의v6전체 suffix보존·updatev6 SHA·실제134개 수가 맞다.

### 수치와 secant 독립 재계산

`analyze_fixed_strap_shoulder_response.py:14`의 world6D 정의에 따라 저장 body p/q에서 p−p_goal 및 Log(R_current R_goal^-1)를 별도 계산했다. 모든1201행의 trace norm과 일치하고 양끝 포함4window 평균·실제float32 delta·forward/backward/central열·W norm·unbounded LS·rank1이 저장값과 맞는다. Quaternion 경로 차이로 생기는 회전 재계산 차이는1e−6° 미만이다.

| 지표 | 기준선 | −.008rad | +.008rad |
|---|---:|---:|---:|
| 최대 초기world 위치오차 mm | 14.084222893 | 15.989064226 | 11.926351230 |
| 최대 초기world 회전오차 ° | 2.920042117 | 2.862552945 | 3.169993195 |
| 5초 위치오차 mm | 13.788517868 | 15.471011383 | 11.848155822 |
| 5초 회전오차 ° | 2.919708139 | 2.862350027 | 3.138566142 |
| 2초pose대비 후기 최대 위치변화 mm | .257785610 | .794536077 | .286205939 |
| 2초pose대비 후기 최대 회전변화 ° | .051002962 | .136578782 | .052760892 |
| Cable law peak N | 24.625970525 | 30.180332576 | 24.943809137 |

- Late 지표는 initialerror scalar 차가 아닌 t=2초 위치벡터/quaternion 대비 변화임을 독립 확인했다. 저장1200개 적용 장력은 직전 trace의13점 경로/속도에서6000/120/300 cable law를 별도 계산한 값과1e−8N 미만 오차로 맞고 first positive step은39/39/40이다. Raw contact λ는 N으로 변환하지 않았다.
- Human self-contact 기록은 세 조건0, palm–G positive rawλ는0이다. Thumb3 positive step은116/675/9, index3는1154/1156/1145, middle3는15/62/18, RHip은모두1200이며 minus에 ring3 22step이 추가된다. Minus thumb3는39~1067, plus는35~43step에만 양값이 관측되어 연속 grip으로 확대할 근거가 없다. 모든 body별 step집계를 원자료에서 재계산했다.
- 4~5초 weighted central norm=.341915178965669m/rad, forward/backward 차이=.173535170469521m/rad, 비율50.753865620849%다. 두 국소 선형 잔차는각.000694142088594m이며 단일 관측열 rank1/상한1이다. Unbounded LS+.027680034091812rad는측정±.008rad 밖이다. 0~.1초 plus평균은baseline과 exact여서 forward열0·불일치200%이고 큰 역보정 근거로 삼지 않는다. 시간평균 접촉응답을 instantaneous Jacobian/6D·66rank/폐루프 안정성으로 인증하지 않는다.

### 실제 그림·provenance·최종 문서

- 실제 chart PNG `d19d03ba92e80f3a13d3e0405686746421090e250ed84c2cf8aba2f1e93bb234`를 열어 두panel/세곡선/초기world 기준/mm·degree/0~5초/2~5초음영/색상·범례4항목·원자료 최대값을 확인했다. 범례와하단caption은축/데이터와겹치지않고 전1201표본 표시범위가맞다. `make_fixed_strap_shoulder_artifacts.py:149`의위치×1000 및회전1배가 표와일치한다. 별도 native hands t0/minus5초/plus5초 PNG도열어 실렌더와주황경로/LA1.101847m표시를확인했다. Plus t0는minus/base t0와SHA exact다. CPU curve를 native 렌더로표시하지않는다.
- Artifact producer SHA `04e4343b3e7397ddc59c1f1da75f3637b14e0648b0a4178e8748f0d4eaac0cbe`, manifest/metadata69입력전후/current SHA·11개 producer/helper/phasewrapper/plan 사전사본·PNG SHA·log SHA·exit0가맞다. Artifact native/physics/actor/train0와실제phase native2/2400을구분한다. 외부 shell호출의command/env는metadata에있지만별도호출script를실행전에archive한기록은없다. `ROOT_VERIFICATION_NOTES.md`의그좁은보존한계표현이정확하며 사전wrapper별도원문보존으로확대인증하지않는다.
- 최종 README SHA `9ab081ab374a773c2692090ad5b86e9abfe1269347e9997078fa9ebb9457a866`, CHANGED_FILES SHA `c1d8e510a310fb64f42bf2955e84515b22ee081f15945e9eeadb837c420145b3`를확인했다. 한국어보고/절대클릭링크·4영상·실제프레임·chart구분·원metric의late정의가맞고모든직접파일링크가존재한다. ROOT_CHANGED_FILES/ROOT_VERIFICATION_NOTES, 결정문서 및 main README1013/PLAN1811/VISUAL_REPORT1877(§102)의기준/current18·LA·수치·134영상·새actor/train0 범위가일치한다.
- `FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md:19`의기준유지/별도Wrist_y양방향응답후유효범위내boundedresidual검토는현재tradeoff/비대칭/외삽한계와정합하다. 후속Wrist_y는아직미실행이며이번자료를자동feedback·초기world완전복원·연주성공·반복재현·전체66제어가능성으로확대하지않는다. Source-profile6/교사checker/actor/training도이번단계에서실행하지않았다.

Critical: 없음. Warning: 미해결 중대 문제 없음. 별도 외부 그림호출script의 사전원문보존 부재는 위와 같이 공개된 기록 한계이며 원자료/소비소스/그림을 재실행·변경하여 보충하지 않는다. Suggestion: 없음. Root의 최종 보존감사/봉인 진행에 검수 blocker 없음.
