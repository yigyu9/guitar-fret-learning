# 첫 접촉 조건의 미달6환경·두 하중 급증 — CPU 후속

**미달 대부분은 단순 과도 해제가 아니라 선택 중지 pad의 잘못된 현·프렛 위치이며, 큰 두 하중 급증은 gate ON 중 발생했다.** 이는 최초 시점 억제를 곧바로 채택할 근거가 아니다. 주분석은122/128 달성(2초 억제128/128), 음창 중지 합력 p5013.14N(2초 억제30.23N)이지만 순간 최대와 성과가 악화됐다. 물리·손목 실패는0이다.

기존 결과와 raw는 변경하지 않았다. 미달6환경+음창 최대env8+전체 최대env26만 대조했다. pad 기하 복원은 미달6×음창29와 두 peak±8 endpoint, 총208표본에 한정했다. 실제 run 입력의 함수/mesh/manifest SHA를 확인한 원래 helper를 사용했으며 positive/position/facing 모두208/208 원래 기록과 일치했다.

| 미달 env | 음창 loaded/candidate/wrong 표본(분모29) | 복원된 선택 middle3 own 원인 | 원본·2초A 달성 |
|---|---:|---|---|
|7|29 / 0 / 29|3현6프렛 + 4현6프렛(17표본은2현6프렛도)|둘 다 달성·29/29 candidate|
|39|29 / 0 / 29|3현5프렛 + 2·4현5프렛(1표본은4현만)|동일|
|57|29 / 0 / 29|3현5프렛 + 2·4현5프렛|동일|
|102|29 / 0 / 29|3현6프렛 + 4현6프렛|동일|
|116|29 / 0 / 29|3현6프렛 + 2·4현6프렛|동일|
|43|13 / 4 / 9|접촉 소실과3현4~5프렛·4현4프렛 후보 혼합|동일|

목표는 중지·3현7프렛이다(표의 현은1부터). 다섯 지속 미달환경은 음창 내내 loaded·wrong이고 목표 position/facing·positive는0이므로 단순히 손가락을 지나치게 떼어 놓은 설명과 다르다. 선택 pad 자체의 own_wrong_fret와 own_wrong_string 후보가 기록된 wrong154표본 모두에 충분했다. 다른 finger2/3 전체 pose가 없어 **other_higher의 동시 기여는 확인할 수 없으며 배제하지 않는다.** body load는 실제 잘못 누른 접촉쌍 압력 인증이 아니다.

env43은 clock720~723(3.000~3.0125s)만 올바른 candidate4개이고,724~738 및740은 unloaded다.739·741~748에서는 loaded이지만4~5프렛 wrong이다. 실제 clean/best streak는12.5ms, contact_progress .416667이며 원래 달성에는 미달했다. 그러므로 이 환경만은 unload/missing과 잘못된 위치의 혼합이다. root의 단일 정상 소리·현압력 보증으로 해석하지 않는다.

| 하중 event | clock/시각 | 직전 중지→peak 중지 / 엄지 N | gate·candidate | 같은시각 원본 / 2초A 중지 N |
|---|---|---:|---|---:|
|전체 첫시도 최대 env26|681 /2.8375s|7.924→116.319 /189.975|ON·직전/peak 양성|84.076 /36.081|
|음창 최대 env8|730 /3.041667s|11.530→99.287 /140.191|ON·직전/peak 양성|77.793 /32.071|

두 event 모두 peak 전에 candidate/positive와 body load가 유지됐다. **gate OFF가 먼저라 억제를 우회했다는 설명은 이 두 peak에서 지지되지 않는다.** gate가 켜져도 force cap은 없으며 고정점 target 증분의 한 법선 성분만 제한한다. 새 물리 접촉쌍의 생성·충격/마찰 분담은 이 자료로 판별할 수 없다. env8은 peak 뒤 clock732에 중지힘0·candidate loss가 나타나고, 다음 control(start732)은 gate OFF 상태에서 clock733에 다시 candidate/14.08N이 생긴다. 이는60Hz gate와240Hz 접촉 사이 지연 사례이나 주 peak보다 뒤다. env26 주변17표본은 gate가 계속 ON이다. 둘 다 최종 달성한 환경이다.

