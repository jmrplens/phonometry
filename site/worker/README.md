# The phonometry.dev preview

The documentation is served at <https://docs.jmrp.io/phonometry/> from GitHub
Pages, and that stays the canonical site. This directory serves the same build
as a preview at <https://phonometry.dev/phonometry/>, from a Cloudflare Worker
on the Free plan in the Phonometry account, with every page marked `noindex`.
Nothing here touches docs.jmrp.io.

## No code on any request

The Worker `phonometry-docs` has Static Assets and no script: no `main`, no
binding, no `run_worker_first`. Cloudflare documents that requests for static
assets are free and unlimited and run no Worker
([billing and limitations](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/)),
so the 100,000 Worker requests a day of Workers Free cannot stop anything the
preview serves. It fails open because it has nothing that can fail.

What a script would have done lives elsewhere:

| On docs.jmrp.io (docs-edge, Transform Rules) | On phonometry.dev |
|---|---|
| Retired addresses, Bulk Redirects list `phonometry_retired` | `_redirects`, written from the same pairs (`redirectPairs()` in `site/scripts/cloudflare-redirects.mjs`) |
| Security headers, response header rule 1 | `_headers` (`lib/headers.mjs`), the same values plus `X-Content-Type-Options`, and `media-src` for the clip host |
| `charset=utf-8` on Markdown and text files | `_headers`, which replaces the bare type the asset server sends for `.md` and `.txt` |
| A page's `Link` to its Markdown copy, `Vary: Accept` | `_headers` |
| The copy's canonical `Link` | `_headers` |
| A 404 that announces nothing | zone response rule `not-found-plain` (`lib/rules.mjs`): `_headers` matches a path whatever the status, so the rule takes the `Link` back off a 404 |
| A year of cache for content-hashed `_astro/` files | zone response rule `astro-immutable`, on a 200 or 304 only, so a missing file is not cached for a year |
| Markdown negotiation, a 302 to `<page>index.md` | zone Single Redirect rule `markdown-twin` (`lib/rules.mjs`) |
| Validators and 304s | the asset server's own `ETag` |
| Byte ranges for the clips | zone rule `clips-to-range-host`: a 302 to docs.jmrp.io, which answers 206, until the R2 bucket exists |

Zone rules run before any Worker and cost no invocation. `_headers` and
`_redirects` are read by the asset server. Static Assets answers a `Range`
request with a 200 and the whole file, which Safari cannot play, hence the clip
rule.

A browser holds the address a clip is redirected to against the page's
Content-Security-Policy, and every page carries two: the meta tag the build
writes (`site/astro.config.mjs`) and the header from `_headers`. Both list the
clip hosts of `mediaOrigins` (`site/src/data/site.mjs`) in `media-src`. On
docs.jmrp.io that entry is the page's own origin, so nothing changes there. A
new clip host (the R2 bucket) goes into `mediaOrigins` first: `stage.mjs`
refuses a build whose pages do not allow every listed host, and
`apply-rules.mjs` refuses a clip host that is not listed. curl cannot see this
kind of failure, so `scripts/check-clip.mjs` plays clips in Chrome and fails on
any policy violation.

| Situation | Pages | Copies | Retired addresses | Clips |
|---|---|---|---|---|
| Normal | served | 302 from the rule, then served | 301 | 302 to a host that answers 206 |
| The account over 100,000 Worker requests (a script added later) | unchanged | unchanged | unchanged | unchanged |
| A zone rule deleted or broken | unchanged | agents get the HTML, which still names the copy in its `Link` | unchanged | Safari cannot seek |
| docs.jmrp.io down | unchanged | unchanged | unchanged | clips fail until R2 |

`main`, a binding or `run_worker_first` must not be added without reviewing that
trade first: with `run_worker_first` a Free account over its quota answers 429
instead of the asset, and `_headers` does not apply to a response a script
builds. The visitor analytics work is where that review belongs.

## The Markdown rule and docs.jmrp.io

