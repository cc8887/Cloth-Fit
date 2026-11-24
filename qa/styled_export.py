"""Reassociate unchanged solved vertices/faces with the corrected source UV set."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser()
p.add_argument('solved',type=Path)
p.add_argument('source_visual_uv',type=Path)
p.add_argument('out',type=Path)
a=p.parse_args()
def read(p):
    lines=p.read_text().splitlines()
    return [[l for l in lines if l.startswith(prefix)] for prefix in ('v ','vt ','f ')]
V,_,F=read(a.solved)
refV,UV,refF=read(a.source_visual_uv)
def vi(f):return [int(i.split('/')[0]) for i in f.split()[1:]]
if len(refV)!=len(V) or len(refF)!=len(F) or any(vi(x)!=vi(y) for x,y in zip(F,refF)):
    raise SystemExit('No exact shared geometry indexing; refusing UV copy')
if not UV or any('/' not in i for f in refF for i in f.split()[1:]):
    raise SystemExit('No complete source UV')
with a.out.open('x') as f:
    f.write('# Vertex coordinates from Cloth-fit unchanged; source UV remapped for preview.\nmtllib cloud_coat.mtl\no Cloud_Coat\n')
    for x in V+UV: f.write(x+'\n')
    f.write('usemtl Red_Cloud_Cloth\ns 1\n')
    for x in refF:f.write(x+'\n')
