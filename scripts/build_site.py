"""Build static, progressively enhanced pages from the checked-in resource manifest."""
import json,re,html,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]; resources=json.loads((R/'data/resources.json').read_text()); esc=html.escape
BOOK='https://quarcs-lab.github.io/macro102-site/'
TUTORS='https://notebook.google.com/notebook/837887f1-e221-4181-b42f-ef2ae52378fa?hl=en'   # the AI Tutors notebook (NotebookLM)
def versioned(path):
 return path+'?v='+hashlib.sha256((R/path).read_bytes()).hexdigest()[:12]
byid={r['id']:r for r in resources}
editorial=json.loads((R/'data/curriculum.json').read_text())
widgets=(R/'audio-player/players.html').read_text()
chunks=re.split(r'(?=<div class="podcast-widget" id=)',widgets)[1:]
widget_chunks={re.search(r'id="([^"]+)"',chunk).group(1):chunk for chunk in chunks}
english_podcasts=[r for r in resources if 'podcast' in r]
players={r['id']:widget_chunks[r['podcast']['id']] for r in english_podcasts}
players[english_podcasts[-1]['id']]=players[english_podcasts[-1]['id']][:-1]
player_assets='<link rel="stylesheet" href="audio-player/podcast-player.css"><script src="audio-player/podcast-player.js" defer></script>'
# The home page exists in English (index.html), Spanish (es/index.html) and Japanese (ja/index.html);
# every other page is English only. data/i18n/<lang>.json holds the home page's strings.
LANGS=('en','es','ja')
I18N={lang:json.loads((R/f'data/i18n/{lang}.json').read_text()) for lang in LANGS}
HUB='https://quarcs-lab.github.io/macro102-hub/'
def relocate(s):
 """Make the relative links of a page written for the site root work one folder down (es/, ja/)."""
 return re.sub(r'(href|src|data-podcast)="(?!https?:|#|mailto:|data:|//|index\.html)([^"]*)"',r'\1="../\2"',s)
def page(name,title,description,body,lang='en'):
 S=I18N[lang]; C=S['chrome']; home=name=='index.html'; book=BOOK if lang=='en' else BOOK+lang+'/'
 urls=['index.html',book,'podcasts.html',TUTORS,'data-apps.html','figure-apps.html']
 if name=='podcasts-ja.html': urls[2]='podcasts-ja.html'
 links=''.join(f'<a href="{url}"'+(' aria-current="page"' if url==name else '')+f'>{label}</a>' for label,url in zip(C['nav'],urls))
 extra=('<link rel="stylesheet" href="'+versioned('assets/home.css')+'">') if home else ''
 if name in ('data-apps.html','figure-apps.html'): extra='<link rel="stylesheet" href="'+versioned('assets/apps.css')+'">'
 if name=='podcasts.html': extra=player_assets+'<link rel="stylesheet" href="'+versioned('assets/podcasts.css')+'"><script src="'+versioned('assets/podcasts.js')+'" defer></script>'
 if name=='podcasts-ja.html': extra=player_assets+'<link rel="stylesheet" href="'+versioned('assets/podcasts.css')+'">'
 canonical=HUB+('' if lang=='en' else lang+'/') if home else HUB+name
 if home:
  # The language versions, the redirect/switcher script and, on es/ja, the strings for site.js and the player
  extra=''.join(f'<link rel="alternate" hreflang="{l}" href="{HUB}{"" if l=="en" else l+"/"}">' for l in LANGS)+f'<link rel="alternate" hreflang="x-default" href="{HUB}">'+extra
  extra='<script src="'+versioned('assets/i18n.js')+'"></script>'+extra
  if lang!='en': extra='<script>window.SITE_I18N='+json.dumps(S['js'],ensure_ascii=False)+';</script>'+extra   # before i18n.js
 bt=S['brand_title']
 # English · Español · 日本語 in the header, after the theme button (home pages only). The hrefs are relative
 # to the site root; relocate() adjusts them on es/ja. Narrow screens show EN · ES · JA (assets/home.css).
 switcher='' if not home else '<div class="lang-switch" role="group" aria-label="Language" translate="no">'+'<span class="lang-sep" aria-hidden="true">·</span>'.join(f'<a href="{href}" lang="{l}" hreflang="{l}" data-lang="{l}" title="{name}"'+(' aria-current="true"' if l==lang else '')+f'><span class="lang-long">{name}</span><span class="lang-short" aria-hidden="true">{l.upper()}</span></a>' for l,name,href in [('en','English','./'),('es','Español','es/'),('ja','日本語','ja/')])+'</div>'
 s=f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | {bt}</title><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#0b1425"><meta property="og:title" content="{esc(title)} — {bt}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="https://quarcs-lab.github.io/macro102-hub/assets/economic-world.jpg"><meta property="og:type" content="website"><link rel="canonical" href="{canonical}"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><script src="assets/theme.js"></script><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;550;600;650;700;750;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet"><link rel="stylesheet" href="{versioned('assets/site.css')}"><script src="{versioned('assets/site.js')}" defer></script>{extra}</head><body><a class="skip" href="#main">{C['skip']}</a><header class="header"><div class="nav-shell"><a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">m<span>↗</span></span><span>{C['brand_html']}</span></a><nav id="navigation" aria-label="{C['nav_aria']}">{links}</nav><button class="icon-button" id="theme-toggle" aria-label="{C['theme_aria']}" title="{C['theme_title']}">☼</button>{switcher}<button class="menu-button" aria-controls="navigation" aria-expanded="false">{C['menu']}</button></div></header><main id="main">{body}</main><footer><div class="shell footer-inner"><div><a class="brand" href="index.html">{bt}</a><p>{C['footer_tagline']}</p><p>{C['footer_by']} <a href="https://carlos-mendez.org/">Carlos Mendez</a> · <a href="{book}">{C['read_book']}</a></p></div><div class="footer-meta"><a href="https://github.com/quarcs-lab/macro102-hub">{C['source_github']}</a><a href="https://github.com/quarcs-lab/macro102-hub/issues">{C['report_issue']}</a><p>© 2026 Carlos Mendez · <a href="{C['license']}">CC BY-NC 4.0</a></p></div></div><div class="shell credit">{C['credit_html']}</div></footer></body></html>'''
 if lang=='en' or name=='podcasts-ja.html': (R/name).write_text(s)
 else: (R/lang).mkdir(exist_ok=True); (R/lang/name).write_text(relocate(s))
