import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("customer lane is usable and has no serious accessibility violations", async ({
  page,
}) => {
  await page.goto("/lane");
  await expect(
    page.getByRole("heading", { name: "Ready for your arrival" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /simulate vehicle arrival/i }).click();
  await expect(page.getByRole("heading", { name: "Welcome" })).toBeVisible();
  await page.getByRole("button", { name: /add classic burger/i }).click();
  await expect(page.locator(".total-row").getByText("$8.50")).toBeVisible();

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});

test("operator can open diagnostics and request handoff", async ({ page }) => {
  await page.goto("/console");
  await expect(
    page.getByRole("heading", { name: "Lane overview" }),
  ).toBeVisible();
  await expect(page.getByText("Event stream")).toBeVisible();
  await page.getByRole("button", { name: "Take over" }).click();
  await expect(page.getByText(/human help/i)).toBeVisible();
});
