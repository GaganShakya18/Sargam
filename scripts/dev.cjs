const { createRequire } = require('node:module');
const { readFileSync } = require('node:fs');
const { execFile, spawn } = require('node:child_process');
const net = require('node:net');
const { resolve } = require('node:path');

const projectDirectory = resolve(__dirname, '..');
const backendDirectory = resolve(projectDirectory, 'backend');
const frontendDirectory = resolve(projectDirectory, 'frontend');
const frontendRequire = createRequire(resolve(frontendDirectory, 'package.json'));
const { loadEnv } = frontendRequire('vite');
const { VITE_API_BASE_URL: apiBaseUrl } = loadEnv('development', frontendDirectory, 'VITE_');
const backendEnvPath = resolve(backendDirectory, '.env');
const children = [];
let stopping = false;

function getDatabaseUrl() {
  let configuredUrl = process.env.DATABASE_URL;

  if (!configuredUrl) {
    try {
      const databaseLine = readFileSync(backendEnvPath, 'utf8')
        .split(/\r?\n/)
        .find((line) => /^\s*DATABASE_URL\s*=/.test(line));
      configuredUrl = databaseLine?.slice(databaseLine.indexOf('=') + 1).trim().replace(/^['"]|['"]$/g, '');
    } catch {}
  }

  return configuredUrl || 'sqlite:///./app.db';
}

function getPostgresWindowsService() {
  const script = [
    "$ErrorActionPreference = 'Stop'",
    "$services = @(Get-Service | Where-Object { $_.Name -like 'postgresql*' -or $_.DisplayName -like '*PostgreSQL*' })",
    "if ($services.Count -eq 0) { [pscustomobject]@{ state = 'missing' } | ConvertTo-Json -Compress; exit 0 }",
    "if ($services.Count -gt 1) { [pscustomobject]@{ state = 'ambiguous'; count = $services.Count } | ConvertTo-Json -Compress; exit 0 }",
    '$service = $services[0]',
    "$startError = $null",
    "if ($service.Status -ne 'Running') { try { Start-Service -Name $service.Name -ErrorAction Stop; $service = Get-Service -Name $service.Name } catch { $startError = $_.Exception.Message } }",
    '[pscustomobject]@{ state = $service.Status.ToString(); name = $service.Name; error = $startError } | ConvertTo-Json -Compress',
  ].join('; ');

  return new Promise((done) => {
    execFile('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], { windowsHide: true }, (error, stdout) => {
      if (error) {
        done({ state: 'query-failed', error: error.message });
        return;
      }

      try {
        done(JSON.parse(stdout.trim()));
      } catch {
        done({ state: 'query-failed', error: 'Could not read the PostgreSQL Windows service status.' });
      }
    });
  });
}

function canConnect(host, port) {
  return new Promise((done) => {
    const socket = net.createConnection({ host, port });
    socket.setTimeout(2000);
    socket.once('connect', () => {
      socket.destroy();
      done(true);
    });
    socket.once('error', () => done(false));
    socket.once('timeout', () => {
      socket.destroy();
      done(false);
    });
  });
}

function canListen(port) {
  return new Promise((done) => {
    const server = net.createServer();
    server.once('error', () => done(false));
    server.listen(port, '0.0.0.0', () => server.close(() => done(true)));
  });
}

async function findFreePort() {
  for (let port = 5173; port < 5200; port += 1) {
    if (await canListen(port)) return port;
  }
  throw new Error('No free Vite port found between 5173 and 5199.');
}

function startProcess(command, args, name, cwd, env = process.env) {
  const child = spawn(command, args, {
    cwd,
    env,
    stdio: 'inherit',
    shell: process.platform === 'win32',
  });
  const exit = new Promise((done) => {
    child.once('exit', (code, signal) => done({ code, signal, name }));
    child.once('error', (error) => {
      child.spawnError = error;
      done({ code: 1, signal: null, name, error });
    });
  });
  children.push({ child, name, exit });
  child.once('error', (error) => {
    console.error(`${name} could not start: ${error.message}`);
  });
  return child;
}

async function waitFor(url, serviceName, child) {
  const deadline = Date.now() + 60000;

  while (Date.now() < deadline) {
    if (child.spawnError) {
      throw new Error(`${serviceName} could not start: ${child.spawnError.message}`);
    }
    if (child.exitCode !== null) {
      throw new Error(`${serviceName} exited before becoming ready (exit code ${child.exitCode}).`);
    }

    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
      if (response.ok) return;
    } catch {}

    await new Promise((done) => setTimeout(done, 500));
  }

  throw new Error(`${serviceName} did not become ready at ${url} within 60 seconds.`);
}

function openBrowser(url) {
  if (process.platform === 'win32') {
    const browser = spawn('powershell.exe', ['-NoProfile', '-Command', `Start-Process '${url}'`], {
      stdio: 'ignore',
      windowsHide: true,
    });
    browser.unref();
  }
}

