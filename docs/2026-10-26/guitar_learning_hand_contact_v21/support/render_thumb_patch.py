"""Static source geometry illustration of the corrected thumb-specific patch."""
from pathlib import Path
import struct,json
import numpy as np
import torch
from scipy.spatial.transform import Rotation
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from guitar_learning.gpu.thumb_support import load_thumb_support
from guitar_learning.tests import test_gpu_environment as fixture

out=Path('/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v21')
font='/usr/share/fonts/truetype/nanum/NanumGothic.ttf';font_manager.fontManager.addfont(font);plt.rcParams['font.family']='NanumGothic';plt.rcParams['axes.unicode_minus']=False
torch.set_num_threads(1)
e,_,_=fixture.TensorSongTests().environment();s=load_thumb_support();row=s['contract']['patch_diagnostics']
payload=Path(row['mesh']).read_bytes();layout=np.dtype([('n','<f4',(3,)),('vertices','<f4',(3,3)),('a','<u2')]);tri=np.frombuffer(payload,dtype=layout,count=struct.unpack_from('<I',payload,80)[0],offset=84)['vertices'].astype(float)
q=row['geom_quaternion_wxyz'];tri=Rotation.from_quat(q[1:]+q[:1]).apply((tri*np.array(row['mesh_scale'])).reshape(-1,3)).reshape(-1,3,3)+row['geom_position_m']
b=e.body[0,e.thumb_support_index].numpy();g=e.guitar_body[0].numpy();Rg=Rotation.from_quat(g[3:7]);Rt=Rotation.from_quat(b[3:7])
transform=lambda p:Rg.inv().apply(Rt.apply(p)+b[:3]-g[:3])
tri=transform(tri.reshape(-1,3)).reshape(-1,3,3);points=transform(s['points_local']);normals=Rg.inv().apply(Rt.apply(s['normals_local']))
rear=s['rear_vertices'];center=float((e.guide['lower_G_m'][0,1]+e.guide['upper_G_m'][0,1])/2);ys=np.array([max(center-.04,rear[0,1]),min(center+.04,rear[2,1])]);frac=(ys-rear[0,1])/(rear[2,1]-rear[0,1]);lo=rear[0,0]+frac*(rear[3,0]-rear[0,0]);hi=rear[1,0]+frac*(rear[2,0]-rear[1,0]);mid=(lo+hi)/2;half=(hi-lo)/4
region=np.array([[mid[0]-half[0],ys[0],0],[mid[0]+half[0],ys[0],0],[mid[1]+half[1],ys[1],0],[mid[1]-half[1],ys[1],0]])
p=s['plane'];region[:,2]=-(region[:,:2]@p[:2]+p[3])/p[2]
rear_window=np.array([[lo[0],ys[0],0],[hi[0],ys[0],0],[hi[1],ys[1],0],[lo[1],ys[1],0]])
rear_window[:,2]=-(rear_window[:,:2]@p[:2]+p[3])/p[2]
fig=plt.figure(figsize=(13,7),facecolor='white')
for k,(elev,azim) in enumerate([(-25,-65),(-10,30)],1):
 ax=fig.add_subplot(1,2,k,projection='3d');ax.add_collection3d(Poly3DCollection(rear_window[None]*1000,facecolors='#d8dde5',edgecolors='#64748b',alpha=.25));ax.add_collection3d(Poly3DCollection(region[None]*1000,facecolors='#68d4ba',edgecolors='#0e8c70',alpha=.25));ax.add_collection3d(Poly3DCollection(tri*1000,facecolors='#e5b6b4',edgecolors='none',alpha=.20));ax.scatter(*(points*1000).T,s=9,color='#2563eb',depthshade=False)
 chosen=int(e.thumb_support['sample_index'][0]);pt=points[chosen];target=pt+e.thumb_support['delta'][0].numpy();ax.plot(*np.array([pt,target]).T*1000,color='#14532d',lw=3);ax.scatter(*(pt*1000),color='#14532d',s=45)
 ax.quiver(*(points[::16]*1000).T,*(normals[::16]*3).T,color='#2563eb',linewidth=.7)
 ax.set(xlim=(-25,40),ylim=(10,110),zlim=(-55,5),xlabel='Gx (mm)',ylabel='Gy (mm)',zlabel='Gz (mm)');ax.view_init(elev=elev,azim=azim);ax.set_box_aspect((65,100,60))
fig.suptitle('초기 엄지의 실제 안쪽 표면 · 수정된 source 축 기준',fontsize=20)
fig.text(.5,.045,'파랑: 안쪽 패드128점/법선   초록: 넥 뒷면 목표영역   붉은 투명면: 엄지 끝마디 원본 메시\n정적 원본 기하 설명 · 선택점 간격1.044mm / 방향cos0.891 · 물리 접촉쌍·압력 인증 아님',ha='center',fontsize=11)
fig.subplots_adjust(top=.9,bottom=.13,wspace=.06);fig.savefig(out/'thumb_patch_initial.png',dpi=150);plt.close(fig)
