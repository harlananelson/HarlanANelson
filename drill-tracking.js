/* Drill session tracking — OPT-IN ONLY.
 *
 * Loaded as a classic <script> by every speech drill, after the drill's main
 * inline script. Adds a "📊 Tracking: off/on" pill button. While OFF (the
 * default) nothing is collected at all. While ON, it records interaction
 * events (button presses, the current exercise, detected answers, feedback
 * text, recognition engine) — never audio — and batches them to
 * /.netlify/functions/track, which stores them in Netlify Blobs for later
 * analysis. The preference persists per browser.
 *
 * Deliberately DOM-based (click listeners + MutationObservers on well-known
 * element ids shared by all four drills) so it needs no hooks inside each
 * drill's own script.
 */
(function () {
  'use strict';

  if (!document.getElementById('decirBtn')) { return; }  // not a drill page

  var PREF = 'drillTracking.v1';
  var ENDPOINT = '/.netlify/functions/track';
  var FLUSH_MS = 12000;

  var drill = (location.pathname.split('/').pop() || 'drill')
    .replace(/\.html?$/i, '').replace(/[^\w-]/g, '').slice(0, 32) || 'drill';

  var enabled = false;
  try { enabled = localStorage.getItem(PREF) === 'on'; } catch (e) {}

  var session = null, t0 = 0, seq = 0, queue = [], flushTimer = null;

  function newSession() {
    session = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14) +
      '-' + Math.random().toString(36).slice(2, 8);
    t0 = Date.now();
    seq = 0;
  }

  function engineState() {
    // Each drill's recognition module stores prefs as <lang>DrillRec.v1.
    try {
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (/DrillRec\.v\d+$/.test(k)) {
          var v = JSON.parse(localStorage.getItem(k) || '{}');
          return v.engine || '';
        }
      }
    } catch (e) {}
    return '';
  }

  function txt(id) {
    var el = document.getElementById(id);
    return el ? (el.textContent || '').trim().slice(0, 300) : '';
  }

  function exerciseSnapshot() {
    return {
      verb: txt('verboLine'),
      tense: txt('tenseLabel'),
      hint: txt('pistaLine'),
      context: txt('contextoLine'),
      state: txt('estadoPill'),
      correct: txt('correctCount'),
      review: txt('wrongCount')
    };
  }

  function record(type, data) {
    if (!enabled) { return; }
    var ev = { seq: seq++, t: Date.now() - t0, type: type };
    if (data) { ev.data = data; }
    queue.push(ev);
    if (!flushTimer) { flushTimer = setTimeout(flush, FLUSH_MS); }
  }

  function flush(useBeacon) {
    if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
    if (!queue.length || !session) { return; }
    var batch = queue.splice(0, 500);
    var payload = JSON.stringify({ session: session, drill: drill, events: batch });
    if (useBeacon && navigator.sendBeacon) {
      navigator.sendBeacon(ENDPOINT, new Blob([payload], { type: 'application/json' }));
      return;
    }
    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      keepalive: true
    }).catch(function () {
      // Put the batch back so a transient failure doesn't lose events.
      queue = batch.concat(queue).slice(0, 2000);
    });
    if (queue.length && !flushTimer) { flushTimer = setTimeout(flush, FLUSH_MS); }
  }

  // ── event capture ──────────────────────────────────────────────────────────
  var BTN_IDS = ['decirBtn', 'nextBtn', 'contextoBtn', 'verboBtn', 'pistaBtn',
    'fraseBtn', 'instruccionesBtn', 'repetirBtn', 'slowToggle',
    'summaryBtn', 'exportBtn'];

  document.addEventListener('click', function (e) {
    if (!enabled) { return; }
    var b = e.target && e.target.closest ? e.target.closest('button') : null;
    if (!b || BTN_IDS.indexOf(b.id) === -1) { return; }
    if (b.id === 'decirBtn' || b.id === 'nextBtn') {
      record('press', { btn: b.id, engine: engineState(), ex: exerciseSnapshot() });
    } else {
      record('press', { btn: b.id });
    }
  }, true);

  function observe(id, type) {
    var el = document.getElementById(id);
    if (!el || !window.MutationObserver) { return; }
    var last = '';
    new MutationObserver(function () {
      if (!enabled) { return; }
      var v = (el.textContent || '').trim();
      if (v && v !== last) {
        last = v;
        record(type, { text: v.slice(0, 300), ex: exerciseSnapshot() });
      }
    }).observe(el, { childList: true, characterData: true, subtree: true });
  }
  observe('transcripcionBox', 'answer');    // what the recognizer heard
  observe('feedbackBox', 'feedback');       // how it was scored

  window.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') { flush(true); }
  });
  window.addEventListener('pagehide', function () { flush(true); });

  // ── the toggle button ──────────────────────────────────────────────────────
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.id = 'trackingToggle';
  btn.className = 'pill';
  btn.style.cursor = 'pointer';
  btn.style.border = 'none';
  btn.style.font = 'inherit';

  function paint() {
    btn.textContent = '📊 Tracking: ' + (enabled ? 'on' : 'off');
    btn.style.opacity = enabled ? '1' : '0.6';
    btn.setAttribute('aria-pressed', enabled ? 'true' : 'false');
    btn.title = enabled
      ? 'Session events are being recorded for analysis. Tap to stop.'
      : 'Off — nothing is collected. Tap to record this session for analysis.';
  }

  btn.addEventListener('click', function () {
    enabled = !enabled;
    try { localStorage.setItem(PREF, enabled ? 'on' : 'off'); } catch (e) {}
    if (enabled) {
      newSession();
      record('session-start', {
        drill: drill, engine: engineState(),
        page: location.pathname, lang: navigator.language,
        screen: screen.width + 'x' + screen.height
      });
    } else {
      record('session-stop');
      flush();
      session = null;
    }
    paint();
  });

  paint();
  var row = document.querySelector('.pillrow');
  if (row) { row.appendChild(btn); }
  else if (document.getElementById('decirBtn').parentNode) {
    document.getElementById('decirBtn').parentNode.appendChild(btn);
  }

  // If the preference was already ON from a previous visit, start a session.
  if (enabled) {
    newSession();
    record('session-start', {
      drill: drill, engine: engineState(), resumedPref: true,
      page: location.pathname, lang: navigator.language,
      screen: screen.width + 'x' + screen.height
    });
  }
})();
