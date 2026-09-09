// Mirrors features/<slug>/screenshots/*.png into site/public/screenshots/<slug>/ so Astro's
// static publicDir copy (which runs before any page/data code executes) picks them up.
// Must run before `astro build` / `astro dev` — see package.json's predev/prebuild scripts.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const siteDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const featuresDir = path.resolve(siteDir, '../features');
const destRoot = path.resolve(siteDir, 'public/screenshots');

if (!fs.existsSync(featuresDir)) {
  process.exit(0);
}

fs.mkdirSync(destRoot, { recursive: true });

const slugs = fs
  .readdirSync(featuresDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && !d.name.startsWith('_'))
  .map((d) => d.name);

let count = 0;
for (const slug of slugs) {
  const srcDir = path.join(featuresDir, slug, 'screenshots');
  if (!fs.existsSync(srcDir)) continue;
  const files = fs
    .readdirSync(srcDir, { withFileTypes: true })
    .filter((f) => f.isFile() && /\.(png|jpe?g|webp|gif)$/i.test(f.name));
  if (files.length === 0) continue;
  const destDir = path.join(destRoot, slug);
  fs.mkdirSync(destDir, { recursive: true });
  for (const f of files) {
    fs.copyFileSync(path.join(srcDir, f.name), path.join(destDir, f.name));
    count += 1;
  }
}

console.log(`sync-screenshots: mirrored ${count} file(s) into public/screenshots/`);