function stopChildren() {
  if (stopping) return;
  stopping = true;

  for (const { child } of children) {
    if (child.exitCode !== null) continue;

    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
    } else {
      child.kill('SIGTERM');
    }
  }
}

process.once('SIGINT', () => {
  stopChildren();
  process.exitCode = 130;
});
process.once('SIGTERM', () => {
  stopChildren();
  process.exitCode = 143;
});

async function main() {
  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is required in frontend/.env.');
  }

  const apiUrl = new URL(apiBaseUrl);
  const configuredDatabaseUrl = getDatabaseUrl();
  const isPostgresUrl = /^postgres(?:ql)?(?:\+[^:]+)?:\/\//i.test(configuredDatabaseUrl);
  const isSqliteUrl = /^sqlite:\/\//i.test(configuredDatabaseUrl);
  if (!isPostgresUrl && !isSqliteUrl) {
    throw new Error('Unsupported DATABASE_URL scheme for development. Use PostgreSQL or the existing SQLite fallback.');
  }

  let backendDatabaseUrl = configuredDatabaseUrl;
  if (isPostgresUrl) {
    const databaseUrl = new URL(configuredDatabaseUrl);
    const databaseHost = databaseUrl.hostname.replace(/^\[|\]$/g, '');
    const databasePort = Number(databaseUrl.port || 5432);
    let databaseReady = await canConnect(databaseHost, databasePort);

    if (!databaseReady && process.platform === 'win32' && ['localhost', '127.0.0.1', '::1'].includes(databaseHost)) {
      const service = await getPostgresWindowsService();
      if (service.state === 'Running') {
        console.log(`Reusing running PostgreSQL Windows service '${service.name}'.`);
      } else if (service.state === 'Stopped' && !service.error) {
        console.log(`Starting PostgreSQL Windows service '${service.name}'.`);
      } else if (service.state === 'Stopped' && service.error) {
        console.warn(`Could not start PostgreSQL service '${service.name}'; using the SQLite development fallback.`);
      } else if (service.state === 'missing') {
        console.warn('No local PostgreSQL service was found; using the SQLite development fallback.');
      } else if (service.state === 'ambiguous') {
        console.warn(`Found ${service.count} PostgreSQL services; using the SQLite development fallback.`);
      } else if (service.error) {
        console.warn(`Could not inspect PostgreSQL services; using the SQLite development fallback.`);
      }

      const canServiceBecomeReady = service.state === 'Running'
        || service.state === 'StartPending'
        || (service.state === 'Stopped' && !service.error);
      if (canServiceBecomeReady) {
        const deadline = Date.now() + 20000;
        while (!databaseReady && Date.now() < deadline) {
          await new Promise((done) => setTimeout(done, 500));
          databaseReady = await canConnect(databaseHost, databasePort);
        }
      }
    }

    if (!databaseReady) {
      console.warn(`PostgreSQL is not reachable at ${databaseHost}:${databasePort}; using the SQLite development fallback.`);
      backendDatabaseUrl = 'sqlite:///./app.db';
    } else {
      console.log(`PostgreSQL is reachable at ${databaseHost}:${databasePort}.`);
    }
  } else {
    console.log('Using the existing SQLite development database; PostgreSQL configuration remains unchanged.');
  }

  const port = await findFreePort();
  console.log('Starting FastAPI first.');

  const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
  const backend = startProcess(
    npm,
    ['run', 'dev:backend'],
    'backend',
    projectDirectory,
    { ...process.env, DATABASE_URL: backendDatabaseUrl },
  );
  await waitFor('http://127.0.0.1:8000/health', 'FastAPI', backend);
  console.log('FastAPI health check passed. Starting Vite.');

  const frontend = startProcess(
    npm,
    ['run', 'dev:frontend', '--', '--port', String(port), '--strictPort'],
    'frontend',
    projectDirectory,
  );
  await waitFor(`http://127.0.0.1:${port}/`, 'Vite', frontend);
  const previewUrl = `http://127.0.0.1:${port}/`;
  console.log(`Vite is ready. Laptop preview: ${previewUrl}`);
  console.log('Opening the laptop preview. Android is optional; use npm run dev:android when a device is connected.');
  openBrowser(previewUrl);

  const result = await Promise.race(children.map(({ exit }) => exit));

  if (!stopping) {
    console.error(result.error
      ? `${result.name} could not start: ${result.error.message}`
      : `${result.name} exited${result.signal ? ` from ${result.signal}` : ` with code ${result.code}`}.`);
    process.exitCode = result.code ?? 1;
  }
  stopChildren();
}

main().catch((error) => {
  console.error(error.message);
  stopChildren();
  process.exitCode = 1;
});