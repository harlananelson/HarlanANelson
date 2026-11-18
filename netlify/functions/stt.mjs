// ElevenLabs Scribe speech-to-text proxy.
// Mirrors tts.mjs: lets the drill transcribe an utterance using the server's
// ELEVENLABS_API_KEY so visitors without their own key can still use the
// ElevenLabs recognition engine. The browser sends a base64-encoded WAV.
import { getStore } from '@netlify/blobs';
import guard from '../lib/guard.js';

export default async (req) => {
  const origin = req.headers.get('origin') || '';
  const cors = guard.corsHeaders(origin);
  const reply = (status, body, headers = {}) => new Response(body, { status, headers: { ...cors, ...headers } });
  if (req.method === 'OPTIONS') {
    return reply(204, null);
  }
  if (req.method !== 'POST') {
    return reply(405, 'Method Not Allowed');
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return reply(400, 'Invalid JSON');
  }

  const { audio_base64, language } = body;

  if (typeof audio_base64 !== 'string' || audio_base64.length === 0) {
    return reply(400, 'Missing audio_base64');
  }
  // Cap payload (~2 MB of base64 ≈ ~15 s of 16 kHz mono WAV) to bound cost.
  if (audio_base64.length > 2_800_000) {
    return reply(413, 'Audio too long');
  }
  const langCode = typeof language === 'string' && /^[a-z]{2,3}$/.test(language) ? language : 'es';

  const refused = await guard.admit({
    origin, headers: req.headers, bucket: 'stt', globalCost: 1,
    store: () => getStore({ name: 'rate-limits', consistency: 'strong' }),
  });
  if (refused) return reply(refused.status, refused.body);

  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return reply(500, 'Server misconfigured: ELEVENLABS_API_KEY not set');
  }

  let bytes;
  try {
    bytes = Buffer.from(audio_base64, 'base64');
  } catch {
    return reply(400, 'Invalid base64 audio');
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
      return reply(response.status, `ElevenLabs: ${text.slice(0, 200)}`);
    }
    return reply(200, text, { 'Content-Type': 'application/json' });
  } catch (err) {
    return reply(502, `Upstream error: ${err.message}`);
  }
};
