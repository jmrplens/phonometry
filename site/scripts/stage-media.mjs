// Stages the documentation media into the site's own asset tree, so the built
// pages serve every figure, animation and report preview from this origin
// instead of hotlinking raw.githubusercontent.com.
//
// Why not hotlink: raw.githubusercontent.com is not a CDN, it caches for five
// minutes against the Pages origin's ten, it is rate limited, GitHub asks
// people not to use it as an asset host, and the URLs were pinned to `main`,
// so renaming a figure silently broke every published page that showed it.
// Serving them here also means the figures finally belong to the pages they
// illustrate rather than to a third origin.
//
// What is staged, and what is not:
//   *.svg    copied verbatim. These are the figure pipeline's output and are
//            already minimal; re-encoding them is not wanted.
//   *.webp   copied, then recompressed in dist by optimize-images.mjs,
//            except the animation posters, which arrive at their quality.
//   *.webm   copied verbatim. Video, nothing here can improve it.
//   *.gif    NOT staged. The GIFs exist only for the markdown mirror on
//            GitHub, which cannot play WebM; the site uses the WebM.
//
// The clips and their posters are not in this repository. They live in
// jmrplens/phonometry-assets (scripts/assets_dir.py says why), and are taken
// from a checkout of it: PHONOMETRY_ASSETS_DIR in the environment or in the
// repository .env, or the sibling ../phonometry-assets that `make assets`
// clones. The docs workflow fetches that checkout at the commit assets.lock
// records, so the published site carries the clips its code was rendered
// against and not whatever that repository's main holds by build time. A
// missing checkout stops the build: a site without its videos is broken, and
// a warning at the bottom of a prebuild log is how that would ship unseen.
//
// The markdown under docs/ keeps its absolute raw.githubusercontent URLs on
// purpose: GitHub renders those files directly and has no build step.
//
// Staged into public/media rather than through Vite's hashed asset pipeline:
// a hundred of these references are hand-written <img> tags inside markdown,
// which a rehype pass rewrites at build time, and that pass cannot know a
// content hash. A stable path is the one scheme both the components and the
// markdown can resolve. GitHub Pages serves everything with the same
// max-age either way, so the hash would buy little here.
//
// Runs as a prebuild step. Output is generated, gitignored, and refreshed only
// when a source file actually changes so repeat builds stay fast.
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
} from 'node:fs';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(here, '..', '..');
const target = join(here, '..', 'public', 'media');

/**
 * The value of KEY in the repository .env, dotenv-style, or undefined.
 *
 * The same file and the same precedence as scripts/fdtd_gpu_remote.py: a real
 * environment variable wins, the file fills in what is unset, quotes come off.
 */
function fromDotEnv(key) {
  const file = join(repoRoot, '.env');
  if (!existsSync(file)) return undefined;
  for (const raw of readFileSync(file, 'utf8').split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const [name, ...rest] = line.split('=');
    if (name.trim() === key) return rest.join('=').trim().replace(/^['"]|['"]$/g, '');
  }
  return undefined;
}

/** The clips directory, resolved as scripts/assets_dir.py resolves it. */
function clipsDir() {
  const configured = process.env.PHONOMETRY_ASSETS_DIR || fromDotEnv('PHONOMETRY_ASSETS_DIR');
  return configured ? resolve(configured) : join(repoRoot, '..', 'phonometry-assets', 'images');
}

const clips = clipsDir();
if (!existsSync(clips)) {
  throw new Error(
    `[stage-media] the clips directory ${clips} does not exist. Run \`make assets\` in the ` +
      'repository root to clone jmrplens/phonometry-assets beside it, or set ' +
      'PHONOMETRY_ASSETS_DIR (environment or .env) to the images/ directory of a checkout.',
  );
}

/** Source directories, and the extensions taken from each. */
const SOURCES = [
  { dir: join(repoRoot, '.github', 'images'), exts: new Set(['.svg', '.webp']) },
  { dir: clips, exts: new Set(['.webp', '.webm']) },
  // The example fiches: the WebP preview each page shows, and the PDF it links
  // to. Together they are under 6 MB, which is worth paying to leave nothing
  // pointing off-origin.
  { dir: join(repoRoot, '.github', 'reports'), exts: new Set(['.webp', '.pdf']) },
];

mkdirSync(target, { recursive: true });

const staged = new Set();
const totals = new Map();
let copied = 0;
let skipped = 0;

for (const { dir, exts } of SOURCES) {
  if (!existsSync(dir)) {
    console.warn(`[stage-media] ${dir} not found, skipping`);
    continue;
  }
  for (const name of readdirSync(dir)) {
    const ext = extname(name).toLowerCase();
    if (!exts.has(ext)) continue;

    const src = join(dir, name);
    const dest = join(target, name);
    if (staged.has(name)) {
      throw new Error(
        `[stage-media] two source files are both named "${name}"; the staged tree is flat, so the names have to be unique`,
      );
    }
    staged.add(name);

    const from = statSync(src);
    totals.set(ext, (totals.get(ext) ?? 0) + from.size);

    // Copy only when the destination is missing or out of date: this runs on
    // every build and the tree is around a thousand files.
    if (existsSync(dest)) {
      const to = statSync(dest);
      if (to.size === from.size && to.mtimeMs >= from.mtimeMs) {
        skipped += 1;
        continue;
      }
    }
    copyFileSync(src, dest);
    copied += 1;
  }
}

// Drop anything a previous run staged that no longer has a source, so a
// renamed or deleted figure does not linger in the published assets.
let removed = 0;
for (const name of readdirSync(target)) {
  if (!staged.has(name)) {
    rmSync(join(target, name), { recursive: true, force: true });
    removed += 1;
  }
}

const megabytes = (n) => (n / 1024 / 1024).toFixed(1);
const breakdown = [...totals.entries()]
  .sort((a, b) => b[1] - a[1])
  .map(([ext, size]) => `${ext.slice(1)} ${megabytes(size)} MB`)
  .join(', ');
const total = [...totals.values()].reduce((a, b) => a + b, 0);

console.log(
  `[stage-media] ${staged.size} files, ${megabytes(total)} MB (${breakdown})` +
    ` | ${copied} copied, ${skipped} unchanged, ${removed} removed`,
);
