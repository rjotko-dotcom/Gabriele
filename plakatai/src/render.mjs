// Renders each poster HTML to an A4-landscape PDF (and a PNG preview).
// Usage: node render.mjs [name ...]   (names without .html; default: all)
import { chromium } from 'playwright';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.resolve(here, '..');
const all = ['1-ego', '2-bio-my-bio', '3-mocha'];
const names = process.argv.slice(2).length ? process.argv.slice(2) : all;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1123, height: 794 }, deviceScaleFactor: 2 });
for (const name of names) {
  await page.goto(pathToFileURL(path.join(here, `${name}.html`)).href, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const overflow = await page.evaluate(() => {
    const p = document.querySelector('.poster');
    const bad = [];
    for (const el of p.querySelectorAll('*')) {
      if (el.scrollHeight > el.clientHeight + 1 && getComputedStyle(el).overflow !== 'visible') bad.push(el.className || el.tagName);
    }
    return { body: document.body.scrollHeight, bad };
  });
  console.log(name, JSON.stringify(overflow));
  await page.pdf({ path: path.join(out, `${name}.pdf`), width: '297mm', height: '210mm', printBackground: true, preferCSSPageSize: true });
  await page.screenshot({ path: path.join(here, `preview-${name}.png`) });
}
await browser.close();
