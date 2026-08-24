import AxeBuilder from '@axe-core/playwright'
import { type Locator, type Page, expect, test } from '@playwright/test'

// Task 56: zero axe-core violations across the app's key screens, plus a
// 375px-viewport pass (no horizontal scroll, 44x44px touch targets) for the
// same screens. Reuses gameplay.spec.ts's navigation flow to reach each one
// against a real backend (LLM_PROVIDER=mock).
//
// Deliberately a single test walking through every screen with one
// registration, not one test per screen: registration is rate-limited to
// 3/hour per IP (Task 19/55), and a suite of one-registration-per-test
// quickly exceeds that against the same e2e backend process.

async function checkNoAxeViolations(page: Page, screenName: string) {
  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations, `${screenName} should have zero axe violations`).toEqual([])
}

async function checkNoHorizontalScroll(page: Page, screenName: string) {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }))
  expect(scrollWidth, `${screenName} should not scroll horizontally at 375px`).toBeLessThanOrEqual(
    clientWidth
  )
}

// Measures the *effective* touch target: the element's own layout box plus
// any hit-area expansion from an `::after` pseudo-element (Task 56's Button
// fix expands the clickable area via `after:-inset-1.5` without changing
// the visible size - boundingBox() alone can't see that, since it only
// measures layout box, not pseudo-element overflow, even though browsers do
// register clicks landing in the pseudo-element's area as clicks on the
// element itself).
async function checkTouchTarget(locator: Locator, label: string) {
  const box = await locator.boundingBox()
  expect(box, `${label} should be visible with a bounding box`).not.toBeNull()

  const afterExpansion = await locator.evaluate((el) => {
    const after = getComputedStyle(el, '::after')
    if (after.content === 'none') return { x: 0, y: 0 }
    const parseInset = (v: string) => (v === 'auto' ? 0 : Math.abs(Number.parseFloat(v)) || 0)
    return {
      x: parseInset(after.left) + parseInset(after.right),
      y: parseInset(after.top) + parseInset(after.bottom),
    }
  })

  const effectiveWidth = box!.width + afterExpansion.x
  const effectiveHeight = box!.height + afterExpansion.y
  expect(effectiveWidth, `${label} effective width should be >= 44px`).toBeGreaterThanOrEqual(44)
  expect(effectiveHeight, `${label} effective height should be >= 44px`).toBeGreaterThanOrEqual(44)
}

test('accessibility: axe-core zero violations + 375px viewport across all key screens', async ({
  page,
}) => {
  const email = `a11y-${Date.now()}@example.com`
  const password = 'correct horse battery'

  // --- Desktop viewport: axe-core across every key screen ---

  await page.goto('/')
  await expect(page.getByText('Fantasy AI Adventure')).toBeVisible()
  await checkNoAxeViolations(page, 'welcome/login screen')

  await page.getByText('Need an account? Register').click()
  await checkNoAxeViolations(page, 'register screen')

  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page).toHaveURL(/\/saves$/)
  await checkNoAxeViolations(page, 'saves list screen')

  await page.getByRole('button', { name: 'New Game' }).click()
  await expect(page).toHaveURL(/\/new-game$/)
  await checkNoAxeViolations(page, 'new-game/origin-select screen')

  await page.getByRole('radio', { name: /Tavern Cook/ }).click()
  await page.getByRole('button', { name: 'Begin adventure' }).click()
  await expect(page).toHaveURL(/\/game\//)
  await expect(
    page.getByText(
      'A cooking fire flares unnaturally blue just as a hooded stranger arrives through the rain.'
    )
  ).toBeVisible()
  await checkNoAxeViolations(page, 'game screen')
  const gameUrl = page.url()

  await page.getByRole('link', { name: 'Settings' }).click()
  await expect(page).toHaveURL(/\/settings$/)
  await checkNoAxeViolations(page, 'settings screen')

  // --- 375px viewport: no horizontal scroll + 44x44px touch targets,
  //     same authenticated session, no second registration needed ---

  await page.setViewportSize({ width: 375, height: 812 })

  await page.goto('/saves')
  await checkNoHorizontalScroll(page, 'saves list screen')
  await checkTouchTarget(page.getByRole('button', { name: 'New Game' }), 'New Game button')

  await page.goto('/new-game')
  await checkNoHorizontalScroll(page, 'new-game/origin-select screen')
  await checkTouchTarget(page.getByRole('radio', { name: /Tavern Cook/ }), 'Tavern Cook origin card')

  await page.goto(gameUrl)
  await expect(
    page.getByText(
      'A cooking fire flares unnaturally blue just as a hooded stranger arrives through the rain.'
    )
  ).toBeVisible()
  await checkNoHorizontalScroll(page, 'game screen')
  await checkTouchTarget(page.getByRole('button', { name: 'Send' }), 'composer Send button')
  // Below the lg breakpoint (Task 37), the persistent inventory panel
  // collapses to a drawer trigger button - that's the actual touch target
  // at this viewport, not the panel itself.
  await checkTouchTarget(page.getByRole('button', { name: /Inventory/ }), 'inventory drawer trigger')

  await page.goto('/settings')
  await checkNoHorizontalScroll(page, 'settings screen')
  await checkTouchTarget(page.getByRole('button', { name: 'Sign out' }), 'Sign out button')
})
