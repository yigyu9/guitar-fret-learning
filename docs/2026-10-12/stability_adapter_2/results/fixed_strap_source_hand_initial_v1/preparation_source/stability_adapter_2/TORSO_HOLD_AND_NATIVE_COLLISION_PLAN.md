# 다음 단위: native 충돌형상 확인과 몸통9 PD 유지 비교

손바닥 source gap은새초기.421670mm→step4(.016667s).151185mm로더가까워졌다가.1초5.792735mm로커졌다. 그런데palm native첫contact/양λ는step125(.520833s)이고요청옆면근접행은0이다. 따라서source초기형상근접과native처음접촉을동일시할수없다. Cooked/active shape·margin조건을먼저확인하고,단순초기각검색을늘리지않는다.

실제palm sourceanchor world변위를분해하면 .1초Chest자세기여15.019088mm/Chest기준팔chain기여11.579934mm,5초73.186215/41.464612mm였다. 이값들은각vector norm이고서로상쇄하므로합을전체변위로쓰지않는다. 정확vector합은재계산으로검증했다. 실제몸통최대좌표drift4.231250°는사용자의‘Torso~Chest 최소움직임’과관련된개선지점이다. Root/하체는이미물리fixed다.

1. 저장trial의동일initialq/G/LA를새native환경에서조회하고 use_collision_geometry=true 카메라와일반camera의초기장면을비교한다. Actor/body/shape mapping/filter와source에대응하는활성collision표현을확인한다. 이초기검사는physics0이며원자료/이미지와실행집계를분리한다. Camera렌더만으로cooked최단거리/관통없음을인증하지않는다. 기존source/native영상/형상은수정하지않는다.
2. 같은palm_wide_near17초기값/기존절대81목표/LA/양팔·손gain/solver를유지하고Torso·Spine·Chest9 stiffness만×2, damping×sqrt(2)한actual5초한회를새출력에기록한다. Scalar second-order관점의damping비율heuristic이지결합몸통의critical damping인증은아니다. Baseline×1은이미완료한current5초원자료로비교한다. Initialbodyq와PDtarget은바꾸지않는다. 이는물리jointPD이며관절/기타stateoverwrite/고정이아니다.
3. 새runner가정확히9관절gain만변경하고다른PDproperties/목표/initialstate를유지하는지readback/AST/SDK검사를한다. 진행중각/몸통/기타finite·root/lowerfixed·oldtargets/oldLA를기록한다. 목표유지와실제몸통움직임을구분한다. 두카메라raw/스트랩표시0~5초151frame,초기값/실제PD9 gain/SHA를저장한다.
4. 실제Chest/palm 초기이동,요청옆면접촉feature·thumb후면/전면지속성과Gworld p/q최대/종료로채택여부를판단한다. 개선없으면gain을새기준으로채택하지않는다. 기타p/q feedback·palm task보정·학습구조는측정후별도소단계로결정하며최종66연주권한을유지한다.

- [ ] native 초기 collision/visual·shape mapping 확인
- [ ] body9만 PD×2 한actual5초·스트랩영상/불변성
- [ ] 원자료/초기이탈·기타오차/면근접 비교·후속유지제어

계획은미실행이다. 몸통PDgain변경은사용자의자율진행승인과최소움직임목표에근거해다음단위에진행한다. 소스/기존gain·경과를덮어쓰지않고별도runner/output을사용한다. 기타gravity/contact/passivestrap,root하체fixed/몸통9기존target/최종66제어권·자유기타복원/유지/연주안정화의전체목표를이어간다.
