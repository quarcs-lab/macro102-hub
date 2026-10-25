"""Package only public runtime files for GitHub Pages."""
import shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist'
if D.exists():shutil.rmtree(D)
D.mkdir()
for f in R.glob('*.html'):shutil.copy2(f,D/f.name)
for lang in ['es','ja']:shutil.copytree(R/lang,D/lang)   # the Spanish and Japanese home pages
for name in ['assets','audio-player','data']:shutil.copytree(R/name,D/name,dirs_exist_ok=True)
(D/'.nojekyll').touch()
print('Packaged dist/')
