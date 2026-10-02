import { expect, test, type Page } from "@playwright/test";

const external = (url: string) => !/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//.test(url) && !url.startsWith("data:") && !url.startsWith("blob:");

async function decide(page: Page, action: string, opts: { reasoning?: string; conf?: number; pick?: string[] } = {}) {
  for (const id of opts.pick ?? []) await page.locator(`[data-evidence="${id}"]`).click();
  await page.locator(`[data-action="${action}"]`).click();
  if (opts.reasoning) await page.locator("#why").fill(opts.reasoning);
  if (opts.conf) await page.locator(`[data-conf="${opts.conf}"]`).click();
  await page.getByTestId("decide").click();
  await expect(page.getByTestId("feedback")).toBeVisible();
}
const cont = (page: Page) => page.getByTestId("continue").click();

test("landing page shows the product and loads no external resources", async ({ page }) => {
  const outside: string[] = [];
  page.on("request", (r) => external(r.url()) && outside.push(r.url()));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "ARTHDARSHAN", level: 1 })).toBeVisible();
  await expect(page.getByText("Train before you face it.").first()).toBeVisible();
  await expect(page.getByText("Practice financial decisions in a world where nothing you do can cost real money.")).toBeVisible();
  for (const cta of ["ENTER SIMULATOR", "LEARN WITH VOICE", "VIEW MY RESILIENCE"]) await expect(page.getByRole("link", { name: new RegExp(cta) }).first()).toBeVisible();
  await expect(page.getByText("SIMULATED · NO REAL MONEY").first()).toBeVisible();
  await expect(page.getByText("Guaranteed 30% returns.").first()).toBeVisible();
  await expect(page.locator("main li a", { hasText: "The Guaranteed Opportunity" })).toBeVisible();
  expect(outside, `external requests: ${outside.join(", ")}`).toEqual([]);
});

test("hero journey: impulsive then careful, with analysis, misconceptions, fingerprint and improvement", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByTestId("player")).toBeVisible();
  await expect(page.getByTestId("narrative")).toContainText("Rahul");
  await expect(page.getByTestId("channel")).toContainText("Guaranteed 30% returns");
  await expect(page.getByTestId("pressure")).toBeVisible();
  await expect(page.getByText("SIMULATED · NO REAL MONEY").first()).toBeVisible();
  // the five actions from the brief
  for (const a of ["invest", "verify", "investigate", "questions", "walk"]) await expect(page.locator(`[data-action="${a}"]`)).toBeVisible();
  // RUN 1 (impulsive)
  await decide(page, "invest", { reasoning: "My friend invested so it is probably legit and it is guaranteed", conf: 5, pick: ["e_guar"] });
  await expect(page.getByTestId("feedback")).toContainText("₹");
  await expect(page.getByTestId("feedback")).toContainText("M001");
  await expect(page.getByTestId("feedback")).toContainText(/RELIANCE ON A PERSONAL RECOMMENDATION/);
  await expect(page.getByTestId("explanation")).not.toContainText(/stupid|careless|irrational/i);
  await cont(page);
  await expect(page.getByTestId("narrative")).toContainText("₹6,500");
  await decide(page, "pay_fee", { reasoning: "I have already paid so I must pay once more to recover it", conf: 4 });
  await expect(page.getByTestId("feedback")).toContainText("M010");
  await cont(page);
  await decide(page, "pay_again");
  await cont(page);   // -> reflection summary
  const summary = page.getByTestId("summary");
  await expect(summary).toBeVisible();
  await expect(summary).toContainText("The requests kept coming");
  await expect(summary).toContainText("Your Financial Resilience Fingerprint");
  await expect(summary).toContainText("Not measured yet");           // honest: dimensions without data are not invented
  await expect(summary).toContainText("Your next training");
  await expect(page.getByTestId("fp-summary")).toContainText(/training opportunity/i);
  // RUN 2 (careful) via the recommended next scenario or replay
  await page.goto("/simulate/play?scenario=guaranteed_opportunity&n=2");
  await expect(page.getByTestId("player")).toBeVisible();
  const ev = ["e_auth", "e_guar", "e_scarce", "e_urgent", "e_stranger", "e_group", "e_missing"];
  await decide(page, "investigate", { reasoning: "Nobody can guarantee 30%, so I will verify it on the official website first", conf: 3, pick: ev });
  await expect(page.getByTestId("feedback")).toContainText(/evidence|pattern/i);
  await cont(page);
  await decide(page, "report_leave", { reasoning: "No registration found so I will report it", conf: 4, pick: ["i_dir", "i_guar", "i_acct"] });
  await cont(page);
  await expect(page.getByTestId("summary")).toContainText("You verified before paying");
  await expect(page.getByTestId("summary").getByText("▲").first()).toBeVisible();   // improvement shown
  // report reflects real data
  await page.goto("/resilience");
  await expect(page.getByRole("heading", { name: "Your Financial Resilience Fingerprint", level: 2 })).toBeVisible();
  await expect(page.getByTestId("insights")).toBeVisible();
  await expect(page.getByText("Improvement over time")).toBeVisible();
  await page.goto("/progress");
  await expect(page.getByTestId("tiles")).toContainText("2");
  await expect(page.getByTestId("recent")).toBeVisible();
});

