"""Convert the supplied official file into packaged PNG and Windows ICO.

No drawing, replacement, crop or background removal is performed.
Usage: .venv/bin/python tools/prepare_branding.py /path/to/official-image.png
"""
import argparse
from pathlib import Path
from PIL import Image

parser=argparse.ArgumentParser()
parser.add_argument('image',type=Path)
args=parser.parse_args()
output=Path(__file__).resolve().parents[1]/'src/drheeklab/assets'
with Image.open(args.image) as original:
    original.load()
    if original.width!=original.height:
        raise ValueError('Use o arquivo oficial quadrado; não será recortado automaticamente.')
    image=original.convert('RGBA')
    output.mkdir(parents=True,exist_ok=True)
    image.save(output/'logo-oficial.png',format='PNG')
    image.save(output/'drheeklab.ico',format='ICO',sizes=[(n,n) for n in (16,24,32,48,64,128,256)])
print('Official PNG and multi-resolution Windows ICO prepared.')
