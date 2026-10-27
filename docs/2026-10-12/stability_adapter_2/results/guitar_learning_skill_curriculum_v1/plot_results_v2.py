"""Closed data only: learning pilot and240Hz actual teacher trajectories."""
from pathlib import Path
import gzip,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from guitar_learning.recording import write,digest
P=Path(__file__).resolve().parent

def main():
 files=[P/'learning_comparison_v1.json',P/'trajectory_analysis_v1.json',P/'left_servo_v3/trace.json.gz',P/'right_grid_native_v2/trace.json.gz',Path(__file__)]
 pins={str(p):digest(p) for p in files}
 data=json.loads(files[0].read_text())['runs'];fig,axes=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
 for role,col in [('left',0),('right',1)]:
  for suffix,label,color in [('1p0','cost weight 1','#3274a1'),('0p1','cost weight 0.1','#d67a25')]:
   rows=data[role+'_cost'+suffix+'_run_v2']['update_series'];x=[r['update'] for r in rows]
   axes[0,col].plot(x,[100*r['successes']/r['episodes'] if r['episodes'] else 0 for r in rows],label=label,color=color,marker='o',markersize=3)
   axes[1,col].plot(x,[r['max_guitar_mm60'] for r in rows],label=label,color=color)
  axes[0,col].set(title=role.title()+' preparation (training exploration)',ylabel='Preparation success (%)',ylim=(-4,104))
  axes[1,col].set(xlabel='PPO update',ylabel='Max guitar displacement (mm, 60Hz)')

  for ax in axes[:,col]:ax.grid(alpha=.2)
 handles,labels=axes[0,0].get_legend_handles_labels()
 fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,-.025),ncol=2,fontsize=9)
 fig.suptitle('Matched single-seed pilot; preparation is not contact / strike success',fontsize=11)
 for ext in ('png','pdf'):fig.savefig(P/('learning_comparison_v2.'+ext),dpi=170,bbox_inches='tight')
 plt.close(fig)
 left=json.loads(gzip.decompress(files[2].read_bytes()));right=json.loads(gzip.decompress(files[3].read_bytes()))
 fig,axes=plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
 def series(trace):
  rows=[m for r in trace for m in r['measurements']];t=[m['music']['task_time_s'] for m in rows]
  return rows,np.array(t)
 rows,t=series(left);valid=[int(next(iter(m['music']['targets'].values()))['candidate']) for m in rows]
 axes[0,0].plot(t,valid,color='#3274a1');axes[0,0].set(title='Left: actual target contact candidate',ylabel='Valid candidate',ylim=(-.1,1.15))
 marker=[np.linalg.norm(next(iter(m['music']['geometry'].values()))['delta'])*1000 for m in rows]
 axes[1,0].plot(t,marker,color='#3274a1',label='Distal origin to midpoint');axes[1,0].axhline(15,color='gray',ls='--',label='Existing reach proxy threshold')
 axes[1,0].set(title='Distal origin to midpoint; dashed = 15mm proxy',ylabel='Marker distance (mm)',xlabel='Time after 2s preparation (s)')
 rr,tr=series(right);samples=[s for r in right for s in r['samples240']];pick=np.array([s['geometry']['pick_G_m'] for s in samples]);starts=np.array([s['geometry']['starts_G_m'][1] for s in samples]);ends=np.array([s['geometry']['ends_G_m'][1] for s in samples]);sx=starts[:,0]+(ends[:,0]-starts[:,0])*(pick[:,1]-starts[:,1])/(ends[:,1]-starts[:,1])
 axes[0,1].plot(tr,(pick[:,0]-sx)*1000,color='#d67a25');axes[0,1].axhline(0,color='gray',ls='--');axes[0,1].set(title='Right: pick across physical string 2',ylabel='Signed lateral distance (mm)')
 for trace,label,color in [(left,'Left hold teacher','#3274a1'),(right,'Right crossing teacher','#d67a25')]:
  rows,t=series(trace);axes[1,1].plot(t,[np.linalg.norm(m['stability']['guitar_delta_m'])*1000 for m in rows],label=label,color=color)
 axes[1,1].set(xlabel='Time after 2s preparation (s)',ylabel='Guitar displacement (mm, 240Hz)');axes[1,1].legend(fontsize=8)
 for ax in axes.ravel():ax.grid(alpha=.2)
 fig.suptitle('Scripted bounded teachers in real physics; these are not learned policies',fontsize=11)
 for ext in ('png','pdf'):fig.savefig(P/('successful_trajectories_v2.'+ext),dpi=170)
 plt.close(fig)
 write(P/'plot_inputs_v2.json',dict(inputs=pins,inputs_unchanged=all(digest(p)==s for p,s in pins.items())))

if __name__=='__main__':main()
