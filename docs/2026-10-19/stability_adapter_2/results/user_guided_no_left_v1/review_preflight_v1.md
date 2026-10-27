# 사용자 기준 자세 첫 source 진단 사전검수

요약 판정: 문제없음. 사용자15각과기타중심의선언한해석이맞으며 현재출력은 source진단으로만사용한다. 소비파일수정·native재실행은하지않았다.

Critical: 0

Warning: 2

- [진단기:20](/home/ajou/yigyu/3/stability_adapter_2/diagnose_user_guided_no_left_v1.py:20): config/manifest/XML읽기후전체inputs map을만들기전에앞선discovery SHA동일성assert가없다. **다음소스버전에서discovery/guitar-discovery와전체map을대조하는기존패턴을복원한다.** 이번실제저장discovery/input/current993SHA는모두일치하므로이번진단입력근거는유효하다. 소비V1을고치지않는다.
- [진단기:31](/home/ajou/yigyu/3/stability_adapter_2/diagnose_user_guided_no_left_v1.py:31): 목표(.175,−.05,.665)는local-bodyBB중심을world변환한점으로정확하다. actualworld축AABB중심은(.17500328,−.04931040,.66388971)로약(0.0033,0.6896,−1.1103)mm다르다. **현재지표를body-localBB중심의world변환점으로명시하고world축AABB/COM과구분한다.** [계획:3](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V1.md:3)의선언한actorroot변환정의와계산은일치한다.

Suggestion: 0

- [진단기:28](/home/ajou/yigyu/3/stability_adapter_2/diagnose_user_guided_no_left_v1.py:28): 사용자Torso/Spine/Chest/RThorax/RShoulder15개값을각각이름순xyz의DOF scalar로deg→rad변환한다. 실제81벡터와전부동일하고현재native모델한계안이다. 다른66각은seed값그대로다. suffix를worldEuler축으로해석하지않는다.
- [진단기:30](/home/ajou/yigyu/3/stability_adapter_2/diagnose_user_guided_no_left_v1.py:30): 현재G:body collisionpiece의localBB중심을계산하고이전native기타quaternion/넥방향을유지한다. gp=(−.224920288,.005725060,.674356234)m이며gp+R*centre=사용자centre를1e−15이내확인했다. actorroot좌표와사용자중심좌표를혼동하지않는다.
- [진단기:18](/home/ajou/yigyu/3/stability_adapter_2/diagnose_user_guided_no_left_v1.py:18): 실제config/candidate/reference/native초기값/helper/원XML·human37/guitar69 및manifest/XMLunion70mesh가before-map에포함된다. 실제입력전후SHA와AST대조가통과했다.
- [진단기:33](/home/ajou/yigyu/3/stability_adapter_2/diagnose_user_guided_no_left_v1.py:33): 현재audit는hip와LEFT/기타 source겹침을발견해source_clear=false다. 이는주어진각도/위치의첫진단이며현재값을native수락이나왼손분리·5초유지로설명하지않는다. 머리world조정/LEFTfit/strike영역손위치/soft범위검색은다음단계의계획이다.
- [계획:7](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_PLAN_V1.md:7): 이후runtime에는기존full81중body9+팔24=33EFFORT/머리6+finger42=48POSITION·유한human보정/중력PD구조가적절하다. 손가락42는목표각유지이고전체상체33관절만움직이는제한으로되돌리지않는다. LEFTtrackingOFF/contact0·rootlower고정·Gfree/strapOFF·원asset·안전한계와native초기FK/모델검사를새후보에서별도확인한다. 현재진단은실제controller나native실행을하지않는다.

- 진단 source SHA256: `3a045ec8b7421dae67a5481495ceb1182a1d19c4ce26393c03957317e6b021dc`
- Plan SHA256: `fef046b0493a8e48d7015421bbd901a1e25d39b03656c8913f6168bc157605d6`
