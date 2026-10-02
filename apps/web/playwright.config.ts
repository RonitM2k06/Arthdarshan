import { defineConfig, devices } from "@playwright/test";

// Expects the app running (python scripts/demo.py --no-browser). If it is not, Playwright starts it.
export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:3000", trace: "off", screenshot: "only-on-failure" },
  projects: [{ name: "desktop", use: { ...devices["Desktop Chrome"], channel: process.env.PW_CHANNEL || "msedge", viewport: { width: 1280, height: 900 } } }],
  webServer: { command: "python ../../scripts/demo.py --no-browser", url: "http://localhost:3000", reuseExistingServer: true, timeout: 240_000 },
});