peak control의 filtered g·delta는 env26 +1.81e-9m, env8 −3.53e-9m로 수치허용오차 안이다. 같은 control의 접선 목표 변경은 .612/.635mm, 이전 control 대비 arm12 teacher 요청 변화 norm은 .01346/.01035rad다. original 대비 요청차는 .49269/.42886rad,2초A 대비 .20072/.23780rad다. 실제 팔12 관절각은 저장되지 않았으므로 요청차를 실제 팔 움직임으로 부르지 않는다. 다른LH 실제각·목표는 raw에 있지만 접촉쌍/힘의 특정 관절 인과는 분리하지 못한다.

## 같은 시각·같은 고정점의 법선속도 분해

아래는 보간 없이 control-start의 J4와 **동일 clock** physics qd4만 연결했다. body/guitar pose에서 고정 material point 및 COM 점속도를 다시 복원해 일치시켰다. 표는 mm/s이며 +는 press-plane 바깥, −는 안쪽이다. `rest(measured)=actual point velocity−J4@qd4`이고 native closure 잔차도 포함하므로 predicted 나머지도 함께 확인했다.

| env/clock | 선택4 성분 | rest(measured) | rest(predicted) | 실제 합 | closure 법선 |
|---|---:|---:|---:|---:|---:|
|26/676|3.83770|-4.34765|-4.29023|-0.50995|0.05742|
|26/680|4.90045|-5.35771|-5.28498|-0.45726|0.07273|
|26/684|-11.91259|-19.91209|-20.12034|-31.82468|-0.20825|
|26/688|5.78060|-11.94213|-11.94507|-6.16153|-0.00294|
|8/724|1.38690|-10.81723|-10.81198|-9.43033|0.00525|
|8/728|1.58876|-13.50980|-13.51056|-11.92104|-0.00076|
|8/736|-2.39559|-9.62564|-9.61367|-12.02123|0.01197|

env8의 peak 전 clock728은 선택4가 +1.589mm/s인데 나머지가−13.510mm/s라 총−11.921mm/s다. env26 peak 전680은 +4.900과−5.358이 상쇄되어 총−.457mm/s다. 따라서 **선택4의 target 법선증분 억제만으로 실제 고정점 안쪽속도가0이 되지는 않는다.** 나머지 DOF의 운동학 성분이 관찰되지만 어느 관절/teacher가 force peak를 만들었는지까지 입증한 것은 아니다. env26 clock680의 closure .0727mm/s는 작은 상쇄 net속도 .457 대비 무시할 수 없고,5.36mm/s rest보다 작다. 점 복원 최대2.98e-8m·COM 속도 복원 최대1.01e-9m/s이며7개 유효 행이다.

**정확 peak clock681/730의 고정점 분해는 미확보다.** 이때60Hz 고정 J가 없고240Hz nearest sample은 fixed187/135와 다른195/192다. 이전/다음 J를 보간하거나 다른 점의 J를 고정점으로 섞지 않았다. env8 clock732는 gate OFF라 고정 J/velocity가 저장0이므로 값 없음으로 남겼다.105개 qd를 복원하거나 새 native 실행을 하지 않았다.

phase별 main 결과·739봉인·raw는 동결 상태다. case_comparison.csv는24환경조건행, peak_timeline.csv는두17endpoint×3조건102행, selected_pad_geometry.csv는208행, fixed_point_velocity_components.csv는8행(7유효/1미확보)이다. peak_windows.png는 실제 endpoint만 연결한 그림이며 표본 사이 연속 peak/압력 보장은 아니다. 원래 실험의 성공은 자연스러운 저부하/접촉pair·force cap·production 자유손 개선과 다르다.
