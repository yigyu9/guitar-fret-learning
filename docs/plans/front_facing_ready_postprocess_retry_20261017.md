# 정지11 후처리 중단 복구

실제 native_baseline_v11은28초6720step 정상완료했고 core29 및17..22초 정지·media는통과했다. feet 후처리Root가종료143으로중단됐고 summary/external이없다. 원인미확정이며물리실패로설명하지않는다. Root가feet완료전에manual을시작한순서오류로manual은선행파일assert에서return1로중단됐다. 원폴더·source·before·log·실패를전부보존하고같은native를재실행하지않는다.

- [ ] 원feet partial CSV/ground/before/log와manual실패metadata의SHA를지금고정한다. 이사후고정을기존의실행전증거로소급하지않는다.
- [ ] execute21은foot/manual/health의출력·외부tag만v12,나머지v11로구분한다. manual10은feet_v12를읽고health7은manual10을pin/import한다. 임계값·계산수학·native/config·control·일정은변경하지않는다. 실제foot계산은원feet5를새out에서다시실행한다.
- [ ] Root21에서manual은core+feet+media완료증거를확인한후시작한다. 기존baseline의native/analysis/media/planes 네stage는before14,새단계/후속동작은새before15로명시연결한다. 기존manual실패와feet미완료는새통과로고쳐쓰지않는다.
- [ ] source/독립CPU/검수FINAL+freeze/Root대조/ACK/새before15 후에새후처리를순차실행한다. physics성공과도구중단원인미확정을구분한다.
- [ ] 새baseline전체10stageAND가통과해야왼손해제등다음native로진행한다. strictEPS0/cause/adoptionFalse·PPO0·83초/재시작미검증을유지한다.
