// Validates EN/ES translation parity: every English page under
// src/content/docs/ (outside es/) must have a Spanish counterpart at the same
// relative path under src/content/docs/es/, and vice-versa. Exits non-zero on
// any mismatch so CI catches a missing or orphaned translation.
import { readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const docsDir = fileURLToPath(new URL("../src/content/docs", import.meta.url));
const esDir = join(docsDir, "es");

function walk(dir) {
	const out = [];
	for (const entry of readdirSync(dir)) {
		const p = join(dir, entry);
		if (statSync(p).isDirectory()) {
			if (p === esDir) continue; // skip the ES subtree when collecting EN
			out.push(...walk(p));
		} else if (/\.(md|mdx)$/.test(entry)) {
			out.push(p);
		}
	}
	return out;
}

// The API reference (reference/api/) is generated in English only; Starlight
// locale fallback serves it on /es/. Exclude the subtree from parity.
const apiRef = join("reference", "api");
const isApiRef = (p) => p === apiRef || p.startsWith(apiRef + sep);

const enPages = walk(docsDir)
	.map((p) => relative(docsDir, p))
	.filter((p) => !isApiRef(p));
const esPages = walk(esDir).map((p) => relative(esDir, p));

const enSet = new Set(enPages);
const esSet = new Set(esPages);

const missingEs = enPages.filter((p) => !esSet.has(p)).sort();
const orphanEs = esPages.filter((p) => !enSet.has(p)).sort();

if (missingEs.length || orphanEs.length) {
	console.error("i18n parity check FAILED:");
	for (const p of missingEs)
		console.error(`  EN page missing ES translation: ${p}`);
	for (const p of orphanEs)
		console.error(`  ES page with no EN original:    es/${p}`);
	process.exit(1);
}

console.log(
	`i18n parity OK: ${enPages.length} EN pages each have an ES translation.`,
);
