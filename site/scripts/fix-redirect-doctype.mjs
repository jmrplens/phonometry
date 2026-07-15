// Astro emits its redirect stub pages with a lowercase `<!doctype html>`,
// which fails the html-validate doctype-style rule the rest of the site
// follows. Uppercase it in place after every build.
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const dist = new URL('../dist/', import.meta.url).pathname;

function* htmlFiles(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(path);
    else if (entry.name.endsWith('.html')) yield path;
  }
}

let fixed = 0;
for (const file of htmlFiles(dist)) {
  const html = readFileSync(file, 'utf8');
  if (html.startsWith('<!doctype html>')) {
    writeFileSync(file, '<!DOCTYPE html>' + html.slice('<!doctype html>'.length));
    fixed += 1;
  }
}
console.log(`[fix-redirect-doctype] uppercased DOCTYPE in ${fixed} file(s)`);
