import { expect, test } from '@playwright/test'

// Exercises the full Phase 3 "Done when" scenario end-to-end against a real
// backend (LLM_PROVIDER=mock, no external API key) and a real SQLite
// database: origin select, the seeded opening scene, a free-form turn, the
// resulting inventory update, and that the same state survives a sign-out
// and sign-back-in.
test('full mock-provider gameplay loop', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`
  const password = 'correct horse battery'

  await page.goto('/')
  await expect(page.getByText('Fantasy AI Adventure')).toBeVisible()
  await page.getByText('Need an account? Register').click()
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Create account' }).click()

  await expect(page).toHaveURL(/\/saves$/)
  await page.getByRole('button', { name: 'New Game' }).click()

  await expect(page).toHaveURL(/\/new-game$/)
  await page.getByRole('radio', { name: /Tavern Cook/ }).click()
  await page.getByRole('button', { name: 'Begin adventure' }).click()

  await expect(page).toHaveURL(/\/game\//)
  await expect(
    page.getByText(
      'A cooking fire flares unnaturally blue just as a hooded stranger arrives through the rain.'
    )
  ).toBeVisible()

  await page.getByLabel('What do you do?').fill('I inspect the ashes by the back door.')
  await page.getByRole('button', { name: 'Send' }).click()
  await expect(page.getByText('The scene shifts in response.')).toBeVisible({ timeout: 15_000 })

  const inventoryPanel = page.getByRole('complementary', { name: 'Inventory' })
  await expect(inventoryPanel.getByText('Iron Cook Knife')).toBeVisible()
  await expect(inventoryPanel.getByText('Ember Charm')).toBeVisible()

  await page.getByRole('link', { name: 'Settings' }).click()
  await expect(page).toHaveURL(/\/settings$/)
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page).toHaveURL(/\/$/)

  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()

  await expect(page).toHaveURL(/\/saves$/)
  await page.getByRole('button', { name: 'Continue' }).click()

  await expect(page).toHaveURL(/\/game\//)
  await expect(page.getByText('The scene shifts in response.')).toBeVisible()
  const restoredInventoryPanel = page.getByRole('complementary', { name: 'Inventory' })
  await expect(restoredInventoryPanel.getByText('Iron Cook Knife')).toBeVisible()
  await expect(restoredInventoryPanel.getByText('Ember Charm')).toBeVisible()
})