test("every scenario is playable from the UI (first safe path)", async ({ page }) => {
  await page.goto("/demo");
  await page.goto("/simulate");
  await expect(page.getByTestId("scenario-grid")).toBeVisible();
  const ids = await page.locator("[data-start]").evaluateAll((els) => els.map((e) => e.getAttribute("data-start")!));
  expect(ids.length).toBeGreaterThanOrEqual(8);
  for (const id of ids.filter((x) => x !== "guaranteed_opportunity")) {
    await page.goto(`/simulate/play?scenario=${id}&n=${id}`);
    await expect(page.getByTestId("player")).toBeVisible();
    for (let step = 0; step < 14; step++) {
      if (await page.getByTestId("summary").isVisible().catch(() => false)) break;
      // choose the first action; flow reaches a terminal state in a few steps for every scenario
      await page.locator("[data-action]").first().click();
      await page.getByTestId("decide").click();
      await expect(page.getByTestId("feedback")).toBeVisible();
      await cont(page);
    }
    await expect(page.getByTestId("summary")).toBeVisible();
  }
});

test("Simple Mode: large text, confirmation before deciding, no timer", async ({ page }) => {
  await page.goto("/demo");
  await page.goto("/settings");
  await page.locator("#sw-simple").click();
  await expect(page.locator("html")).toHaveAttribute("data-simple", "true");
  await page.goto("/simulate/play?scenario=urgent_decision&n=simple");
  await expect(page.getByTestId("player")).toBeVisible();
  await expect(page.getByTestId("pressure")).toBeVisible();
  await expect(page.locator('svg[aria-label$="seconds left"]')).toHaveCount(0);   // slower pacing: no countdown ring
  await page.locator('[data-action="pause"]').click();
  await page.getByTestId("decide").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Go back" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByTestId("decide").click();
  await page.getByRole("button", { name: "Yes, decide" }).click();
  await expect(page.getByTestId("feedback")).toBeVisible();
  const fs = await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize));
  expect(fs).toBeGreaterThanOrEqual(20);
  await page.goto("/settings");
  await page.locator("#sw-simple").click();   // restore
});

test("Hindi and Hinglish: the hero scenario changes language", async ({ page }) => {
  await page.goto("/demo");
  await page.goto("/settings");
  await page.locator('[data-lang="hi"]').click();
  await page.goto("/simulate/play?scenario=guaranteed_opportunity&n=hi");
  await expect(page.getByTestId("narrative")).toContainText("राहुल");
  await expect(page.locator('[data-action="walk"]')).toContainText("छोड़");
  await page.goto("/settings");
  await page.locator('[data-lang="hinglish"]').click();
  await page.goto("/simulate/play?scenario=guaranteed_opportunity&n=hg");
  await expect(page.getByTestId("narrative")).toContainText("pehli job");
  await page.goto("/settings");
  await page.locator('[data-lang="en"]').click();
});

