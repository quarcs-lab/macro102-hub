/* Host-page navigation and featured playback; the shared audio runtime owns controls. */
(() => {
  const page = document.querySelector('.podcasts-page');
  if (!page) return;
  const search = document.querySelector('#resource-search');
  const topic = document.querySelector('#topic-filter');
  function reveal(target) {
    if (target.closest('.resource')?.hidden) {
      search.value = ''; topic.value = '';
      search.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
  page.querySelectorAll('a[href^="#chapter-"]').forEach(link => {
    link.addEventListener('click', () => {
      const target = document.getElementById(link.hash.slice(1));
      if (target) reveal(target);
    });
  });
  const start = page.querySelector('[data-podcast-start]');
  start.hidden = false;
  start.addEventListener('click', () => {
    const player = document.getElementById(start.dataset.podcastStart);
    reveal(player);
    const audio = player.querySelector('audio');
    if (audio.paused) audio.play().catch(() => {
      player.querySelector('.podcast-status').textContent = 'Audio could not play. Please try again, or listen on Spotify.';
    });
    player.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
    player.focus({ preventScroll: true });
  });
  const count = document.querySelector('#result-count');
  function episodeCount() { count.textContent = `${page.querySelectorAll('.episode:not([hidden])').length} of 21 episodes`; }
  search.addEventListener('input', episodeCount); topic.addEventListener('change', episodeCount); episodeCount();
})();
