/* Speaker diarization for the live translator — sherpa-onnx (WASM).
 *
 * Loads lazily — the WASM glue + segmentation + embedding models
 * (~57 MB total) only download when the user clicks "Diarize speakers".
 * Files are fetched directly from the official k2-fsa Hugging Face Space,
 * which already hosts them with permissive CORS:
 *   https://huggingface.co/spaces/k2-fsa/web-assembly-speaker-diarization-sherpa-onnx
 *
 * Exposes:
 *   window.TranslatorDiarize.load(onProgress) -> Promise
 *   window.TranslatorDiarize.diarize(samples16kFloat32, opts) -> [{start,end,speaker}]
 *   window.TranslatorDiarize.isLoaded()  -> boolean
 *   window.TranslatorDiarize.sampleRate()-> number (16000)
 */
(function () {
  'use strict';
  if (typeof window === 'undefined') { return; }

  var HF = 'https://huggingface.co/spaces/k2-fsa/web-assembly-speaker-diarization-sherpa-onnx/resolve/main/';
  var WRAPPER_URL = HF + 'sherpa-onnx-speaker-diarization.js';
  var GLUE_URL    = HF + 'sherpa-onnx-wasm-main-speaker-diarization.js';

  var loadPromise = null;
  var sd = null;
  var sampleRate = 16000;

  function loadScript(url) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = url;
      s.async = false;
      s.crossOrigin = 'anonymous';
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('Script load failed: ' + url)); };
      document.head.appendChild(s);
    });
  }

  function load(onProgress) {
    if (loadPromise) { return loadPromise; }
    loadPromise = new Promise(function (resolve, reject) {
      if (onProgress) { onProgress({ state: 'loading' }); }
      // Configure Emscripten BEFORE the glue script runs. The glue reads
      // Module.locateFile for the .wasm and .data, and Module.onRuntimeInitialized
      // when the WASM module + preloaded data are ready.
      window.Module = window.Module || {};
      window.Module.locateFile = function (path) { return HF + path; };
      window.Module.onRuntimeInitialized = function () {
        try {
          if (typeof window.createOfflineSpeakerDiarization !== 'function') {
            throw new Error('createOfflineSpeakerDiarization missing (wrapper script failed to load)');
          }
          sd = window.createOfflineSpeakerDiarization(window.Module);
          sampleRate = sd.sampleRate || 16000;
          if (onProgress) { onProgress({ state: 'ready', sampleRate: sampleRate }); }
          resolve();
        } catch (err) {
          if (onProgress) { onProgress({ state: 'error', error: String((err && err.message) || err) }); }
          reject(err);
        }
      };
      window.Module.print    = function (m) { if (onProgress) { onProgress({ state: 'log', msg: String(m) }); } };
      window.Module.printErr = function (m) { if (onProgress) { onProgress({ state: 'log', msg: 'err: ' + String(m) }); } };
      // Load the small JS wrapper first (defines createOfflineSpeakerDiarization),
      // then the WASM glue (which kicks off the .wasm + .data downloads).
      loadScript(WRAPPER_URL).then(function () {
        return loadScript(GLUE_URL);
      }).catch(function (err) {
        if (onProgress) { onProgress({ state: 'error', error: err.message }); }
        reject(err);
      });
    });
    return loadPromise;
  }

  function diarize(samples16k, options) {
    if (!sd) { throw new Error('Speaker model not loaded'); }
    options = options || {};
    if (options.numClusters != null || options.threshold != null) {
      try {
        sd.setConfig({
          clustering: {
            numClusters: options.numClusters != null ? options.numClusters : -1,
            threshold:   options.threshold   != null ? options.threshold   : 0.5
          }
        });
      } catch (e) { /* ignore — keep previous config */ }
    }
    return sd.process(samples16k);
  }

  window.TranslatorDiarize = {
    load: load,
    diarize: diarize,
    isLoaded: function () { return !!sd; },
    sampleRate: function () { return sampleRate; }
  };
})();
