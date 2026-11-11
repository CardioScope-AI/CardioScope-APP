// Contrôle HTTP de la version compilée, sans dépendance supplémentaire.
// node scripts/verify-frontend.mjs http://127.0.0.1:5173 --with-api
const base = new URL(process.argv[2] ?? 'http://127.0.0.1:5173');
const withApi = process.argv.includes('--with-api');

async function request(path) {
  return fetch(new URL(path, base), { signal: AbortSignal.timeout(10000) });
}

try {
  const response = await request('/');
  if (response.status !== 200) throw new Error(`Accueil : HTTP ${response.status}`);
  const html = await response.text();
  if (html.includes('/@vite/client') || html.includes('/src/main.')) {
    throw new Error('Serveur de développement détecté : lancer npm run preview après le build.');
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
  if (withApi) {
    const health = await request('/api/health');
    const body = await health.json();
    if (!((health.status === 200 && body.model_ready === true && body.status === 'ready')
      || (health.status === 503 && body.model_ready === false && body.status === 'model_unavailable'))) {
      throw new Error(`Réponse health inattendue : HTTP ${health.status}`);
    }
    console.log(`OK : proxy /api/health, HTTP ${health.status}, modèle ${body.model_ready ? 'prêt' : 'absent'}.`);
  }
} catch (error) {
  console.error(`Échec : ${error.message}`);
  process.exitCode = 1;
}
