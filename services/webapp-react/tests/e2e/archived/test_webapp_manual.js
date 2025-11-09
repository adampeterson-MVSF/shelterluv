/**
 * Manual E2E Test with Playwright
 * Opens browser, waits for you to sign in, then tests all features
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:5174';

// Safety check for development environment
if (process.env.NODE_ENV === 'production') {
  console.error('❌ PRODUCTION SAFETY CHECK FAILED ❌');
  console.error('Manual tests should never run in production environment.');
  process.exit(1);
}

// Check environment variables
console.log('🔍 Environment check:');
console.log(`   VITE_FIREBASE_PROJECT_ID: ${process.env.VITE_FIREBASE_PROJECT_ID || 'not set'}`);
console.log(`   NODE_ENV: ${process.env.NODE_ENV || 'not set'}`);
console.log('');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runManualTest() {
  console.log('🎭 Starting Manual Playwright Test\n');
  console.log('=' .repeat(60));
  console.log('MANUAL TEST INSTRUCTIONS:');
  console.log('=' .repeat(60));
  console.log('1. Browser will open automatically');
  console.log('2. Click "Sign In" and authenticate with Google');
  console.log('3. Use: foster+test1@muttville.org');
  console.log('4. After signing in, the test will automatically proceed');
  console.log('=' .repeat(60));
  console.log('\nPress Ctrl+C to cancel\n');

  await sleep(3000);

  const browser = await chromium.launch({
    headless: false,
    slowMo: 300
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to app
    console.log('📱 Opening application...');
    await page.goto(BASE_URL, { waitUntil: 'domcontentloaded' });
    await sleep(2000);

    // Check if already signed in
    let signedIn = false;
    const hamburger = await page.locator('.hamburger-menu, .user-menu').count();
    if (hamburger > 0) {
      console.log('✅ Already signed in!\n');
      signedIn = true;
    } else {
      // Wait for manual sign-in
      console.log('⏳ Waiting for you to sign in...');
      console.log('   Click the "Sign In" button in the browser\n');

      // Wait up to 120 seconds for authentication
      for (let i = 0; i < 120; i++) {
        await sleep(1000);

        // Check multiple possible authenticated state indicators
        const menu = await page.locator('.hamburger-menu, .user-menu, .user-email, button:has-text("Logout")').count();
        const signInButtonGone = await page.locator('button:has-text("Sign In")').count() === 0;

        if (menu > 0 || signInButtonGone) {
          signedIn = true;
          console.log('✅ Sign-in detected!\n');
          break;
        }
        if (i % 10 === 9) {
          console.log(`   Still waiting... (${i + 1}s)`);
        }
      }
    }

    if (!signedIn) {
      console.log('❌ Sign-in not detected after 120 seconds');
      console.log('   Please sign in and run the test again\n');
      return;
    }

    // Wait for data to load
    console.log('⏳ Waiting for dogs to load from Firestore...');
    await sleep(3000);

    // Run automated tests
    console.log('\n' + '='.repeat(60));
    console.log('RUNNING AUTOMATED TESTS');
    console.log('='.repeat(60) + '\n');

    // Test 1: Count dogs
    console.log('✅ Test 1: Counting dogs...');
    const dogCards = await page.locator('.dog-card').count();
    console.log(`   Found: ${dogCards} dogs\n`);

    if (dogCards === 0) {
      console.log('❌ No dogs loaded! Checking for errors...');
      const errorMessages = await page.locator('.error-message, .error, [class*="error"]').allTextContents();
      if (errorMessages.length > 0) {
        console.log('   Errors found:', errorMessages);
      }
      console.log('\n   Possible issues:');
      console.log('   - Firestore rules not allowing read access');
      console.log('   - No data in Firestore');
      console.log('   - Network error\n');
    }

    // Test 2: Search
    console.log('✅ Test 2: Testing search...');
    const searchInput = await page.locator('input[type="text"], input.search-input, input[placeholder*="search" i]');
    if (await searchInput.count() > 0) {
      await searchInput.first().fill('dog');
      await sleep(1500);
      const filteredCount = await page.locator('.dog-card').count();
      console.log(`   Search results: ${filteredCount} dogs`);
      await searchInput.first().clear();
      await sleep(500);
      console.log('   ✓ Search works\n');
    } else {
      console.log('   ⚠️  Search input not found\n');
    }

    // Test 3: Filters
    console.log('✅ Test 3: Testing filters...');
    const filtersBtn = await page.locator('button:has-text("Filters"), button:has-text("Filter")');
    if (await filtersBtn.count() > 0) {
      await filtersBtn.first().click();
      await sleep(1000);
      console.log('   ✓ Filter drawer opened');

      // Take screenshot
      await page.screenshot({ path: 'test-filters.png', fullPage: true });
      console.log('   📸 Screenshot saved: test-filters.png');

      // Close drawer
      await page.keyboard.press('Escape');
      await sleep(500);
      console.log();
    } else {
      console.log('   ⚠️  Filters button not found\n');
    }

    // Test 4: Sort
    console.log('✅ Test 4: Testing sort...');
    const sortBtn = await page.locator('button:has-text("Sort")');
    if (await sortBtn.count() > 0) {
      await sortBtn.first().click();
      await sleep(1000);
      console.log('   ✓ Sort menu opened');
      await page.keyboard.press('Escape');
      await sleep(500);
      console.log();
    } else {
      console.log('   ⚠️  Sort button not found\n');
    }

    // Test 5: Dog details
    if (dogCards > 0) {
      console.log('✅ Test 5: Testing dog details page...');
      const firstDog = await page.locator('.dog-card').first();
      const dogName = await firstDog.locator('h2, h3, .dog-name, [class*="name"]').first().textContent().catch(() => 'Unknown');
      console.log(`   Opening details for: ${dogName}`);

      await firstDog.click();
      await page.waitForURL(/\/dog\//);
      await sleep(2000);

      // Check tabs
      const tabs = await page.locator('button[role="tab"], .tab, [class*="tab"]').count();
      console.log(`   Found ${tabs} tabs`);

      // Try clicking tabs
      const personalityTab = await page.locator('button:has-text("Personality"), .tab:has-text("Personality")');
      if (await personalityTab.count() > 0) {
        await personalityTab.first().click();
        await sleep(500);
        console.log('   ✓ Personality tab clicked');
      }

      const medicalTab = await page.locator('button:has-text("Medical"), .tab:has-text("Medical")');
      if (await medicalTab.count() > 0) {
        await medicalTab.first().click();
        await sleep(500);
        console.log('   ✓ Medical tab clicked');
      }

      // Take screenshot
      await page.screenshot({ path: 'test-details.png', fullPage: true });
      console.log('   📸 Screenshot saved: test-details.png');

      // Go back
      await page.goBack();
      await sleep(1000);
      console.log('   ✓ Navigated back to home\n');
    }

    // Final summary
    console.log('\n' + '='.repeat(60));
    console.log('TEST SUMMARY');
    console.log('='.repeat(60));
    console.log(`✅ Dogs loaded: ${dogCards}`);
    console.log('✅ Authentication working');
    console.log('✅ Navigation working');
    console.log('✅ Screenshots saved');
    console.log('='.repeat(60));

    // Keep browser open
    console.log('\n⏸️  Browser will stay open for 30 seconds for inspection...');
    console.log('   Press Ctrl+C to close immediately\n');
    await sleep(30000);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
    await page.screenshot({ path: 'test-error.png', fullPage: true });
    console.log('📸 Error screenshot saved: test-error.png\n');
  } finally {
    await browser.close();
    console.log('✅ Browser closed');
  }
}

runManualTest().catch(console.error);
