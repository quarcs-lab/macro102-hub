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
    const rows = [...document.querySelectorAll('.resource')], count = document.querySelector('#result-count'), appendices = document.querySelector('#appendices');
    let filtering = false, priorAppendicesOpen = false;
    // Offer only topics represented on this page.
    [...topic.options].forEach(o => { if (o.value && !rows.some(r => r.dataset.topic === o.value)) o.remove(); });
    function filter() {
      const query = search.value.toLowerCase().trim(), chapterQuery = query.match(/\b(chapter|appendix)\s+(\d+|[a-i])\b/);
      const words = (chapterQuery ? query.replace(chapterQuery[0], '') : query).split(/\s+/).filter(Boolean); let n = 0;
      rows.forEach(row => { const label = row.dataset.search.toLowerCase().match(/^(chapter|appendix)\s+(\d+|[a-i])\b/); const identifierMatches = !chapterQuery || (label && label[1] === chapterQuery[1] && (label[1] === 'chapter' ? Number(label[2]) === Number(chapterQuery[2]) : label[2] === chapterQuery[2])); const match = identifierMatches && words.every(w => row.dataset.search.toLowerCase().includes(w)) && (!topic.value || row.dataset.topic === topic.value); row.hidden = !match; if (match) n++; else row.querySelectorAll('audio').forEach(a => a.pause()); });
      const active = !!query || !!topic.value;
      document.querySelectorAll('.curriculum-group').forEach(group => { group.hidden = ![...group.querySelectorAll('.resource')].some(row => !row.hidden); });
      if (appendices) {
        if (active && !filtering) priorAppendicesOpen = appendices.open;
        const matches = [...appendices.querySelectorAll('.resource')].some(row => !row.hidden);
        appendices.hidden = active && !matches;
        if (active && matches) appendices.open = true;
        else if (!active && filtering) appendices.open = priorAppendicesOpen;
      }
      filtering = active;
      count.textContent = `${n} of ${rows.length} resources`; document.querySelector('.empty').hidden = n !== 0;
    }
    search.addEventListener('input', filter); topic.addEventListener('change', filter); filter();
  }
  const viewer = document.querySelector('#mindmap-viewer');
  if (viewer && typeof viewer.showModal === 'function') {
    const image = document.querySelector('#mindmap-image'), title = document.querySelector('#mindmap-title'), original = document.querySelector('#mindmap-original'), status = document.querySelector('#mindmap-status');
    let trigger;
    document.querySelectorAll('[data-map-title]').forEach(link => link.addEventListener('click', e => {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault(); trigger = link; title.textContent = link.dataset.mapTitle;
      image.alt = `${link.dataset.mapTitle} mind map`; original.href = link.href;
      status.textContent = 'Loading the full-resolution mind map…';
      image.src = link.href; viewer.showModal();
    }));
    image.addEventListener('load', () => { status.textContent = ''; });
    image.addEventListener('error', () => { status.textContent = 'The mind map could not load. Use Open original to view the source image.'; });
    document.querySelector('#close-mindmap').addEventListener('click', () => viewer.close());
    viewer.addEventListener('click', e => { if (e.target === viewer) { const r = viewer.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) viewer.close(); } });
    viewer.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); viewer.close(); } });
    viewer.addEventListener('close', () => trigger?.focus());
  }
  const appendixSection = document.querySelector('#appendices');
  if (appendixSection) {
    appendixSection.addEventListener('toggle', () => { if (!appendixSection.open) appendixSection.querySelectorAll('audio').forEach(audio => audio.pause()); });
    function revealAnchor() { const id = decodeURIComponent(location.hash.slice(1)); const target = id && document.getElementById(id); if (target && appendixSection.contains(target) && target !== appendixSection) appendixSection.open = true; }
    revealAnchor(); window.addEventListener('hashchange', revealAnchor);
  }
  const deck = document.querySelector('.question-deck');
  if (deck) {
    const slides = [...deck.querySelectorAll('[data-slide]')], dots = [...deck.querySelectorAll('[data-go]')], pause = document.querySelector('#pause-slides'), media = matchMedia('(prefers-reduced-motion: reduce)');
    let index = 0, paused = media.matches, hover = false, focused = false, timer;
    function render() { slides.forEach((s,i) => { s.hidden = i !== index; }); dots.forEach((d,i) => d.setAttribute('aria-pressed', String(i===index))); document.querySelector('#slide-count').textContent = `0${index+1} / 06`; }
    function schedule() { clearInterval(timer); if (!paused && !hover && !focused && !document.hidden && !media.matches) timer = setInterval(() => { index = (index+1)%slides.length; render(); }, 10000); }
    function move(i) { index=(i+slides.length)%slides.length; render(); schedule(); }
    function updatePause() { pause.disabled = media.matches; pause.title = media.matches ? 'Automatic rotation is off because reduced motion is enabled' : ''; pause.textContent = paused ? '▶ Play' : 'Ⅱ Pause'; const status = document.querySelector('#rotation-status'); if (status) status.textContent = media.matches ? 'Automatic rotation off' : paused ? 'Automatic rotation paused' : 'Changes every 10 seconds'; pause.setAttribute('aria-label', paused ? 'Start automatic rotation' : 'Pause automatic rotation'); pause.setAttribute('aria-pressed',String(paused)); }
    dots.forEach((d, i) => {
      d.addEventListener('click', () => move(Number(d.dataset.go)));
      d.addEventListener('keydown', e => {
        const next = e.key === 'ArrowRight' ? (i+1)%dots.length : e.key === 'ArrowLeft' ? (i+dots.length-1)%dots.length : e.key === 'Home' ? 0 : e.key === 'End' ? dots.length-1 : null;
        if (next !== null) { e.preventDefault(); dots[next].focus(); move(next); }
      });
    });
    document.querySelector('#previous-slide').addEventListener('click', () => move(index-1)); document.querySelector('#next-slide').addEventListener('click', () => move(index+1));
    pause.addEventListener('click', () => { paused=!paused; updatePause(); schedule(); });
    deck.addEventListener('mouseenter', () => {hover=true;schedule();});deck.addEventListener('mouseleave', () => {hover=false;schedule();});
    deck.addEventListener('focusin', () => {focused=true;schedule();});deck.addEventListener('focusout', () => {setTimeout(() => {focused=deck.contains(document.activeElement);schedule();},0);});
    document.addEventListener('visibilitychange',schedule);media.addEventListener('change',()=>{paused=media.matches;updatePause();schedule();});updatePause();schedule();
  }
})();
