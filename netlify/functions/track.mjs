// Opt-in drill session tracking sink.
// The drills' tracking module (drill-tracking.js) POSTs batches of session
// events here; each batch is stored as its own blob so concurrent writes
// never race. Pull data for analysis with:
//   npx netlify-cli blobs:list drill-tracking
//   npx netlify-cli blobs:get drill-tracking <key>
import { getStore } from '@netlify/blobs';

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: CORS });
  }
  if (req.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405, headers: CORS });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response('Invalid JSON', { status: 400, headers: CORS });
  }

  const { session, drill, events } = body || {};
  if (typeof session !== 'string' || !/^[\w-]{6,64}$/.test(session)) {
    return new Response('Missing/invalid session', { status: 400, headers: CORS });
  }
  if (typeof drill !== 'string' || !/^[\w-]{1,32}$/.test(drill)) {
    return new Response('Missing/invalid drill', { status: 400, headers: CORS });
  }
  if (!Array.isArray(events) || events.length === 0) {
    return new Response('No events', { status: 400, headers: CORS });
  }
  // Bound cost/abuse: cap batch size and total payload (~200 KB).
  if (events.length > 500 || JSON.stringify(events).length > 200_000) {
    return new Response('Batch too large', { status: 413, headers: CORS });
  }

  const store = getStore('drill-tracking');
  const key = `${drill}/${session}/${Date.now()}`;
  await store.setJSON(key, {
    drill,
    session,
    received: new Date().toISOString(),
    ua: req.headers.get('user-agent') || '',
    events,
  });

  return new Response(JSON.stringify({ ok: true, stored: events.length }), {
    status: 200,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
};
