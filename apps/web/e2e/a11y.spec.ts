import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function audit(page: Page, label: string) {
  const res = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  const bad = res.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  const summary = bad.map((v) => `${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")} — ${v.help}`);
  expect(summary, `axe violations on ${label}`).toEqual([]);
}

const PAGES = ["/", "/simulate", "/learn?tab=concepts&concept=risk", "/learn?tab=lab", "/learn?tab=sims&sim=fee_erosion", "/learn?tab=ask", "/learn?tab=quiz", "/learn?tab=safety",
  "/resilience", "/progress", "/settings", "/profile", "/privacy"];

test.describe("accessibility (axe, WCAG 2.x A/AA: serious+critical must be zero)", () => {
  test.beforeEach(async ({ page }) => { await page.emulateMedia({ reducedMotion: "reduce" }); await page.goto("/demo"); await expect(page.getByTestId("player")).toBeVisible(); });

  for (const path of PAGES) {
    test(`page ${path}`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await audit(page, path);
    });
  }

  test("simulator scene, feedback and summary", async ({ page }) => {
    await page.goto("/simulate/play?scenario=guaranteed_opportunity&n=a11y");
    await expect(page.getByTestId("player")).toBeVisible();
    await audit(page, "player");
    await page.locator('[data-evidence="e_guar"]').click();
    await page.locator('[data-action="walk"]').click();
    await page.locator("#why").fill("No one can guarantee returns");
    await page.getByTestId("decide").click();
    await expect(page.getByTestId("feedback")).toBeVisible();
    await audit(page, "feedback");
    await page.getByTestId("continue").click();
    await expect(page.getByTestId("summary")).toBeVisible();
    await audit(page, "summary");
  });

  test("Simple Mode (high contrast) pages", async ({ page }) => {
    await page.goto("/settings");
    await page.locator("#sw-simple").click();
    for (const path of ["/", "/simulate", "/settings"]) { await page.goto(path); await page.waitForLoadState("networkidle"); await audit(page, `simple ${path}`); }
    await page.goto("/simulate/play?scenario=urgent_decision&n=a11ys");
    await expect(page.getByTestId("player")).toBeVisible();
    await audit(page, "simple player");
    await page.goto("/settings");
    await page.locator("#sw-simple").click();
  });

  test("keyboard: can complete a decision without a mouse", async ({ page }) => {
    await page.goto("/simulate/play?scenario=guaranteed_opportunity&n=kbd");
    await expect(page.getByTestId("player")).toBeVisible();
    await page.locator('[data-action="walk"]').focus();
    await page.keyboard.press("Enter");
    await expect(page.locator('[data-action="walk"]')).toHaveAttribute("aria-checked", "true");
    await page.getByTestId("decide").focus();
    await page.keyboard.press("Enter");
    await expect(page.getByTestId("feedback")).toBeVisible();
    await expect(page.getByTestId("continue")).toBeFocused();
  });

  test("language attribute and skip link", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
  });
});
