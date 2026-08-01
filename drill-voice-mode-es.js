/* Spanish drill — 🎧 Modo voz (voice-only, hands-free operation).
 *
 * Loaded as a classic <script> AFTER the drill's main inline script and the
 * recognition-engine shim, so it can see the drill globals (hablar, revisar,
 * elegir, decirRespuesta, textoEjercicio, textoPista, registro, actual, $).
 *
 * The mode is a small state machine over functions the drill already has:
 *   speak prompt (verb + context + hint) -> open mic -> the engines score the
 *   answer through revisar() (which already SPEAKS the result) -> on correct,
 *   advance and loop; on incorrect, one spoken retry, then advance.
 *
 * Voice commands (recognized instead of scoring when the utterance is short):
 *   "siguiente"           skip to the next exercise
 *   "repite" / "repetir"  hear the prompt again
 *   "pista"               hear the hint again
 *   "para" / "detente" / "alto"   stop voice mode
 *
 * A Screen Wake Lock keeps the phone awake while the mode runs (browsers
 * suspend JS when the screen locks, so true screen-off use isn't possible in
 * a web app).
 */
(function () {
  'use strict';

  if (typeof revisar !== 'function' || typeof elegir !== 'function' ||
      typeof hablar !== 'function' || typeof $ !== 'function') { return; }

  var vmActive = false;
  var vmRetried = false;      // one retry per exercise on an incorrect answer
  var vmWatchdog = null;      // recovers the loop if the mic delivers nothing
  var vmListenTries = 0;
  var wakeLock = null;

  // ── wake lock ──────────────────────────────────────────────────────────────
  function acquireLock() {
    if (!('wakeLock' in navigator)) { return; }
    navigator.wakeLock.request('screen').then(function (l) {
      wakeLock = l;
    }).catch(function () { /* not fatal — mode still works */ });
  }
  function releaseLock() {
    if (wakeLock) { try { wakeLock.release(); } catch (e) {} wakeLock = null; }
  }
  document.addEventListener('visibilitychange', function () {
    if (vmActive && document.visibilityState === 'visible') { acquireLock(); }
  });

  // ── the state machine ──────────────────────────────────────────────────────
  function clearWatchdog() {
    if (vmWatchdog) { clearTimeout(vmWatchdog); vmWatchdog = null; }
  }

  function speakThen(texto, next) {
    // hablar() cancels any queued audio, so sequencing goes through the
    // completion callback; a safety timer keeps the loop alive if the
    // callback is never fired (e.g. a TTS request failed).
    var done = false;
    function once() { if (!done) { done = true; clearWatchdog(); next(); } }
    clearWatchdog();
    vmWatchdog = setTimeout(once, 25000);
    hablar(texto, once);
  }

  function promptExercise() {
    if (!vmActive) { return; }
    vmRetried = false;
    speakThen(textoEjercicio(), listen);
  }

  function listen() {
    if (!vmActive) { return; }
    clearWatchdog();
    // If the engines deliver silence/no speech, deliver() never reaches
    // revisar(); this watchdog re-opens the mic (twice), then re-prompts.
    vmWatchdog = setTimeout(function () {
      if (!vmActive) { return; }
      vmListenTries += 1;
      if (vmListenTries <= 2) { listen(); }
      else { vmListenTries = 0; promptExercise(); }
    }, 30000);
    decirRespuesta();
  }

  function advance() {
    if (!vmActive) { return; }
    elegir();
    promptExercise();
  }

  function afterFeedbackSpoken() {
    if (!vmActive) { return; }
    var last = (typeof registro !== 'undefined' && registro.length)
      ? registro[registro.length - 1] : null;
    var correct = !!(last && last.correcto);
    if (correct || vmRetried) {
      setTimeout(advance, 600);
    } else {
      vmRetried = true;
      setTimeout(listen, 600);   // the drill already said "Revisa esta idea…"
    }
  }

  // ── voice commands ─────────────────────────────────────────────────────────
  function norm(s) {
    return (s || '').toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-zñ ]/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function command(text) {
    var t = norm(text);
    if (!t || t.split(' ').length > 2) { return false; }  // real answers are longer
    if (t === 'siguiente') { speakThen('Siguiente.', advance); return true; }
    if (t === 'repite' || t === 'repetir') { promptExercise(); return true; }
    if (t === 'pista') { speakThen(textoPista(), listen); return true; }
    if (t === 'para' || t === 'detente' || t === 'alto') { stop(true); return true; }
    return false;
  }

  // ── hooks into the drill ───────────────────────────────────────────────────
  // revisar() speaks its verdict with no completion callback; while voice
  // mode is active this wrapper lends the NEXT callback-less hablar() call
  // (i.e. that verdict) a callback that resumes the loop.
  var vmHook = null;
  var _hablar = hablar;
  hablar = function (texto, alTerminar, opciones) {
    if (vmActive && vmHook && !alTerminar) {
      alTerminar = vmHook; vmHook = null;
    }
    return _hablar(texto, alTerminar, opciones || {});
  };

  var _revisar = revisar;
  revisar = function (usuario) {
    if (vmActive) {
      clearWatchdog();
      vmListenTries = 0;
      if (command(usuario)) { return; }
      vmHook = function () { setTimeout(afterFeedbackSpoken, 300); };
      var out = _revisar(usuario);
      if (vmHook) {           // feedback path didn't speak — keep the loop alive
        vmHook = null;
        setTimeout(afterFeedbackSpoken, 1500);
      }
      return out;
    }
    return _revisar(usuario);
  };

  // ── UI ─────────────────────────────────────────────────────────────────────
  var btn = document.createElement('button');
  btn.type = 'button';
  btn.id = 'voiceModeBtn';
  btn.className = 'btn secondary-strong next';

  function paint() {
    btn.textContent = vmActive ? '🎧 Modo voz: activo' : '🎧 Modo voz';
    btn.title = vmActive
      ? 'Termina el modo de solo voz (también puedes decir «para»)'
      : 'Modo de solo voz: la app lee el ejercicio y abre el micrófono sola. Di «siguiente», «repite», «pista» o «para».';
  }

  function start() {
    vmActive = true;
    vmListenTries = 0;
    paint();
    acquireLock();
    // Start inside the click gesture chain: speak a brief intro, then loop.
    speakThen('Modo voz activado. Di para, cuando quieras terminar.', promptExercise);
  }

  function stop(spoken) {
    vmActive = false;
    vmHook = null;
    clearWatchdog();
    releaseLock();
    paint();
    if (spoken) { _hablar('Modo voz terminado.'); }
    else { cancelarAudio(); }
  }

  btn.addEventListener('click', function () {
    if (vmActive) { stop(false); } else { start(); }
  });

  paint();
  var row = document.querySelector('.actions-primary');
  if (row) { row.appendChild(btn); }
})();
