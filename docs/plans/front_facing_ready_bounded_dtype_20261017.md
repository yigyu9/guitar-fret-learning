# 실제 유지제어 증거의 혼합 정밀도 재구성

실제 native_baseline_v10은28초6720step 정상완료했다. 원 analyzer10 core29 중28PASS/target ownership만FAIL, 저장719 hand maintenance는모두PASS였다. 별도 실제CPU로719행의bounded vector만False,후속stage AND는모두True임을분리했다. 원failedcore/외부return2와모든물리는보존한다.

Native lower/upper field는F32 copy, Scene8.q_ref는initial_q.astype(float)인F64이다. Motion3이bounds사본에대입할때F32반올림, +1e-6도F32산술이고 qref±.8과max/min에서F64승격한다. 기존analyzer10과초기CPU는모두F64를가정했다. 실제719행모두이혼합경로로각vector exact일치했고,원F64기대와최대약4.77e-8rad 차이다. 기준epsilon이나실제명령을바꾸지않는다.

- [x] 원실패보존·실제719혼합경로독립대조.
- [ ] 새analyzer11은위bounds재구성만교정하고각row에별도bounded체크도기록한다. 원29gate/fit/command/물리문턱유지.
- [ ] 실제719 helper CPU/ULP변조반례·독립FINAL/SHA·RootACK/새before12.
- [ ] Root16은baseline10기존raw읽기전용만허용하고analysis_baseline_v10_retry_v1로출력한다. 새native/action은명시금지. 원물리재실행0.
- [ ] 새core통과후기존source5/remaining6/feet4/media3/manual8/health5/fretting3/hold1로동일baseline후속감사. source/math는변경하지않고manual/fretting의--core만새retry경로를쓴다.

향후action의config.baseline summary anchor연결은이읽기전용감사성과를확인한뒤새계획/runner버전에서명시한다. 이문서만으로기존false anchor를성공으로해석하지않는다. 원EPS0잔차/solver원인False/최종채택False·현힘미검증유지.
