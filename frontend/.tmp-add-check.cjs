const { chromium } = require('playwright');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('pageerror', err => console.log('pageerror:', err.stack || err.message));
  page.on('response', async res => {
    const url = res.url();
    if (url.includes('/api/favorites') || url.includes('/api/history/recent') || url.includes('/api/history/products/')) {
      try {
        console.log('api', res.status(), url, await res.text());
      } catch {}
    }
  });

  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });
  await page.locator('input').nth(0).fill('buyer@example.com');
  await page.locator('input').nth(1).fill('Buyer123!');
  await page.locator('form').getByRole('button', { name: '登录' }).click();
  await page.waitForURL('http://127.0.0.1:5173/', { timeout: 10000 });

  await page.goto('http://127.0.0.1:5173/products/2', { waitUntil: 'networkidle' });
  const buttonTextBefore = await page.locator('.secondary-actions .minor-action').nth(0).innerText();
  console.log('favorite button before:', buttonTextBefore);
  await page.locator('.secondary-actions .minor-action').nth(0).click();
  await page.waitForTimeout(1000);
  const buttonTextAfter = await page.locator('.secondary-actions .minor-action').nth(0).innerText();
  console.log('favorite button after:', buttonTextAfter);

  await page.goto('http://127.0.0.1:5173/favorites', { waitUntil: 'networkidle' });
  console.log('favorites text:', (await page.locator('main').innerText()).slice(0, 1000));

  await browser.close();
})();