def intro(kicker,title,desc): return f'<section class="page-intro shell"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="lead">{desc}</p></section>'
def searchbox(label): return f'<div class="filter-bar"><label>Search {label}<input type="search" id="resource-search" placeholder="Try growth, inflation, or Chapter 7…"></label><label>Topic<select id="topic-filter"><option value="">All topics</option>'+''.join(f'<option>{esc(g)}</option>' for g in dict.fromkeys(r['group'] for r in resources))+'</select></label><p id="result-count" role="status"></p></div>'
def localize_player(chunk,lang,r,label,title):
 """Translate the visible labels of an English podcast widget (its audio and transcript stay English)."""
 P=I18N[lang]['player']; short=r['label'].replace(' 0',' ')   # "Chapter 1", as the widget writes it
 chunk=chunk.replace(f"{short} · {r['title']}",P['episode'].format(label=label,title=title))
 chunk=chunk.replace(f"{short} mind map",P['mind_map_of'].format(label=label))
 chunk=re.sub(r'<noscript>.*?</noscript>','',chunk,count=1,flags=re.S)
 for english,translated in P['labels'].items(): chunk=chunk.replace(english,translated)
 return chunk
def home(lang):
 S=I18N[lang]; K=S['card']; en=lang=='en'
 titles=S.get('titles',{}); groups=S.get('groups',{}); text=S.get('curriculum',editorial)
 def title_of(r): return r['title'] if en else titles[r['id']]
 def group_of(r): return r['group'] if en else groups[r['group']]
 def label_of(r): return K['chapter_label'].format(n=r['id'][2:] if en else int(r['id'][2:])) if r['id'].startswith('ch') else K['appendix_label'].format(n=r['id'][-1])
 slide_html=''
 for i,sl in enumerate(S['slides']):
  id=sl['id']; chart=f'assets/charts/{id}.svg' if en else f'assets/charts/{id}-{lang}.svg'
  slide_html+=f'<article class="question-slide" data-slide="{i}" aria-label="{S["slide_aria"].format(n=i+1,topic=sl["topic"])}"'+(' hidden' if i else '')+f'><img class="scene-art" src="assets/scenes/{id}.jpg" alt="" aria-hidden="true" width="1200" height="800" loading="{"eager" if i == 0 else "lazy"}" decoding="async"><div class="slide-intro"><p class="eyebrow">{sl["topic"]}</p><h2>{sl["question"]}</h2></div><img class="chart" src="{versioned(chart)}" alt="{sl["alt"]}" width="640" height="360"><div class="slide-caption"><p>{sl["description"]}</p><div class="chart-meta">{sl["source"]}</div><a href="{byid[sl["chapter"]]["book"]}">{S["explore_chapter"].format(n=int(sl["chapter"][2:]))} <span aria-hidden="true">↗</span></a></div></article>'
 selectors=''.join(f'<button class="question-selector" data-go="{i}" aria-label="{S["show_question"].format(n=i+1,label=label)}" aria-pressed="{str(i==0).lower()}">{label}</button>' for i,label in enumerate(S['topic_labels']))
 hero=S['hero_html'].replace('{ch1}',byid['ch01']['book']).replace('{slides}',slide_html).replace('{selectors}',selectors)
 def card(r):
  e=text[r['id']]; chapter=r['id'].startswith('ch'); number=r['id'][2:] if chapter else r['id'][-1]
  anchor=f"chapter-{int(number)}" if chapter else f"appendix-{number.lower()}"
  label=label_of(r); title=title_of(r)
  actions=[('↗',K['read_chapter'] if chapter else K['read_appendix'],r['book']),('</>',K['open_notebook'],r['colab'])]
  if r.get('slides'): actions.append(('▤',K['slides'],r['slides']))
  for kind,key,icon in [('data','data_apps','↗'),('model','figure_apps','↗')]:
   if kind in r['apps']: actions.append((icon,K[key],r['apps'][kind]['url']))
  links=''.join(f'<a class="chapter-action{ " chapter-action-primary" if i==0 else ""}" href="{esc(url)}" target="_blank" rel="noopener"><span aria-hidden="true">{esc(icon)}</span>{text_}</a>' for i,(icon,text_,url) in enumerate(actions))
  player=players.get(r['id'],'').replace('Listen AI Podcast',S['listen'])
  if player and not en: player=localize_player(player,lang,r,label,title)
  tag=f'<span class="chapter-tag">{K["start_here"]}</span>' if r['id']=='ch01' else ''
  search=label+' '+title+' '+e['question']+' '+group_of(r)
  if not en: search=r['label']+' '+search+' '+r['title']   # English chapter numbers and titles match too
  return f'''<article id="{anchor}" class="chapter-card resource" data-topic="{esc(group_of(r))}" data-search="{esc(search)}" aria-labelledby="title-{r['id']}"><div class="chapter-top"><span class="chapter-number">{number}</span><span class="chapter-method">{esc(title)}</span>{tag}</div><div class="chapter-story"><h3 id="title-{r['id']}">{esc(e['question'])}</h3><p>{esc(e['introduction'])}</p></div><a class="chapter-thumb" href="{esc(r['mindmap'])}" data-map-title="{esc(label+': '+title)}" aria-label="{esc(K['enlarge'].format(label=label))}" target="_blank" rel="noopener"><img src="{r['preview']}" alt="{esc(K['map_alt'].format(label=label,title=title))}" loading="lazy" width="900" height="600"><span class="art-caption">{K['map_caption']} <span aria-hidden="true">↗</span></span></a><div class="chapter-actions">{links}</div>{player}</article>'''
 search=f'<div class="filter-bar"><label>{S["search_label"].format(label=S["search_target"])}<input type="search" id="resource-search" placeholder="{S["search_placeholder"]}"></label><label>{S["topic_label"]}<select id="topic-filter"><option value="">{S["all_topics"]}</option>'+''.join(f'<option>{esc(g)}</option>' for g in dict.fromkeys(group_of(r) for r in resources))+'</select></label><p id="result-count" role="status"></p></div>'
 directory='<section class="home-curriculum" id="curriculum" aria-labelledby="curriculum-title"><div class="shell"><span id="chapters" class="anchor-alias"></span><div class="section-heading curriculum-heading"><div>'+S['curriculum_heading_html']+'</div>'+search+player_assets
 for group in dict.fromkeys(r['group'] for r in resources if r['id'].startswith('ch')):
  name=group if en else groups[group]
  directory+=f'<section class="curriculum-group" aria-label="{esc(name)}"><h3 class="group-title">{esc(name)}</h3><div class="chapter-grid">'+''.join(card(r) for r in resources if r['group']==group)+'</div></section>'
 directory+='<details class="appendices" id="appendices"><summary><span>'+S['appendices_summary_html']+'</span><span class="overview-toggle" aria-hidden="true">+</span></summary><div class="chapter-grid">'+''.join(card(r) for r in resources if r['id'].startswith('app'))+f'</div></details><p class="empty" hidden>{S["empty"]}</p><p class="curriculum-credit">{S["curriculum_credit"]}</p></div></section>'
 page('index.html',S['page_title'],S['page_description'],hero+S['pillars_html']+directory+S['viewer_html'],lang)
