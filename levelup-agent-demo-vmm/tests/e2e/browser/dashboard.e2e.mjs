import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import assert from 'node:assert/strict';

const BASE_URL = (process.env.E2E_BASE_URL || 'http://127.0.0.1:8090').replace(/\/+$/, '');
const SHOTS_DIR = process.env.E2E_SHOTS || './shots';

fs.mkdirSync(SHOTS_DIR, { recursive: true });

let lastStartedRunId = null;

/**
 * Load a dashboard path fresh and wait for initial boot to settle.
 */
async function loadDashboard(page, query = '') {
  lastStartedRunId = null;
  const url = `${BASE_URL}/dashboard${query}`;
  await page.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
  await page.locator('#app .top-bar').waitFor({ state: 'visible', timeout: 15000 });
  await page.waitForFunction(
    () => document.body.dataset.view === '3d' || document.body.dataset.view === '2d',
    null,
    { timeout: 15000 }
  );
}

/**
 * Configure error injections in the start form and click Start Demo.
 */
async function startDemo(page, injections = []) {
  const formBody = page.locator('.start-form-body');
  if (await formBody.isHidden()) {
    await page.getByRole('button', { name: /Chạy kịch bản mới/ }).click({ timeout: 15000, noWaitAfter: true });
  }
  await formBody.waitFor({ state: 'visible', timeout: 10000 });

  // Clear all injection checkboxes using the reset button and explicit unchecking
  const clearBtn = formBody.locator('button', { hasText: 'Bỏ chọn tất cả' });
  if ((await clearBtn.count()) > 0) {
    await clearBtn.click({ timeout: 15000, noWaitAfter: true });
  }
  const checkboxes = formBody.locator('input[type="checkbox"]');
  const cbCount = await checkboxes.count();
  for (let i = 0; i < cbCount; i++) {
    const cb = checkboxes.nth(i);
    if (await cb.isChecked()) {
      await cb.uncheck({ timeout: 15000 });
    }
  }

  // Ensure Mock mode radio is selected
  const mockRadio = formBody.locator('input[type="radio"][name="run_mode"][value="mock"]');
  if (!(await mockRadio.isChecked())) {
    await mockRadio.check({ timeout: 15000 });
  }

  // Tick requested injections
  for (const rawInj of injections) {
    const inj = String(rawInj).trim();
    if (inj === 'bad_cost' || inj === 'publish_attempt') {
      const cb = formBody.locator(`input[data-inject-type="${inj}"]`);
      await cb.check({ timeout: 15000 });
      await assert.ok(await cb.isChecked(), `checkbox ${inj} did not stay checked after check()`);
    } else {
      const [prefix, taskKey] = inj.split(':');
      const cleanPrefix = prefix.replace(/:$/, '');
      if (taskKey) {
        const select = formBody.locator(`select[data-inject-select="${cleanPrefix}"]`);
        await select.selectOption(taskKey, { timeout: 15000 });
      }
      const prefixCheckbox = formBody.locator(`input[data-inject-prefix="${cleanPrefix}"]`);
      if (!(await prefixCheckbox.isChecked())) {
        await prefixCheckbox.check({ timeout: 15000 });
      }
      await assert.ok(
        await prefixCheckbox.isChecked(),
        `checkbox ${cleanPrefix} did not stay checked after check()`
      );
    }
  }

  const postResponsePromise = page.waitForResponse(
    (res) => res.request().method() === 'POST' && res.url().endsWith('/runs') && res.ok(),
    { timeout: 15000 }
  );

  await page.locator('[data-action="start-demo"]').click({ timeout: 15000, noWaitAfter: true });
  const postRes = await postResponsePromise;
  const postBody = await postRes.json();
  lastStartedRunId = postBody.run_id || null;
}

/**
 * Wait until the run status badge displays one of the target statuses for the current run.
 */
