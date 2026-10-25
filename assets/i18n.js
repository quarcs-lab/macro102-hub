// The home page in three languages: index.html (English), es/index.html and ja/index.html. Only the
// home page is translated. Loaded in <head> by those three pages only.
(() => {
  // Shared with the book's home pages (same origin), so a choice made on one site holds on the other.
  const KEY = 'macro102-home-lang';
  const here = (document.documentElement.lang || 'en').slice(0, 2);
  function saved(value) {
    try { if (value === undefined) return localStorage.getItem(KEY); localStorage.setItem(KEY, value); } catch { return null; }
  }
  function browserLang() {
    const l = ((navigator.languages && navigator.languages[0]) || navigator.language || '').toLowerCase();
    return l.startsWith('es') ? 'es' : l.startsWith('ja') ? 'ja' : 'en';
  }
  // Spanish and Japanese browsers go from the English home page to es/ or ja/ before anything is drawn.
  // A language picked in the switcher wins; es/, ja/ and links to a section (#...) never redirect.
  if (here === 'en' && !location.hash) {
    let want = saved();
    if (!['en', 'es', 'ja'].includes(want)) want = browserLang();
    if (want !== 'en') { location.replace(want + '/'); return; }
  }
  document.addEventListener('click', e => {
    const link = e.target.closest && e.target.closest('.lang-switch a[data-lang]');
    if (link) saved(link.dataset.lang);
  });

  // es/ja: the podcast runtime (audio-player/podcast-player.js, generator-owned) writes English labels
  // as it plays; translate them as they appear. The audio, transcripts and section titles stay English.
  const P = window.SITE_I18N && window.SITE_I18N.player;
  if (!P) return;
  const TEXT = [
    [/^Read along$/, P.read_along], [/^Hide transcript$/, P.hide_transcript],
    [/^Now: Part (\d+) · (.*)$/, P.now_part], [/^Now: (.*)$/, P.now], [/^Part (\d+) · (.*)$/, P.part],
    [/^Audio could not play\./, P.error_play], [/^Audio is unavailable\./, P.error_audio],
    [/^Interactive transcript unavailable\./, P.error_transcript]
  ];
  const ATTR = [
    [/^Play podcast$/, P.play], [/^Pause podcast$/, P.pause],
    [/^Playback speed: (.*)×\. Click to change$/, P.speed], [/^(\d\d:\d\d) of (\d\d:\d\d)$/, P.of]
  ];
  function translate(value, rules) {
    for (const [pattern, out] of rules) {
      const m = value.match(pattern);
      if (m) return out.replace(/\$(\d)/g, (_, i) => m[i]);
    }
    return null;
  }
  function fix(el) {
    if (el.nodeType !== 1 || !el.closest('.podcast-player')) return;
    if (el.childNodes.length === 1 && el.firstChild.nodeType === 3) {
      const t = translate(el.textContent, TEXT);
      if (t !== null && t !== el.textContent) el.textContent = t;
    }
    for (const name of ['aria-label', 'aria-valuetext']) {
      const v = el.getAttribute(name);
      const t = v && translate(v, ATTR);
      if (t && t !== v) el.setAttribute(name, t);
    }
  }
  new MutationObserver(mutations => {
    for (const m of mutations) {
      const target = m.target.nodeType === 3 ? m.target.parentElement : m.target;
      if (target) fix(target);
      m.addedNodes.forEach(n => { if (n.nodeType === 1) { fix(n); n.querySelectorAll('*').forEach(fix); } });
    }
  }).observe(document.documentElement, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['aria-label', 'aria-valuetext'] });
})();
