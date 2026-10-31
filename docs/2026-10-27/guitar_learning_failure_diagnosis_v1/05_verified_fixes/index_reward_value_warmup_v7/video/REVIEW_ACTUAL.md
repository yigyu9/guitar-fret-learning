# V7 final300 actual native-video independent review

PASS with no findings. This review covers actual frozen video artifacts; no checkpoint loading, NN forward, new native/GPU run or training was performed.

All694 original input hashes and exact before/after maps were independently rechecked. The selected final300 deterministic V7 checkpoint SHA remains unchanged; model/optimizer freeze, accepted1000-step value-warmup contract, copied source settings, NN-only helper calls0, completed/closed scene and restored source alias were confirmed.

The complete128 episode JSON, including all9 reward components and384 source-note opportunities, exactly matches the selected deterministic source evaluation. Every learning_control_env0 array is bit-identical except net_body_force_n, whose maximum difference is7.62939453125e-6N and is reported separately. Native capture q/target/body and raw reward match the replay trace exactly across354 control endpoints. The9 captured cumulative-term differences sum to the raw per-tick reward within2.7939677238464355e-8; their episode-total maximum difference from source9 term totals is3.725290298461914e-9. These are cumulative float32 difference logs; per-tick9 term sums are not claimed bit-exact.

Independent ffprobe counted177 decoded H.264 frames in each hand/fullbody file:1280x720,30fps,5.9s. Both complete streams also passed strict CPU ffmpeg decode with return0 and no errors. Capture frame times match1/30..177/30 seconds.

Visual QA inspected frames0,30,60,90,120,176 from both views. Fullbody remains upright, with the head above the feet, floor below, human and guitar visible. The hand view shows the hand/neck and visible finger motion; inspected frames are neither blank nor upside down. The video verifies native pixels and replay identity, not acoustic performance, finger/string pair pressure, or musical success.

The scope remains fixed guitar, selected index4 axes, source3 notes and seed7. Other seeds/fingers/free guitar/J33/original67 notes remain incomplete.
