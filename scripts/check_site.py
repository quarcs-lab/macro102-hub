"""Check the complete static publication and optionally its remote resource URLs."""
import argparse,concurrent.futures,hashlib,html.parser,json,re,sys,urllib.request,urllib.parse
from pathlib import Path
R=Path(__file__).resolve().parents[1]; p=argparse.ArgumentParser();p.add_argument('--remote',action='store_true');p.add_argument('--stamp-i18n',action='store_true',help='record that data/i18n/es.json and ja.json match the current English strings');a=p.parse_args(); errors=[]
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
files=list(R.glob('*.html'))+list(R.glob('es/*.html'))+list(R.glob('ja/*.html'))+list((R/'audio-player/transcripts').glob('*.html'))
pages={}
for f in files:
 doc=Page(f);doc.feed(f.read_text());pages[f.resolve()]=doc
 if doc.h1!=1:errors.append(f'{f.name}: expected one h1, got {doc.h1}')
for f,doc in pages.items():
 for link in doc.links:
  u=urllib.parse.urlsplit(link)
  if u.scheme or u.netloc:continue
  dest=(f.parent/urllib.parse.unquote(u.path)).resolve() if u.path else f
  if dest.is_dir():dest=dest/'index.html'   # e.g. the language switcher's es/ and ../
  if not dest.is_file():errors.append(f'{f.name}: missing {link}')
  elif u.fragment and dest in pages and urllib.parse.unquote(u.fragment) not in pages[dest].ids:errors.append(f'{f.name}: broken anchor {link}')
resources=json.loads((R/'data/resources.json').read_text());config=json.loads((R/'player-config.json').read_text())
assert len(resources)==30
assert sum(ep['id'].startswith('podcast-ch') for ep in config['episodes'])==21
ja_catalog=json.loads((R/'data/podcasts-ja.json').read_text())
ja_episodes=[item for item in ja_catalog['episodes'] if item.get('status')=='publicly_verified']
assert sum(ep['id'].startswith('podcast-ja-') for ep in config['episodes'])==len(ja_episodes)
assert pages[(R/'podcasts.html').resolve()].audios==21
japanese_page=(R/'podcasts-ja.html').read_text()
assert pages[(R/'podcasts-ja.html').resolve()].audios==len(ja_episodes)
for item in ja_episodes:
 assert f'data-podcast="audio-player/transcripts/{item["id"]}.json"' in japanese_page
 assert 'English Japanese transcript' in japanese_page
 assert f'href="{item["transcript_page"]}"' in japanese_page
 assert f'id="chapter-{item["chapter"]}"' in japanese_page
assert 'audio-player/podcast-player.js' in japanese_page
for lang in ('','es/','ja/'):
 assert pages[(R/lang/'index.html').resolve()].audios==21,lang
 page_=(R/lang/'index.html').read_text()
 assert page_.count('class="chapter-card resource"')==30 and page_.count('data-map-title=')==30 and page_.count('class="question-selector"')==6,lang
 assert f'<html lang="{lang[:2] or "en"}">' in page_,lang
home=(R/'index.html').read_text()
assert 'class="hero-art"' not in home
editorial=json.loads((R/'data/curriculum.json').read_text())
for resource in resources:
 assert resource['id'] in editorial
 assert resource.get('mindmap') and resource.get('slides') and resource.get('preview'),resource['id']
 assert resource['slides'] in home and resource['mindmap'] in home,resource['id']
 assert editorial[resource['id']]['question'] and editorial[resource['id']]['introduction']

for episode in config['episodes']:
 src=json.loads((R/episode['transcript']).read_text());out=json.loads((R/'audio-player/transcripts'/f'{episode["id"]}.json').read_text())
 assert src==out,episode['id']
 assert re.match(r'https://open.spotify.com/episode/[A-Za-z0-9]{22}$',episode['spotify_url'])
assert len(list((R/'assets/charts').glob('*.svg')))==18
# The Spanish and Japanese home pages: every string translated, and made from the current English
# (data/i18n/en.json and data/curriculum.json); after changing those, update es.json and ja.json, then --stamp-i18n.
def keys(d,prefix=''):
 return {prefix+k for k,v in d.items() if not isinstance(v,dict)}|{x for k,v in d.items() if isinstance(v,dict) for x in keys(v,prefix+k+'.')}
en=json.loads((R/'data/i18n/en.json').read_text())
source=hashlib.sha256((R/'data/i18n/en.json').read_bytes()+(R/'data/curriculum.json').read_bytes()).hexdigest()
for lang in ('es','ja'):
 path=R/f'data/i18n/{lang}.json';tr=json.loads(path.read_text())
 if a.stamp_i18n:tr['source_sha256']=source;path.write_text(json.dumps(tr,ensure_ascii=False,indent=1)+'\n')
 missing=keys(en)-keys(tr)
 if missing:errors.append(f'{lang}.json: missing {sorted(missing)}')
 for r in resources:
  if r['id'] not in tr['titles'] or r['id'] not in tr['curriculum'] or r['group'] not in tr['groups']:errors.append(f'{lang}.json: no translation for {r["id"]}')
 if len(tr['slides'])!=len(en['slides']) or len(tr['topic_labels'])!=len(en['topic_labels']):errors.append(f'{lang}.json: slides differ from en.json')
 if tr.get('source_sha256')!=source:errors.append(f'{lang}.json: the English home-page strings changed since it was translated; update data/i18n/{lang}.json, then run check_site.py --stamp-i18n')
 for c in ('growth','recessions','inflation','employment','policy','global'):
  if not (R/f'assets/charts/{c}-{lang}.svg').is_file():errors.append(f'missing assets/charts/{c}-{lang}.svg')
if a.remote:
 urls={r[key] for r in resources for key in ('book','slides','mindmap')}|{app['url'] for r in resources for app in r['apps'].values()}|{ep['audio_sources'][0]['src'] for ep in config['episodes']}
 def check(url):
  try:
   req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'macro102-hub-link-check/1.0'})
   with urllib.request.urlopen(req,timeout=25) as r:
    return None if r.status==200 else f'{r.status}: {url}'
  except Exception as e:return f'{url}: {e}'
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:errors += [x for x in pool.map(check,sorted(urls)) if x]
 print(f'Checked {len(urls)} live book/app/audio destinations.')
if errors:print('\n'.join(errors));sys.exit(1)
print(f'PASS: {len(pages)} HTML pages; local assets, anchors, IDs, 21 English and {len(ja_episodes)} Japanese timed transcripts, episode mappings, 18 charts (en/es/ja), and the translated home pages.')