for lang in LANGS: home(lang)
# App collections share chapter questions and mind maps with the listening page.
for kind,name,label,hook,desc,featured_id in [
 ('data','data-apps.html','Data Apps','Find the facts.<br>Ask better questions.','Explore the evidence behind the book. Compare economies, trace changes over time, and discover the patterns that macroeconomic models aim to explain.','ch03'),
 ('model','figure-apps.html','Figure Apps','Change an assumption.<br>See the economy respond.','Put the book’s models to work. Explore interactive figures, change parameters, and follow the mechanisms connecting growth, employment, inflation, and policy.','ch05')]:
 available=[r for r in resources if kind in r['apps']]
 featured=byid[featured_id]; fe=editorial[featured_id]
 noun='data' if kind=='data' else 'model'
 feature_caption='Trace living standards across countries and centuries.' if kind=='data' else 'Explore saving, capital accumulation, and the steady state.'
 body=f'''<div class="apps-page"><section class="apps-hero shell" aria-labelledby="page-title"><div class="apps-hero-copy"><p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>{len(available)} CHAPTER COLLECTIONS. LEARN BY DOING.</p><h1 id="page-title">{label.split()[0]} <span>Apps</span></h1><p class="apps-hook">{hook}</p><p class="apps-description">{desc}</p><div class="actions"><a class="button primary" href="#app-collections">Explore {label} <span aria-hidden="true">↓</span></a></div><p class="apps-hero-note">Start with a question. Open a chapter. Explore the {noun}.</p><div class="apps-facts"><span><strong>{len(available)}</strong> chapter collections</span><span><strong>Interactive</strong> exploration</span><span>From the book · Organized by chapter</span></div></div><figure class="apps-feature"><div class="apps-feature-top"><p class="eyebrow">FEATURED CHAPTER</p><span>{esc(featured['label'])}</span></div><a class="apps-feature-map" href="{esc(featured['mindmap'])}" target="_blank" rel="noopener" aria-label="Enlarge {esc(featured['label'])} mind map"><img src="{featured['preview']}" alt="{esc(featured['title'])} mind map" width="900" height="600" fetchpriority="high"><span>Explore the mind map <span aria-hidden="true">↗</span></span></a><p class="apps-feature-title">{esc(featured['title'])}</p><h2>{esc(fe['question'])}</h2><p class="apps-feature-description">{feature_caption}</p><figcaption><a href="{esc(featured['apps'][kind]['url'])}"><span class="apps-launch-icon" aria-hidden="true">↗</span><span>Open {label}<small>{esc(featured['label'])} collection</small></span><span class="apps-launch-arrow" aria-hidden="true">→</span></a></figcaption></figure></section><section class="apps-collection" id="app-collections" aria-labelledby="collection-title"><div class="shell"><div class="apps-collection-heading"><div><p class="eyebrow">EXPLORE BY CHAPTER</p><h2 id="collection-title">One question.<br><span>A way to explore it.</span></h2></div><p>Choose a chapter below. Use its mind map to see the big picture, then open the apps to investigate the details.</p></div>'''+searchbox('chapter collections')+'<div class="apps-chapter-grid">'
 for r in available:
  e=editorial[r['id']]; app=r['apps'][kind]
  searchable=' '.join([r['label'],r['title'],e['question'],r['group'],*[html.unescape(t) for t in app['topics']]])
  body+=f'''<article id="chapter-{int(r['id'][2:])}" class="apps-chapter-card resource" data-topic="{esc(r['group'])}" data-search="{esc(searchable)}" aria-labelledby="question-{r['id']}"><div class="apps-chapter-header"><span class="apps-chapter-number" aria-hidden="true">{r['id'][2:]}</span><div><p class="eyebrow">{esc(r['label'])} · {esc(r['group'])}</p><p class="apps-chapter-title">{esc(r['title'])}</p></div></div><h3 id="question-{r['id']}">{esc(e['question'])}</h3><p class="apps-chapter-description">{esc(e['introduction'])}</p><a class="apps-chapter-map" href="{esc(r['mindmap'])}" target="_blank" rel="noopener" aria-label="Enlarge {esc(r['label'])} mind map"><img src="{r['preview']}" alt="{esc(r['title'])} mind map" loading="lazy" width="900" height="600"><span>Explore the chapter map <span aria-hidden="true">↗</span></span></a><div class="apps-chapter-actions"><a class="button primary" href="{esc(app['url'])}">Open {label} <span aria-hidden="true">↗</span></a><a class="text-link" href="{esc(r['book'])}">Read chapter <span aria-hidden="true">↗</span></a></div></article>'''
 body+='</div><p class="empty" hidden>No matching chapter collections. Try another search or topic.</p>'
 if kind=='model': body+='<p class="apps-book-note">Figure Apps are called Model Apps in the book.</p>'
 body+='</div></section></div>'
 page(name,label,desc,body)
