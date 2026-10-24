(() => {
  const theme = document.querySelector('#theme-toggle');
  function themeLabel() { theme.setAttribute('aria-label', `Switch to ${document.documentElement.classList.contains('light') ? 'dark' : 'light'} theme`); }
  themeLabel();
  theme.addEventListener('click', () => { const light = document.documentElement.classList.toggle('light'); try { localStorage.setItem('theme', light ? 'light' : 'dark'); } catch {} themeLabel(); });
  const menu = document.querySelector('.menu-button'), nav = document.querySelector('#navigation');
  menu.addEventListener('click', () => { const open = nav.classList.toggle('is-open'); menu.setAttribute('aria-expanded', String(open)); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.classList.contains('is-open')) { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded','false'); menu.focus(); }});
  const search = document.querySelector('#resource-search'), topic = document.querySelector('#topic-filter');
  if (search) {
    const rows = [...document.querySelectorAll('.resource')], count = document.querySelector('#result-count');
    // Offer only topics represented on this page.
    [...topic.options].forEach(o => { if (o.value && !rows.some(r => r.dataset.topic === o.value)) o.remove(); });
    function filter() { const words = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean); let n = 0;
      rows.forEach(row => { const match = words.every(w => row.dataset.search.toLowerCase().includes(w)) && (!topic.value || row.dataset.topic === topic.value); row.hidden = !match; if (match) n++; else row.querySelectorAll('audio').forEach(a => a.pause()); });
      count.textContent = `${n} of ${rows.length} resources`; document.querySelector('.empty').hidden = n !== 0;
    }
    search.addEventListener('input', filter); topic.addEventListener('change', filter); filter();
  }
  const deck = document.querySelector('.question-deck');
  if (deck) {
    const slides = [...deck.querySelectorAll('[data-slide]')], dots = [...deck.querySelectorAll('[data-go]')], pause = document.querySelector('#pause-slides'), media = matchMedia('(prefers-reduced-motion: reduce)');
    let index = 0, paused = media.matches, hover = false, focused = false, timer;
    function render() { slides.forEach((s,i) => { s.hidden = i !== index; }); dots.forEach((d,i) => d.setAttribute('aria-pressed', String(i===index))); document.querySelector('#slide-count').textContent = `0${index+1} / 06`; }
    function schedule() { clearInterval(timer); if (!paused && !hover && !focused && !document.hidden && !media.matches) timer = setInterval(() => { index = (index+1)%slides.length; render(); }, 9000); }
    function move(i) { index=(i+slides.length)%slides.length; render(); schedule(); }
    function updatePause() { pause.disabled = media.matches; pause.title = media.matches ? 'Automatic rotation is off because reduced motion is enabled' : ''; pause.textContent = paused ? '▶' : 'Ⅱ'; pause.setAttribute('aria-label', paused ? 'Start automatic rotation' : 'Pause automatic rotation'); pause.setAttribute('aria-pressed',String(paused)); }
    dots.forEach(d => d.addEventListener('click', () => move(Number(d.dataset.go))));
    document.querySelector('#previous-slide').addEventListener('click', () => move(index-1)); document.querySelector('#next-slide').addEventListener('click', () => move(index+1));
    pause.addEventListener('click', () => { paused=!paused; updatePause(); schedule(); });
    deck.addEventListener('mouseenter', () => {hover=true;schedule();});deck.addEventListener('mouseleave', () => {hover=false;schedule();});
    deck.addEventListener('focusin', () => {focused=true;schedule();});deck.addEventListener('focusout', () => {setTimeout(() => {focused=deck.contains(document.activeElement);schedule();},0);});
    document.addEventListener('visibilitychange',schedule);media.addEventListener('change',()=>{paused=media.matches;updatePause();schedule();});updatePause();schedule();
  }
})();
