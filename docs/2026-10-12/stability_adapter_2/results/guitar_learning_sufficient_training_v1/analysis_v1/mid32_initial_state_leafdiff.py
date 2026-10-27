from pathlib import Path
import hashlib,json
base=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1');out=base/'analysis_v1'
def diffs(a,b,path=''):
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:yield {'path':path+'.'+k,'kind':'mapping_key','baseline':a.get(k),'mid32':b.get(k)}
   else:yield from diffs(a[k],b[k],path+'.'+k)
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b):yield {'path':path+'.length','kind':'length','baseline':len(a),'mid32':len(b)}
  for i,(x,y) in enumerate(zip(a,b)):yield from diffs(x,y,path+'[%d]'%i)
 elif type(a)!=type(b) or a!=b:yield {'path':path,'kind':'leaf','baseline':a,'mid32':b}
keys=['human_position105','human_velocity105','guitar_bodies','target105','last_target105','codec_target81','previous_action39','controller_history']
records={}
for mode in ['deterministic','stochastic']:
 rows=[]
 for i in range(20):
  name='case_%03d'%i;ap=base/('baseline_'+mode+'_v2')/name/'initial_state.json';bp=base/('mid32_'+mode+'_v1')/name/'initial_state.json';a=json.loads(ap.read_text());b=json.loads(bp.read_text());d=list(diffs(a,b));different_keys=[k for k in a if a[k]!=b[k]]
  row={'case_index':i,'baseline_path':str(ap),'mid32_path':str(bp),'same_top_level_keys':set(a)==set(b),'different_top_level_values':different_keys,'kinematic_target_controller_blocks_exact_equal':{k:a[k]==b[k] for k in keys},'leaf_or_length_difference_count':len(d),'native_contact_count':[len(a['contact_history']['native_contacts']['contacts']),len(b['contact_history']['native_contacts']['contacts'])]}
  if i<3:row['example_leaf_differences']=d[:12]
  rows.append(row)
 records[mode]={'all_top_level_key_sets_same':all(r['same_top_level_keys'] for r in rows),'kinematic_target_controller_all_20_exact_equal':all(all(r['kinematic_target_controller_blocks_exact_equal'].values()) for r in rows),'differences_confined_to_contact_history':all(set(r['different_top_level_values'])<= {'contact_history'} for r in rows),'rows':rows}
result={'schema':'guitar_learning.mid32_initial_state_leafdiff.v1','scope':'Read-only stored JSON comparison. Raw contact arrays are compared by saved index; index differences are not matched contact point displacement. Hidden solver state not observed; no root-cause inference.','physical_state_blocks':keys,'modes':records,'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'mid32_initial_state_leafdiff.json').write_text(json.dumps(result,indent=2)+'\n');print({k:{n:v for n,v in d.items() if n!='rows'} for k,d in records.items()})
