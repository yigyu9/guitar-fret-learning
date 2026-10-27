# 후속 action 분석 기록 분기 교정

기존 reanalysis_link 계획의 Root17은 baseline-only Root16에서 복사하면서 main tag의 stage==analysis 조건을 남겼다. 독립검수에서 action 분석도이미존재하는baseline retry기록을선택함을발견했다. main/full_case 모두case==baseline and stage==analysis일때만retry태그를사용하도록새Root18에서해당literal1곳만고친다. 소비Root17·generation·기존결과는보존한다.

실제AST tag식을모든case/stage조합에서계산하고full_case의식·예상외부기록경로와비교한다. 기존baseline을재실행하거나생산실패를숨기지않는다. active후속Root18/run13,plannedbefore13/ACKv4,원nativev10/cfgv3·gain/cap·기하검사는동일하다. 독립FINAL/RootACK와모든baseline감사AND전새action native0.
