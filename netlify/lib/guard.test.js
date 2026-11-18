// Run with: node --test netlify/
const test = require('node:test');
const assert = require('node:assert/strict');
const { isAllowedOrigin, corsHeaders, limitsFor, consume, clientIp, admit } = require('./guard');

function fakeStore() {
  const m = new Map();
  return {
    m,
    async get(k) { return m.has(k) ? JSON.parse(m.get(k)) : null; },
    async setJSON(k, v) { m.set(k, JSON.stringify(v)); },
  };
}

test('origin allowlist', () => {
  const env = {};
  assert.ok(isAllowedOrigin('https://harlananelson.com', env));
  assert.ok(isAllowedOrigin('https://www.harlananelson.com', env));
  assert.ok(isAllowedOrigin('https://deploy-preview-12--neon-melba-851f2a.netlify.app', env));
  assert.ok(isAllowedOrigin('http://localhost:8888', env));
  assert.ok(!isAllowedOrigin('https://evil.example', env));
  assert.ok(!isAllowedOrigin('https://harlananelson.com.evil.example', env));
  assert.ok(!isAllowedOrigin('https://x--neon-melba-851f2a.netlify.app.evil.example', env));
  assert.ok(!isAllowedOrigin('', env));
  assert.ok(!isAllowedOrigin(undefined, env));
  assert.ok(isAllowedOrigin('https://other.example', { ALLOWED_ORIGINS: 'https://a.example, https://other.example' }));
});

test('cors echoes only allowed origins', () => {
  assert.equal(corsHeaders('https://harlananelson.com', {})['Access-Control-Allow-Origin'], 'https://harlananelson.com');
  assert.equal(corsHeaders('https://evil.example', {})['Access-Control-Allow-Origin'], undefined);
});

test('limits read env overrides', () => {
  assert.deepEqual(limitsFor('tts', {}), { perIpHourly: 120, globalDaily: 20000 });
  assert.deepEqual(limitsFor('stt', { STT_GLOBAL_DAILY: '5', STT_PER_IP_HOURLY: 'x' }), { perIpHourly: 120, globalDaily: 5 });
  assert.throws(() => limitsFor('nope', {}));
});

test('per-IP hourly limit', async () => {
  const s = fakeStore();
  const limits = { perIpHourly: 2, globalDaily: 100 };
  const now = new Date('2026-11-18T10:15:00Z');
  assert.ok((await consume(s, { bucket: 'stt', ip: '1.2.3.4', limits, now })).ok);
  assert.ok((await consume(s, { bucket: 'stt', ip: '1.2.3.4', limits, now })).ok);
  const r = await consume(s, { bucket: 'stt', ip: '1.2.3.4', limits, now });
  assert.equal(r.ok, false);
  assert.equal(r.status, 429);
  // a different IP is still allowed; next hour resets
  assert.ok((await consume(s, { bucket: 'stt', ip: '5.6.7.8', limits, now })).ok);
  assert.ok((await consume(s, { bucket: 'stt', ip: '1.2.3.4', limits, now: new Date('2026-11-18T11:00:00Z') })).ok);
  // raw IPs are never stored in keys
  for (const k of s.m.keys()) assert.ok(!k.includes('1.2.3.4'));
});

test('global daily cap counts cost, across IPs', async () => {
  const s = fakeStore();
  const limits = { perIpHourly: 100, globalDaily: 1000 };
  const now = new Date('2026-11-18T10:00:00Z');
  assert.ok((await consume(s, { bucket: 'tts', ip: 'a', globalCost: 600, limits, now })).ok);
  assert.equal((await consume(s, { bucket: 'tts', ip: 'b', globalCost: 500, limits, now })).ok, false);
  assert.ok((await consume(s, { bucket: 'tts', ip: 'b', globalCost: 400, limits, now })).ok);
  assert.ok((await consume(s, { bucket: 'tts', ip: 'b', globalCost: 400, limits, now: new Date('2026-11-19T00:00:00Z') })).ok);
});

test('client ip from Netlify header, forwarded-for, or Headers object', () => {
  assert.equal(clientIp({ 'x-nf-client-connection-ip': '9.9.9.9', 'x-forwarded-for': '1.1.1.1' }), '9.9.9.9');
  assert.equal(clientIp({ 'x-forwarded-for': '1.1.1.1, 2.2.2.2' }), '1.1.1.1');
  assert.equal(clientIp(new Headers({ 'x-nf-client-connection-ip': '3.3.3.3' })), '3.3.3.3');
  assert.equal(clientIp({}), 'unknown');
});

test('admit: refuses bad origin, passes good, fails closed on store error', async () => {
  const env = { TTS_GLOBAL_DAILY: '10' };
  const store = fakeStore();
  assert.equal((await admit({ origin: 'https://evil.example', headers: {}, bucket: 'tts', store, env })).status, 403);
  assert.equal(await admit({ origin: 'https://harlananelson.com', headers: {}, bucket: 'tts', globalCost: 5, store, env }), null);
  assert.equal((await admit({ origin: 'https://harlananelson.com', headers: {}, bucket: 'tts', globalCost: 6, store, env })).status, 429);
  const broken = { async get() { throw new Error('down'); }, async setJSON() {} };
  assert.equal((await admit({ origin: 'https://harlananelson.com', headers: {}, bucket: 'tts', store: broken, env })).status, 503);
  assert.equal((await admit({ origin: 'https://harlananelson.com', headers: {}, bucket: 'tts', store: () => { throw new Error('no ctx'); }, env })).status, 503);
});
