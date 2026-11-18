const { test, expect } = require("@playwright/test");

const baseUrl = process.env.ELMS_BROWSER_BASE_URL || "http://127.0.0.1:8000";

test.describe("B2B admission confirmation", () => {
	test("renders the company admission controls", async ({ page }) => {
		await page.goto(`${baseUrl}/app/elms-learning`);
		await expect(page.locator("[data-b2b-admission]")).toBeVisible();
		await expect(page.locator("[data-admission-preview-action]")).toBeVisible();
		await expect(page.locator("[data-admission-confirm]")).toBeDisabled();
	});

	test("confirms a parsed import and shows the result report", async ({ page }) => {
		const importId = process.env.ELMS_B2B_IMPORT_ID;
		test.skip(!importId, "ELMS_B2B_IMPORT_ID must point to a parsed fixture import");

		await page.goto(`${baseUrl}/app/elms-learning`);
		await page.locator("[data-admission-import]").fill(importId);
		await page.locator("[data-admission-preview-action]").click();
		await expect(page.locator("[data-admission-preview]")).toContainText("Осталось мест");
		await expect(page.locator("[data-admission-confirm]")).toBeEnabled();

		await page.locator("[data-admission-confirm]").click();
		await expect(page.locator("[data-admission-result]")).toContainText("Зачислено");
	});
});