A rule expression cannot read q-values. The rule sends a request for a slash
page to its copy when one of its Accept fields names `text/markdown` and names
no HTML type (`text/html`, `application/xhtml+xml`) before it; the Spanish API
pages, which have no copy, are excluded. Against docs-edge's `prefersMarkdown`,
which weighs q-values and gives a tie to Markdown, it disagrees in two classes,
both reached only by clients that name `text/markdown`:

| Class | Example Accept | docs.jmrp.io | phonometry.dev |
|---|---|---|---|
| A: an HTML type is named before `text/markdown` | `text/html;q=0.5, text/markdown` | Markdown | HTML |
| B: `text/markdown` carries `q=0`, or a lower q than an HTML type named after it | `text/markdown;q=0, */*`, `text/markdown;q=0.1, text/html` | HTML | Markdown |

`test/negotiation.test.mjs` crosses `text/markdown` with the HTML types,
`text/*`, `*/*` and `text/plain` at every q and in every order (18,690
Accepts), and fails on a disagreement outside these two classes. A browser
names HTML first and never reaches class B. A client that gets the HTML still
finds the copy in the page's `Link` header and in llms.txt.

For an address that does not exist, the rule cannot know there is no page: a
Markdown-preferring request for `/phonometry/nope/` gets a 302 to
`/phonometry/nope/index.md`, which answers 404, where docs.jmrp.io answers the
404 directly. Both 404s carry no `Link`.

## Files

| Path | What it is |
|---|---|
| `wrangler.jsonc` | The Worker: assets only, `phonometry.dev` as its Custom Domain, no workers.dev address |
| `stage.mjs` | Stages a build into `stage/` and runs every check first |
| `lib/headers.mjs`, `lib/redirects.mjs`, `lib/twins.mjs` | What `_headers` and `_redirects` say, and which pages have no Markdown copy |
| `lib/staging.mjs` | The checks: 20,000 files and 25 MiB a file (Workers Free), no `_headers` or `_redirects` in the build, the pages without a copy equal to the exclusions, every redirect target served |
| `lib/rules.mjs`, `lib/rulesets.mjs`, `scripts/apply-rules.mjs` | The zone rules, their drift check and the script that puts them |
| `lib/zone.mjs`, `scripts/apply-zone.mjs` | The DNS records and zone settings, and the script that applies them |
| `lib/cloudflare.mjs` | The API calls, and the account and zone ids every script acts on |
| `lib/clip-check.mjs`, `scripts/check-clip.mjs` | What a playing clip has to report, and the check that plays clips of the live preview in Chrome |
| `lib/quota.mjs`, `scripts/check-quota.mjs` | The daily Workers request count, read by hand |
| `test/` | `node --test`, no network: every check on small trees made to fail it, the scripts on recorded API answers |

`package.json` and its own lockfile hold wrangler and puppeteer (for the clip
check), so the documentation build never downloads either.

## Building for phonometry.dev

`PHONOMETRY_SITE` picks the host a build is made for, from a closed list in
`site/src/data/site.mjs`: unset (or `docs.jmrp.io`) is the build docs.jmrp.io
serves, byte for byte; `phonometry.dev` names phonometry.dev in every canonical
URL, `og:url`, structured data `@id`, sitemap, robots.txt, Markdown copy and llms
file; anything else stops the build. The base path stays `/phonometry` in both
for now, so every link the pages write is the same; moving to the root is a
later change.

```bash
cd site
PHONOMETRY_SITE=phonometry.dev pnpm build
node worker/stage.mjs --from dist --site phonometry.dev
```

The preview deploys docs.yml's own build (unset), so its canonical URLs name
docs.jmrp.io, which is right for a preview.

## Deploying

The account is named in `wrangler.jsonc`, and the account and zone in
`lib/cloudflare.mjs`. wrangler reads the file before `CLOUDFLARE_ACCOUNT_ID`,
and the scripts ignore `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_ZONE_ID` (they
say so when either names something else), so a shell set up for another
account cannot deploy, roll back or put rules anywhere but here.

The first deploy creates the Worker and its Custom Domain (Cloudflare creates
the apex DNS record and a certificate). It is run once by hand with the account
key:

```bash
cd site/worker
pnpm install --frozen-lockfile
node stage.mjs --from ../dist            # or the unpacked github-pages artifact
CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... pnpm exec wrangler deploy --config wrangler.jsonc
```

