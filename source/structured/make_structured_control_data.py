"""Generate local interactive deltas from one-parameter-off previews.

Generate the six mesh variants at --<key> 0 while holding any other parameter
at the frozen default. Usage: python make_structured_control_data.py PATH_TO_VARIANTS.
Each path is <key>/garment.obj. Only subtracts positions and checks exact face/UV.
"""
import json,sys
from pathlib import Path
src=Path(__file__).resolve().parent
stage=Path(sys.argv[1]).resolve()
info=json.loads((src/'geometry.json').read_text())
defaults={k:info['profile'][k] for k in ('chest','waist','abdomen','sleeve','hem','structure')}
def read(p):
 obj=p.read_text().splitlines()
 return [tuple(map(float,x.split()[1:])) for x in obj if x.startswith('v ')], [x for x in obj if x.startswith(('f ','vt '))]
base,topology=read(src/'garment.obj')
ds={}
for k,v in defaults.items():
 alt,comp=read(stage/k/'garment.obj')
 assert topology==comp and len(alt)==len(base),k
 ds[k]=[[round((x-y)/v,9) for x,y in zip(p,q)] for p,q in zip(base,alt)]
(src/'structured_controls.json').write_text(json.dumps({'indexing':'zero-based OBJ index with source topology exact','default_v4_positions':base,'defaults':defaults,'preview_deltas_at_one':ds},separators=(',',':'))+'\n')
