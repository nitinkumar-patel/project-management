import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: "http://127.0.0.1:3210",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "rm -f ../data/playwright.sqlite3 && cd ../backend && PYTHONPATH=src PROJECT_MANAGEMENT_DB_PATH=../data/playwright.sqlite3 uv run uvicorn project_management_backend.main:app --host 127.0.0.1 --port 8010",
      url: "http://127.0.0.1:8010/api/health",
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command:
        "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010 npm run dev -- --hostname 127.0.0.1 --port 3210",
      url: "http://127.0.0.1:3210",
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
