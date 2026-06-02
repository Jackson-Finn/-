import { expect, test } from '@playwright/test'

async function login(page, email, password) {
  await page.goto('/login')
  await page.locator('form input').first().fill(email)
  await page.locator('form input[type="password"]').fill(password)
  await page.locator('form').getByRole('button', { name: '登录' }).click()
  await page.waitForLoadState('networkidle')
}

test('storefront uses restrained marketplace copy on home and login', async ({ page }) => {
  await page.goto('/login')

  await expect(page.getByRole('heading', { name: '登录你的账户' })).toBeVisible()
  await expect(page.getByText('登录高级版交易平台')).toHaveCount(0)

  await login(page, 'buyer@example.com', 'Buyer123!')

  await expect(page.getByRole('heading', { name: '在售商品' })).toBeVisible()
  await expect(page.getByText('发现宝贝，聊好价格，轻松交易。')).toHaveCount(0)
})

test('product detail emphasizes trust and transaction information', async ({ page }) => {
  await login(page, 'buyer@example.com', 'Buyer123!')
  await page.goto('/')
  await page.locator('a[href^="/products/"]').first().click()
  await page.waitForLoadState('networkidle')

  await expect(page.getByRole('heading', { name: '交易方式与平台保障' })).toBeVisible()
  await expect(page.getByText('平台保障', { exact: false }).first()).toBeVisible()
  await expect(page.getByRole('button', { name: '立即下单' })).toBeVisible()
})

test('admin dashboard uses operations-oriented language', async ({ page }) => {
  await login(page, 'admin@example.com', 'Admin123!')
  await page.goto('/admin/dashboard')

  await expect(page.getByRole('heading', { name: '运营概览' })).toBeVisible()
  await expect(page.getByRole('button', { name: '处理待审商品' })).toBeVisible()
  await expect(page.getByText('后台概览')).toHaveCount(0)
})