# The listening page adapts generated widgets; managed player files stay untouched.
episodes=[r for r in resources if 'podcast' in r]
config=json.loads((R/'player-config.json').read_text())
episode_config={r['id']:ep for r,ep in zip(episodes,config['episodes'])}
for ep in config['episodes']:
 if ep['id'] not in episode_config:
  episode_config[ep['id']]=ep
  players[ep['id']]=widget_chunks[ep['id']]
JAPANESE_CATALOG=json.loads((R/'data/podcasts-ja.json').read_text())
JAPANESE_EPISODES=[item for item in JAPANESE_CATALOG['episodes'] if item.get('status') in ('publicly_verified','website_ready_spotify_pending')]
def duration_label(seconds):
 seconds=int(seconds)
 return f'{seconds//60:02d}:{seconds%60:02d}'
def listening_player(r):
 chunk=players[r['id']]
 chunk=re.sub(r'<div class="podcast-launch-row">.*?</div>', '', chunk, count=1, flags=re.S)
 chunk=re.sub(r'<noscript>.*?</noscript>', '', chunk, count=1, flags=re.S)
 chunk=re.sub(r'<a class="podcast-mindmap".*?</a>', '', chunk, count=1, flags=re.S)
 # Keep the runtime's disclosure hooks in the DOM, but show controls immediately here.
 ep=episode_config[r['id']]
 hook=f'<button hidden data-podcast-toggle aria-expanded="true" aria-controls="{ep["id"]}-player" type="button">Open audio player</button>'
 chunk=chunk.replace('<section ',hook+'<section ',1)
 chunk=chunk.replace('class="podcast-player"','class="podcast-player episode-player"',1)
 chunk=re.sub(r'(<section[^>]+) hidden>',r'\1 tabindex="-1">',chunk,count=1)
 chunk=chunk.replace('class="podcast-close"','hidden class="podcast-close"',1)
 if r['id'].startswith('podcast-ja-'):
  transcript_link=f'<a class="podcast-action-link" href="{esc(ep["study_url"])}" target="_blank" rel="noopener" aria-label="English Japanese transcript (opens in a new tab)"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M14 3h7v7m0-7L10 14"/><path d="M10 3H3v18h18v-7"/></svg>English Japanese transcript</a>\n    '
  spotify_anchor=r'(?=\s*<a class="podcast-action-link" href="https://open\.spotify\.com/episode/)'
  target=spotify_anchor if re.search(spotify_anchor,chunk) else r'(?=\s*<a class="podcast-action-link" href="audio-player/transcripts/)'
  chunk=re.sub(target, '\n    '+transcript_link, chunk, count=1)
  for english, japanese in {
   'Chapter 1 · Macroeconomics': '第1章 · マクロ経済学入門',
   '第1章 · マクロ経済学入門': '第1章 · マクロ経済学入門',
   'AI podcast · ': '日本語版 AI音声 · ',
   'Now: Opening': '再生中：はじめに',
   'Close the podcast player': 'プレーヤーを閉じる',
   'Your browser does not support audio playback. You can read the transcript below.': 'お使いのブラウザーは音声再生に対応していません。下のトランスクリプトをお読みください。',
   'Seek in podcast': 'ポッドキャストの再生位置',
   'Back 15 seconds': '15秒戻る',
   'Play podcast': 'ポッドキャストを再生',
   'Forward 30 seconds': '30秒進む',
   'Playback speed: 1×. Click to change': '再生速度：1×。クリックで変更',
   'Episode sections': 'エピソードのセクション',
   '<span>Read along</span>': '<span>文字を追う</span>',
   'Open Transcript': '日本語トランスクリプト',
   'Listen on Spotify': 'Spotifyで聴く',
   ' (opens in a new tab)': '（新しいタブで開きます）',
   'Timed transcript. Select a passage to seek.': '時間付きトランスクリプト。段落を選ぶとその位置へ移動します。',
   '> Follow audio<': '> 音声に合わせて移動<',
   ' podcast study player"': 'の日本語ポッドキャスト・プレーヤー"',
   ' podcast">': 'の日本語ポッドキャスト">',
  }.items():
   if english != japanese: chunk=chunk.replace(english,japanese)
 return '\n'.join(line.rstrip() for line in chunk.replace('<h5>','<h3>').replace('</h5>','</h3>').splitlines())+'\n'

