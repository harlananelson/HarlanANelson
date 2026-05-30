/* Spanish drill — pluggable speech-recognition engines.
 *
 * Spanish-localized sibling of drill-recognition-engines.js (the Swahili one).
 * Loaded as a classic <script> AFTER the drill's main inline script, so it can
 * see the drill globals ($, reconocimiento, revisar, escuchando, modoDecir,
 * modoAutomatico, ultimaTranscripcion).
 *
 * It adds a "Reconocimiento" selector and replaces the global `reconocimiento`
 * with a shim that dispatches by chosen engine:
 *   browser     - the built-in Web Speech API (default; needs Chrome/Edge)
 *   whisper     - on-device Whisper via Transformers.js (any browser, incl. iPad)
 *   elevenlabs  - ElevenLabs Scribe STT, reusing the key you already use for TTS
 *   cloud       - OpenAI gpt-4o-transcribe (bring your own key)
 * For the non-browser engines it records one utterance, detects the end by
 * silence, transcribes it, and feeds the text into the existing revisar() flow.
 *
 * The on-device worker (drill-whisper-worker.js) is shared with the Swahili
 * drill and is language-parameterized, so we just pass language:'spanish'.
 */
(function () {
  'use strict';

  if (typeof revisar !== 'function' || typeof $ !== 'function') { return; }  // not the drill page

  var WHISPER_MODEL = 'onnx-community/whisper-base';
  var STORE = 'spanishDrillRec.v1';
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
    setBox('transcripcionBox', text || 'No se detectó voz.');
    escuchando = false;
    var b = $('decirBtn');
    if (b) { b.classList.remove('recording'); b.textContent = 'Decir respuesta'; }
    setBox('vozPill', 'Micrófono: listo');
    var active = modoAutomatico || modoDecir;
    modoAutomatico = false;
    modoDecir = false;
    if (active && text) {
      ultimaTranscripcion = text;
      revisar(text);
    } else if (active) {
      showBad('No se detectó una respuesta por voz.');
      try { $('feedbackBox').innerHTML += ' Pulsa de nuevo para intentarlo.'; } catch (e) {}
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
      showBad('Este navegador no puede acceder al micrófono.'); deliver(''); return;
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
      showBad('No se pudo acceder al micrófono: ' + ((err && err.message) || err));
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
    setBox('vozPill', 'Micrófono: transcribiendo');
    setBox('transcripcionBox', 'Transcribiendo...');
    var total = 0, k;
    for (k = 0; k < fr.length; k++) { total += fr[k].length; }
    var merged = new Float32Array(total), off = 0;
    for (k = 0; k < fr.length; k++) { merged.set(fr[k], off); off += fr[k].length; }
    resampleTo16k(merged, rate).then(function (a16) {
      if (!altActive) { return; }
      if (state.engine === 'cloud') { cloudTranscribe(a16); }
      else if (state.engine === 'elevenlabs') { elevenlabsTranscribe(a16); }
      else { whisperTranscribe(a16); }
    }).catch(function () {
      showBad('Falló el procesamiento del audio.');
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

  function bufToBase64(buf) {
    var bytes = new Uint8Array(buf), bin = '', chunk = 0x8000;
    for (var i = 0; i < bytes.length; i += chunk) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(bin);
  }

  // ── on-device Whisper ──────────────────────────────────────────────────────
  var whisper = null, whisperJob = 0;
  function ensureWhisper() {
    if (whisper) { return whisper; }
    try {
      whisper = new Worker('drill-whisper-worker.js', { type: 'module' });
      whisper.onmessage = onWhisperMsg;
      whisper.onerror = function (err) {
        showBad('Error del motor de voz: ' + ((err && err.message) || 'no se pudo iniciar'));
      };
    } catch (e) {
      whisper = null;
    }
    return whisper;
  }
  function whisperTranscribe(a16) {
    var w = ensureWhisper();
    if (!w) { showBad('No se pudo iniciar el motor de voz en el dispositivo.'); deliver(''); return; }
    w.curId = ++whisperJob;
    w.postMessage({
      type: 'transcribe', id: w.curId, audio: a16,
      model: WHISPER_MODEL, device: 'wasm', language: 'spanish'
    }, [a16.buffer]);
  }
  function onWhisperMsg(e) {
    var m = e.data || {};
    if (m.type === 'status') {
      if (m.state === 'loading') { setBox('transcripcionBox', 'Cargando modelo de voz (solo la primera vez)...'); }
      else if (m.state === 'error') { showBad('No se pudo cargar el modelo de voz: ' + m.error); }
      return;
    }
    if (m.type === 'progress') {
      var d = m.data;
      if (d && d.status === 'progress' && d.file && d.total) {
        var pct = Math.floor((d.loaded || 0) / d.total * 100);
        setBox('transcripcionBox', 'Descargando modelo de voz... ' + pct + '%');
      }
      return;
    }
    if (m.type === 'transcript') {
      if (!altActive || m.id !== whisper.curId) { return; }
      if (m.ok) { deliver(m.text); }
      else { showBad('Falló la transcripción: ' + m.error); deliver(''); }
    }
  }

  // ── ElevenLabs Scribe STT ───────────────────────────────────────────────────
  // Reuses the ElevenLabs key the drill already stores for TTS (el_api_key in
  // the "Voz" settings). With no user key it falls back to the server-side proxy
  // (/.netlify/functions/stt), mirroring how the TTS path works.
  function elevenlabsTranscribe(a16) {
    var wav = encodeWav(a16, 16000);
    var userKey = '';
    try { userKey = (localStorage.getItem('el_api_key') || '').trim(); } catch (e) {}

    function handleText(t) { if (altActive) { deliver(typeof t === 'string' ? t : ''); } }
    function handleErr(err) {
      showBad('Falló la transcripción de ElevenLabs: ' + ((err && err.message) || err));
      deliver('');
    }

    if (userKey) {
      var form = new FormData();
      form.append('model_id', 'scribe_v1');
      form.append('language_code', 'es');
      form.append('file', new Blob([wav], { type: 'audio/wav' }), 'answer.wav');
      fetch('https://api.elevenlabs.io/v1/speech-to-text', {
        method: 'POST', headers: { 'xi-api-key': userKey }, body: form
      }).then(parseElevenLabs).then(handleText).catch(handleErr);
    } else {
      fetch('/.netlify/functions/stt', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ audio_base64: bufToBase64(wav), language: 'es' })
      }).then(parseElevenLabs).then(handleText).catch(function (err) {
        showBad('La transcripción de ElevenLabs necesita tu clave (botón “Voz”) o el proxy del servidor: ' + ((err && err.message) || err));
        deliver('');
      });
    }
  }
  function parseElevenLabs(res) {
    return res.text().then(function (body) {
      if (!res.ok) {
        var d = body;
        try { var j = JSON.parse(body); if (j && j.detail) { d = (j.detail.message || JSON.stringify(j.detail)); } } catch (e) {}
        throw new Error(res.status + (d ? ' - ' + String(d).slice(0, 200) : ''));
      }
      var data;
      try { data = JSON.parse(body); } catch (e) { throw new Error('Respuesta ilegible de la API de transcripción'); }
      return (data && typeof data.text === 'string') ? data.text : '';
    });
  }

  // ── cloud transcription (OpenAI gpt-4o-transcribe) ─────────────────────────
  function cloudTranscribe(a16) {
    var key = (state.openaiKey || '').trim();
    if (!key) {
      showBad('La transcripción en la nube necesita una clave de OpenAI — introdúcela en los ajustes de Reconocimiento.');
      deliver(''); return;
    }
    var form = new FormData();
    form.append('file', new Blob([encodeWav(a16, 16000)], { type: 'audio/wav' }), 'answer.wav');
    form.append('model', (state.cloudModel || 'gpt-4o-transcribe').trim());
    form.append('language', 'es');
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
        try { data = JSON.parse(body); } catch (e) { throw new Error('Respuesta ilegible de la API de transcripción'); }
        return (data && typeof data.text === 'string') ? data.text : '';
      });
    }).then(function (t) {
      if (altActive) { deliver(t); }
    }).catch(function (err) {
      showBad('Falló la transcripción en la nube: ' + ((err && err.message) || err));
      deliver('');
    });
  }

  // ── the recognizer shim (drop-in for the Web Speech object) ────────────────
  var shim = {
    lang: 'es-ES', continuous: false, interimResults: true, maxAlternatives: 1,
    onresult: null, onend: null, onerror: null, onstart: null,
    start: function () {
      if (state.engine === 'browser') {
        if (browserRecog) { browserRecog.start(); }
        else { showBad('El reconocimiento del navegador no está disponible. Elige el motor Whisper.'); deliver(''); }
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

  // ── the "Reconocimiento" selector UI ────────────────────────────────────────
  function buildUI() {
    var anchor = $('decirBtn');
    if (!anchor || !anchor.parentNode) { return; }
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:.6rem 0;font-size:.92rem;';

    var lab = document.createElement('span');
    lab.textContent = 'Reconocimiento:';
    lab.style.fontWeight = '600';

    var sel = document.createElement('select');
    sel.style.cssText = 'padding:.35rem .5rem;border-radius:.5rem;';
    [['browser', 'Navegador  (usa Chrome/Edge)'],
     ['whisper', 'Whisper en el dispositivo  (cualquier navegador)'],
     ['elevenlabs', 'ElevenLabs Scribe  (usa tu clave de Voz)'],
     ['cloud', 'Nube  (OpenAI gpt-4o-transcribe)']].forEach(function (o) {
      var op = document.createElement('option');
      op.value = o[0]; op.textContent = o[1];
      sel.appendChild(op);
    });
    sel.value = state.engine;

    var key = document.createElement('input');
    key.type = 'password';
    key.placeholder = 'Clave de OpenAI (sk-...)';
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
