# Root 실제 검증 기록 — fixed-LA 관절 비교

Native session48785는 exit0/한초기화/1200step/5초로 끝났으며 analysis83065도 exit0/17검사를 통과했다. Root는 native/analysis를 재실행하지 않았다. Freshactual14게이트와 selfsource1188쌍,초기81/PD/LAreadback을 확인했다. 두 조건LA는1.1018469719600776m exact이며 held63과1200clock/파형·나머지PDgain/G초기값 동일이다. 초기18과 대응목표만 바뀌었고 gain조절 효과와 혼동하지 않는다.

실제 t0 hands00000과5초 hands00150 PNG를 열어 native캡처·주황route/가림점선·LA표시를 확인했다. 네이티브카메라 영상은 sourceproxy/MuJoCo렌더가 아니다. 차트 QA는 그림 생성 뒤 별도 추가한다.

2초기준 후기변화 위치46.4915867%/회전44.5192475% 개선,초기회전+.025714316°의tradeoff를 모두 기록했다. 초기세계p/q복원·운지연주·반복재현이 끝났다고 주장하지 않는다. 실제손목좌표진폭.146929176→.149525970°는scalarq의동일static기준1Hzfit이며boneSO3가아니다. Palm양의rawλ0/selfcontact0도원자료와대조했다. Rawλ는N이아니며selfcontact0으로모든동적관통0을증명하지않는다. Native각범위미세초과는analysis에남겼다. Passive길이고정이어도route/장력은바뀐다.

Preparation wrapperv1은첫실행에소비됐고그source/metadata/log를그대로보존했다. Native전에검수에서basename평탄copy의입력원문충돌을발견해원형을고치지않고wrapperv2를새로만들었다. v1 preparation사전복사는3개원문이름이고충돌없음, native/analysisv2는원경로를유지한복사와manifest를첫실행전에대조했다. 이보완을물리재시도로집계하지않는다. 실제native실행은한번이다.

이전CPU/Gym경고와같은CUDA없음/CPUPhysX및visualgeom메시지는native.log에보존했다. 완료/finiteness/렌더/원자료확인을그로그와구분한다. 전체sourceprofile6호환/정책연결/actor/학습은미실행이다. 기존phase의원artifact-v1 metadata byte동일성미확인한계도그대로보존한다.

독립검수는review.md,최종입력·원자료·이전phase·영상모음보존검사는final_verification.json에기록한다.

## 그림 첫시도 실패와 v2 보완

첫그림 producer는late값을초기오차scalar의2초차이로잘못검산해렌더전에exit1로끝났다. 실제analysis의late값은world위치벡터변위/quaternion상대회전이맞으며기존독립원자료검증도이를따른다. 잘못된검산을허용하도록tolerance를완화하지않고, 원본producer/SHA a70d4fdab599c2255cd2f53d4d61bbee95b27858fd6180e6625b0db210d66ba5 및사전snapshot/실패로그/명령·exit기록을보존했다. 첫실패실행의input전후SHA맵은별도로저장되지않은한계를실패metadata에명시한다. 원A producer는수정하지않았고새_v2.py/새artifacts/v2/에서원본metrics helper를사전SHA복사해직접재사용한다. Root는v2의지표정의와plot필드·단위를실행전에검토했다. 물리·분석·actor를다시실행하지않았다.

## Root v2 실제 PNG QA 완료

Root가v2 timeseries PNG(SHA82fd434e843fe2fcbd4f0531d807ef68b1a30717efb277ad6b98f6eeb8ab5a65)를실제열었다. 초기world오차곡선의position_error_m×1000/rotation_error_deg와t0..5s/회색2..5s를원자료·producer와대조했다. 범례/캡션이선과겹치지않고수치범위를포함한다. 곡선의initialerror와표의2s기준vector/quaternion변화는서로다른지표임을명시한다. v2 exit0/input199/SHA·sourcecopy141개의기록을확인하며그림을재생성하지않았다. v2 source/PNG/manifest/log/metadata는동결한다.