def replace_div_contents(document, opening_tag, content):
 start=document.index(opening_tag)
 content_start=start+len(opening_tag)
 tags=re.finditer(r'</?div\b[^>]*>',document[content_start:])
 depth=1
 for match in tags:
  token=match.group(0)
  depth += -1 if token.startswith('</') else 1
  if depth==0:
   closing_start=content_start+match.start()
   return document[:content_start]+content+document[closing_start:]
 raise ValueError(f'Unclosed integration wrapper: {opening_tag}')
first=episodes[0]; first_ep=episode_config[first['id']]
total_minutes=round(sum(r['podcast']['duration'] for r in episodes)/60)
body=f'''<div class="podcasts-page"><section class="podcast-hero shell" aria-labelledby="page-title"><div class="podcast-hero-copy"><p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>21 CHAPTERS. A NEW WAY TO LISTEN.</p><h1 id="page-title">AI <span>Podcasts</span></h1><p class="podcast-hook">Hear the question.<br>Follow the reasoning.</p><p class="podcast-description">From rising living standards to recessions and inflation, explore the ideas behind the whole economy. Listen at your own pace, jump to a section, or follow the conversation word by word.</p><div class="podcast-hero-actions"><a class="button primary" href="#episodes">Explore the episodes <span aria-hidden="true">↓</span></a><a class="button secondary" href="podcasts-ja.html" lang="ja" hreflang="ja">Explore the episodes in Japanese <span aria-hidden="true">↗</span></a><p>Start at Chapter 1, or follow your curiosity.</p></div><div class="collection-facts"><span><strong>21</strong> English episodes</span><span><strong>{total_minutes}</strong> minutes of listening</span><span>Read along as you listen</span></div></div><figure class="podcast-feature" aria-labelledby="featured-title"><div class="feature-top"><span class="eyebrow">YOUR FIRST LISTEN</span><span class="tiny-tag">CHAPTER 01 · {duration_label(first['podcast']['duration'])}</span></div><a class="featured-art" href="#chapter-1" aria-label="Explore Chapter 1: Introduction to Macroeconomics"><img src="{first['preview']}" width="900" height="600" alt="Introduction to Macroeconomics: the chapter mind map" fetchpriority="high"></a><h2 id="featured-title">What can we learn by looking at the whole economy?</h2><p>Income. Jobs. Prices.<br>Start with the questions that connect them.</p><figcaption><button class="feature-listen" type="button" data-podcast-start="{first_ep['id']}-player" hidden><span class="listen-circle" aria-hidden="true">▶</span><span>Start listening<small>Introduction to Macroeconomics · Chapter 1</small></span><span class="listen-arrow" aria-hidden="true">↘</span></button><noscript><a href="#chapter-1">Go to Chapter 1’s audio player ↓</a></noscript></figcaption></figure></section><section class="shell episode-collection" id="episodes" aria-labelledby="episodes-title"><div class="collection-heading"><div><p class="eyebrow">THE LISTENING COLLECTION</p><h2 id="episodes-title">One chapter. One big question.</h2></div><p>Explore the facts. Follow the model.<br>Connect the reasoning to the real world.</p></div>'''
body+='<nav class="episode-directory" aria-label="Jump to a podcast chapter">'+''.join(f'<a href="#chapter-{int(r["id"][2:])}"><span>{r["id"][2:]}</span>{esc(r["title"])}<span class="chapter-arrow" aria-hidden="true">↗</span></a>' for r in episodes)+'</nav>'
body+='<div class="listening-guide"><span class="guide-icon" aria-hidden="true">♫</span><p><strong>Make it your conversation.</strong> Change the speed, revisit a section, or select <strong>Read along</strong> to follow the transcript. Each episode also opens on Spotify.</p><span class="guide-label">LISTEN · PAUSE · REFLECT</span></div>'+searchbox('episodes')+'<div class="episodes">'
for r in episodes:
 e=editorial[r['id']]; ep=episode_config[r['id']]; n=int(r['id'][2:])
 transcript=json.loads((R/ep['transcript']).read_text())
 notes=''.join(f'<li>{esc(section["title"])}</li>' for section in transcript['sections'][1:-1])
 body+=f'''<article class="episode resource" id="chapter-{n}" aria-labelledby="episode-{n}-title" data-topic="{esc(r['group'])}" data-search="{esc(r['label']+' '+r['title']+' '+e['question']+' '+r['group'])}"><header class="episode-header"><span class="episode-number" aria-hidden="true">{r['id'][2:]}</span><div><p class="eyebrow">{esc(r['label'])} / {esc(r['title'])}</p><h2 id="episode-{n}-title">{esc(e['question'])}</h2></div><span class="episode-duration" aria-label="Duration {duration_label(r['podcast']['duration'])}">◷ {duration_label(r['podcast']['duration'])}</span></header><div class="episode-grid"><div class="episode-context"><a class="episode-art" href="{esc(r['mindmap'])}" target="_blank" rel="noopener" aria-label="View {esc(r['label'])} mind map at full size (opens in a new tab)"><img src="{r['preview']}" alt="{esc(r['title'])} mind map" loading="lazy" width="900" height="600"><span>Explore the mind map <span aria-hidden="true">↗</span></span></a><p class="episode-description">{esc(e['introduction'])}</p><div class="listening-notes"><h3>Listen for</h3><ul>{notes}</ul></div><a class="episode-book" href="{r['book']}">Read the chapter <span aria-hidden="true">↗</span></a></div><div class="episode-listening">{listening_player(r)}</div></div></article>'''
