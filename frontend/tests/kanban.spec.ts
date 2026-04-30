import { expect, test } from "@playwright/test";

const signIn = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
};

test("requires sign in before showing the board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).not.toBeVisible();
});

test("shows an error for invalid login", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Username").fill("wrong");
  await page.getByLabel("Password").fill("credentials");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByText("Invalid username or password.")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).not.toBeVisible();
});

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await page.reload();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("logs out after successful login", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Kanban Studio" })
  ).not.toBeVisible();
});

test("persists a column rename after reload", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  const titleInput = firstColumn.getByLabel("Column title");

  await titleInput.fill("Ideas");
  await titleInput.press("Enter");
  await expect(titleInput).toHaveValue("Ideas");

  await page.reload();
  await expect(firstColumn.getByLabel("Column title")).toHaveValue("Ideas");
});

test("asks the AI a question without changing the board", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/ai/chat", async (route) => {
    const boardResponse = await page.request.get("http://127.0.0.1:8010/api/board");
    const board = await boardResponse.json();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        message: "The board has five active columns.",
        appliedUpdates: [],
        board,
      }),
    });
  });

  await page.getByLabel("Message").fill("Summarize the board");
  await page.getByRole("button", { name: /send to ai/i }).click();

  await expect(page.getByText("The board has five active columns.")).toBeVisible();
});

test("refreshes the board when the AI updates it", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/ai/chat", async (route) => {
    const createResponse = await page.request.post("http://127.0.0.1:8010/api/cards", {
      data: {
        columnId: "col-backlog",
        title: "AI e2e card",
        details: "Created from mocked AI chat.",
      },
    });
    const board = await createResponse.json();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        message: "I added the requested card.",
        appliedUpdates: [{ type: "create_card", summary: "Created card 'AI e2e card'." }],
        board,
      }),
    });
  });

  await page.getByLabel("Message").fill("Create an AI e2e card");
  await page.getByRole("button", { name: /send to ai/i }).click();

  await expect(page.getByText("I added the requested card.")).toBeVisible();
  await expect(page.getByText("Created card 'AI e2e card'.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "AI e2e card" })).toBeVisible();
});
