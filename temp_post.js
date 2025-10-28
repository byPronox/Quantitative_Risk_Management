/**
 * Simple POST helper to call backend /nmap/scan
 * Usage: node temp_post.js
 */
const url = 'http://localhost:8000/nmap/scan';

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
