# 실제 완료 원자료 독립 검수

change-reviewer가 training_v2를 읽기전용 검수했다. 최종 판정: 추가 문제없음.

- CRC를포함해전이2048행/4096개를끝까지읽어sampled/logged/durable/committed일치와유실0을확인했다.
- 양worker는episode0의1969tick/32.8166667초에targets=expired=67로완료했다. LH각1/RH0·2/협응0/원50·100ms각0이며음악성공False다.
- 이후episode1각79tick을수집했고rollout경계의중간reset/시계단절은없었다.
- Root고정/기타free·중력ON/금지API0/exit0을확인했다. scene각create1/destroy1/loadasset2/reset기록2,원nativeidentity보존과persistent감사통과다.
- inputs1753개현재SHA불변. final.pt는updates8/state500/67targets/런타임계약exact/발행SHA일치/Adam35·19다. root의실제strictload검사와일치했다.
- 실제과거joint PPO를새SongPolicy+전곡config로읽었을때schema/architecture/input/control/config mismatch로명시거절되는것도CPU확인했다.

두완주궤적은PPO업데이트가사이에개입한학습중episode다. final.pt고정정책의전곡성능평가나전곡음악숙련성공으로설명하면안된다. 검수자는원자료를수정하거나native실험/학습제어를수행하지않았다.
