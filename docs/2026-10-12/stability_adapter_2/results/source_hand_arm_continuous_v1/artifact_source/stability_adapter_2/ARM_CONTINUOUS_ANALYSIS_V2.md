# 저장 분석의 부동소수점 검산 정정

물리/source 탐색은 정상 종료됐고 두seed800회에서clear후보는없다. 최초저장분석은행33충돌목적값의절대오차허용치1e−8을넘어중단됐다. Source값76113175.66485968와독립재계산76113175.6648597의차이는1.4901161193847656e−8이다. 이는대규모무차원목적함수의마지막자리수준이며geometry/초기각/held/실행결과를변경할근거가아니다.

최초analyzer·invocation·partial사본/manifest·실패기록을보존한다. 새analyze_arm_continuous_v2.py는같은저장자료를읽고각구성항/총합의검산허용치를 `1e−10 + 8*float64_epsilon*max(abs(source),abs(recomputed))`로정한다. 이는목적값산술의재계산오차만다루며관절범위·입력exact·HG보고임계값·물리성공조건을완화하지않는다. 최대관측구성항/총합차이도별도기록한다. 새analysis_v2출력/사본/실행기록을쓰며sourceoptimizer/native/영상은재실행하지않는다.
