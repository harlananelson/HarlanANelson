// ElevenLabs Scribe speech-to-text proxy.
// Mirrors tts.js: lets the drill transcribe an utterance using the server's
// ELEVENLABS_API_KEY so visitors without their own key can still use the
// ElevenLabs recognition engine. The browser sends a base64-encoded WAV.
exports.handler = async (event) => {
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    };
  }
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: 'Method Not Allowed' };
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    return { statusCode: 400, body: 'Invalid JSON' };
  }

  const { audio_base64, language } = body;

  if (typeof audio_base64 !== 'string' || audio_base64.length === 0) {
    return { statusCode: 400, body: 'Missing audio_base64' };
  }
  // Cap payload (~2 MB of base64 ≈ ~15 s of 16 kHz mono WAV) to bound cost.
  if (audio_base64.length > 2_800_000) {
    return { statusCode: 413, body: 'Audio too long' };
  }
  const langCode = typeof language === 'string' && /^[a-z]{2,3}$/.test(language) ? language : 'es';

  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return { statusCode: 500, body: 'Server misconfigured: ELEVENLABS_API_KEY not set' };
  }

  let bytes;
  try {
    bytes = Buffer.from(audio_base64, 'base64');
  } catch {
    return { statusCode: 400, body: 'Invalid base64 audio' };
  }

  try {
    const form = new FormData();
    form.append('model_id', 'scribe_v1');
    form.append('language_code', langCode);
    form.append('file', new Blob([bytes], { type: 'audio/wav' }), 'answer.wav');

    const response = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {
      method: 'POST',
      headers: { 'xi-api-key': apiKey },
      body: form,
    });

    const text = await response.text();
    if (!response.ok) {
      return { statusCode: response.status, body: `ElevenLabs: ${text.slice(0, 200)}` };
    }
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
      body: text,
    };
  } catch (err) {
    return { statusCode: 502, body: `Upstream error: ${err.message}` };
  }
};
