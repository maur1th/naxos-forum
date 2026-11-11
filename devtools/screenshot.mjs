// Usage: node screenshot.mjs [path] [out.png] [--mobile] [--login]
// Takes a screenshot of a forum page for quick visual checks while doing
// frontend work. Run `./seed.sh` once first if you need --login.
import { chromium, devices } from 'playwright';

const args = process.argv.slice(2);
const flags = new Set(args.filter((a) => a.startsWith('--')));
const [path = '/', out = 'shot.png'] = args.filter((a) => !a.startsWith('--'));
const base = process.env.FORUM_URL || 'http://localhost:8081';

const browser = await chromium.launch();
const context = await browser.newContext(
  flags.has('--mobile') ? { ...devices['Pixel 7'] } : { viewport: { width: 1280, height: 800 } },
);
const page = await context.newPage();
page.on('console', (m) => m.type() === 'error' && console.error('console error:', m.text()));
if (flags.has('--login')) {
  await page.goto(`${base}/user/login/`);
  await page.fill('input[name=username]', 'e2e');
  await page.fill('input[name=password]', 'e2e-password');
  await page.click('[type=submit]');
}
await page.goto(base + path);
await page.screenshot({ path: out, fullPage: true });
console.log(`saved ${out} (${page.url()})`);
await browser.close();
