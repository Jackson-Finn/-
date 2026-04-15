const { chromium } = require('playwright');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', msg => console.log('console:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('pageerror:', err.stack || err.message));
  page.on('requestfailed', req => console.log('requestfailed:', req.url(), req.failure()?.errorText));
  page.on('response', async res => {
    const url = res.url();
    if (url.includes('/api/favorites') || url.includes('/api/history/recent') || url.includes('/api/history/products/')) {
      try {
        console.log('api response', res.status(), url, await res.text());
      } catch (e) {
        console.log('api response read failed', url, e.message);
      }
    }
  });

  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });
  const emailInput = page.locator('input').nth(0);
  const passwordInput = page.locator('input').nth(1);
  await emailInput.fill('buyer@example.com');
  await passwordInput.fill('Buyer123!');
  await page.locator('form').getByRole('button', { name: '登录' }).click();
  await page.waitForURL('http://127.0.0.1:5173/', { timeout: 10000 });
  console.log('after login url', page.url());

  await page.goto('http://127.0.0.1:5173/products/2', { waitUntil: 'networkidle' });
  console.log('product url', page.url());
  await page.getByRole('button', { name: /收藏|已收藏/ }).click();
  await page.waitForTimeout(1000);

  await page.goto('http://127.0.0.1:5173/favorites', { waitUntil: 'networkidle' });
  console.log('favorites url', page.url());
  console.log('favorites main', (await page.locator('main').innerText()).slice(0, 1200));

  await page.goto('http://127.0.0.1:5173/history', { waitUntil: 'networkidle' });
  console.log('history url', page.url());
  console.log('history main', (await page.locator('main').innerText()).slice(0, 1200));

  await browser.close();
})();
