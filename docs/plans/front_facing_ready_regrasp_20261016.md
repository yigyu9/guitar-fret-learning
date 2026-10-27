# 초기 자세 재접촉 실제 닫힘 판정 보완

본 보완은 최초 새 source/물리 실행 전에 정의하며, 앞선 전체 계획의 정지·해제·타현·지지 문턱은 유지한다. 재접촉을 단순 손목 도달 또는 palm/몸통 접촉으로 대신하지 않는다.

닫기 시작 시점의 실제 손가락 관절값을 기준으로 한다. 원개방 검사에서 사전선정된 active축마다 d=sign(2396step의 닫힌 최종목표−개방목표), required=min(.10rad,.5×사전예상 명령개방량)을 계산한다. 닫기 이후5초 dwell의 모든240Hz 표본에서 같은 한 축 이상이 d×(현재actual q−닫기시작actual q)≥required와 |actual q−2396 닫힌목표|≤.10rad를 동시에 만족해야 한다. 시간마다 서로 다른 축을 선택해 대체하지 않는다. 입력에 없는 회전성분을 새 채널로 추가하지 않는다.

동시에 원물리 neck에 실제 LH 손가락이 양의 lambda로 접촉하는 표본비율95% 이상, 실제 손목의 초기grasp G-relative 위치참조 대비2cm 이내, 원기타/몸통/발/삼중지지 기준을 모두 요구한다. neck의 실제 collision-enabled body명은 원자산/기존nativeproperties와 대조해 spec에 사전 저장한다. 현/표식/proxy/palm/팔·몸통 접촉으로 neck-finger 접촉을 대신하지 않는다. lambda는 보정된압현력N이 아니다.
