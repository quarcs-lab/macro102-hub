#!/usr/bin/env python3
"""Refresh public book metadata and portable player inputs; never reads private scans."""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='https://quarcs-lab.github.io/macro102-site/'
p=argparse.ArgumentParser(); p.add_argument('--book',type=Path,default=ROOT.parent/'macro102-site'); p.add_argument('--player-skill',type=Path,default=Path.home()/'.codex/skills/created-audio-player'); a=p.parse_args()
book=a.book.resolve()
def group(n):
 return 'Foundations' if n<=2 else 'Long-run growth' if n<=6 else 'Labor & inflation' if n<=8 else 'Business cycles & policy' if n<=15 else 'Decisions & the global economy'
resources=[]; episodes=[]
podcasts=json.loads((book/'podcasts/podcasts.json').read_text())
for f in sorted((book/'src').glob('*.qmd')):
 if not re.match(r'(ch\d\d|app[A-I])-',f.stem): continue
 slug=f.stem; text=f.read_text(); chapter=slug.startswith('ch'); ident=slug[:4]; n=int(slug[2:4]) if chapter else None
 title=re.search(r'^# (.+)',text,re.M).group(1)
 title=re.sub(r'^(?:\d+\.|Appendix [A-I][.:]?|[A-I]\.)\s*','',title)
 title=re.sub(r'\s*\{.*\}$','',title)
 image=re.search(r'<img src="([^"]+)"',text)
 preview=None
 if image:
  path=image.group(1).split('/main/')[-1] if '/main/' in image.group(1) else image.group(1)
  if (book/path).is_file():
   name=f'{ident}.jpg'
   subprocess.run(['sips','-Z','900','-s','format','jpeg','-s','formatOptions','78',str(book/path),'--out',str(ROOT/'assets/previews'/name)],check=True,stdout=subprocess.DEVNULL)
   preview='assets/previews/'+name
 apps={}
 for kind in ['data','model']:
  path=f'apps/{ident}-{kind}-apps.html'
  if (book/path).is_file():
   html=(book/path).read_text()
   heads=re.findall(r'<h[23][^>]*>(.*?)</h[23]>',html,re.S)
   heads=[re.sub('<[^>]+>','',h).replace('Anchor','').strip() for h in heads]
   heads=[h for h in heads if h and not h.lower().startswith(('table of','on this','navigation'))]
   apps[kind]={'url':BASE+path,'topics':heads[:5]}
 resources.append({'id':ident,'slug':slug,'title':title,'label':f'Chapter {n:02}' if chapter else f'Appendix {ident[-1]}','group':group(n) if chapter else 'Appendices','book':BASE+f'notebooks/{slug}.html','colab':f'https://colab.research.google.com/github/quarcs-lab/macro102-site/blob/main/notebooks/{slug}.ipynb','preview':preview,'apps':apps})
 if slug in podcasts:
  m=podcasts[slug]; eid='podcast-'+slug
  src=book/f'podcasts/player/transcripts/{eid}.json'; dst=ROOT/f'transcript-inputs/{eid}.json';shutil.copy2(src,dst)
  episodes.append({'id':eid,'title':f'Chapter {n} · {m["title"]}','audio_sources':[{'src':BASE+m['src'],'type':'audio/mpeg'}],'transcript':str(dst.relative_to(ROOT)),'spotify_url':m['spotify_url'],'return_url':f'podcasts.html#{eid}','image':{'src':BASE+image.group(1).split('/main/')[-1],'alt':f'Chapter {n} mind map'},'note':'AI-generated narration. Transcript timing is approximate.'})
  resources[-1]['podcast']={'id':eid,'duration':m['duration'],'spotify':m['spotify_url']}
resources.sort(key=lambda r:(r['id'].startswith('app'),r['id']))
(ROOT/'data/resources.json').write_text(json.dumps(resources,indent=2)+'\n')
config={'site_title':'Data Science & Macroeconomics','integration_page':'podcasts.html','launch_label':'Listen AI Podcast','narration_label':'AI podcast','episodes':episodes}
(ROOT/'player-config.json').write_text(json.dumps(config,indent=2)+'\n')
subprocess.run([sys.executable,str(a.player_skill/'scripts/build_player.py'),'--config',str(ROOT/'player-config.json'),'--root',str(ROOT),'--check'],check=True)
subprocess.run([sys.executable,str(a.player_skill/'scripts/build_player.py'),'--config',str(ROOT/'player-config.json'),'--root',str(ROOT)],check=True)
print(f'Refreshed {len(resources)} resources and {len(episodes)} podcasts.')
