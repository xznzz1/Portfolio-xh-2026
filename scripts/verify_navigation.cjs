// Browser regression check for collection navigation and photo controls.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const tmp = path.join(root, '.tmp');
const base = process.argv[2] || 'https://portfolio-xh-2026.pages.dev/';
const label = process.argv[3] || 'navigation';
const projects = [
  ['above-the-wall', "ARC'TERYX"], ['between-ridges', 'MAMMUT'],
  ['cornice-line', 'SALOMON'], ['upward', 'PELLIOT'],
  ['a-moment-on-the-wall', 'LUMITREK'], ['campaign-one', 'CANON'],
  ['project-title', 'LA SPORTIVA'], ['campaign-two', 'FPA'], ['forest-camp', 'SCARPA'],
];

(async () => {
  await fs.mkdir(tmp, { recursive: true });
  process.env.TEMP = tmp;
  process.env.TMP = tmp;
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const results = [];
  const errors = [];
  const external = new Set();
  try {
    for (const mobile of [false, true]) {
      const context = await browser.newContext({
        viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
        isMobile: mobile, hasTouch: mobile,
      });
      const origin = new URL(base).origin;
      await context.route('**/*', route => {
        const url = new URL(route.request().url());
        if (url.protocol.startsWith('http') && url.origin !== origin) {
          external.add(url.href);
          return route.abort();
        }
        return route.continue();
      });
      const page = await context.newPage();
      const cmsRequests = new Map();
      page.on('request', r => {
        if (r.url().includes('.framercms')) cmsRequests.set(r.url(), (cmsRequests.get(r.url()) || 0) + 1);
      });
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      page.on('pageerror', e => errors.push(e.message));
      page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });
      await page.goto(base, { waitUntil: 'networkidle' });
      const probe = await page.evaluate(() => window.__portfolioNavigationProbe = Math.random());
      for (const [slug, title] of projects) {
        const start = performance.now();
        await page.locator(`a[href*="/work/${slug}"]`).first().click();
        await page.waitForFunction(title => document.querySelector('h1')?.innerText.trim() === title, title);
        await page.getByRole('link', { name: /Back to work/i }).waitFor({ state: 'visible' });
        const enteredMs = Math.round(performance.now() - start);
        assert.equal(await page.evaluate(() => window.__portfolioNavigationProbe), probe, 'Project navigation reloaded the document');

        const photoCount = await page.evaluate(() => {
          for (const element of document.querySelectorAll('[aria-live]')) {
            const counter = element.textContent.trim().match(/^(\d+)\s*\/\s*(\d+)$/);
            if (counter) return Number(counter[2]);
          }
          return 0;
        });
        assert.ok(photoCount > 0, `Missing photo collection: ${slug}`);
        for (let photo = 2; photo <= photoCount; photo++) {
          await page.getByRole('button', { name: 'Next image', exact: true }).click();
          await page.waitForFunction(photo => [...document.querySelectorAll('[aria-live]')].some(element => Number(element.textContent.trim().match(/^(\d+)\s*\//)?.[1]) === photo), photo);
          await page.evaluate(async () => { await Promise.all([...document.images].filter(i => i.getClientRects().length).map(i => i.decode().catch(() => {}))); });
          assert.equal(await page.locator('img').evaluateAll(images => images.filter(i => i.getClientRects().length && !i.naturalWidth).length), 0, `Broken photo ${photo}: ${slug}`);
        }
        if (photoCount > 1) {
          await page.getByRole('button', { name: 'Previous image', exact: true }).click();
          await page.waitForFunction(photo => [...document.querySelectorAll('[aria-live]')].some(element => Number(element.textContent.trim().match(/^(\d+)\s*\//)?.[1]) === photo), photoCount - 1);
          await page.getByRole('button', { name: 'Show photo 1', exact: true }).click();
        }

        if (slug === 'above-the-wall') {
          await page.getByRole('button', { name: 'Next image', exact: true }).click();
          await page.waitForFunction(() => /02\s*\/\s*02/.test(document.body.innerText));
          await page.getByRole('button', { name: 'Previous image', exact: true }).click();
          await page.waitForFunction(() => /01\s*\/\s*02/.test(document.body.innerText));
          await page.getByRole('button', { name: 'Close series', exact: true }).click();
          await page.getByRole('button', { name: 'Close series', exact: true }).waitFor({ state: 'hidden' });
          await page.waitForFunction(() => [...document.querySelectorAll('h1')].some(h => h.innerText.includes('OUTDOOR')));
          assert.equal(await page.evaluate(() => window.__portfolioNavigationProbe), probe, 'Closing the photo reloaded the document');
          await page.locator('a[href*="/work/above-the-wall"]').first().click();
          await page.waitForFunction(() => document.querySelector('h1')?.innerText.trim() === "ARC'TERYX");
          await page.getByRole('button', { name: 'Close series', exact: true }).waitFor({ state: 'visible' });
          await page.screenshot({ path: path.join(tmp, `${label}-${mobile ? 'mobile' : 'desktop'}-gallery.png`) });
        }
        await page.evaluate(async () => {
          await Promise.all([...document.images].filter(i => i.getClientRects().length).map(i => i.decode().catch(() => {})));
        });
        assert.equal(await page.locator('img').evaluateAll(images => images.filter(i => i.getClientRects().length && !i.naturalWidth).length), 0, `Broken project image: ${slug}`);
        assert.equal(await page.locator('#__framer-badge-container').count(), 0);

        const backStart = performance.now();
        await page.getByRole('link', { name: /Back to work/i }).click();
        await page.waitForFunction(() => !document.querySelector('a[href]')?.textContent.includes('Back to work') && [...document.querySelectorAll('h1')].some(h => h.innerText.includes('OUTDOOR')));
        await page.locator('a[href*="/work/above-the-wall"]').first().waitFor({ state: 'visible' });
        await page.waitForFunction(() => {
          const image = document.querySelector('a[href*="/work/above-the-wall"] img');
          if (!image?.naturalWidth) return false;
          for (let element = image; element; element = element.parentElement) {
            const style = getComputedStyle(element);
            if (Number(style.opacity) < 0.95 || style.visibility === 'hidden' || style.display === 'none') return false;
          }
          const rect = image.getBoundingClientRect();
          return rect.bottom > 0 && rect.top < innerHeight;
        }, null, { timeout: 8000 });
        assert.equal(await page.getByRole('link', { name: /Back to work/i }).count(), 0, 'Project view persisted after Back to work');
        assert.equal(await page.evaluate(() => window.__portfolioNavigationProbe), probe, 'Back to work reloaded the document');
        assert.equal(new URL(page.url()).hash, '#work');
        results.push({ mobile, slug, photos: photoCount, enteredMs, backMs: Math.round(performance.now() - backStart) });
      }
      await page.waitForTimeout(800);
      await page.screenshot({ path: path.join(tmp, `${label}-${mobile ? 'mobile' : 'desktop'}-returned.png`) });
      for (const [url, count] of cmsRequests) {
        assert.equal(new URL(url).searchParams.has('range'), false, 'Framer range query remains');
        assert.equal(count, 1, `Collection file fetched repeatedly: ${url}`);
      }
      results.push({ mobile, cachedCollectionRequests: Object.fromEntries(cmsRequests) });
      const direct = await context.newPage();
      direct.on('pageerror', e => errors.push(e.message));
      direct.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      await direct.goto(new URL('work/above-the-wall/', base).href, { waitUntil: 'networkidle' });
      const directProbe = await direct.evaluate(() => window.__portfolioNavigationProbe = Math.random());
      await direct.getByRole('link', { name: /Back to work/i }).click();
      await direct.waitForFunction(() => [...document.querySelectorAll('h1')].some(h => h.innerText.includes('OUTDOOR')));
      await direct.locator('a[href*="/work/above-the-wall"]').first().waitFor({ state: 'visible' });
      assert.equal(await direct.evaluate(() => window.__portfolioNavigationProbe), directProbe, 'Direct-entry Back to work reloaded the document');
      results.push({ mobile, directProjectBack: true });
      await context.close();
    }
    assert.deepEqual(errors, []);
    assert.deepEqual([...external], []);
    console.log(JSON.stringify({ transitions: results.filter(r => r.slug).length, errors, external: [...external], results }));
  } finally {
    await fs.writeFile(path.join(tmp, `${label}-report.json`), JSON.stringify({ results, errors, external: [...external] }, null, 2));
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });
