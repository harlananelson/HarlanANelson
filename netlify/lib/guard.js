// Shared abuse guard for the Netlify functions (tts, stt, track).
//
// The functions spend money (ElevenLabs) or storage (Blobs) on behalf of
// whoever calls them, so each request must pass two checks:
//
//   1. Origin allowlist. Browsers always send an Origin header on a POST, so a
//      request from any other website is refused. A script (curl) can forge
//      Origin, so this stops casual cross-site use, not a determined caller.
//   2. Usage limits, kept as counters in Netlify Blobs:
//        - per client IP per hour (requests), and
//        - for the whole site per UTC day (requests, or characters for TTS).
//      The daily site-wide cap is what actually bounds the bill, because it
//      holds even against a caller who forges Origin and rotates IPs.
//
// Blobs has no atomic increment, so two simultaneous requests can both read
// the same count and both pass. The limits are therefore soft by a few
// requests. That is acceptable for cost control; it is not exact metering.
//
// Limits are overridable with environment variables in the Netlify UI
// (see limitsFor). ALLOWED_ORIGINS adds comma-separated origins to the list.

const crypto = require('crypto');

const DEFAULT_ORIGINS = [
  'https://harlananelson.com',
  'https://www.harlananelson.com',
  'https://neon-melba-851f2a.netlify.app',
];
const ORIGIN_PATTERNS = [
  /^https:\/\/[a-z0-9-]+--neon-melba-851f2a\.netlify\.app$/, // deploy previews
  /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/,              // netlify dev
];

function extraOrigins(env) {
  return String((env && env.ALLOWED_ORIGINS) || '')
    .split(',').map((s) => s.trim()).filter(Boolean);
}

function isAllowedOrigin(origin, env = process.env) {
  if (typeof origin !== 'string' || origin === '') return false;
  if (DEFAULT_ORIGINS.includes(origin) || extraOrigins(env).includes(origin)) return true;
  return ORIGIN_PATTERNS.some((re) => re.test(origin));
}

// CORS headers that name the caller's origin instead of '*'.
function corsHeaders(origin, env = process.env) {
  const h = {
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    Vary: 'Origin',
  };
  if (isAllowedOrigin(origin, env)) h['Access-Control-Allow-Origin'] = origin;
  return h;
}

function envInt(env, name, fallback) {
  const v = parseInt((env && env[name]) || '', 10);
  return Number.isFinite(v) && v >= 0 ? v : fallback;
}

// Default limits per function. globalDaily is in requests, except tts where
// it is in characters (ElevenLabs bills TTS per character).
function limitsFor(bucket, env = process.env) {
  const defaults = {
    tts:   { perIpHourly: 120, globalDaily: 20000 }, // characters/day
    stt:   { perIpHourly: 120, globalDaily: 300 },   // requests/day
    track: { perIpHourly: 240, globalDaily: 5000 },  // requests/day
  }[bucket];
  if (!defaults) throw new Error(`unknown bucket ${bucket}`);
  const B = bucket.toUpperCase();
  return {
    perIpHourly: envInt(env, `${B}_PER_IP_HOURLY`, defaults.perIpHourly),
    globalDaily: envInt(env, `${B}_GLOBAL_DAILY`, defaults.globalDaily),
  };
}

function hashIp(ip) {
  // Keys hold a hash, not the address itself.
  return crypto.createHash('sha256').update(String(ip || 'unknown')).digest('hex').slice(0, 24);
}

function clientIp(headers) {
  const get = (k) => (typeof headers.get === 'function' ? headers.get(k) : headers[k]);
  const direct = get('x-nf-client-connection-ip');
  if (direct) return direct;
  const fwd = get('x-forwarded-for');
  return fwd ? String(fwd).split(',')[0].trim() : 'unknown';
}

async function readCount(store, key) {
  const v = await store.get(key, { type: 'json' });
  return v && Number.isFinite(v.n) ? v.n : 0;
}

// Check and record one request. Returns { ok: true } or
// { ok: false, status, reason }. `store` needs get(key,{type:'json'}) and
// setJSON(key,value) — a Netlify Blobs store, or a fake in tests.
async function consume(store, { bucket, ip, globalCost = 1, limits, now = new Date() }) {
  const hour = now.toISOString().slice(0, 13); // YYYY-MM-DDTHH (UTC)
  const day = hour.slice(0, 10);
  const ipKey = `${bucket}/ip/${hashIp(ip)}/${hour}`;
  const allKey = `${bucket}/all/${day}`;

  const [ipN, allN] = await Promise.all([readCount(store, ipKey), readCount(store, allKey)]);
  if (ipN + 1 > limits.perIpHourly) {
    return { ok: false, status: 429, reason: 'Too many requests from this address; try again later' };
  }
  if (allN + globalCost > limits.globalDaily) {
    return { ok: false, status: 429, reason: 'Daily usage limit reached; try again tomorrow' };
  }
  await Promise.all([
    store.setJSON(ipKey, { n: ipN + 1 }),
    store.setJSON(allKey, { n: allN + globalCost }),
  ]);
  return { ok: true };
}

function rateStore(event) {
  // Required lazily so the pure functions above can be tested without the package.
  const blobs = require('@netlify/blobs');
  // Lambda-style (exports.handler) functions must hand Blobs their event first.
  if (event && typeof blobs.connectLambda === 'function') blobs.connectLambda(event);
  return blobs.getStore({ name: 'rate-limits', consistency: 'strong' });
}

// Full gate for a request. Returns null when the request may proceed, or a
// { status, body } refusal. Fails CLOSED: if the counters cannot be read or
// written, the request is refused, because the alternative is unmetered spend.
async function admit({ origin, headers, bucket, globalCost = 1, lambdaEvent, store, env = process.env }) {
  if (!isAllowedOrigin(origin, env)) return { status: 403, body: 'Forbidden origin' };
  try {
    // `store` may be a store, or a function returning one (so creating it is inside this try).
    const s = typeof store === 'function' ? store() : (store || rateStore(lambdaEvent));
    const r = await consume(s, { bucket, ip: clientIp(headers), globalCost, limits: limitsFor(bucket, env) });
    return r.ok ? null : { status: r.status, body: r.reason };
  } catch (err) {
    console.error(`[guard] ${bucket} limiter failed:`, err);
    return { status: 503, body: 'Usage limiter unavailable' };
  }
}

module.exports = { isAllowedOrigin, corsHeaders, limitsFor, consume, clientIp, hashIp, admit };
