const { admit, corsHeaders } = require('../lib/guard');

exports.handler = async (event) => {
  const origin = event.headers.origin || event.headers.Origin || '';
  const cors = corsHeaders(origin);
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: cors };
  }
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, headers: cors, body: 'Method Not Allowed' };
  }

  let body;
  try {
    body = JSON.parse(event.body || '{}');
  } catch {
    return { statusCode: 400, headers: cors, body: 'Invalid JSON' };
  }

  const { text, voice_id, speed } = body;

  if (typeof text !== 'string' || text.length === 0) {
    return { statusCode: 400, headers: cors, body: 'Missing text' };
  }
  if (text.length > 500) {
    return { statusCode: 413, headers: cors, body: 'Text too long (max 500 chars)' };
  }
  if (typeof voice_id !== 'string' || !/^[a-zA-Z0-9]{16,32}$/.test(voice_id)) {
    return { statusCode: 400, headers: cors, body: 'Invalid voice_id' };
  }
  const safeSpeed = typeof speed === 'number' && speed >= 0.5 && speed <= 1.2 ? speed : 0.95;

  const refused = await admit({ origin, headers: event.headers, bucket: 'tts', globalCost: text.length, lambdaEvent: event });
  if (refused) return { statusCode: refused.status, headers: cors, body: refused.body };

  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return { statusCode: 500, headers: cors, body: 'Server misconfigured: ELEVENLABS_API_KEY not set' };
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
      return { statusCode: response.status, body: `ElevenLabs: ${errText.slice(0, 200)}` };
    }

    const buffer = await response.arrayBuffer();
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'public, max-age=3600',
        ...cors,
      },
      body: Buffer.from(buffer).toString('base64'),
      isBase64Encoded: true,
    };
  } catch (err) {
    return { statusCode: 502, headers: cors, body: `Upstream error: ${err.message}` };
  }
};
