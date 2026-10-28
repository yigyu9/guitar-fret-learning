# 검지 distal 이산 표본 여유: 분석 준비

소유는 analysis/만이다. root 상위PLAN과 producer의 최종schema를 따른다. 새runs는 root의 두child 종료0 통보 전 읽지 않으며 source/prep/원raw/전역문서·NN·분포·보상·판정·제어를 바꾸지 않는다. 새GPU/native/fit/PPO는0이다.

- [x] phrase의 source/schema와 시간창·표본ID·frame·실패mask를 확인하고 두 child job/argv/종료0 완료guard를 연결했다. --self-check의 불완전/외부명령 거부 fixture가 통과했다.
- [x] 원 pad_target_geometry를 CPU로 직접 재사용해 P=128 aggregate와 P=1 batch 펼침·nearest/witness 구분·sourcevalid 보존을 작은독립fixture로 검산했다. 원finite-cell inset/obliqueplane/samepoint 테스트4개도 통과했다(self_check.py, actual자료/GPU/model 읽기0).
- [x] 실제완료 뒤 네환경 첫시도·지정구간·연속60Hz clock·동일원128 표본ID·body/plane/점/법선 유한성과 원aggregate 대응만 확인한다. 원128평가를 재감사하는 작업이 아니다.
- [x] 거리·signedheight·cos·셀/방향·loaded·candidate·native release latch를 분리해 간단한 타임라인을 만든다. nearest는 candidate witness와 다를 수 있고 음수height를 분리여유로 부르지 않는다.
- [ ] source+새실제신호의 통합 독립검수를 기존reviewer에게 순차 위임한다. 직접관련SHA와 원native콜백/입력/장면종료 감사를 재사용하며 전체재귀감사/추가조건/새std추정은 하지 않는다.

측정범위는 index3의 지정굽힘안쪽128점·env0..3·60Hz유한구간뿐이다. 전체피부·다른마디·원force접촉쌍/현압력·240Hz연속성·다른124환경의기하/실제사건을 인증하지 않는다. 같은A candidate의 재등장과 원released latch·말단무하중을 구분한다. 새성공/clearance threshold를 만들지 않는다.

root의 저장 초안은 A의 원press에서 B7 공유press를 처음 넘는 제어 끝점까지(clock 692..920, 간격4, 58끝점)이다. 최종 producer schema와 일치한 뒤에만 이 창을 분석 입력으로 확정한다. static local point/normal/source-valid와 body→world→guitar 변환을 대조하고, 같은 표본의 거리·height·cos·position/facing를 재계산한다. P128 any/nearest와 P1 집계는 별도로 확인하며 loaded와 candidate/wrong은 원native 신호로 구분한다. first/failure/reset은 저장된 endpoint 시각 그대로 표에 남기고 실패 이후를 유효 사건으로 세지 않는다.

실제 실행 확인은 원 commands와 두 launcher child의 종료0, 선행 actual PASS, 새 observer/native 감사의 완료·입력불변·닫기 여부만 직접 관련 SHA로 확인한다. 타임라인은 저장된 끝점의 candidate on/off·재등장·release latch·distal load와 표본 기하를 겹쳐 보이며, 두 끝점 사이 사건시각이나 피부 전체 이격은 추정하지 않는다. 최종 source/schema 인계 후 analyze.py --root-completed 경로만 준비했다. 실제 실행은 root 두 child0 통보 후로 제한하며 아직 새 runs·모델을 읽거나 실제 결과파일을 만들지 않았다.

CPU 명령: CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B analysis/analyze.py --self-check. 실제 완료 뒤 같은 명령의 --root-completed로 실행한다. 결과는 results_v1/{comparison.json,verification.json,RESULTS.md,timeline.png}에만 새로 쓴다. valid_snapshot은 producer가 검사한 네 distal13 상태의 결과를 재사용하며, 저장되지 않은 나머지 distal13 유한성까지 역복원했다고 주장하지 않는다.

root의 두 child 실제종료0 인계 뒤 actual main이 통과했다. 두 조건 각각232행/네환경58끝점·valid232·실패0, 원 point/P128/cached/loaded 및 독립 pose 변환을 확인했다. 원 phase3 요청 범위 표와 env0 대표3행 그림만 보강했다. 처음 성공한8panel 결과는 before_phase3_summary/에 역사기록으로 보존하며 현재 검수범위는 아래 현행7파일이다.
