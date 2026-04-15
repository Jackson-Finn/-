const { chromium } = require('playwright');

(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.on('console', msg => console.log('console:', msg.type(), msg.text()));
  page.on('pageerror', err => console.log('pageerror:', err.stack || err.message));
  page.on('requestfailed', req => console.log('requestfailed:', req.url(), req.failure()?.errorText));

  await page.goto('http://127.0.0.1:5173/login', { waitUntil: 'networkidle' });
  console.log('url after goto', page.url());

  const emailInput = page.locator('input').nth(0);
  const passwordInput = page.locator('input').nth(1);
  await emailInput.fill('buyer@example.com');
  await passwordInput.fill('Buyer123!');
  await page.getByRole('button', { name: '登录' }).click();
  await page.waitForURL('http://127.0.0.1:5173/', { timeout: 10000 });
  console.log('url after login', page.url());

  const sidebarText = await page.locator('.sidebar').innerText();
  console.log('sidebar text:', sidebarText);

  await page.getByRole('link', { name: /我的收藏/ }).click();
  await page.waitForTimeout(1500);
  console.log('url after favorites click', page.url());
  console.log('main text snippet favorites:', (await page.locator('main').innerText()).slice(0, 500));

  await page.getByRole('link', { name: /最近浏览/ }).click();
  await page.waitForTimeout(1500);
  console.log('url after history click', page.url());
  console.log('main text snippet history:', (await page.locator('main').innerText()).slice(0, 500));

  await browser.close();
})();