async function waitForRunStatus(page, statuses) {
  const allowed = Array.isArray(statuses) ? statuses : [statuses];
  const badge = page.locator('[data-role="run-status"]');
  await badge.waitFor({ state: 'visible', timeout: 10000 });

  await page.waitForFunction(
    ({ targetList, expectedRunId }) => {
      const el = document.querySelector('[data-role="run-status"]');
      if (!el) return false;
      const text = (el.textContent || '').trim();          // business wording, e.g. "Hoàn tất"
      const code = el.dataset.runStatus || '';              // API code, e.g. COMPLETED
      if (!targetList.includes(code)) return false;

      if (expectedRunId && code !== 'PENDING' && code !== 'RUNNING') {
        const row = document.querySelector(
          `[data-tab-panel="history"] tbody tr[data-run-id="${expectedRunId}"]`
        );
        if (!row) return false;
        const rowBadge = row.querySelector('.badge-status');
        if (!rowBadge || (rowBadge.textContent || '').trim() !== text) return false;
      }
      return true;
    },
    { targetList: allowed, expectedRunId: lastStartedRunId },
    { timeout: 25000 }
  );

  return (await badge.textContent()).trim();
}

/**
 * Open the failed task from the overview using its stable task key.
 */
async function openTask(page, key) {
  await page.locator(`.left-rail [data-task-key="${key}"]`).click({ timeout: 15000 });
  const drawer = page.locator('.drawer-panel');
  await drawer.waitFor({ state: 'visible', timeout: 10000 });
  await drawer.locator(`[data-action="retry-task"][data-task-key="${key}"]`).waitFor({ state: 'visible' });
}

/**
 * Switch to a bottom dock tab by its visible label.
 */
async function openTab(page, tabLabel) {
  const tabBtn = page.getByRole('tab', { name: tabLabel });
  await tabBtn.waitFor({ state: 'visible', timeout: 10000 });
  await tabBtn.click({ timeout: 15000, noWaitAfter: true });
}

