"""현행 생성기로 중지 6→7프렛의 무음 두 음 과제를 한 번 생성한다."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
import wave

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT))
SONG='virtual_middle_s3_f6_f7_AB_v2'


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def fingering(gap):
    if gap not in (.5,.75,1.):raise ValueError('휴지 .5/.75/1초 필요')
    notes=[];presses=[];hand=[]
    for start,fret in ((0.,6),(1.5+gap,7)):
        end=start+1.5
        notes.append(dict(t_on=start,t_off=end,string=3,fret=fret,midi=55+fret,finger=2,barre=False,grip=None))
        presses.append(dict(finger=2,string=3,fret=fret,barre=False,t_press=start,t_release=end,strikes=[start]))
        hand.append(dict(t=start,P=fret-1,grip=None))
    return dict(purpose='synthetic_middle_two_fret_transition_v2',transition_gap_s=gap,
        convention='string 0 = low-E; runtime string2=standard third string; silent clock only',
        notes=notes,presses=presses,hand=hand,stats=dict(dropped_invalid_fret=0),diagnostics=[],violations=[])


def build_bundle(gap,song=SONG):
    from guitar_learning.tool import build_fret_training_data as fret
    from guitar_learning.tool.build_strike_training_data import build_strike_training_data
    from guitar_learning.tool.build_strike_plan import build_strike_plan
    from guitar_learning.tool.register_song_bundle import write_manifest,write_tablature_if_missing
    from guitar_learning.song.task import make_task
    data=fingering(gap);bundle=ROOT/'data/song_bundles'/song
    bundle.mkdir(parents=True,exist_ok=False)
    for name in ('source','mapping','training'):(bundle/name).mkdir()
    audio=bundle/'source/audio.wav'
    with wave.open(str(audio),'wb') as stream:
        stream.setparams((1,2,16000,0,'NONE','not compressed'))
        stream.writeframes(b'\0\0'*round((3.+gap)*16000))
    mapping=bundle/'mapping/fingering.json';write(mapping,data)
    fret.main(['--fingering',str(mapping),'--audio',str(audio),'--out',str(bundle/'training/fret_training.json')])
    strike=bundle/'training/strike_training.json';document=build_strike_training_data(data,source_path=mapping)
    write(strike,document);write(bundle/'training/strike_plan.json',build_strike_plan(document,source_path=strike))
    write_tablature_if_missing(bundle)
    sources={str(Path(inspect.getsourcefile(f)).resolve()):hashlib.sha256(Path(inspect.getsourcefile(f)).read_bytes()).hexdigest()
        for f in (fret.main,build_strike_training_data,build_strike_plan,write_manifest,build_bundle)}
    write_manifest(song,bundle,dict(generator_source_sha256=sources,mode='synthetic ABv2; silent clock only',immutable_after_creation=True))
    task=make_task(bundle)
    assert [(t.string,t.fret,t.finger,t.onset_s,t.end_s) for t in task.targets]==[(2,6,2,3.,4.5),(2,7,2,4.5+gap,6.+gap)]
    assert task.duration_s==6.5+gap
    return bundle


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--gap',type=float,choices=(.5,.75,1.),required=True)
    args=parser.parse_args();print(build_bundle(args.gap))
