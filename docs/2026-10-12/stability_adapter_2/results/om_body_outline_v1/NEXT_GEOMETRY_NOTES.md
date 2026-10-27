# 후속 바디 메시 메모

CAD+X(넥 방향)를body+Y, CAD+Y를body+X로 옮긴 변환은det=-1이며원본평면곡선의winding을반전한다. 현재추출bodyXY점순서의signed area는양수(CCW)다. 후속메시의앞판+Z/뒤판-Z/측판법선을명시적으로검사하고뒤판face순서를뒤집는다. 좌우대칭2D비교검증을3Dwatertight/normal/충돌검증으로확대하지않는다.

윤곽449점(구간접합중복포함)은미터단위다. 후속triangulation은연속중복점을정리하고단위/폐합/area보존을다시검사한다. 지판/넥결합면과외부두께는추가로확인하며이번소단계에서native자산은변경하지않았다.
