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

  const { text, voice_id, speed } = body;

  if (typeof text !== 'string' || text.length === 0) {
    return reply(400, 'Missing text');
  }
  if (text.length > 500) {
    return reply(413, 'Text too long (max 500 chars)');
  }
  if (typeof voice_id !== 'string' || !/^[a-zA-Z0-9]{16,32}$/.test(voice_id)) {
    return reply(400, 'Invalid voice_id');
  }
  const safeSpeed = typeof speed === 'number' && speed >= 0.5 && speed <= 1.2 ? speed : 0.95;

  const refused = await guard.admit({
    origin, headers: req.headers, bucket: 'tts', globalCost: text.length,
    store: () => getStore({ name: 'rate-limits', consistency: 'strong' }),
  });
  if (refused) return reply(refused.status, refused.body);

  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return reply(500, 'Server misconfigured: ELEVENLABS_API_KEY not set');
  }

  try {
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice_id}`, {
      method: 'POST',
      headers: {
        'xi-api-key': apiKey,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg',
      },
      body: JSON.stringify({
        text,
        model_id: 'eleven_multilingual_v2',
        voice_settings: { stability: 0.75, similarity_boost: 0.85, style: 0.0, speed: safeSpeed },
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      return reply(response.status, `ElevenLabs: ${errText.slice(0, 200)}`);
    }

    const buffer = await response.arrayBuffer();
    return reply(200, buffer, {
      'Content-Type': 'audio/mpeg',
      'Cache-Control': 'public, max-age=3600',
    });
  } catch (err) {
    return reply(502, `Upstream error: ${err.message}`);
  }
};
