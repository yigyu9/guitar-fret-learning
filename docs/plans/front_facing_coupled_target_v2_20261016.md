# 정면 자세: 몸통 공동 목표와 가슴 상대 전진 보완

native1은Chest5.31068°로실패했다. native2의Chest-only0.8°직립 목표는Chest최대4.88024°로개선했으나 Torso5.03331°/Spine5.22696° 및 유지가슴접촉0%로실패했다. 발·heading·기타변위·원제어산술은유지되었다. Spine실제접촉은두실행모두유지100%이며,새로Spine접촉이생겼다고해석하지않는다. 원시각관절·접촉·sourcegap전체진단은diagnosis_target_v1에있다. 거기5.317/6.219N은legacy3mmforce이며최종9.25mm요청으로해석하면안된다. 최종힘은새diagnosis_target_v2에서분리검사한다.

다음후보는Torso/Spine/Chest의worldorientation에동일한0.8°직립회전을적용한뒤Spine만공동goal에서world앞쪽0.3°굽힘을추가한다. Chestworldgoal은공동직립값을유지하여Chest와Spine의상대위치변화가다르도록한다. 이는이전통과자세posture_target_v2의상대전진아이디어를새source7에검사하는가설이다. 이전성공으로인증하지않는다. 예측gap/상대전진·실제native접촉을구분한다.

Root/의자/초기source7/G초기배치/하체/손가락·원limit·8zero 불변,원K/D/cap/rate·Chestdepth7→9.25mm·원bias/right-world가설불변. 필요LH12와HeadNeck6목표는world pose보상을한다. 오른팔최종목표는runtime worldIK소유임을구분한다. 직접G힘·부착·매stepstate주입·학습없음.

target_v2와새config/새native출력으로원25기준전체를다시검사한다. 원5°·지지95%·발95%/sole·heading2°target/5°actual기준완화는없다. 통과후같은설정으로반복한다. 이미소비된source/계획/config/log/raw/diagnosis/리뷰는수정하지않는다.
