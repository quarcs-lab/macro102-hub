(() => {
  const root = document.documentElement;
  const button = document.getElementById('transcript-theme');
  try {
    root.classList.toggle('light', localStorage.getItem('theme') === 'light');
  } catch { /* Reading remains available when storage is blocked. */ }
  const update = () => {
    button.setAttribute('aria-pressed', String(root.classList.contains('light')));
  };
  button.hidden = false;
  update();
  button.addEventListener('click', () => {
    root.classList.toggle('light');
    try {
      localStorage.setItem('theme', root.classList.contains('light') ? 'light' : 'dark');
    } catch { /* The theme can still change without persistent storage. */ }
    update();
  });
})();
