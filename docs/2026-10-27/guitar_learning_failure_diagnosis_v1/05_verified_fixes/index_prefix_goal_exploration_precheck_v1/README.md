# 목표각 모델의 후보 탐색폭 사전대조 준비

원70e/PPO0/지도1000 모델을 원GoalPolicy·원계약/metadata로 full strict load한 뒤 선택action17..20에대응하는 finger_log_std[0:4]만공식후보log로바꾼다. 원checkpoint/다른72state/나머지12finger std·effective39std중35개/평균·critic/관측·settings/물리·9보상은유지한다. 저장모델/분포동일성이아닌명시적execution override이며 새checkpoint·fit/PPO는없다.

각조건 --execute deterministic / --execute stochastic, 출력 runs/<mode>. 두명령은 cpu_inputs/commands.json에게시한다. 원fullstrict load의RNG복원후 seed7을다시고정하고 원prefix evaluator는정책호출flag True를요청한다. 얇은proxy가요청True와실제True/False를구분하며 원policy.act의mean/log_std/latent/action/logp를그대로사용한다. stochastic actor호출의RNG전진과개입후모델고정은별도감사한다. 구old model+RNGfrozen콜백/finish는호출하지않고 execution_override.json에이를명시한다. 전체RNG변화와actor호출전진도구분한다.

원GoalPool의변환은전control한번, NN은첫tick부터며 reference/N호출0이다. 원128cap/native105/90쌍·원범위/4rad/s/PD/손목v3/currentgoalDIPguard/비선택B·엄지035·3음시계·128첫시도실패포함분모를재사용한다. 원env0 60Hz trace·4env관측/typedgoal·128guard를같은형식으로남긴다. 실제sampling모드는새sidecar에명시하며 원evaluation의condition='policy'만으로deterministic이라고해석하지않는다.

모든출력은새경로만·기존/깨진symlink거부,finally복원·장면닫기/입력전후검사는원base launcher를재사용한다. root만두native scene을직렬실행하며CPU준비PASS는실제성과가아니다. 후보는전역L상한공식하나이며가동범위축소·최적std·모집단잡음꼬리0·실제관절/힘/PPO효과를뜻하지않는다. 원fit exit1·명시적회복수용이력과음악126/해제73·후속PPO미충족은유지한다.

공식float64 sigma와실제float32 log→exp std를따로기록하며, L×공식sigma(수학적nominal상한)와 L×실제effective std/nominal대미세잔차도 execution_override.json에별도로남긴다. 최초CPU검사의임의rtol2e−7은 log/exp왕복잔차2.0043e−9에서실패해 before_cpu_fix_01/에보존했고, 최종검사는 원float32적용경로 exact와공식대잔차보고로명확화했다. 계수조정·후보선택은없다.
