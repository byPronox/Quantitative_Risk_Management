/**
 * Simple POST helper to call microservice /api/v1/scan directly
 * Usage: node temp_post_micro.js
 */
const url = 'http://localhost:8004/api/v1/scan';

(async () => {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ip: '192.168.100.2' })
    });

    const text = await res.text();
    console.log('HTTP STATUS:', res.status);
    try {
      const json = JSON.parse(text);
      console.log(JSON.stringify(json, null, 2));
    } catch (e) {
      console.log('RESPONSE (non-JSON):');
      console.log(text);
    }
  } catch (err) {
    console.error('REQUEST ERROR:', err && err.message ? err.message : err);
    process.exit(1);
  }
})();
