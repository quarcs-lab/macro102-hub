/* Standard player: no service, framework, or host-page globals required. */
(() => {
  if (window.StandardAudioPlayer) { window.StandardAudioPlayer.init(); return; }
  const instances = new Map();
  const playersIn = root => root.matches?.('[data-podcast]') ? [root] : [...root.querySelectorAll('[data-podcast]')];
  const formatTime = seconds => {
    const value = Math.max(0, Math.floor(seconds || 0));
    return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`;
  };
  const pauseOthers = audio => {
    for (const player of instances.keys()) {
      const other = player.querySelector('audio');
      if (other !== audio) other.pause();
    }
  };
  async function startPlayback(audio, status) {
    pauseOthers(audio);
    try {
      await audio.play();
      if (status.textContent.startsWith('Audio could not play.')) status.textContent = '';
    } catch (error) {
      if (error.name !== 'AbortError') status.textContent = 'Audio could not play. Please try again. You can also open the transcript.';
    }
  }
  async function mount(player) {
    if (instances.has(player)) return;
    const controller = new AbortController();
    instances.set(player, controller);
    const on = (element, event, handler, options = {}) => element.addEventListener(event, handler, { ...options, signal: controller.signal });
    const audio = player.querySelector('audio');
    const status = player.querySelector('.podcast-status');
    const launch = player.closest('.podcast-widget').querySelector('[data-podcast-toggle]');
    on(launch, 'click', () => {
      const opening = launch.getAttribute('aria-expanded') !== 'true';
      launch.setAttribute('aria-expanded', String(opening));
      player.hidden = !opening;
      if (opening) startPlayback(audio, status);
      else audio.pause();
    });
    on(player.querySelector('.podcast-close'), 'click', () => {
      launch.setAttribute('aria-expanded', 'false');
      player.hidden = true;
      audio.pause();
      launch.focus();
    });
    on(audio, 'play', () => pauseOthers(audio));
    on(audio, 'error', () => { status.textContent = 'Audio is unavailable. You can still open the transcript or listen on Spotify.'; });
    try {
      const response = await fetch(player.dataset.podcast, { signal: controller.signal });
      if (!response.ok) throw new Error('Transcript unavailable');
      const episode = await response.json();
      if (!(episode.duration > 0) || !episode.sections?.length || !episode.segments?.length) throw new Error('Invalid transcript');
      const play = player.querySelector('.podcast-play');
      const seek = player.querySelector('[data-seek]');
      const transcript = player.querySelector('.podcast-passages');
      const transcriptPanel = player.querySelector('.podcast-transcript');
      const transcriptToggle = player.querySelector('.podcast-transcript-toggle');
      const follow = player.querySelector('[data-follow]');
      let currentPassage = -1, currentSection = -1, pendingSeek = null, following = follow.checked;
      player.querySelector('[data-episode-minutes]').textContent = Math.round(episode.duration / 60);
      const sectionName = (section, index) => index > 0 && index < episode.sections.length - 1 ? `Part ${index} · ${section.title}` : section.title;
      const chapterButtons = episode.sections.map((section, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        const time = document.createElement('time');
        time.textContent = formatTime(section.start);
        const title = document.createElement('span');
        title.textContent = sectionName(section, index);
        button.append(time, title);
        button.setAttribute('aria-label', `${section.title}, ${formatTime(section.start)}`);
        on(button, 'click', () => jump(section.start));
        player.querySelector('.podcast-chapters').append(button);
        if (index > 0) {
          const cut = document.createElement('span');
          cut.style.left = `${100 * section.start / episode.duration}%`;
          player.querySelector('.podcast-cuts').append(cut);
        }
        return button;
      });
      const passageButtons = episode.segments.map((segment, index) => {
        const section = episode.sections.find(item => item.segment === index);
        if (section) {
          const heading = document.createElement('h6');
          heading.textContent = section.title;
          transcript.append(heading);
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.dataset.speaker = segment.speaker;
        const speaker = document.createElement('span');
        speaker.className = 'podcast-speaker';
        const time = document.createElement('time');
        time.textContent = formatTime(segment.start);
        speaker.append(segment.speaker, time);
        const text = document.createElement('span');
        text.textContent = segment.text;
        button.append(speaker, text);
        on(button, 'click', () => jump(segment.start));
        transcript.append(button);
        return button;
      });
      function jump(time) {
        const total = Number.isFinite(audio.duration) ? audio.duration : episode.duration;
        const target = Math.max(0, Math.min(total, time));
        if (audio.readyState === 0) { pendingSeek = target; audio.load(); }
        else audio.currentTime = target;
        update(target);
      }
      function scrollToPassage() {
        if (!following || transcriptPanel.hidden || currentPassage < 0) return;
        const container = transcript.getBoundingClientRect();
        const rect = passageButtons[currentPassage].getBoundingClientRect();
        transcript.scrollTop += rect.top - container.top - transcript.clientHeight / 3;
      }
      function update(time = audio.currentTime) {
        const total = Number.isFinite(audio.duration) ? audio.duration : episode.duration;
        seek.max = total;
        seek.value = time;
        seek.setAttribute('aria-valuetext', `${formatTime(time)} of ${formatTime(total)}`);
        player.querySelector('[data-elapsed]').textContent = formatTime(time);
        player.querySelector('[data-duration]').textContent = formatTime(total);
        player.querySelector('[data-progress]').style.width = `${100 * time / total}%`;
        const section = Math.max(0, episode.sections.findLastIndex(item => item.start <= time));
        if (section !== currentSection) {
          chapterButtons[currentSection]?.removeAttribute('aria-current');
          chapterButtons[section].setAttribute('aria-current', 'true');
          player.querySelector('.podcast-now').textContent = `Now: ${sectionName(episode.sections[section], section)}`;
          currentSection = section;
        }
        const index = episode.segments.findLastIndex(item => item.start <= time);
        const active = index >= 0 && time < episode.segments[index].end ? index : -1;
        if (active !== currentPassage) {
          passageButtons[currentPassage]?.removeAttribute('aria-current');
          passageButtons[active]?.setAttribute('aria-current', 'true');
          currentPassage = active;
          scrollToPassage();
        }
      }
      const stopFollowing = () => { following = false; follow.checked = false; };
      on(transcript, 'wheel', stopFollowing, { passive: true });
      on(transcript, 'touchstart', stopFollowing, { passive: true });
      on(transcript, 'keydown', event => {
        if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End'].includes(event.key)) stopFollowing();
      });
      on(follow, 'change', () => { following = follow.checked; scrollToPassage(); });
      on(transcriptToggle, 'click', () => {
        transcriptPanel.hidden = !transcriptPanel.hidden;
        transcriptToggle.setAttribute('aria-expanded', String(!transcriptPanel.hidden));
        transcriptToggle.querySelector('span').textContent = transcriptPanel.hidden ? 'Read along' : 'Hide transcript';
        scrollToPassage();
      });
      on(play, 'click', () => { if (audio.paused) startPlayback(audio, status); else audio.pause(); });
      function updatePlay() {
        const playing = !audio.paused;
        play.setAttribute('aria-label', playing ? 'Pause podcast' : 'Play podcast');
        play.setAttribute('aria-pressed', String(playing));
        play.querySelector('[data-play-icon]').toggleAttribute('hidden', playing);
        play.querySelector('[data-pause-icon]').toggleAttribute('hidden', !playing);
      }
      for (const event of ['play', 'pause', 'playing', 'ended']) on(audio, event, updatePlay);
      on(audio, 'timeupdate', () => update());
      on(audio, 'progress', () => {
        if (audio.buffered.length) player.querySelector('[data-buffer]').style.width = `${100 * audio.buffered.end(audio.buffered.length - 1) / episode.duration}%`;
      });
      on(audio, 'loadedmetadata', () => {
        if (pendingSeek !== null) { audio.currentTime = pendingSeek; pendingSeek = null; }
        update();
      });
      on(seek, 'input', () => jump(Number(seek.value)));
      player.querySelectorAll('[data-skip]').forEach(button => on(button, 'click', () => jump((pendingSeek ?? audio.currentTime) + Number(button.dataset.skip))));
      const speeds = [1, 1.25, 1.5, 1.75, 2, .75];
      on(player.querySelector('[data-speed]'), 'click', event => {
        const speed = speeds[(speeds.indexOf(audio.playbackRate) + 1) % speeds.length];
        audio.playbackRate = speed;
        event.currentTarget.textContent = `${speed}×`;
        event.currentTarget.setAttribute('aria-label', `Playback speed: ${speed}×. Click to change`);
      });
      update();
      updatePlay();
      player.querySelectorAll('[data-enhanced]').forEach(element => { element.hidden = false; });
      player.classList.add('enhanced');
      if (!audio.error && !status.textContent.startsWith('Audio could not play.')) status.textContent = '';
    } catch (error) {
      if (controller.signal.aborted) return;
      status.textContent = 'Interactive transcript unavailable. You can still listen, open the transcript, or listen on Spotify using the links below.';
    }
  }
  function destroy(root = document) {
    for (const player of playersIn(root)) {
      const controller = instances.get(player);
      if (!controller) continue;
      controller.abort();
      player.querySelector('audio').pause();
      instances.delete(player);
      player.classList.remove('enhanced');
      player.hidden = true;
      const launch = player.closest('.podcast-widget').querySelector('[data-podcast-toggle]');
      launch.setAttribute('aria-expanded', 'false');
      player.querySelectorAll('[data-enhanced]').forEach(element => { element.hidden = true; });
      player.querySelectorAll('.podcast-chapters, .podcast-passages, .podcast-cuts').forEach(element => element.replaceChildren());
      player.querySelector('.podcast-transcript').hidden = true;
      const toggle = player.querySelector('.podcast-transcript-toggle');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.querySelector('span').textContent = 'Read along';
    }
  }
  window.StandardAudioPlayer = { init: (root = document) => Promise.all(playersIn(root).map(mount)), destroy };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => window.StandardAudioPlayer.init(), { once: true });
  else window.StandardAudioPlayer.init();
})();
