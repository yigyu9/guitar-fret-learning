"""Native 240Hz measurements; source selected gap is not cooked penetration."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[1]
fig,axes=plt.subplots(4,1,figsize=(12,9),sharex=True,layout='constrained')
for color,(file,label) in enumerate([('native_thumb_hold/physics_env0000.npz','No thumb request'),('support/thumb_native_protocol/smooth_tape_measurements.npz','Slow thumb target tape / hold / release')]):
 raw=np.load(P/file);t=raw['time_s']
 for ax,key,scale in [(axes[0],'thumb_normal_load',1),(axes[1],'thumb_signed_gap',1000),(axes[3],'thumb_contact_candidate',1)]:ax.plot(t,raw[key]*scale,lw=1,label=label,color=f'C{color}')
 if 'control_witness_gap' in raw:axes[2].plot(t,raw['control_witness_gap']*1000,lw=1,label=label,color=f'C{color}')
axes[0].set_ylabel('Rear-normal resultant (N)');axes[1].set_ylabel('Reward-selected gap (mm)');axes[2].set_ylabel('Control witness gap (mm)');axes[3].set_ylabel('Candidate (0/1)');axes[3].set_xlabel('Physical time (s)')
for a in axes:a.grid(alpha=.2)
axes[0].legend(loc='upper right');fig.suptitle('Native GPU thumb diagnostic: geometry and resultant are distinct measurements')
fig.savefig(P/'native_thumb_contact_trace.png',dpi=160);plt.close(fig)
