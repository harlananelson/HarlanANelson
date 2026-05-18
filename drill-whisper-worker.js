/* Swahili drill — on-device Whisper transcription worker (Transformers.js).
 * Loaded as a module worker. Lifted from the live-translator worker, which
 * was hardened against the ONNX Runtime q8 / graph-optimizer / WebGPU bugs.
 *
 * Messages in:  {type:'load', model, device}
 *               {type:'transcribe', id, audio (Float32 @16kHz), model, device, language}
 *               {type:'clear'}
 * Messages out: {type:'status'|'progress'|'log'|'transcript', ...}
 */

['log', 'info', 'warn', 'error'].forEach(function (lvl) {
  var orig = console[lvl];
  console[lvl] = function () {
    try {
      var p = [];
      for (var i = 0; i < arguments.length; i++) {
        var a = arguments[i];
        p.push(typeof a === 'string' ? a : (function () {
          try { return JSON.stringify(a); } catch (e) { return String(a); }
        })());
      }
      self.postMessage({ type: 'log', msg: '[whisper.' + lvl + '] ' + p.join(' ') });
    } catch (e) { /* ignore */ }
    if (orig) { orig.apply(console, arguments); }
  };
});

function log(msg) { self.postMessage({ type: 'log', msg: '[whisper] ' + msg }); }

function errDetail(err) {
  if (!err) { return 'unknown error'; }
  var s = (err.name ? err.name + ': ' : '') + (err.message || String(err));
  if (err.stack) { s += '  ||stack: ' + String(err.stack).split('\n').slice(0, 5).join(' | '); }
  return s;
}

let tjs = null;
let transcriber = null;
let loadedKey = '';
let loadingPromise = null;
let forcedDevice = null;
let currentDevice = null;
const jobs = [];
let draining = false;

self.onmessage = function (e) {
  const m = e.data || {};
  if (m.type === 'load') {
    ensure(m.model, m.device).catch(function () { /* status already posted */ });
  } else if (m.type === 'transcribe') {
    jobs.push(m);
    ensure(m.model, m.device).then(drain).catch(function () {
      failAll('Speech model failed to load');
    });
  } else if (m.type === 'clear') {
    jobs.length = 0;
  }
};

async function getLib() {
  if (tjs) { return tjs; }
  const url = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.2.0';
  log('importing Transformers.js: ' + url);
  try {
    tjs = await import(url);
  } catch (err) {
    log('IMPORT FAILED: ' + errDetail(err));
    throw new Error('Transformers.js failed to import - ' + ((err && err.message) || err));
  }
  if (tjs && tjs.env) { tjs.env.allowLocalModels = false; }
  log('Transformers.js imported OK');
  return tjs;
}

function ensure(model, device) {
  const dev = forcedDevice || (device === 'webgpu' ? 'webgpu' : 'wasm');
  const key = model + '|' + dev;
  if (transcriber && loadedKey === key) { return Promise.resolve(transcriber); }
  if (loadingPromise && loadedKey === key) { return loadingPromise; }
  loadedKey = key;
  transcriber = null;
  self.postMessage({ type: 'status', state: 'loading', model: model });
  loadingPromise = loadModel(model, dev);
  return loadingPromise;
}

async function loadModel(model, dev) {
  let lib;
  try {
    lib = await getLib();
  } catch (err) {
    self.postMessage({ type: 'status', state: 'error', error: String((err && err.message) || err) });
    throw err;
  }
  const pipeline = lib.pipeline;
  if (typeof pipeline !== 'function') {
    const msg = 'Transformers.js loaded but exposes no pipeline() function';
    self.postMessage({ type: 'status', state: 'error', error: msg });
    throw new Error(msg);
  }
  // Graph optimizer disabled (ORT crashes on these Whisper exports otherwise).
  // fp16/WebGPU when asked; fp32/wasm is the universal fallback.
  const attempts = [];
  function addAttempt(dt, dv) {
    const k = dt + '|' + dv;
    for (let j = 0; j < attempts.length; j++) { if (attempts[j].k === k) { return; } }
    attempts.push({ dt: dt, dv: dv, k: k });
  }
  if (dev === 'webgpu') { addAttempt('fp16', 'webgpu'); }
  addAttempt('fp32', 'wasm');
  addAttempt('fp16', 'wasm');
  let lastErr = null;
  for (let i = 0; i < attempts.length; i++) {
    const a = attempts[i];
    try {
      log('loading "' + model + '" dtype=' + a.dt + ' device=' + a.dv + ' (graph-opt disabled)');
      transcriber = await pipeline('automatic-speech-recognition', model, {
        dtype: a.dt,
        device: a.dv,
        session_options: { graphOptimizationLevel: 'disabled' },
        progress_callback: function (p) { self.postMessage({ type: 'progress', data: p }); }
      });
      currentDevice = a.dv;
      log('model ready: ' + model + ' [dtype=' + a.dt + ', ' + a.dv + ']');
      self.postMessage({ type: 'status', state: 'ready', model: model, device: a.dv });
      return transcriber;
    } catch (err) {
      lastErr = err;
      log('attempt failed (dtype=' + a.dt + ', device=' + a.dv + '): ' + errDetail(err));
    }
  }
  self.postMessage({ type: 'status', state: 'error', error: String((lastErr && lastErr.message) || lastErr || 'model load failed') });
  throw lastErr || new Error('Model load failed');
}

async function drain() {
  if (draining) { return; }
  draining = true;
  try {
    while (jobs.length) {
      const job = jobs.shift();
      if (!transcriber) {
        self.postMessage({ type: 'transcript', id: job.id, ok: false, error: 'Speech model not loaded' });
        continue;
      }
      try {
        const out = await transcriber(job.audio, { language: job.language || 'swahili', task: 'transcribe' });
        const text = (out && typeof out.text === 'string' ? out.text : '').trim();
        self.postMessage({ type: 'transcript', id: job.id, ok: true, text: text });
      } catch (err) {
        log('transcription failed: ' + errDetail(err));
        if (currentDevice === 'webgpu' && forcedDevice !== 'wasm') {
          forcedDevice = 'wasm';
          log('inference failed on WebGPU - reloading on WASM and retrying');
          transcriber = null; loadedKey = ''; loadingPromise = null;
          try {
            await ensure(job.model, 'wasm');
            jobs.unshift(job);
            continue;
          } catch (e2) {
            self.postMessage({ type: 'transcript', id: job.id, ok: false, error: 'WASM fallback failed: ' + errDetail(e2) });
            continue;
          }
        }
        self.postMessage({ type: 'transcript', id: job.id, ok: false, error: String((err && err.message) || err) });
      }
    }
  } finally {
    draining = false;
  }
}

function failAll(msg) {
  while (jobs.length) {
    const job = jobs.shift();
    self.postMessage({ type: 'transcript', id: job.id, ok: false, error: msg });
  }
}
