/* eslint-env node */
/**
 * Shelterluv animal list explorer (Playwright)
 *
 * Usage:
 *   SHELTERLUV_USER=... SHELTERLUV_PASS=... node services/webapp-react/dev_tools/shelterluv_explorer/explore_animal_list.js [--headed]
 *
 * This script navigates to the ShelterLuv animals dashboard and explores the structure
 * of the animal list/table to identify selectors for scraping animal IDs.
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

function parseArgs(argv) {
  const args = { headed: false };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--headed') args.headed = true;
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

async function login({ page, username, password }) {
  const loginUrl = 'https://new.shelterluv.com/login';
  await page.goto(loginUrl, { waitUntil: 'domcontentloaded' });

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

  // Submit form
  const submitBtn = page.getByRole('button', { name: /log ?in|sign ?in/i });
  if (await submitBtn.count()) {
    await submitBtn.first().click();
  } else {
    await page.keyboard.press('Enter');
  }

  // Wait for post-login
  try {
    await Promise.race([
      page.waitForURL(/new\.shelterluv\.com\//, { timeout: 15000 }),
      page.waitForLoadState('load', { timeout: 15000 })
    ]);
  } catch {}

  await page.screenshot({ path: path.join(__dirname, 'artifacts', 'login-after.png') });
}

async function exploreAnimalList(page, outDir) {
  const results = {
    selectors: {},
    findings: {}
  };

  console.log('🏠 Navigating to animals dashboard...');
  await page.goto("https://new.shelterluv.com/dashboard?tab=animals");
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // Take initial screenshot
  await page.screenshot({ path: path.join(outDir, 'animals-dashboard.png'), fullPage: true });

  // Check for "In Custody View" button
  console.log('👀 Looking for "In Custody View" button...');
  const inCustodyButton = page.getByText("In Custody View");
  if (await inCustodyButton.count() > 0) {
    console.log('🔘 Found "In Custody View" button, clicking...');
    await inCustodyButton.first().click();
    await page.waitForTimeout(2000);
    results.findings.inCustodyButtonFound = true;
  } else {
    console.log('⚠️ "In Custody View" button not found');
    results.findings.inCustodyButtonFound = false;
  }

  // Wait for content to load
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, 'in-custody-view.png'), fullPage: true });

  // Explore different selector strategies
  console.log('🔍 Exploring selectors for animal rows...');

  // Strategy 1: data-cy attributes (current implementation)
  const dataCyRows = page.locator('[data-cy^="animal-row-"]');
  const dataCyCount = await dataCyRows.count();
  console.log(`📊 data-cy rows found: ${dataCyCount}`);
  results.selectors.dataCy = {
    selector: '[data-cy^="animal-row-"]',
    count: dataCyCount,
    sample: dataCyCount > 0 ? await dataCyRows.first().getAttribute('data-cy') : null
  };

  // Strategy 2: Table rows (tbody tr)
  const tableRows = page.locator('tbody tr');
  const tableRowCount = await tableRows.count();
  console.log(`📊 tbody tr rows found: ${tableRowCount}`);
  results.selectors.tableRows = {
    selector: 'tbody tr',
    count: tableRowCount
  };

  // Strategy 3: Rows with specific classes
  const classRows = page.locator('tr[class*="animal"], tr[class*="row"]');
  const classRowCount = await classRows.count();
  console.log(`📊 class-based rows found: ${classRowCount}`);
  results.selectors.classRows = {
    selector: 'tr[class*="animal"], tr[class*="row"]',
    count: classRowCount
  };

  // Strategy 4: Role-based rows
  const roleRows = page.getByRole('row');
  const roleRowCount = await roleRows.count();
  console.log(`📊 role=row rows found: ${roleRowCount}`);
  results.selectors.roleRows = {
    selector: 'getByRole("row")',
    count: roleRowCount
  };

  // Strategy 5: Links containing animal URLs
  const animalLinks = page.locator('a[href*="/animal/"]');
  const animalLinkCount = await animalLinks.count();
  console.log(`📊 animal links found: ${animalLinkCount}`);
  results.selectors.animalLinks = {
    selector: 'a[href*="/animal/"]',
    count: animalLinkCount,
    sampleHrefs: []
  };

  // Get sample hrefs
  for (let i = 0; i < Math.min(animalLinkCount, 3); i++) {
    const href = await animalLinks.nth(i).getAttribute('href');
    results.selectors.animalLinks.sampleHrefs.push(href);
  }

  // Strategy 6: Look for Muttville ID patterns (MVSF-A-)
  const muttvilleTexts = page.locator('text=/MVSF-A-/');
  const muttvilleCount = await muttvilleTexts.count();
  console.log(`📊 Muttville ID texts found: ${muttvilleCount}`);
  results.selectors.muttvilleTexts = {
    selector: 'text=/MVSF-A-/',
    count: muttvilleCount
  };

  // Strategy 7: Look for data-testid attributes
  const testIdElements = page.locator('[data-testid]');
  const testIdCount = await testIdElements.count();
  console.log(`📊 data-testid elements found: ${testIdCount}`);
  results.selectors.testIdElements = {
    selector: '[data-testid]',
    count: testIdCount,
    sampleTestIds: []
  };

  // Get sample test IDs
  for (let i = 0; i < Math.min(testIdCount, 5); i++) {
    const testId = await testIdElements.nth(i).getAttribute('data-testid');
    results.selectors.testIdElements.sampleTestIds.push(testId);
  }

  // Check if there's pagination
  const paginationElements = page.locator('.pagination, [aria-label*="pagination"], nav[aria-label*="pagination"]');
  const paginationCount = await paginationElements.count();
  console.log(`📊 pagination elements found: ${paginationCount}`);
  results.findings.pagination = {
    count: paginationCount,
    selectors: ['.pagination', '[aria-label*="pagination"]', 'nav[aria-label*="pagination"]']
  };

  // Look for "Next" buttons
  const nextButtons = page.locator('button:has-text("Next"), [aria-label*="next"], .pagination .next');
  const nextButtonCount = await nextButtons.count();
  console.log(`📊 next buttons found: ${nextButtonCount}`);
  results.findings.nextButtons = {
    count: nextButtonCount,
    selectors: ['button:has-text("Next")', '[aria-label*="next"]', '.pagination .next']
  };

  // Take a detailed screenshot of the first few rows
  if (tableRowCount > 0) {
    console.log('📸 Taking detailed screenshot of table structure...');
    const firstRow = tableRows.first();
    await firstRow.screenshot({ path: path.join(outDir, 'first-row.png') });
  }

  return results;
}

async function main() {
  const { headed } = parseArgs(process.argv);

  const username = requireEnv('SHELTERLUV_USER');
  const password = requireEnv('SHELTERLUV_PASS');

  const outDir = path.join(__dirname, 'artifacts');
  await ensureDir(outDir);

  const browser = await chromium.launch({ headless: !headed, slowMo: headed ? 150 : 0 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('🔐 Logging in to ShelterLuv...');
    await login({ page, username, password });

    console.log('🔍 Exploring animal list structure...');
    const results = await exploreAnimalList(page, outDir);

    const outJson = path.join(outDir, 'animal_list_selectors.json');
    await fs.promises.writeFile(outJson, JSON.stringify(results, null, 2));
    console.log(`\n✅ Results written: ${outJson}`);

    // Print summary
    console.log('\n📋 SUMMARY:');
    console.log(`- In Custody View button found: ${results.findings.inCustodyButtonFound}`);
    console.log(`- Best animal row selector: ${Object.entries(results.selectors)
      .filter(([k, v]) => k !== 'animalLinks' && k !== 'testIdElements')
      .sort((a, b) => b[1].count - a[1].count)[0]?.[0] || 'none'}`);
    console.log(`- Animal links found: ${results.selectors.animalLinks.count}`);
    console.log(`- Muttville IDs visible: ${results.selectors.muttvilleTexts.count}`);
    console.log(`- Pagination detected: ${results.findings.pagination.count > 0}`);

  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error(err.message);
  process.exit(1);
});
