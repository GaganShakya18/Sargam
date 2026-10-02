const { createRequire } = require('node:module');
const { resolve } = require('node:path');
const { spawn } = require('node:child_process');

const frontendDirectory = resolve(__dirname, '..', 'frontend');
const frontendRequire = createRequire(resolve(frontendDirectory, 'package.json'));
const { loadEnv } = frontendRequire('vite');
const { VITE_API_BASE_URL: apiBaseUrl } = loadEnv('development', frontendDirectory, 'VITE_');
const port = Number(process.env.VITE_DEV_PORT || 5175);

if (!apiBaseUrl) {
  throw new Error('VITE_API_BASE_URL is required in frontend/.env for Android development.');
}

const apiUrl = new URL(apiBaseUrl);
const host = apiUrl.hostname;
const devServerUrl = `http://${host}:${port}`;

if (['localhost', '127.0.0.1', '::1'].includes(host)) {
  throw new Error('VITE_API_BASE_URL must use the laptop LAN address for a physical Android device.');
}

const viteUrl = `http://127.0.0.1:${port}/`;
const apiPort = apiUrl.port || (apiUrl.protocol === 'https:' ? '443' : '80');
const healthUrl = `http://127.0.0.1:${apiPort}/health`;

async function waitFor(url, serviceName) {
  const deadline = Date.now() + 60000;

  while (Date.now() < deadline) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
      if (response.ok) return;
    } catch {}

    await new Promise((done) => setTimeout(done, 500));
  }

  throw new Error(`${serviceName} did not become reachable at ${url}.`);
}

async function main() {
  console.log(`Waiting for local Vite at ${viteUrl} and FastAPI at ${healthUrl}...`);
  await Promise.all([waitFor(viteUrl, 'Vite'), waitFor(healthUrl, 'FastAPI')]);

  const capacitorBin = frontendRequire.resolve('@capacitor/cli/bin/capacitor');
  const child = spawn(
    process.execPath,
    [capacitorBin, 'run', 'android', '--live-reload', '--host', host, '--port', String(port)],
    {
      cwd: frontendDirectory,
      stdio: 'inherit',
      env: { ...process.env, CAPACITOR_DEV_SERVER_URL: devServerUrl },
    },
  );

  child.on('error', (error) => {
    console.error(`Could not start Capacitor Android: ${error.message}`);
    process.exitCode = 1;
  });

  child.on('exit', (code, signal) => {
    process.exitCode = code ?? (signal ? 1 : 0);
  });
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});