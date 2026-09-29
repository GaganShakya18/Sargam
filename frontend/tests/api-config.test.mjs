import assert from 'node:assert/strict';

const { resolveApiBaseUrl } = await import('../src/services/apiConfig.js');

assert.equal(resolveApiBaseUrl({ hostname: 'localhost', protocol: 'http:' }), 'http://localhost:8000/api');
assert.equal(resolveApiBaseUrl({ hostname: '10.0.2.2', protocol: 'http:' }), 'http://10.0.2.2:8000/api');
assert.equal(resolveApiBaseUrl({ hostname: '192.168.1.10', protocol: 'http:' }), 'http://192.168.1.10:8000/api');
assert.equal(
	resolveApiBaseUrl({ hostname: '127.0.0.1', protocol: 'http:' }, 'http://192.168.137.1:8000/api'),
	'http://127.0.0.1:8000/api',
);
assert.equal(
	resolveApiBaseUrl({ hostname: '192.168.137.1', protocol: 'http:' }, 'http://192.168.137.1:8000/api'),
	'http://192.168.137.1:8000/api',
);
assert.equal(
	resolveApiBaseUrl({ hostname: 'localhost', protocol: 'https:' }, 'http://192.168.137.1:8000/api', true),
	'http://192.168.137.1:8000/api',
);
assert.equal(
	resolveApiBaseUrl({ hostname: 'localhost', protocol: 'http:' }, 'http://192.168.137.1:8000/api', true),
	'http://192.168.137.1:8000/api',
);

console.log('api config tests passed');
