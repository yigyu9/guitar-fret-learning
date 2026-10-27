# 높인 허벅지 후보의 발 여유 보완

Hip−.08rad의source8은오른무릎을28.975mm높이지만발전체를5mm평면에맞추는soft목표가발목bottomspan15.67mm/발끝6.58mm로기울어지는절충을만든다. 이발목표는불채택한다. source9는이미계산된source8의상체/기타/Hip각과지지witness를그대로보존하고,그하위오른Knee/Ankle/Toe유효5축만다시최적화한다. 발을지면에붙이지않고최저점5mm이하에만큰penalty를주며기존발방향을우선보존한다. 높이를낮추는보조목표는작게준다. root/왼다리/zero8/형상/물성/finitegain·cap은불변이다.

source9최종float32의발min≥.5mm/bottomspan≤3mm,전체관절범위/zero8exact와전체upright제한범위의새audit를선정gate로사용한다. source8valid는발기준승인이아니다. 양손/상체/기타/Hip의FK가source8과동일한지assert하고원105모델/native초기각도/FK로다시검증한다. 실제정지5초Chest·RShoulder접촉성공후에만15초해제한다. 한계와원자료/실패를보존하며PPO는없다.
