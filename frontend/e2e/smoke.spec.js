import { test, expect } from "@playwright/test";

test("dashboard renders standings from the embedded database", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".dashboard-view")).toBeVisible();
  await expect(page.getByText("Galatasaray").first()).toBeVisible();
});

test("season page lists its matches", async ({ page }) => {
  await page.goto("/#/season/2025");
  await expect(page.locator(".match-list")).toBeVisible();
  await expect(page.locator(".match-list .match-timeline-link").first()).toBeVisible();
});

test("search finds a team and navigates to its page", async ({ page }) => {
  await page.goto("/");
  const input = page.locator(".search-input");
  await input.click();
  await input.pressSequentially("Galata");
  const result = page.locator(".search-result", { hasText: "Galatasaray" }).first();
  await expect(result).toBeVisible();
  await result.click();
  await expect(page).toHaveURL(/#\/team\/Galatasaray/);
});

test("event-type filter narrows the match list", async ({ page }) => {
  await page.goto("/#/season/2025");
  const links = page.locator(".match-list .match-timeline-link");
  await expect(links.first()).toBeVisible();
  const before = await links.count();
  await page.locator(".filter-select").nth(1).selectOption("var");
  await expect.poll(async () => await links.count()).toBeLessThan(before);
});

test("match page embeds the highlight video", async ({ page }) => {
  await page.goto("/#/match/14109887");
  await expect(page.locator(".video-panel iframe")).toBeVisible();
});
