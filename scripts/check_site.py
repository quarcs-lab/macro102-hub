"""Check the complete static publication and optionally its remote resource URLs."""
import argparse,concurrent.futures,html.parser,json,re,sys,urllib.request,urllib.parse
from pathlib import Path
R=Path(__file__).resolve().parents[1]; p=argparse.ArgumentParser();p.add_argument('--remote',action='store_true');a=p.parse_args(); errors=[]
class Page(html.parser.HTMLParser):
 def __init__(self,path):super().__init__();self.path=path;self.ids=set();self.links=[];self.audios=0;self.h1=0
 def handle_starttag(self,t,attrs):
  d=dict(attrs)
  if 'id' in d:
   if d['id'] in self.ids:errors.append(f'{self.path.name}: duplicate ID {d["id"]}')
   self.ids.add(d['id'])
  for attr in ['href','src','data-podcast']:
   if attr in d:self.links.append(d[attr])
  if t=='img' and 'alt' not in d:errors.append(f'{self.path.name}: image missing alt')
  if t=='audio':
   self.audios+=1
   if d.get('preload')!='none':errors.append('Audio preload must be none')
  if t=='h1':self.h1+=1
files=list(R.glob('*.html'))+list((R/'audio-player/transcripts').glob('*.html'))
pages={}
for f in files:
 doc=Page(f);doc.feed(f.read_text());pages[f.resolve()]=doc
 if doc.h1!=1:errors.append(f'{f.name}: expected one h1, got {doc.h1}')
for f,doc in pages.items():
 for link in doc.links:
  u=urllib.parse.urlsplit(link)
  if u.scheme or u.netloc:continue
  dest=(f.parent/urllib.parse.unquote(u.path)).resolve() if u.path else f
  if not dest.is_file():errors.append(f'{f.name}: missing {link}')
  elif u.fragment and dest in pages and urllib.parse.unquote(u.fragment) not in pages[dest].ids:errors.append(f'{f.name}: broken anchor {link}')
resources=json.loads((R/'data/resources.json').read_text());config=json.loads((R/'player-config.json').read_text())
assert len(resources)==30 and len(config['episodes'])==21
assert pages[(R/'podcasts.html').resolve()].audios==21
for episode in config['episodes']:
 src=json.loads((R/episode['transcript']).read_text());out=json.loads((R/'audio-player/transcripts'/f'{episode["id"]}.json').read_text())
 assert src==out,episode['id']
 assert re.match(r'https://open.spotify.com/episode/[A-Za-z0-9]{22}$',episode['spotify_url'])
assert len(list((R/'assets/charts').glob('*.svg')))==6
if a.remote:
 urls={r['book'] for r in resources}|{app['url'] for r in resources for app in r['apps'].values()}|{ep['audio_sources'][0]['src'] for ep in config['episodes']}
 def check(url):
  try:
   req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'macro102-hub-link-check/1.0'})
   with urllib.request.urlopen(req,timeout=25) as r:
    return None if r.status==200 else f'{r.status}: {url}'
  except Exception as e:return f'{url}: {e}'
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:errors += [x for x in pool.map(check,sorted(urls)) if x]
 print(f'Checked {len(urls)} live book/app/audio destinations.')
if errors:print('\n'.join(errors));sys.exit(1)
print(f'PASS: {len(pages)} HTML pages; local assets, anchors, IDs, 21 complete transcripts, episode mappings, and six charts.')
