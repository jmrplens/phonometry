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
| Security headers, response header rule 1 | `_headers` (`lib/headers.mjs`), the same values plus `X-Content-Type-Options` |
| A page's `Link` to its Markdown copy, `Vary: Accept` | `_headers` |
| The copy's canonical `Link` | `_headers` |
| Markdown negotiation, a 302 to `<page>index.md` | zone Single Redirect rule `markdown-twin` (`lib/rules.mjs`) |
| Validators and 304s | the asset server's own `ETag` |
| Byte ranges for the clips | zone rule `clips-to-range-host`: a 302 to docs.jmrp.io, which answers 206, until the R2 bucket exists |

Zone rules run before any Worker and cost no invocation. `_headers` and
`_redirects` are read by the asset server. Static Assets answers a `Range`
request with a 200 and the whole file, which Safari cannot play, hence the clip
rule.

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
pages, which have no copy, are excluded. Against docs-edge's `prefersMarkdown`
it disagrees on exactly these Accepts, all of them sent only by clients that
ask for Markdown by name (`test/negotiation.test.mjs` lists them and fails on a
new one):

| Accept | docs.jmrp.io | phonometry.dev |
|---|---|---|
| `text/html,text/markdown` | Markdown (a tie goes to Markdown) | HTML |
| `application/xhtml+xml, text/markdown` | Markdown | HTML |
| `text/markdown;q=0, text/html` | HTML | Markdown |
| `text/markdown;q=0.5, text/html` | HTML | Markdown |
| `text/markdown;level=1;q=0` | HTML | Markdown |

A client that gets the HTML still finds the copy in the page's `Link` header
and in llms.txt.

## Files

| Path | What it is |
|---|---|
| `wrangler.jsonc` | The Worker: assets only, `phonometry.dev` as its Custom Domain, no workers.dev address |
| `stage.mjs` | Stages a build into `stage/` and runs every check first |
| `lib/headers.mjs`, `lib/redirects.mjs`, `lib/twins.mjs` | What `_headers` and `_redirects` say, and which pages have no Markdown copy |
| `lib/staging.mjs` | The checks: 20,000 files and 25 MiB a file (Workers Free), no `_headers` or `_redirects` in the build, the pages without a copy equal to the exclusions, every redirect target served |
| `lib/rules.mjs`, `lib/rulesets.mjs`, `scripts/apply-rules.mjs` | The zone rules, their drift check and the script that puts them |
| `lib/zone.mjs`, `scripts/apply-zone.mjs` | The DNS records and zone settings, and the script that applies them |
| `lib/quota.mjs`, `scripts/check-quota.mjs` | The daily quota check |
| `test/` | `node --test`, no network: every check on small trees made to fail it, the scripts on recorded API answers |

`package.json` and its own lockfile hold wrangler, so the documentation build
never downloads it.

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

The first deploy creates the Worker and its Custom Domain (Cloudflare creates
the apex DNS record and a certificate). It is run once by hand with the account
key:

```bash
cd site/worker
pnpm install --frozen-lockfile
node stage.mjs --from ../dist            # or the unpacked github-pages artifact
CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... CLOUDFLARE_ACCOUNT_ID=... \
  pnpm exec wrangler deploy --config wrangler.jsonc
```

After that, `.github/workflows/site-preview.yml` redeploys: Actions > Site
preview > Run workflow, with the id of a docs.yml run on main. It needs the
environment `phonometry-preview` (deployment branch `main`) with the secrets
`CF_PHONOMETRY_DEPLOY_TOKEN` (Account: Workers Scripts Edit; zone: Workers
Routes Edit) and `CF_PHONOMETRY_RULES_TOKEN` (zone: Dynamic URL Redirects Edit,
Transform Rules Edit, Zone Read), and the repository variables
`CF_PHONOMETRY_ACCOUNT_ID` and `CF_PHONOMETRY_ZONE_ID`. The job stages, deploys,
checks what the assets answer, checks the zone rules against `lib/rules.mjs`
(or puts them, with the `apply_rules` input, saving what was there as an
artifact), and checks what the rules answer.

The zone itself, once, from the maintainer's machine:

```bash
CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... CLOUDFLARE_ZONE_ID=... node scripts/apply-zone.mjs           # the plan
CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=... CLOUDFLARE_ZONE_ID=... node scripts/apply-zone.mjs --apply   # applies it, saving what was there
```

It creates a proxied `www` placeholder (`AAAA 100::`, redirected by a zone
rule), a null MX, an SPF that authorises no sender, DMARC reject and a revoked
DKIM key, and it turns off email obfuscation and automatic HTTPS rewrites (both
rewrite the bytes of the build) and turns on HTTPS everywhere with HSTS. A
record already in the place of one of these is reported and left alone.

wrangler prints "Read N files" counting folders as well as files; the limit
counts files, and stage.mjs prints that number.

## The quota alert

Cloudflare sends no notice for the Workers Free daily count. The scheduled job
`.github/workflows/workers-quota.yml` reads it every 30 minutes from the
GraphQL Analytics API (dataset `workersInvocationsAdaptive`, summed over every
script, since the quota is per account) and fails at 70 % of the day, warns at
50 %, fails when the day before reached 99 %, and fails on a script not listed
in the repository variable `CF_PHONOMETRY_EXPECTED_SCRIPTS` (space separated,
empty today). A failed scheduled run mails whoever last changed its cron line.
It needs the secret `CF_PHONOMETRY_ANALYTICS_TOKEN` (Account Analytics Read);
it is skipped until `CF_PHONOMETRY_ACCOUNT_ID` is set. Run it by hand with
threshold 0 to see it fail and the mail arrive.

After the first deploy, the count is read again: if requests for assets show
under `phonometry-docs` (Cloudflare documents that they are not billed, not
whether this dataset lists them), add the name to the expected list and read
the total as an upper bound. The job would then only raise false alarms, never
miss one.

## Rolling back

| What | How |
|---|---|
| A deploy | `pnpm exec wrangler rollback`, or delete the Custom Domain (phonometry.dev goes offline, nothing else changes) |
| Zone rules | PUT the `rules` of the file `apply-rules.mjs --apply` saved |
| Zone records and settings | delete the records it reports as created; set each value back from the file it saved |
| Tokens and secrets | roll or delete the token; `gh secret delete` |
| The quota job | `gh workflow disable workers-quota.yml` |

## First-deploy checks

1. A page answers 200 with `x-robots-tag: noindex`, the security headers, an
   `etag` and its `Link` to the copy; the copy answers `text/markdown` with its
   canonical `Link`; the Spanish API pages carry no `Link`.
2. A request with `Accept: text/markdown` gets the 302 with `Vary: Accept` and
   `Cache-Control: no-store`; a browser Accept does not.
3. Every retired address answers 301; one with a query string keeps it (if it
   does not, the pairs move to an account Bulk Redirects list, which runs before
   Workers and keeps the query).
4. `/phonometry/nope/` and `/nope` answer 404 with the site's page.
5. A clip with a byte range: 302, then 206 from docs.jmrp.io.
6. `www.phonometry.dev/x?y` answers 301 to `phonometry.dev/x?y`.
7. A page's bytes equal the build's file.
8. Whether `_headers` reach the `_redirects` responses (CORS on redirects).