body+=f'''</div><p class="empty" hidden>No matching episodes. Try another search or topic.</p><p class="resource-note">AI-generated discussions accompany the book. Check explanations against the chapter and its sources. Transcript timing is approximate.</p><div class="listening-close"><p class="eyebrow">KEEP THE QUESTION GOING</p><h2>Heard an idea you want to explore?</h2><p>Bring it to the book. Work through the data, experiment with a model, and make the reasoning your own.</p><a class="button primary" href="{BOOK}">Open the book <span aria-hidden="true">↗</span></a></div></section></div>'''
page('podcasts.html','AI Podcasts','Listen to all 21 macroeconomics chapters with timed transcripts, section navigation, and Spotify links.',body)
# Japanese episodes are driven by the website-ready catalog and share the English player runtime.
ja_episodes=sorted(JAPANESE_EPISODES,key=lambda item:item['chapter'])
if not ja_episodes: raise SystemExit('Japanese catalog has no website-ready episodes.')
first_ja=ja_episodes[0]
show_url=JAPANESE_CATALOG['show']['spotify_url']
ja_directory=''.join(f'<a href="#chapter-{item["chapter"]}"><span>{item["chapter"]:02}</span>{esc(item["title"])}<span class="chapter-arrow" aria-hidden="true">↗</span></a>' for item in ja_episodes)
ja_cards=[]
for item in ja_episodes:
 r={'id':item['id'],'title':f'第{item["chapter"]}章 · {item["title"]}','label':f'第{item["chapter"]}章'}
 topics=''.join(f'<li>{esc(topic)}</li>' for topic in item['topics'])
 search=esc(' '.join([r['title'],item['question'],item['description'],*item['topics']]))
 player=listening_player(r)
 release_badge='' if item.get('status')=='publicly_verified' else '<span class="tiny-tag">Spotify公開準備中</span>'
 ja_cards.append(f'''<article class="episode resource" id="chapter-{item["chapter"]}" aria-labelledby="episode-{item["chapter"]}-title" data-topic="基礎" data-search="{search}"><header class="episode-header"><span class="episode-number" aria-hidden="true">{item["chapter"]:02}</span><div><p class="eyebrow">{r["title"]}</p><h2 id="episode-{item["chapter"]}-title">{esc(item["question"])}</h2></div><span class="episode-duration" aria-label="再生時間 {duration_label(item["duration"])}">◷ {duration_label(item["duration"])}</span>{release_badge}</header><div class="episode-grid"><div class="episode-context"><a class="episode-art" href="{esc(item["artwork"])}" target="_blank" rel="noopener" aria-label="第{item["chapter"]}章のマインドマップを拡大表示"><img src="{esc(item["artwork"])}" alt="第{item["chapter"]}章のマインドマップ" loading="lazy" width="320" height="320"><span>マインドマップを見る <span aria-hidden="true">↗</span></span></a><p class="episode-description">{esc(item["description"])}</p><div class="listening-notes"><h3>このエピソードで扱う内容</h3><ul>{topics}</ul></div><a class="episode-book" href="{esc(item["book_url"])}" target="_blank" rel="noopener">本書の第{item["chapter"]}章を読む <span aria-hidden="true">↗</span></a></div><div class="episode-listening">{player}</div></div></article>''')
