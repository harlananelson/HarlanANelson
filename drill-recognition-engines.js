/* Swahili drill — pluggable speech-recognition engines.
 *
 * Loaded as a classic <script> AFTER the drill's main inline script, so it can
 * see the drill globals ($, reconocimiento, revisar, escuchando, modoDecir,
 * modoAutomatico, ultimaTranscripcion).
 *
 * It adds a "Recognition" selector and replaces the global `reconocimiento`
 * with a shim that dispatches by chosen engine:
 *   browser  - the built-in Web Speech API (default; Swahili needs Chrome)
 *   whisper  - on-device Whisper via Transformers.js (any browser, incl. iPad)
 *   cloud    - OpenAI gpt-4o-transcribe (bring your own key)
 * For whisper/cloud it records one utterance, detects the end by silence,
 * transcribes it, and feeds the text into the drill's existing revisar() flow.
 */
(function () {
  'use strict';

  if (typeof revisar !== 'function' || typeof $ !== 'function') { return; }  // not the drill page

  var WHISPER_MODEL = 'onnx-community/whisper-base';
  var STORE = 'swahiliDrillRec.v1';
  var state = { engine: 'browser', openaiKey: '', cloudModel: 'gpt-4o-transcribe' };
  try {
    var saved = JSON.parse(localStorage.getItem(STORE) || '{}');
    if (saved.engine) { state.engine = saved.engine; }
    if (typeof saved.openaiKey === 'string') { state.openaiKey = saved.openaiKey; }
    if (saved.cloudModel) { state.cloudModel = saved.cloudModel; }
  } catch (e) { /* ignore */ }
  function save() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (e) {} }

  var browserRecog = (typeof reconocimiento !== 'undefined') ? reconocimiento : null;

  // ── feed a recognized string into the drill (mirrors the Web Speech onend) ──
  function setBox(id, text) { try { var el = $(id); if (el) { el.textContent = text; } } catch (e) {} }
  function showBad(msg) { try { $('feedbackBox').innerHTML = '<span class="bad">' + msg + '</span>'; } catch (e) {} }

  function deliver(text) {
    text = (text || '').trim();
    altActive = false;
    setBox('transcripcionBox', text || 'No speech detected.');
    escuchando = false;
    var b = $('decirBtn');
    if (b) { b.classList.remove('recording'); b.textContent = 'Say answer'; }
    setBox('vozPill', 'Mic: ready');
    var active = modoAutomatico || modoDecir;
    modoAutomatico = false;
    modoDecir = false;
    if (active && text) {
      ultimaTranscripcion = text;
      revisar(text);
    } else if (active) {
      showBad('No voice response was detected.') ;
      try { $('feedbackBox').innerHTML += ' Press again to try.'; } catch (e) {}
    }
  }

  // ── audio capture + single-utterance voice-activity detection ──────────────
  var ac = null, micStream = null, srcNode = null, proc = null, gain = null;
  var capturing = false, altActive = false, srcRate = 48000;
  var vState = 'idle', frames = [], speechMs = 0, silenceMs = 0, totalMs = 0;
  var FRAME = 4096, THRESH = 0.012, SIL_END = 900, MAX_MS = 15000, NOSPEECH_MS = 8000, MIN_SPEECH = 250;

  function startCapture() {
    altActive = true;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showBad('This browser cannot access the microphone.'); deliver(''); return;
    }
    navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    }).then(function (stream) {
      if (!altActive) { stream.getTracks().forEach(function (t) { t.stop(); }); return; }
      micStream = stream;
      var Ctx = window.AudioContext || window.webkitAudioContext;
      ac = new Ctx();
      srcRate = ac.sampleRate || 48000;
      srcNode = ac.createMediaStreamSource(stream);
      proc = ac.createScriptProcessor(FRAME, 1, 1);
      gain = ac.createGain();
      gain.gain.value = 0;
      proc.onaudioprocess = onAudio;
      srcNode.connect(proc);
      proc.connect(gain);
      gain.connect(ac.destination);
      capturing = true;
      vState = 'idle'; frames = []; speechMs = 0; silenceMs = 0; totalMs = 0;
      if (ac.resume) { ac.resume(); }
    }).catch(function (err) {
      showBad('Could not access the microphone: ' + ((err && err.message) || err));
      deliver('');
    });
  }

  function onAudio(e) {
    if (!capturing) { return; }
    var inp = e.inputBuffer.getChannelData(0);
    var f = new Float32Array(inp), n = f.length, s = 0, i;
    for (i = 0; i < n; i++) { s += f[i] * f[i]; }
    var rms = Math.sqrt(s / n), ms = (n / srcRate) * 1000;
    totalMs += ms;
    if (rms >= THRESH) {
      vState = 'speech';
      frames.push(f);
      speechMs += ms;
      silenceMs = 0;
    } else if (vState === 'speech') {
      frames.push(f);
      silenceMs += ms;
      if (silenceMs >= SIL_END) { finishCapture(); return; }
    }
    if (vState === 'speech' && totalMs >= MAX_MS) { finishCapture(); return; }
    if (vState === 'idle' && totalMs >= NOSPEECH_MS) { finishCapture(); return; }
  }

  function teardownCapture() {
    capturing = false;
    try { if (proc) { proc.disconnect(); proc.onaudioprocess = null; } } catch (e) {}
    try { if (srcNode) { srcNode.disconnect(); } } catch (e) {}
    try { if (gain) { gain.disconnect(); } } catch (e) {}
    try { if (micStream) { micStream.getTracks().forEach(function (t) { t.stop(); }); } } catch (e) {}
    try { if (ac) { ac.close(); } } catch (e) {}
    ac = micStream = srcNode = proc = gain = null;
  }

  function abortCapture() { altActive = false; teardownCapture(); frames = []; }

  function finishCapture() {
    var fr = frames, sp = speechMs, rate = srcRate;
    teardownCapture();
    frames = [];
    if (!altActive) { return; }
    if (sp < MIN_SPEECH || !fr.length) { deliver(''); return; }
    setBox('vozPill', 'Mic: transcribing');
    setBox('transcripcionBox', 'Transcribing...');
    var total = 0, k;
    for (k = 0; k < fr.length; k++) { total += fr[k].length; }
    var merged = new Float32Array(total), off = 0;
    for (k = 0; k < fr.length; k++) { merged.set(fr[k], off); off += fr[k].length; }
    resampleTo16k(merged, rate).then(function (a16) {
      if (!altActive) { return; }
      if (state.engine === 'cloud') { cloudTranscribe(a16); }
      else { whisperTranscribe(a16); }
    }).catch(function () {
      showBad('Audio processing failed.');
      deliver('');
    });
  }

  function resampleTo16k(samples, rate) {
    if (rate === 16000) { return Promise.resolve(samples); }
    var OAC = window.OfflineAudioContext || window.webkitOfflineAudioContext;
    var n = Math.max(1, Math.round(samples.length * 16000 / rate));
    var oac = new OAC(1, n, 16000);
    var buf = oac.createBuffer(1, samples.length, rate);
    if (buf.copyToChannel) { buf.copyToChannel(samples, 0); }
    else { buf.getChannelData(0).set(samples); }
    var src = oac.createBufferSource();
    src.buffer = buf;
    src.connect(oac.destination);
    src.start();
    return oac.startRendering().then(function (rendered) {
      return new Float32Array(rendered.getChannelData(0));
    });
  }

  function encodeWav(samples, sampleRate) {
    var n = samples.length;
    var buf = new ArrayBuffer(44 + n * 2);
    var view = new DataView(buf);
    function wstr(off, str) { for (var i = 0; i < str.length; i++) { view.setUint8(off + i, str.charCodeAt(i)); } }
    wstr(0, 'RIFF'); view.setUint32(4, 36 + n * 2, true); wstr(8, 'WAVE');
    wstr(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true);
    view.setUint16(34, 16, true); wstr(36, 'data'); view.setUint32(40, n * 2, true);
    var off = 44;
    for (var i = 0; i < n; i++) {
      var v = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(off, v < 0 ? v * 0x8000 : v * 0x7fff, true);
      off += 2;
    }
    return buf;
  }

  // ── on-device Whisper ──────────────────────────────────────────────────────
  var whisper = null, whisperJob = 0;
  function ensureWhisper() {
    if (whisper) { return whisper; }
    try {
      whisper = new Worker('drill-whisper-worker.js', { type: 'module' });
      whisper.onmessage = onWhisperMsg;
      whisper.onerror = function (err) {
        showBad('Speech engine error: ' + ((err && err.message) || 'failed to start'));
      };
    } catch (e) {
      whisper = null;
    }
    return whisper;
  }
  function whisperTranscribe(a16) {
    var w = ensureWhisper();
    if (!w) { showBad('Could not start the on-device speech engine.'); deliver(''); return; }
    w.curId = ++whisperJob;
    w.postMessage({
      type: 'transcribe', id: w.curId, audio: a16,
      model: WHISPER_MODEL, device: 'wasm', language: 'swahili'
    }, [a16.buffer]);
  }
  function onWhisperMsg(e) {
    var m = e.data || {};
    if (m.type === 'status') {
      if (m.state === 'loading') { setBox('transcripcionBox', 'Loading speech model (first use only)...'); }
      else if (m.state === 'error') { showBad('Speech model failed to load: ' + m.error); }
      return;
    }
    if (m.type === 'progress') {
      var d = m.data;
      if (d && d.status === 'progress' && d.file && d.total) {
        var pct = Math.floor((d.loaded || 0) / d.total * 100);
        setBox('transcripcionBox', 'Downloading speech model... ' + pct + '%');
      }
      return;
    }
    if (m.type === 'transcript') {
      if (!altActive || m.id !== whisper.curId) { return; }
      if (m.ok) { deliver(m.text); }
      else { showBad('Transcription failed: ' + m.error); deliver(''); }
    }
  }

  // ── cloud transcription (OpenAI gpt-4o-transcribe) ─────────────────────────
  function cloudTranscribe(a16) {
    var key = (state.openaiKey || '').trim();
    if (!key) {
      showBad('Cloud transcription needs an OpenAI API key — enter it in the Recognition settings.');
      deliver(''); return;
    }
    var form = new FormData();
    form.append('file', new Blob([encodeWav(a16, 16000)], { type: 'audio/wav' }), 'answer.wav');
    form.append('model', (state.cloudModel || 'gpt-4o-transcribe').trim());
    form.append('language', 'sw');
    fetch('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST', headers: { 'authorization': 'Bearer ' + key }, body: form
    }).then(function (res) {
      return res.text().then(function (body) {
        if (!res.ok) {
          var d = body;
          try { var j = JSON.parse(body); if (j && j.error) { d = j.error.message || j.error.type || body; } } catch (e) {}
          throw new Error(res.status + (d ? ' - ' + String(d).slice(0, 200) : ''));
        }
        var data;
        try { data = JSON.parse(body); } catch (e) { throw new Error('Unreadable response from transcription API'); }
        return (data && typeof data.text === 'string') ? data.text : '';
      });
    }).then(function (t) {
      if (altActive) { deliver(t); }
    }).catch(function (err) {
      showBad('Cloud transcription failed: ' + ((err && err.message) || err));
      deliver('');
    });
  }

  // ── the recognizer shim (drop-in for the Web Speech object) ────────────────
  var shim = {
    lang: 'sw-KE', continuous: false, interimResults: true, maxAlternatives: 1,
    onresult: null, onend: null, onerror: null, onstart: null,
    start: function () {
      if (state.engine === 'browser') {
        if (browserRecog) { browserRecog.start(); }
        else { showBad('Browser speech recognition is not available. Pick the Whisper engine.'); deliver(''); }
      } else {
        startCapture();
      }
    },
    stop: function () {
      if (state.engine === 'browser') { if (browserRecog) { try { browserRecog.stop(); } catch (e) {} } }
      else { abortCapture(); }
    },
    abort: function () {
      if (state.engine === 'browser') { if (browserRecog) { try { browserRecog.abort(); } catch (e) {} } }
      else { abortCapture(); }
    }
  };
  reconocimiento = shim;

  // ── the "Recognition" selector UI ──────────────────────────────────────────
  function buildUI() {
    var anchor = $('decirBtn');
    if (!anchor || !anchor.parentNode) { return; }
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:.6rem 0;font-size:.92rem;';

    var lab = document.createElement('span');
    lab.textContent = 'Recognition:';
    lab.style.fontWeight = '600';

    var sel = document.createElement('select');
    sel.style.cssText = 'padding:.35rem .5rem;border-radius:.5rem;';
    [['browser', 'Browser  (use Chrome for Swahili)'],
     ['whisper', 'On-device Whisper  (any browser)'],
     ['cloud', 'Cloud  (OpenAI gpt-4o-transcribe)']].forEach(function (o) {
      var op = document.createElement('option');
      op.value = o[0]; op.textContent = o[1];
      sel.appendChild(op);
    });
    sel.value = state.engine;

    var key = document.createElement('input');
    key.type = 'password';
    key.placeholder = 'OpenAI API key (sk-...)';
    key.autocomplete = 'off';
    key.value = state.openaiKey;
    key.style.cssText = 'flex:1;min-width:200px;padding:.35rem .5rem;border-radius:.5rem;';

    function syncKey() { key.style.display = (state.engine === 'cloud') ? '' : 'none'; }

    sel.addEventListener('change', function () {
      state.engine = sel.value;
      save();
      syncKey();
      if (state.engine === 'whisper') {
        var w = ensureWhisper();
        if (w) { w.postMessage({ type: 'load', model: WHISPER_MODEL, device: 'wasm' }); }
      }
    });
    key.addEventListener('input', function () {
      state.openaiKey = key.value.trim();
      save();
    });
    syncKey();

    row.appendChild(lab);
    row.appendChild(sel);
    row.appendChild(key);
    anchor.parentNode.insertBefore(row, anchor);
  }

  buildUI();
})();
