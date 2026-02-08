import { test, expect } from "@playwright/test";

const BASE = "http://localhost:5176";
const API = "http://localhost:8000/api";

// ── Navigation & Page Load ───────────────────────────────────────────────────

test.describe("Navigation", () => {
  test("homepage loads with nav bar and dashboard", async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator(".brand")).toHaveText("PAT");
    await expect(page.locator("h1")).toHaveText("Portfolio Dashboard");
  });

  test("all nav links are present", async ({ page }) => {
    await page.goto(BASE);
    const nav = page.locator(".nav");
    await expect(nav.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Analytics" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Signals" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Options" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Optimize" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Alerts" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Paper Trade" })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Import" })).toBeVisible();
  });

  test("navigate to each page", async ({ page }) => {
    await page.goto(BASE);

    await page.click('a[href="/analytics"]');
    await expect(page.locator("h1")).toHaveText("Analytics");

    await page.click('a[href="/signals"]');
    await expect(page.locator("h1")).toHaveText("Signal Scanner");

    await page.click('a[href="/options"]');
    await expect(page.locator("h1")).toHaveText("Options & LEAPS");

    await page.click('a[href="/optimize"]');
    await expect(page.locator("h1")).toHaveText("Portfolio Optimizer");

    await page.click('a[href="/alerts"]');
    await expect(page.locator("h1")).toHaveText("Alerts");

    await page.click('a[href="/paper"]');
    await expect(page.locator("h1")).toHaveText("Paper Trading");

    await page.click('a[href="/import"]');
    await expect(page.locator("h1")).toHaveText("Import Portfolio");
  });
});

// ── Dashboard ────────────────────────────────────────────────────────────────

test.describe("Dashboard", () => {
  test("shows empty state when no positions", async ({ page }) => {
    await page.goto(BASE);
    await expect(
      page.getByText("No open positions")
    ).toBeVisible({ timeout: 10000 });
  });
});

// ── Alerts ───────────────────────────────────────────────────────────────────

test.describe("Alerts", () => {
  test("create and delete an alert", async ({ page }) => {
    await page.goto(`${BASE}/alerts`);
    await expect(page.locator("h1")).toHaveText("Alerts");

    // Create alert
    await page.fill('input[placeholder="Symbol"]', "AAPL");
    await page.fill('input[placeholder="Threshold"]', "200");
    await page.fill('input[placeholder="Note (optional)"]', "Test alert");
    await page.click("text=Add Alert");

    // Verify it appears in the table
    await expect(page.locator("table")).toBeVisible({ timeout: 5000 });
    await expect(page.locator("td.symbol")).toHaveText("AAPL");

    // Delete it
    await page.click(".del-btn");
    await expect(page.getByText("No alerts yet")).toBeVisible({ timeout: 5000 });
  });

  test("check alerts button works", async ({ page }) => {
    await page.goto(`${BASE}/alerts`);

    // Create alert first
    await page.fill('input[placeholder="Symbol"]', "MSFT");
    await page.fill('input[placeholder="Threshold"]', "500");
    await page.click("text=Add Alert");
    await expect(page.locator("table")).toBeVisible({ timeout: 5000 });

    // Check alerts
    await page.click("text=Check All Alerts");
    await expect(page.locator(".check-results")).toBeVisible({ timeout: 15000 });

    // Cleanup
    await page.click(".del-btn");
  });
});

// ── Paper Trading ────────────────────────────────────────────────────────────

test.describe("Paper Trading", () => {
  test.beforeAll(async ({ request }) => {
    // Reset paper account so tests start from a clean $100k state
    await request.post(`${API}/paper/reset`);
  });

  test("shows default account with $100k", async ({ page }) => {
    await page.goto(`${BASE}/paper`);
    await expect(page.locator("h1")).toHaveText("Paper Trading");
    await expect(page.getByText("$100,000.00")).toBeVisible({ timeout: 10000 });
  });

  test("open and close a paper trade", async ({ page }) => {
    await page.goto(`${BASE}/paper`);
    await expect(page.getByText("$100,000.00").first()).toBeVisible({ timeout: 10000 });

    // Open a trade
    await page.fill('input[placeholder="Symbol"]', "AAPL");
    await page.fill('input[placeholder="Qty"]', "10");
    await page.fill('input[placeholder="Entry $"]', "150");
    await page.click(".trade-btn");

    // Verify open trade appears
    await expect(page.getByRole("heading", { name: "Open Positions" })).toBeVisible({ timeout: 5000 });
    await expect(page.locator("table td.symbol").first()).toHaveText("AAPL");

    // Close the trade
    await page.fill('input[placeholder="Exit $"]', "160");
    await page.click(".close-btn");

    // Verify trade history appears
    await expect(page.locator("text=Trade History")).toBeVisible({ timeout: 5000 });
  });
});

// ── Import ───────────────────────────────────────────────────────────────────

test.describe("Import", () => {
  test("import page loads with upload form", async ({ page }) => {
    await page.goto(`${BASE}/import`);
    await expect(page.locator("h1")).toHaveText("Import Portfolio");
    await expect(page.locator('input[type="file"]')).toBeVisible();
    await expect(page.locator(".import-btn")).toBeVisible();
  });
});

// ── Optimize ─────────────────────────────────────────────────────────────────

test.describe("Optimize", () => {
  test("optimize page loads with input and button", async ({ page }) => {
    await page.goto(`${BASE}/optimize`);
    await expect(page.locator("h1")).toHaveText("Portfolio Optimizer");
    await expect(page.locator(".symbols-input")).toBeVisible();
    await expect(page.locator(".opt-btn")).toHaveText("Optimize");
  });
});

// ── Analytics ────────────────────────────────────────────────────────────────

test.describe("Analytics", () => {
  test("analytics page loads", async ({ page }) => {
    await page.goto(`${BASE}/analytics`);
    await expect(page.locator("h1")).toHaveText("Analytics");
  });
});

// ── Backend Health ───────────────────────────────────────────────────────────

test.describe("Backend API", () => {
  test("health endpoint returns ok", async ({ request }) => {
    const resp = await request.get(`${API}/health`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe("ok");
  });

  test("CORS headers present", async ({ request }) => {
    const resp = await request.get(`${API}/health`, {
      headers: { Origin: "http://localhost:5176" },
    });
    expect(resp.ok()).toBeTruthy();
    expect(resp.headers()["access-control-allow-origin"]).toBe("*");
  });
});