first_duration=duration_label(first_ja['duration'])
ja_body=f'''<div class="podcasts-page"><section class="podcast-hero shell" aria-labelledby="page-title"><div class="podcast-hero-copy"><p class="eyebrow"><span class="status-dot" aria-hidden="true"></span>日本語版 · {len(ja_episodes)}章の音声を公開中</p><h1 id="page-title">AI <span>ポッドキャスト</span></h1><p class="podcast-hook">問いを聞き、<br>考え方をたどる。</p><p class="podcast-description">マクロ経済学の問いや、経済学者が答えを考えるために使うモデルを、日本語の会話で紹介します。音声を聞きながら、英語との対訳、ふりがな、用語集も利用できます。</p><div class="podcast-hero-actions"><a class="button primary" href="#episodes">日本語版のエピソードを聴く <span aria-hidden="true">↓</span></a><a class="button secondary" href="{esc(show_url)}" target="_blank" rel="noopener">Spotifyで番組を開く <span aria-hidden="true">↗</span></a></div><div class="collection-facts"><span><strong>{len(ja_episodes)}</strong> 章の音声を再生可能</span><span>第{ja_episodes[-1]["chapter"]+1}章以降は制作中</span><span>対訳・ふりがな付き</span></div></div><figure class="podcast-feature" aria-labelledby="featured-title"><div class="feature-top"><span class="eyebrow">最初に聴くエピソード</span><span class="tiny-tag">第{first_ja["chapter"]}章 · {first_duration}</span></div><a class="featured-art" href="#chapter-{first_ja["chapter"]}" aria-label="第{first_ja["chapter"]}章 {esc(first_ja["title"])}"><img src="{esc(first_ja["artwork"])}" width="320" height="320" alt="第{first_ja["chapter"]}章のマインドマップ" fetchpriority="high"></a><h2 id="featured-title">{esc(first_ja["question"])}</h2><p>{esc(first_ja["description"])}</p><figcaption><a class="feature-listen" href="#chapter-{first_ja["chapter"]}"><span class="listen-circle" aria-hidden="true">↓</span><span>第{first_ja["chapter"]}章を聴く<small>{esc(first_ja["title"])}</small></span><span class="listen-arrow" aria-hidden="true">↘</span></a></figcaption></figure></section><section class="shell episode-collection" id="episodes" aria-labelledby="episodes-title"><div class="collection-heading"><div><p class="eyebrow">日本語版のエピソード</p><h2 id="episodes-title">再生できるエピソード</h2></div><p>音声を聞き、対訳で内容を確認し、用語集で専門用語を復習できます。</p></div><nav class="episode-directory" aria-label="日本語ポッドキャストの章">{ja_directory}</nav><div class="listening-guide"><span class="guide-icon" aria-hidden="true">♫</span><p><strong>聞きながら学ぶ。</strong>プレーヤーの「English Japanese transcript」から英日対訳を確認できます。Spotifyへのリンクは番組で配信中の章に表示されます。</p><span class="guide-label">聴く · 止める · 振り返る</span></div><div class="episodes">{"".join(ja_cards)}</div><p class="resource-note">日本語版の音声はAIによるナレーションです。教科書 Charles I. Jones, <i>Macroeconomics</i>, 第6版（2024年）に基づく独立した学習用コンテンツであり、著者・出版社による承認や提携を示すものではありません。</p><div class="listening-close"><p class="eyebrow">次の問いへ</p><h2>聞いた内容を、本書で確かめる。</h2><p>データを見て、モデルを動かし、経済の考え方を自分で試してみましょう。</p><a class="button primary" href="https://quarcs-lab.github.io/macro102-site/ja/">日本語版の本を開く <span aria-hidden="true">↗</span></a></div></section></div>'''
page('podcasts-ja.html','日本語版 AIポッドキャスト','マクロ経済学の日本語AIポッドキャスト。音声、英日対訳、ふりがな、用語集を利用できます。',ja_body,'ja')
body=intro('AI TUTORS · FORTHCOMING','A thinking partner.<br>For your next question.','A dedicated space for AI tutors that accompany the book. This collection is forthcoming.')+f'''<section class="shell tutor-section"><div class="tutor-panel"><div class="tutor-art" aria-hidden="true"><span>?</span><i>Y</i><b>π</b><em>g</em></div><div><span class="coming-badge">IN DEVELOPMENT</span><h2>More ways to work<br>through an idea.</h2><p>The tutors will appear here when they are available. In the meantime, start with the book’s explanations, explore its interactive figures, or listen to a chapter discussion.</p><div class="actions"><a class="button primary" href="{BOOK}">Read the book ↗</a><a class="text-link" href="figure-apps.html">Explore Figure Apps →</a></div></div></div></section>'''
page('tutors.html','AI Tutors — Forthcoming','AI tutors for Data Science & Macroeconomics are forthcoming. Explore the book and its existing resources today.',body)
print('Built six static pages.')
