import { defineConfig, devices } from '@playwright/test'

const BACKEND_PORT = 8000
const FRONTEND_PORT = 5173

// Isolated from the dev-compose database (./data/game.db) so this suite
// never touches or is affected by a developer's own local save data.
// Gitignored via the repo's blanket `*.db` pattern.
const E2E_DATABASE_URL = 'sqlite+aiosqlite:///./e2e-test.db'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: `http://localhost:${FRONTEND_PORT}`,
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      // Chained as one shell command since webServer doesn't support a
      // separate "setup" step - alembic upgrade head is idempotent, so
      // this is safe to run on every invocation, not just the first.
      command: `uv run alembic upgrade head && uv run uvicorn app.main:app --port ${BACKEND_PORT}`,
      cwd: '../backend',
      url: `http://localhost:${BACKEND_PORT}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        DATABASE_URL: E2E_DATABASE_URL,
        LLM_PROVIDER: 'mock',
      },
    },
    {
      command: 'npm run dev',
      url: `http://localhost:${FRONTEND_PORT}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
})