After that, `.github/workflows/site-preview.yml` redeploys: Actions > Site
preview > Run workflow, with the id of a docs.yml run on main. Before it
downloads anything it reads that run back and stops unless it is a successful
push or dispatch of docs.yml on main in this repository whose commit main
contains, and it logs the commit it deploys. It needs the environment
`phonometry-preview` (deployment branch `main`) with the secrets
`CF_PHONOMETRY_DEPLOY_TOKEN` (Account: Workers Scripts Edit; zone: Workers
Routes Edit) and `CF_PHONOMETRY_RULES_TOKEN` (zone: Dynamic URL Redirects Edit,
Transform Rules Edit, Zone Read). The job stages, deploys, checks what the
assets answer, checks the zone rules against `lib/rules.mjs` (or puts them,
with the `apply_rules` input, saving what was there as an artifact), checks
what the rules answer, and plays two clips in Chrome.

The zone itself, from the maintainer's machine:

```bash
CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... node scripts/apply-zone.mjs           # the plan
CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... node scripts/apply-zone.mjs --apply   # applies it, saving what was there
```

It creates a proxied `www` placeholder (`AAAA 100::`, redirected by a zone
rule); on the apex and on `www`, a null MX and an SPF that authorises no
sender; DMARC reject and a revoked DKIM key. It turns off email obfuscation
and automatic HTTPS rewrites (both rewrite the bytes of the build) and turns on
HTTPS everywhere with HSTS. A record already in the place of one of these is
reported and left alone.

wrangler prints "Read N files" counting folders as well as files; the limit
counts files, and stage.mjs prints that number.

## The quota alert

The preview runs no script, so it spends none of the 100,000 Worker requests a
day of Workers Free; the count matters only once a script is added. The alert
belongs to the account, as a Cloudflare notification on that count (custom
analytics over Workers invocations, threshold 80,000 for the UTC day), mailed
to the account's address. Nothing in this repository schedules a check.

`scripts/check-quota.mjs` reads the same count by hand from the GraphQL
Analytics API (dataset `workersInvocationsAdaptive`, summed over every script,
since the quota is per account), prints it per script with the projection to
00:00 UTC, and exits 1 at 70 % of the day, when the day before reached 99 %, or
on a script not passed with `--expect`.

## Rolling back

| What | How |
|---|---|
| A deploy | `pnpm exec wrangler rollback <version>` from this directory (the account comes from `wrangler.jsonc`), or delete the Custom Domain (phonometry.dev goes offline, nothing else changes) |
| Zone rules | PUT the `rules` of the file `apply-rules.mjs --apply` saved |
| Zone records and settings | delete the records it reports as created; set each value back from the file it saved |
| Tokens and secrets | roll or delete the token; `gh secret delete` |

## First-deploy checks

1. A page answers 200 with `x-robots-tag: noindex`, the security headers, an
   `etag` and its `Link` to the copy; the copy answers
   `text/markdown; charset=utf-8` with its canonical `Link` and one
   `Content-Type`; llms.txt and robots.txt answer `text/plain; charset=utf-8`;
   the Spanish API pages carry no `Link`.
2. A request with `Accept: text/markdown` gets the 302 with `Vary: Accept` and
   `Cache-Control: no-store`; a browser Accept does not.
3. Every retired address answers 301; one with a query string keeps it (if it
   does not, the pairs move to an account Bulk Redirects list, which runs before
   Workers and keeps the query).
4. `/phonometry/nope/`, `/phonometry/nope/index.md` and `/nope` answer 404 with
   the site's page, `text/html`, no `Link` and `Vary: Accept-Encoding`; a
   missing `_astro/` file is not cached for a year, a present one is.
5. A clip with a byte range: 302, then 206 from docs.jmrp.io; and
   `node scripts/check-clip.mjs` plays clips in Chrome with no policy violation
   (curl cannot see a blocked clip).
6. `www.phonometry.dev/x?y` answers 301 to `phonometry.dev/x?y`.
7. A page's bytes equal the build's file.
8. Whether `_headers` reach the `_redirects` responses (CORS on redirects).