test("Learn: concepts, simulation, Hinglish question with sources, safety gateway", async ({ page }) => {
  await page.goto("/demo");
  await page.goto("/learn?tab=concepts&concept=volatility");
  await expect(page.getByTestId("concept-detail")).toContainText("Volatility");
  await expect(page.getByTestId("concept-detail")).toContainText("Simple explanation");
  // simulation responds to sliders
  await page.goto("/learn?tab=sims&sim=fee_erosion");
  await expect(page.getByTestId("sim-chart")).toContainText("ILLUSTRATIVE");
  await expect(page.getByTestId("sim-insights")).toBeVisible();
  const before = await page.getByTestId("sim-insights").innerText();
  await page.locator("#p-fee").fill("5");
  await expect(async () => expect(await page.getByTestId("sim-insights").innerText()).not.toEqual(before)).toPass();
  // Hinglish voice-first question (typed path)
  await page.goto("/learn?tab=ask");
  await page.getByLabel("Ask what a term means").fill("Volatility kya hoti hai?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByTestId("answer")).toContainText(/utaar|ooncha|volatility/i);
  await expect(page.getByTestId("answer")).toContainText("Sources");
  // safety gateway
  await page.goto("/learn?tab=safety");
  await page.getByRole("button", { name: "What stock should I buy tomorrow?" }).click();
  await expect(page.getByTestId("safety-result")).toContainText("Blocked");
  await expect(page.getByTestId("safety-result")).toContainText(/doesn't tell anyone|Nobody can/);
  await page.getByRole("button", { name: "Run", exact: true }).click();
  await expect(page.getByTestId("output-rewrite")).toBeVisible();
});

test("Evidence Lab teaches the verification workflow", async ({ page }) => {
  await page.goto("/demo");
  await page.goto("/learn?tab=lab");
  await page.getByRole("button", { name: "Telegram message (fictional)" }).click();
  await expect(page.getByTestId("lab-result")).toContainText("warning signals");
  await expect(page.getByTestId("lab-result")).toContainText("INDEPENDENT VERIFICATION");
});

test("mobile: bottom navigation, no horizontal scroll", async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 375, height: 800 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Mobile" })).toBeVisible();
  for (const path of ["/", "/simulate", "/learn", "/resilience", "/progress", "/settings", "/privacy"]) {
    await page.goto(path);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `horizontal overflow on ${path}`).toBeLessThanOrEqual(1);
  }
  await page.goto("/simulate/play?scenario=guaranteed_opportunity&n=m");
  await expect(page.getByTestId("player")).toBeVisible();
  const playOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(playOverflow, "horizontal overflow in the simulator on mobile").toBeLessThanOrEqual(1);
  await expect(page.getByTestId("decide")).toBeVisible();
  await ctx.close();
});

test("server down shows a clear message instead of a blank page", async ({ page }) => {
  await page.route("**/api/**", (r) => r.abort());
  await page.goto("/simulate");
  await expect(page.getByRole("alert").first()).toBeVisible();
});

test("privacy: export and delete my learning data", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByTestId("player")).toBeVisible();
  await decide(page, "walk");
  await page.goto("/settings");
  page.once("dialog", (d) => d.accept());
  await page.getByTestId("reset-data").click();
  await expect(page.getByRole("status").filter({ hasText: "Done" })).toBeVisible();
  await page.goto("/progress");
  await expect(page.getByTestId("tiles")).toContainText("0");
  await page.goto("/privacy");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("How your data is handled");
});

test("sample learner (scripted persona) shows a populated, honest fingerprint and improvement", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: /sample learner/i }).click();
  await expect(page).toHaveURL(/\/resilience/);
  await expect(page.getByRole("heading", { name: "Your Financial Resilience Fingerprint", level: 2 })).toBeVisible();
  await expect(page.getByText("Improvement over time")).toBeVisible();
  await expect(page.getByTestId("insights")).toBeVisible();
  await expect(page.getByText("▲").first()).toBeVisible();
});
