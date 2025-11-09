/* eslint-env node */
/**
 * Shelterluv selector explorer (Playwright)
 *
 * Usage:
 *   SHELTERLUV_USER=... SHELTERLUV_PASS=... node services/webapp-react/shelterluv/explore_selectors.js [--dog https://...] [--headed]
 *
 * Notes:
 * - Credentials are read strictly from environment variables; nothing is written to disk.
 * - If a dog URL is provided, the script will open it after login. Otherwise it will
 *   keep the session at the post-login landing page so you can navigate manually.
 * - The script prints recommended, role-based selectors for each tab/section and
 *   saves screenshots under services/webapp-react/shelterluv/artifacts/.
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const DEFAULT_LOGIN_ORIGIN = 'https://new.shelterluv.com';

function parseArgs(argv) {
  const args = { headed: false, dog: process.env.SHELTERLUV_DOG_URL || '' };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--headed') args.headed = true;
    else if (a === '--dog') args.dog = argv[i + 1] || '';
  }
  return args;
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

async function ensureDir(dirPath) {
  await fs.promises.mkdir(dirPath, { recursive: true });
}

async function login({ page, username, password, origin }) {
  const loginUrl = `${origin || DEFAULT_LOGIN_ORIGIN}/login`;
  await page.goto(loginUrl, { waitUntil: 'domcontentloaded' });
  // snapshot for debugging
  try { await page.screenshot({ path: path.join(__dirname, 'artifacts', 'login-form.png') }); } catch {}

  // Try common field names first; fall back to role/name queries
  const userInput = page.locator('input[name="username"], input#username, input[type="email"]');
  const passInput = page.locator('input[name="password"], input#password, input[type="password"]');

  if ((await userInput.count()) === 0 || (await passInput.count()) === 0) {
    // As a fallback, rely on accessible names
    await page.getByLabel(/user(name)?|email/i).first().fill(username);
    await page.getByLabel(/pass(word)?/i).first().fill(password);
  } else {
    await userInput.first().fill(username);
    await passInput.first().fill(password);
  }

  // Submit form (prefer submit button with role)
  const submitBtn = page.getByRole('button', { name: /log ?in|sign ?in/i });
  if (await submitBtn.count()) {
    await submitBtn.first().click();
  } else {
    await page.keyboard.press('Enter');
  }

  // Wait for post-login signal
  try {
    await Promise.race([
      page.waitForURL(/new\.shelterluv\.com\//, { timeout: 15000 }),
      page.waitForLoadState('load', { timeout: 15000 })
    ]);
  } catch {}
  try { await page.screenshot({ path: path.join(__dirname, 'artifacts', 'login-after.png') }); } catch {}
}

function selectorsCatalog() {
  // Use role-based, text-stable selectors. Avoid brittle class/id where possible.
  return {
    tabs: {
      profile: { selector: ["getByRole('tab', { name: 'Profile' })"], note: 'Top tab' },
      behavioral: { selector: ["getByRole('tab', { name: 'Behavioral' })"], note: 'Top tab' },
      medical: { selector: ["getByRole('tab', { name: 'Medical' })"], note: 'Top tab' },
      files: { selector: ["getByRole('tab', { name: 'Files' })"], note: 'Top tab' },
      history: { selector: ["getByRole('tab', { name: 'History' })"], note: 'Top tab' },
      attributes: { selector: ["getByRole('tab', { name: 'Attributes' })"], note: 'Side/accordion tab' },
      memos: { selector: ["getByRole('tab', { name: 'Memos' })"], note: 'Side/accordion tab' }
    },
    behavioral: {
      plan: "getByRole('tab', { name: 'Plan' })",
      assessment: "getByRole('tab', { name: 'Assessment' })",
      playgroups: "getByRole('tab', { name: 'Playgroups' })",
      behaviorChecks: "getByRole('tab', { name: 'Behavior Checks' })"
    },
    medical: {
      summary: "getByRole('tab', { name: 'Summary' })",
      diagnoses: "getByRole('tab', { name: 'Diagnoses' })",
      diagnosticTests: "getByRole('tab', { name: 'Diagnostic Tests' })",
      vaccines: "getByRole('tab', { name: 'Vaccines' })",
      dailyObservations: "getByRole('tab', { name: 'Daily Observations' })",
      physicalExams: "getByRole('tab', { name: 'Physical Exams' })",
      treatments: "getByRole('tab', { name: 'Treatments' })",
      procedures: "getByRole('tab', { name: 'Procedures/Surgeries' })"
    },
    history: {
      intakesOutcomes: "getByRole('tab', { name: 'Intakes/Outcomes' })",
      caretakers: "getByRole('tab', { name: 'Caretakers' })",
      statuses: "getByRole('tab', { name: 'Statuses' })",
      locations: "getByRole('tab', { name: 'Locations' })",
      categories: "getByRole('tab', { name: 'Categories' })",
      profileEdits: "getByRole('tab', { name: 'Profile Edits' })"
    },
    memos: {
      latest: "getByRole('tab', { name: 'Latest' })",
      medical: "getByRole('tab', { name: 'Medical' })",
      newMemoType: "getByRole('combobox', { name: /type/i })",
      templateBtn: "getByRole('button', { name: /template/i })",
      addMemoBtn: "getByRole('button', { name: /add memo/i })",
      memoItems: "getByRole('listitem')"
    },
    attributes: {
      sectionHeading: "getByRole('heading', { name: /Behavioral Attributes/i })",
      pill: `locator('[class*="badge" i], [class*="chip" i]')`,
      editBtn: "getByRole('button', { name: /edit attributes/i })"
    },
    files: {
      addAttachment: "getByRole('button', { name: /add attachment/i })",
      rows: "getByRole('row')",
      nameHeader: "getByRole('columnheader', { name: 'Name' })",
      typeHeader: "getByRole('columnheader', { name: 'Type' })",
      deliveryHeader: "getByRole('columnheader', { name: /Document Delivery/i })"
    }
  };
}

async function clickIfExists(locator) {
  if (await locator.count()) {
    await locator.first().click();
    await locator.page().waitForLoadState('networkidle');
    return true;
  }
  return false;
}

async function explore(page, outDir) {
  const cats = selectorsCatalog();
  const results = { clicked: {}, foundCounts: {} };

  // Top tabs
  for (const k of Object.keys(cats.tabs)) {
    const loc = page.getByRole('tab', { name: new RegExp(k.replace(/([A-Z])/g, ' $1'), 'i') });
    const clicked = await clickIfExists(loc);
    results.clicked[k] = clicked;
    await page.screenshot({ path: path.join(outDir, `tab-${k}.png`), fullPage: true });
  }

  // Behavioral subtabs
  await clickIfExists(page.getByRole('tab', { name: /Behavioral/i }));
  for (const [k, expr] of Object.entries(cats.behavioral)) {
    try {
      // Debug: show expression being evaluated to help stabilize selectors
      console.log(`[selectors] behavioral.${k}: page.${expr}`);
      const loc = eval(`page.${expr}`); // eslint-disable-line no-eval
      const clicked = await clickIfExists(loc);
      results.clicked[`behavioral.${k}`] = clicked;
    } catch (e) {
      console.warn(`Failed to eval behavioral.${k}:`, e.message);
      results.clicked[`behavioral.${k}`] = false;
    }
  }
  await page.screenshot({ path: path.join(outDir, 'behavioral.png'), fullPage: true });

  // Medical subtabs
  await clickIfExists(page.getByRole('tab', { name: /Medical/i }));
  for (const [k, expr] of Object.entries(cats.medical)) {
    try {
      console.log(`[selectors] medical.${k}: page.${expr}`);
      const loc = eval(`page.${expr}`); // eslint-disable-line no-eval
      const clicked = await clickIfExists(loc);
      results.clicked[`medical.${k}`] = clicked;
    } catch (e) {
      console.warn(`Failed to eval medical.${k}:`, e.message);
      results.clicked[`medical.${k}`] = false;
    }
  }
  await page.screenshot({ path: path.join(outDir, 'medical.png'), fullPage: true });

  // Files table
  await clickIfExists(page.getByRole('tab', { name: /Files/i }));
  results.foundCounts.filesRows = await page.getByRole('row').count();
  await page.screenshot({ path: path.join(outDir, 'files.png'), fullPage: true });

  // History subtabs
  await clickIfExists(page.getByRole('tab', { name: /History/i }));
  for (const [k, expr] of Object.entries(cats.history)) {
    try {
      console.log(`[selectors] history.${k}: page.${expr}`);
      const loc = eval(`page.${expr}`); // eslint-disable-line no-eval
      const clicked = await clickIfExists(loc);
      results.clicked[`history.${k}`] = clicked;
    } catch (e) {
      console.warn(`Failed to eval history.${k}:`, e.message);
      results.clicked[`history.${k}`] = false;
    }
  }
  await page.screenshot({ path: path.join(outDir, 'history.png'), fullPage: true });

  // Attributes
  await clickIfExists(page.getByRole('tab', { name: /Attributes/i }));
  results.foundCounts.attributePills = await page.locator('[class*="badge" i], [class*="chip" i]').count();
  await page.screenshot({ path: path.join(outDir, 'attributes.png'), fullPage: true });

  // Memos
  await clickIfExists(page.getByRole('tab', { name: /Memos/i }));
  for (const [k, expr] of Object.entries(cats.memos)) {
    if (k === 'memoItems') continue;
    try {
      console.log(`[selectors] memos.${k}: page.${expr}`);
      const loc = eval(`page.${expr}`); // eslint-disable-line no-eval
      await clickIfExists(loc);
    } catch (e) {
      console.warn(`Failed to eval memos.${k}:`, e.message);
    }
  }
  results.foundCounts.memoItems = await page.getByRole('listitem').count();
  await page.screenshot({ path: path.join(outDir, 'memos.png'), fullPage: true });

  return { selectors: cats, results };
}

async function main() {
  const { headed, dog } = parseArgs(process.argv);

  const username = requireEnv('SHELTERLUV_USER');
  const password = requireEnv('SHELTERLUV_PASS');

  const outDir = path.join(__dirname, 'artifacts');
  await ensureDir(outDir);

  const browser = await chromium.launch({ headless: !headed, slowMo: headed ? 150 : 0 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    let origin = DEFAULT_LOGIN_ORIGIN;
    if (dog) {
      try { origin = new URL(dog).origin; } catch (e) { /* no-op */ }
    }
    await login({ page, username, password, origin });

    if (dog) {
      await page.goto(dog, { waitUntil: 'domcontentloaded' });
      // allow client-side scripts to settle
      await page.waitForTimeout(1000);
    } else {
      console.log('Logged in. Provide --dog <url> to auto-open a profile, or navigate manually.');
      // Give the operator a brief window to navigate if running headed
      if (headed) await page.waitForTimeout(2000);
    }

    const { selectors, results } = await explore(page, outDir);

    const outJson = path.join(outDir, 'selectors.json');
    await fs.promises.writeFile(outJson, JSON.stringify({ selectors, results }, null, 2));
    console.log(`\nSelectors written: ${outJson}`);
  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});