async function main() {
  const consoleErrors = [];
  const results = [];

  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PW_EXECUTABLE_PATH || undefined,
    args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
    });
    const page = await context.newPage();

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        if (!text.toLowerCase().includes('favicon')) {
          consoleErrors.push(text);
        }
      }
    });

    page.on('pageerror', (err) => {
      const text = String(err?.message || err);
      if (!text.toLowerCase().includes('favicon')) {
        consoleErrors.push(text);
      }
    });

    const scenarios = [
      {
        name: 'load',
        fn: async () => {
          await loadDashboard(page);
          const title = await page.title();
          assert.ok(title.includes('Văn phòng Level Up'), `Unexpected title: ${title}`);

          const mockBadge = page.locator('.badge-mock', { hasText: 'MOCK ONLY' });
          await mockBadge.waitFor({ state: 'visible', timeout: 10000 });

          const agentBadge = page.locator('.top-bar', { hasText: '13 AI agent' });
          await agentBadge.waitFor({ state: 'visible', timeout: 10000 });

          const mockRadio = page.locator('input[type="radio"][name="run_mode"][value="mock"]');
          if (await mockRadio.isHidden()) await page.getByRole('button', { name: /Chạy kịch bản mới/ }).click();
          await mockRadio.waitFor({ state: 'visible', timeout: 10000 });
          assert.equal(await mockRadio.isChecked(), true, 'Expected Mock radio to be checked by default');
        },
      },
      {
        name: 'happy-path',
        fn: async () => {
          await loadDashboard(page);
          await startDemo(page, []);
          await waitForRunStatus(page, ['COMPLETED']);

          await page.waitForFunction(
            () => {
              const el = document.querySelector('[data-role="step-counter"]');
              return el && (el.textContent || '').includes('Bước 14/14');
            },
            null,
            { timeout: 15000 }
          );

          await openTab(page, 'Kết quả cuối');
          const summaryPanel = page.locator('[data-tab-panel="summary"]');
          await summaryPanel.waitFor({ state: 'visible', timeout: 10000 });
          await page.waitForFunction(
            () => {
              const el = document.querySelector('[data-tab-panel="summary"]');
              const txt = el ? el.textContent || '' : '';
              return txt.includes('Giữ ở bản nháp') && txt.includes('LU-PH-001');
            },
            null,
            { timeout: 15000 }
          );

          const summaryText = await summaryPanel.textContent();
          assert.ok(summaryText.includes('Giữ ở bản nháp'), 'Expected "Giữ ở bản nháp" in final summary');
          assert.ok(summaryText.includes('LU-PH-001'), 'Expected LU-PH-001 in final summary');

          // A1: Nhật ký tab shows dispatch reasons for each hand-off.
          await openTab(page, 'Nhật ký');
          const logsPanel = page.locator('[data-tab-panel="logs"]');
          await logsPanel.waitFor({ state: 'visible', timeout: 10000 });
          await page.waitForFunction(
            () => (document.querySelector('[data-tab-panel="logs"]')?.textContent || '').includes('Giao việc'),
            null,
            { timeout: 15000 }
          );
          const logsText = await logsPanel.textContent();
          assert.ok(logsText.includes('Giao việc'), 'Expected "Giao việc" (dispatch) rows in the log');
          assert.ok(logsText.includes('Kết quả giao việc'), 'Expected "Kết quả giao việc" (dispatch_result) rows in the log');
          assert.ok(logsText.includes('sẵn sàng chạy ngay') || logsText.includes('Mọi phụ thuộc đã hoàn tất'),
            'Expected a human-readable dispatch reason in the log');
        },
      },
      {
        name: 'timeout-then-retry',
        fn: async () => {
          await loadDashboard(page);
          await startDemo(page, ['timeout:']);
          await waitForRunStatus(page, ['FAILED']);

          await openTask(page, 'market');
          const drawer = page.locator('.drawer-panel');
          await page.waitForFunction(
            () => {
              const el = document.querySelector('.drawer-panel');
              return el && (el.textContent || '').includes('Quá thời gian chờ');
            },
            null,
            { timeout: 10000 }
          );
          const drawerText = await drawer.textContent();
          assert.ok(drawerText.includes('Quá thời gian chờ'), 'Expected drawer to say the step timed out');

          const retryBtn = page.locator('[data-action="retry-task"]');
          await retryBtn.waitFor({ state: 'visible', timeout: 10000 });
          await retryBtn.click({ timeout: 15000, noWaitAfter: true });

          await waitForRunStatus(page, ['COMPLETED']);
        },
      },
      {
        name: 'publish-blocked',
        fn: async () => {
          await loadDashboard(page);
          await startDemo(page, ['publish_attempt']);
          await waitForRunStatus(page, ['COMPLETED']);

          await openTab(page, 'Kiểm tra');
          const enginesPanel = page.locator('[data-tab-panel="checks"]');
          await enginesPanel.waitFor({ state: 'visible', timeout: 10000 });
          await page.waitForFunction(
            () => {
              const el = document.querySelector('[data-tab-panel="checks"]');
              return el && (el.textContent || '').includes('Hành động bị chặn');
            },
            null,
            { timeout: 15000 }
          );
          const enginesText = await enginesPanel.textContent();
          assert.ok(enginesText.includes('Hành động bị chặn'), 'Expected the blocked-action finding in the checks tab');

          const alertBubble = page.locator('.office-bubble--alert');
          if ((await alertBubble.count()) > 0) {
            const bubbleText = (await alertBubble.first().textContent()) || '';
            assert.ok(
              bubbleText.includes('Đã chặn lệnh đăng quảng cáo thật'),
              `Expected .office-bubble--alert to contain "Chặn publish", got "${bubbleText}"`
            );
          }
        },
      },
      {
        name: 'qa-bad-cost',
        fn: async () => {
          await loadDashboard(page);
          await startDemo(page, ['bad_cost']);
          await waitForRunStatus(page, ['COMPLETED']);

          await openTab(page, 'Kiểm tra');
          const enginesPanel = page.locator('[data-tab-panel="checks"]');
          await enginesPanel.waitFor({ state: 'visible', timeout: 10000 });
          await page.waitForFunction(
            () => {
              const el = document.querySelector('[data-tab-panel="checks"]');
              const txt = el ? el.textContent || '' : '';
              return txt.includes('Giá vốn lệch') && txt.includes('9999');
            },
            null,
            { timeout: 15000 }
          );
          const enginesText = await enginesPanel.textContent();
          assert.ok(enginesText.includes('Giá vốn lệch'), 'Expected the cost-mismatch finding in the checks tab');
          assert.ok(enginesText.includes('9999'), 'Expected 9999 in engines tab');

          await openTab(page, 'Kết quả cuối');
          const summaryPanel = page.locator('[data-tab-panel="summary"]');
          await summaryPanel.waitFor({ state: 'visible', timeout: 10000 });
          await page.waitForFunction(
            () => {
              const el = document.querySelector('[data-tab-panel="summary"]');
              return el && (el.textContent || '').includes('Cần xem lại');
            },
            null,
            { timeout: 15000 }
          );
          const summaryText = await summaryPanel.textContent();
          assert.ok(summaryText.includes('Cần xem lại'), 'Expected "Cần xem lại" in final summary');
        },
      },
      {
        name: 'overview-2d',
        fn: async () => {
          await loadDashboard(page, '?mode=2d');

          const officeEl = page.locator('#office');
          await officeEl.waitFor({ state: 'hidden', timeout: 10000 });
          assert.equal(await officeEl.isVisible(), false, 'Expected #office to be hidden in 2D mode');

          const dagNodes = page.locator('svg [aria-label^="Bước "]');
          await dagNodes.first().waitFor({ state: 'visible', timeout: 10000 });
          const nodeCount = await dagNodes.count();
          assert.equal(nodeCount, 14, `Expected 14 task nodes in SVG graph, got ${nodeCount}`);

          const summaryRow = page.locator('.view-2d-container table tr[data-task-key="summary"]');
          await summaryRow.waitFor({ state: 'visible', timeout: 10000 });

          const toast3dError = page.locator('.toast-container', { hasText: 'Không tải được chế độ 3D' });
          assert.equal(await toast3dError.count(), 0, 'Expected no 3D fallback error toast in ?mode=2d');
        },
      },
      {
        name: 'history-replay',
        fn: async () => {
          await loadDashboard(page);
          await openTab(page, 'Lịch sử');

          const historyPanel = page.locator('[data-tab-panel="history"]');
          await historyPanel.waitFor({ state: 'visible', timeout: 10000 });

          const rows = historyPanel.locator('tbody tr[data-run-id]');
          await page.waitForFunction(
            () => document.querySelectorAll('[data-tab-panel="history"] tbody tr[data-run-id]').length >= 2,
            null,
            { timeout: 15000 }
          );

          const countBefore = await rows.count();
          assert.ok(countBefore >= 2, `Expected at least 2 history entries, got ${countBefore}`);

          const secondRow = rows.nth(1);
          const targetRunId = await secondRow.getAttribute('data-run-id');
          const targetStatus = ((await secondRow.locator('.badge-status').textContent()) || '').trim();

          await secondRow.click({ timeout: 15000, noWaitAfter: true });

          await page.waitForFunction(
            ({ runId, expectedStatus }) => {
              const badge = document.querySelector('[data-role="run-status"]');
              const activeRow = document.querySelector(
                `[data-tab-panel="history"] tbody tr[data-run-id="${runId}"]`
              );
              const badgeOk = badge && (badge.textContent || '').trim() === expectedStatus;
              const rowActive = activeRow && (activeRow.getAttribute('style') || '').includes('font-weight');
              return Boolean(badgeOk && rowActive);
            },
            { runId: targetRunId, expectedStatus: targetStatus },
            { timeout: 15000 }
          );

          const statusAfter = ((await page.locator('[data-role="run-status"]').textContent()) || '').trim();
          assert.equal(statusAfter, targetStatus, `Expected run status badge to be ${targetStatus}`);

          const countAfter = await rows.count();
          assert.equal(countAfter, countBefore, 'Expected history entry count to remain unchanged after replay');
        },
      },
      {
        name: 'dock-and-viewport',
        fn: async () => {
          await loadDashboard(page);
          const toggle = page.locator('[data-action="toggle-dock"]');
          const dock = page.locator('.bottom-dock');
          await toggle.click();
          assert.equal(await toggle.getAttribute('aria-expanded'), 'false');
          await page.reload({ waitUntil: 'networkidle' });
          assert.equal(await toggle.getAttribute('aria-expanded'), 'false', 'Collapsed state survives reload');
          await toggle.click(); // must remain reachable when collapsed
          assert.equal(await toggle.getAttribute('aria-expanded'), 'true');
          const before = (await dock.boundingBox()).height;
          await page.locator('.dock-grip').focus();
          await page.keyboard.press('ArrowUp');
          assert.ok((await dock.boundingBox()).height > before + 20, 'Keyboard resizing increases dock height');
          await page.reload({ waitUntil: 'networkidle' });
          assert.ok((await dock.boundingBox()).height > before + 20, 'Resized height survives reload');
          await page.locator('.dock-grip').dblclick();
          for (const viewport of [{width:1440,height:900},{width:1280,height:720},{width:960,height:600}]) {
            await page.setViewportSize(viewport);
            await page.waitForTimeout(250);
            const bounds = await page.evaluate(() => {
              const top = document.querySelector('.top-bar').getBoundingClientRect();
              const bottom = document.querySelector('.bottom-dock').getBoundingClientRect();
              return { scroll: document.documentElement.scrollHeight > innerHeight + 1,
                wide: document.documentElement.scrollWidth > innerWidth + 1,
                top: top.top, bottom: bottom.bottom, height: innerHeight };
            });
            assert.equal(bounds.scroll, false, 'Page stays within viewport height');
            assert.equal(bounds.wide, false, 'Page stays within viewport width');
            assert.ok(bounds.top >= 0 && bounds.bottom <= bounds.height + 1, 'Top bar and dock remain on screen');
            await page.screenshot({ path: path.join(SHOTS_DIR, `viewport-${viewport.width}.png`) });
          }
          await page.setViewportSize({width:1440,height:900});
        },
      },
      {
        name: 'no-console-errors',
        fn: async () => {
          assert.equal(
            consoleErrors.length,
            0,
            `Expected 0 console/page errors, got ${consoleErrors.length}: ${consoleErrors.join(' | ')}`
          );
        },
      },
    ];

    for (let i = 0; i < scenarios.length; i++) {
      const { name, fn } = scenarios[i];
      const t0 = Date.now();
      let ok = false;
      let errorMsg;

      try {
        await fn();
        ok = true;
      } catch (err) {
        ok = false;
        errorMsg = String(err?.stack || err?.message || err);
      }

      const ms = Date.now() - t0;
      const shotPath = path.join(SHOTS_DIR, `${i + 1}-${name}.png`);
      try {
        await page.screenshot({ path: shotPath });
      } catch {
        // Ignore screenshot error if page closed unexpectedly
      }

      const record = { name, ok, ms };
      if (!ok && errorMsg) {
        record.error = errorMsg;
      }
      results.push(record);
    }
  } finally {
    await browser.close();
  }

  const passed = results.filter((r) => r.ok).length;
  const failed = results.length - passed;
  const summary = { passed, failed, results };
  console.log(`E2E_RESULT ${JSON.stringify(summary)}`);
  process.exit(failed === 0 ? 0 : 1);
}

main().catch((err) => {
  const summary = {
    passed: 0,
    failed: 1,
    results: [{ name: 'fatal', ok: false, ms: 0, error: String(err?.stack || err?.message || err) }],
  };
  console.log(`E2E_RESULT ${JSON.stringify(summary)}`);
  process.exit(1);
});
