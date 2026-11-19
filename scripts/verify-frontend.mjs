// Contrôle HTTP de la version compilée, sans dépendance supplémentaire.
// node scripts/verify-frontend.mjs http://127.0.0.1:5173 --with-api
const base = new URL(process.argv[2] ?? 'http://127.0.0.1:5173');
const withApi = process.argv.includes('--with-api');
const withNginx = process.argv.includes('--with-nginx');
const report = { verified_at_utc: new Date().toISOString(), base: base.origin, checks: {} };

async function request(path) {
  return fetch(new URL(path, base), { signal: AbortSignal.timeout(10000) });
}

try {
  const response = await request('/');
  if (response.status !== 200) throw new Error(`Accueil : HTTP ${response.status}`);
  const html = await response.text();
  report.checks.html = response.status;
  if (html.includes('/@vite/client') || html.includes('/src/main.')) {
    throw new Error('Serveur de développement détecté : servir les fichiers compilés après le build.');
  }
  const assets = [...html.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)].map(match => match[1]);
  if (!assets.some(path => path.endsWith('.js')) || !assets.some(path => path.endsWith('.css'))) {
    throw new Error('Les fichiers JavaScript et CSS compilés sont absents du HTML.');
  }
  for (const asset of assets) {
    const result = await request(asset);
    const mime = result.headers.get('content-type') ?? '';
    if (!result.ok || (asset.endsWith('.js') ? !/javascript/.test(mime) : !/text\/css/.test(mime))) {
      throw new Error(`Fichier compilé invalide : ${asset} (HTTP ${result.status}, ${mime}).`);
    }
  }
  console.log(`OK : HTML et ${assets.length} fichiers compilés servis, sans client Vite de développement.`);
  report.checks.compiled_assets = assets.length;
  if (withApi) {
    const health = await request('/api/health');
    const body = await health.json();
    if (!((health.status === 200 && body.model_ready === true && body.status === 'ready')
      || (health.status === 503 && body.model_ready === false && body.status === 'model_unavailable'))) {
      throw new Error(`Réponse health inattendue : HTTP ${health.status}`);
    }
    console.log(`OK : proxy /api/health, HTTP ${health.status}, modèle ${body.model_ready ? 'prêt' : 'absent'}.`);
    report.checks.api_health = health.status;
  }
  if (withNginx) {
    const route = await request('/simulation');
    if (route.status !== 200 || await route.text() !== html) {
      throw new Error('Le rechargement direct de la SPA ne retourne pas index.html.');
    }
    const missingAsset = await request('/assets/app21-missing.js');
    if (missingAsset.status !== 404) throw new Error('Un asset absent doit répondre 404.');
    if (!/no-cache/.test(response.headers.get('cache-control') ?? '')) {
      throw new Error('Le HTML doit être revalidé.');
    }
    const asset = await request(assets[0]);
    if (!/immutable/.test(asset.headers.get('cache-control') ?? '')) {
      throw new Error('Les assets compilés doivent être mis en cache.');
    }
    const missingApi = await request('/api/app21-missing');
    if (missingApi.status !== 404 || !(await missingApi.json()).error) {
      throw new Error('Le proxy doit conserver le 404 JSON backend.');
    }
    const invalid = await fetch(new URL('/api/predict?app21=validation', base), {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: '{}', signal: AbortSignal.timeout(10000),
    });
    if (invalid.status !== 422 || (await invalid.json()).error?.code !== 'validation_error') {
      throw new Error('Le proxy doit transmettre le POST JSON et conserver le 422.');
    }
    if (!/no-store/.test(invalid.headers.get('cache-control') ?? '')) {
      throw new Error('Une réponse API ne doit pas être mise en cache.');
    }
    report.checks.spa_reload = 200;
    report.checks.missing_asset = 404;
    report.checks.api_missing_route = 404;
    report.checks.api_invalid_post = 422;
    report.checks.cache_headers = true;
    console.log('OK : SPA, asset absent, cache et erreurs JSON à travers Nginx.');
  }
  const reportIndex = process.argv.indexOf('--report');
  if (reportIndex !== -1) {
    const path = process.argv[reportIndex + 1];
    if (!path || path.startsWith('--')) throw new Error('Chemin --report manquant.');
    const { writeFile } = await import('node:fs/promises');
    await writeFile(path, JSON.stringify(report, null, 2) + '\n');
  }
} catch (error) {
  console.error(`Échec : ${error.message}`);
  process.exitCode = 1;
}
