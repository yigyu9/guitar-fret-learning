# 보존된 분석 보완 기록

native1은녹화카메라키누락의0step셋업실패이며native2는정상실행/원Fret safety done까지492steps를마친음악실패이다. 소스·로그·원시trace·영상은모두보존했다.

분석v1은PREP quaternion 원숫자exact검사에서중단했다. 정지baseline trace는unit quaternion,새dual trace는native raw quaternion을기록해숫자가최대5.89277e−8차이지만정규화후회전차는0rad다. raw q81/rootp와실제effort명령480행은exact. v2는이표현차이를분리했다.

분석v2는raw OBJ부품의로컬bounds를G origin좌표의bodycenter로잘못사용했다. 이출력은기타중심수치에사용하지않는다. v3은검증된CapsuleBodyDistance의body.pos를포함한63개충돌조각좌표에서bodyBB중심을계산하며manifest/asset/meshes/helper를inputSHA에명시했다. 기존verifications/source/실패로그를보존하고canonical은connection_verification_v3.json이다. 두정책출력재생/제어수식/실제종료판정은바뀌지않았다. 재학습/재물리실행은없다.
