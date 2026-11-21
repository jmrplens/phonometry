# phonometry.dev

The documentation is served at <https://phonometry.dev/>, the canonical site,
at the root, from a Cloudflare Worker on the Free plan in the Phonometry
account. This directory holds that Worker, its staging, its zone rules and its
quota guard. Nothing here touches docs.jmrp.io, where the site was published
under `/phonometry/` before: every address there answers a permanent redirect
to the same page here, from Bulk Redirects lists in the jmrp.io account
(CONTRIBUTING.md, 5b). GitHub Pages, which served it, is deployed no more and
keeps its last deployment.

## Code only for the beacon

Every file is a Static Asset and runs no script: pages, `_astro`, media,
images, PDFs, the search index, the Markdown copies (`/index.md`,
`/*/index.md`), the llms files, the sitemaps and robots.txt. Cloudflare
documents that requests for static assets are free and unlimited and run no
Worker
([billing and limitations](https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/)),
so the 100 000 Worker requests a day of Workers Free cannot stop any of them,
and neither can a fault in the Worker's code or a deploy of it that fails.

The Worker `phonometry-docs` runs `src/index.mjs` for exactly the one path
`assets.run_worker_first` lists (`lib/worker-paths.mjs`, held equal by
`test/wrangler.test.mjs`): the visitor beacon `/_v`, a POST that no file
answers. A path that matches no pattern never reaches it, a missing one
included. The files agents read run no JavaScript and so never send the
beacon; the zone's own analytics count every request to them, path, user
agent, network and status, without any Worker (section "Visitor
analytics").

With `run_worker_first` a Free account over its quota answers 429 on that
path instead of running it, so the quota guard (section "Quota") switches the
beacon off at 95 % of the day; no file is ever affected.

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
| Byte ranges for the clips | zone rule `clips-to-range-host`: a 302 to `clipBase` (`site/src/data/site-targets.json`), the clip host, which answers 206 (section "Where the clips are served from") |
| Addresses under an old base path | zone rules `legacy-base-slash` and `legacy-base-bare`: `/phonometry/X` answers a 301 to `/X` and `/phonometry` to `/`, the query kept, generated because the site is served at the root and `site-targets.json` lists a legacy origin under that base |
| A page written without its trailing slash, a 301 to the address with it (GitHub Pages' own answer) | zone Single Redirect rule `trailing-slash` (`lib/rules.mjs`): a GET or HEAD of a path with no slash at its end and no dot anywhere, `/_v`, `/cdn-cgi/`, `/404` and every `…/index` aside, answers a 301 to the path with its slash, the query kept, before the asset server's 307 |

Zone rules run before any Worker and cost no invocation. `_headers` and
`_redirects` are read by the asset server. Static Assets answers a `Range`
request with a 200 and the whole file, which Safari cannot play, hence the clip
rule.

The trailing-slash rule reads a path with no dot as a page, which holds
because the build has no file whose address holds no dot and no page under a
folder whose name holds one: the staging step refuses either
(`slashRuleProblems` in `lib/staging.mjs`, which reads each address as the rule
does, whole), since such a file would be sent away from itself to an address
that answers 404, and such a page would keep the 307. A file without an
extension under a folder with a dot, as `.well-known/` may hold, is no address
the rule reads and passes. The asset server answers two dotless addresses
without a slash itself, and the rule leaves both to it, since its 301 to the
slash form would come straight back as the asset server's 307, a loop: a
folder's page at `<folder>/index`, which the asset server sends on to the
folder, and the not-found page, `404.html`, which it serves at `/404`. The
staging step refuses any other page served flat (an `.html` file not named
`index.html`), which would loop the same way. The rule leaves `/cdn-cgi/` alone, where Cloudflare
answers its own requests, a challenge's among them, as Cloudflare's guide to
troubleshooting rules asks. An address that names nothing gets the 301 too,
then the 404 at its slash form. A retired
address written without its slash takes two hops where `_redirects` alone took
one, the rule's 301 to the slash form and then the `_redirects` 301 to its
page; the 440 retired addresses do not fit an exclusion in the expression,
which takes 4 096 characters.

A browser holds the address a clip is redirected to against the page's
Content-Security-Policy, and every page carries two: the meta tag the build
writes (`site/astro.config.mjs`) and the header from `_headers`. Both list the
clip hosts of `mediaOrigins` (`site/src/data/site-targets.json`) in
`media-src`. A new clip host goes into `mediaOrigins` first, and `clipBase`
beside it names where the rule sends a clip: `stage.mjs` refuses a build whose
pages do not allow every listed host, and `apply-rules.mjs` refuses a clip host
that is not listed. curl cannot see this kind of failure, so
`scripts/check-clip.mjs` plays clips in Chrome and fails on any policy
violation. The clip host is filled apart from the deploy, so before anything
goes live the deploy asks it for the first byte of every clip it staged
(`scripts/check-clip-host.mjs`) and stops unless each answers a 206 with the
staged size: a clip added or re-rendered while the host lacks it fails the
deploy instead of 404-ing on the site.

### Where the clips are served from

The clip host is the R2 bucket `phonometry-media` of the Phonometry account,
at its custom domain:

```json
"mediaOrigins": ["https://media.phonometry.dev"],
"clipBase": "https://media.phonometry.dev/"
```

Until that bucket holds every clip, the clips stay where GitHub Pages served
them, behind docs.jmrp.io, whose catch-all redirect leaves
`/phonometry/media/*.webm` alone so it keeps answering 206. The site goes there
by changing those two values in `site-targets.json`, and nothing else:

```json
"mediaOrigins": ["https://docs.jmrp.io"],
"clipBase": "https://docs.jmrp.io/phonometry/media/"
```

Every reader of the clip host (the pages' policy, the Worker's header, the
staging check, the zone rule, the deploy's clip checks) takes it from there,
and the check that refuses a link to the old host (`scripts/base-path.mjs`)
lets that `clipBase` through; `scripts/base-path.test.mjs` makes each of the
two edits above and holds the check to it.

| Situation | Every file (pages, `_astro`, media, copies, llms, sitemaps, robots.txt) | Beacon `/_v` | Retired addresses | Clips |
|---|---|---|---|---|
| Normal | assets, no code | 204, one data point | 301 | 302 to a host that answers 206 |
| 80 % of the day's Workers requests | unchanged | unchanged; the account's notification mails the maintainer | unchanged | unchanged |
| 95 % (the guard tripped, until its first run after 00:00 UTC) | unchanged | blocked by the WAF before any Worker, not logged | unchanged | unchanged |
| Quota spent before the guard acts | unchanged | 429 | unchanged | unchanged |
| Guard down or without its token | unchanged | unchanged (429 only once the quota is spent) | unchanged | unchanged |
| The Worker's code fails or a deploy of it breaks | unchanged | no page view counted | unchanged | unchanged |
| Analytics Engine write fails | unchanged | 204 | unchanged | unchanged |
| A zone rule deleted or broken | agents asking for Markdown get the HTML, which still names the copy in its `Link` | the Worker still checks method, Origin and size | unchanged | Safari cannot seek |
| The clip host down | unchanged | unchanged | unchanged | clips fail; the deploy's clip check stops the next deploy |

Any other binding, a route besides the Custom Domain, or a new
`run_worker_first` pattern fails `test/wrangler.test.mjs` until it is added on
purpose; the staging step refuses a staged file the pattern would catch, so
no file can become an invocation by accident.

## Visitor analytics

Every beacon the Worker receives writes one data point to the Analytics
Engine dataset `phonometry_dev_requests` of the Phonometry account, in the
layout docs-edge writes for docs.jmrp.io (`docs_edge_requests`): the logging
block of `lib/edge-log.mjs` is a verbatim copy of docs-edge's, and
`test/edge-log.test.mjs` compares the two texts when the jmrp.io repository is
on the machine. The maintainer's ingestion reads both datasets the same way.
Nothing is reduced: client address, full User-Agent, referrer, query string,
location and network as Cloudflare reports them.

Reads of the files agents fetch (the Markdown copies, the llms files, the
sitemaps, robots.txt) run no code and write no data point. The zone's HTTP
analytics count them, like every other request to the zone: GraphQL
`httpRequestsAdaptiveGroups` on the zone gives path, status, user agent,
network (ASN) and country, which is how a crawler is told from a probe by the
network it comes from.

The beacon (`lib/beacon.mjs`) is one inline script under 1 KB that
`stage.mjs --beacon` puts before `</body>` of every staged page: the copy the
deploy uploads, never the build itself. After `load` it posts the
page path, query, referrer, navigation type, load time, screen, viewport,
pixel ratio, language, time zone, a webdriver flag (automated browsers are
counted and flagged, not skipped) and a 404 flag with `navigator.sendBeacon`
to `/_v` of the page's own origin. A prerendered page reports when it is shown.
The 404 page reports wherever it stands, a missing Markdown copy or llms file
included: no Worker runs there, so the beacon is the only count of a browser
that lands on it.

| | Page view (beacon) |
|---|---|
| index1, blobs 1 to 20, doubles 1 to 9 | docs-edge's for the page: the page's path, query and referrer, method `GET`, status 200 (404 on the 404 page), Accept empty; visitor facts from the beacon's request |
| blob 12 (verdict) | `beacon`, `beacon-limited` (over 30 a minute from one address, still 204), or `beacon-rejected-method\|origin\|size\|body` (with blob 1 `/_v` and the real status) |
| blob 20 | docs-edge's 14 fields, with the page navigation's Sec-Fetch fields (dest `document`, mode `navigate`, site from the referrer: `none`, `same-origin`, `same-site` or `cross-site`) in place of the beacon POST's, then navigation type, 404 flag, webdriver flag, language and time zone |
| doubles 10 to 15 | load time (ms), screen width and height, viewport width and height, pixel ratio |

Appending is what the docs-edge contract allows; nothing is reordered. A
request the WAF blocks (below) never reaches the Worker and is not logged.

The zone keeps junk off the Worker before it runs (`lib/rules.mjs`,
`apply-rules.mjs --phase waf`, applied by hand because the CI rules token has
no WAF scope): `beacon-shape` blocks anything at `/_v` but a POST whose Origin
is the site, and `beacon-rate` blocks an address after 10 beacons in 10
seconds for 10 seconds (the Free plan's one rate rule).

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
`text/*`, `*/*` and `text/plain` at every q and in every order (18 690
Accepts), and fails on a disagreement outside these two classes. A browser
names HTML first and never reaches class B. A client that gets the HTML still
finds the copy in the page's `Link` header and in llms.txt.

For an address that does not exist, the rule cannot know there is no page: a
Markdown-preferring request for `/nope/` gets a 302 to `/nope/index.md`, which
answers 404, where docs.jmrp.io answered the 404 directly. Both 404s carry no
`Link`.

## Files

| Path | What it is |
|---|---|
| `wrangler.jsonc` | The Worker: the assets, `src/index.mjs` for the beacon only, the dataset and the per-address limiter, `phonometry.dev` as its Custom Domain, no workers.dev address |
| `wrangler.assets-only.jsonc` | The same Worker with the code taken out, uploaded beside it on every deploy for the quota guard |
| `src/index.mjs`, `lib/worker-paths.mjs` | The Worker's handler, and the one path that runs it |
| `lib/beacon.mjs`, `lib/edge-log.mjs` | The beacon script, what the Worker accepts from it, and the data point (docs-edge's logging block, verbatim) |
| `guard/`, `lib/guard.mjs`, `scripts/quota-switch.mjs` | The quota guard Worker (Cron Trigger, no route), its decision, and the same decision run by hand |
| `scripts/guard-state.mjs`, `scripts/check-beacon.mjs` | What a deploy reads of the guard before it goes live and after, and the beacon check against the live deployment |
| `scripts/site-address.mjs` | Where a deploy's checks find the pages: the served host, the base path, the canonical site and the clip host, from `src/data/site-targets.json` |
| `stage.mjs` | Stages a build into `stage/` and runs every check first |
| `lib/headers.mjs`, `lib/redirects.mjs`, `lib/twins.mjs` | What `_headers` and `_redirects` say, and which pages have no Markdown copy |
| `lib/staging.mjs` | The checks: 20 000 files and 25 MiB a file (Workers Free), no `_headers` or `_redirects` in the build, the pages without a copy equal to the exclusions, every redirect target served |
| `lib/rules.mjs`, `lib/rulesets.mjs`, `scripts/apply-rules.mjs` | The zone rules (redirects, response headers, and with `--phase waf` the beacon's WAF and rate rules), their drift check and the script that prints (`--print`), checks or puts them |
| `lib/zone.mjs`, `scripts/apply-zone.mjs` | The DNS records and zone settings, and the script that applies them |
| `lib/cloudflare.mjs` | The API calls, and the account and zone ids every script acts on |
| `lib/clip-check.mjs`, `scripts/check-clip.mjs` | What a playing clip has to report, and the check that plays clips of the live site in Chrome |
| `scripts/check-clip-host.mjs` | The deploy's check that every staged clip answers at the clip host, a 206 with its staged size |
| `lib/quota.mjs`, `scripts/check-quota.mjs` | The daily Workers request count, read by hand |
| `test/` | `node --test`, no network: every check on small trees made to fail it, the Worker on fake bindings, the guard and the scripts on recorded API answers |

`package.json` and its own lockfile hold wrangler and puppeteer (for the clip
check), so the documentation build never downloads either.

## Building for phonometry.dev

`site/src/data/site-targets.json` names one host, phonometry.dev, served at the
root, and the build made with nothing set is the one it serves: every canonical
URL, `og:url`, structured data `@id`, sitemap, robots.txt, Markdown copy and
llms file names it, and the pages link each other root-relative.
`PHONOMETRY_SITE` may name that host; anything else stops the build.

```bash
cd site
pnpm build
rm -rf worker/stage                      # staging refuses a directory that exists
node worker/stage.mjs --from dist --site phonometry.dev
```

Whether the staged build carries `X-Robots-Tag: noindex` is not a choice:
`stage.mjs` drops it exactly when the build names phonometry.dev, the host it
is served on, as canonical and phonometry.dev is the canonical site, the
`default` target of `site-targets.json` (`indexableBuild` in
`lib/staging.mjs`), and keeps it on any other build. The build above is
indexable; the llms files keep their own `noindex` (`lib/headers.mjs`).
`--indexable` only states that the noindex is expected to go, and is refused
for any build that keeps it.

## Deploying

The account is named in `wrangler.jsonc`, and the account and zone in
`lib/cloudflare.mjs`. wrangler reads the file before `CLOUDFLARE_ACCOUNT_ID`,
and the scripts ignore `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_ZONE_ID` (they
say so when either names something else), so a shell set up for another
account cannot deploy, roll back or put rules anywhere but here.

The first deploy creates the Worker and its Custom Domain (Cloudflare creates
the apex DNS record and a certificate). Analytics Engine has to be enabled on
the account once, in the dashboard (Workers > Analytics Engine): until then a
deploy with the dataset binding answers error 10089. Every deploy uploads two
versions of the same stage, the assets-only one first, tagged as a pair so the
quota guard can roll between them. A version can only be uploaded to a Worker
that exists, so on an account without `phonometry-docs` the first deploy runs
the `wrangler deploy` line first and the `versions upload` line after it, with
the same `<k>`; every later deploy runs them in the order shown:

```bash
cd site/worker
pnpm install --frozen-lockfile
rm -rf stage                             # staging refuses a directory that exists
node stage.mjs --from ../dist --beacon   # or the unpacked github-pages artifact
export CLOUDFLARE_EMAIL=... CLOUDFLARE_API_KEY=...
pnpm exec wrangler versions upload --config wrangler.assets-only.jsonc --tag assets-<k>
pnpm exec wrangler deploy --config wrangler.jsonc --tag full-<k> --message "full half of <k>"
pnpm exec wrangler deploy --config guard/wrangler.jsonc     # the quota guard, once
```

`<k>` names the deploy, and no two deploys share it (CI uses the run id and
attempt of its own run, so a re-run uploads a new pair).

A deploy by hand reads the guard's state first, as site-deploy.yml does:
`node scripts/guard-state.mjs` with the account key prints `tripped`, `mark`
and `rule`. With `tripped=true` the full half is only uploaded
(`wrangler versions upload --config wrangler.jsonc --tag full-<k>`) and the
assets-only half goes live under the off mark it printed
(`wrangler versions deploy --config wrangler.jsonc --version-tag assets-<k>@100
--message "<mark>: off, deploy of <k>" --yes`), so whoever switched the code
paths off still switches this deploy back on. With `tripped=false` the deploy
carries `--message "full half of <k>"`, or, with a `mark` (the guard may still
have its rule to turn off), `--message "<mark>: on, full half of <k>"`: the
message names the pair, which is how the check below finds this deploy. The guard, or quota-switch.mjs,
can switch between that read and the deploy: `node scripts/guard-state.mjs
--since <deployment> --pair <k>`, with the `deployment` the first read
printed, then says `switched=true` and the `tripped` and `mark` that switch
left, and when they differ from the first read the deploy is promoted again
the way they say (`wrangler versions deploy --version-tag assets-<k>@100` or
`full-<k>@100`, with the same messages). Cron Triggers need the
account's workers.dev subdomain to exist; both Workers keep workers.dev and
preview URLs off, so nothing answers there.

After that, `.github/workflows/site-deploy.yml` deploys every build of main:
docs.yml calls it after the build, in the same run (job `deploy-site`, with
the run's id, the attempt the build ran in and `apply_rules` on), and it runs
by hand too, Actions > Site deploy > Run workflow, with the id of an earlier
docs.yml run on main, to put that build back. Before it downloads anything it
checks where the pages come from and stops unless they are a push or dispatch
of docs.yml on main in this repository whose commit main contains, and it logs
the commit it deploys. It tells the two modes apart by the run id: called, the
id passed in is its own run's (a called workflow runs inside its caller's run,
whose event it reports as its own, so the event cannot tell them apart), the
caller is read from the run's context (`github.workflow_ref` has to be
docs.yml of this repository, `github.ref` main), because that run has not
concluded yet, and the pages are an artifact of the same run; by hand, the run
named is read back through the API and has to have succeeded. Every address
the checks after the deploy use (the served host, the base path, the canonical
site, the clip host, whether the pages are indexable and the old base path)
comes from `scripts/site-address.mjs`, which reads `src/data/site-targets.json`.
Before the Worker goes live the job holds robots.txt's sitemap to a staged
file and every staged clip to the clip host (`scripts/check-clip-host.mjs`);
after it, a page answers with no `noindex`, the home page answers itself,
llms.txt keeps its `noindex`, and `/phonometry/signals/?q=1` and `/phonometry`
answer one 301 to the root. Runs on main queue rather than cancel each other
(docs.yml's concurrency), so a deploy is never cut between the two versions of
its pair. It needs the environment
`phonometry-preview` (deployment branch `main`) with the secrets
`CF_PHONOMETRY_DEPLOY_TOKEN` (Account: Workers Scripts Edit; zone: Workers
Routes Edit) and `CF_PHONOMETRY_RULES_TOKEN` (zone: Dynamic URL Redirects Edit,
Transform Rules Edit, Zone Read). The job stages with the beacon, reads whether the
quota guard holds the code paths off (`scripts/guard-state.mjs`), uploads the
assets-only version and deploys the full one as a tagged pair, checks what the
assets answer (and that the beacon answers what the live deployment says, `scripts/check-beacon.mjs`, and the WAF refuses a GET of it), checks the zone rules against `lib/rules.mjs` (or puts them,
with the `apply_rules` input, saving what was there as an artifact), checks
what the rules answer, and plays two clips in Chrome. While the guard holds
the code paths off, the job only uploads the full half, puts the assets-only
half live under the off mark the live deployment had, so the guard (or
`quota-switch.mjs --mode on`) switches this deploy back on with the rest.
After the deploy it reads the deployments made since the state it read, and
when the guard or `quota-switch.mjs` switched in between, it promotes the
half that switch calls for, under its mark. The beacon check reads the live
deployment just before and after its POST of `/_v` (and probes again when it
changed meanwhile): 204 with full code live; held off, the WAF rule's 403
or, while that rule is not on yet, the assets-only half's 404 (no asset is
called `_v`), never a 204. A GET of `/_v` answers the WAF's 403 either way.

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

The zone rules (`lib/rules.mjs`), from the maintainer's machine:

```bash
node scripts/apply-rules.mjs --print                                            # the JSON each entrypoint would hold, no credential, no request
CLOUDFLARE_API_TOKEN=... node scripts/apply-rules.mjs --check                   # what differs on the zone; writes nothing
CLOUDFLARE_API_TOKEN=... node scripts/apply-rules.mjs --apply --backup-dir ..   # puts the phases that differ, saving what was there
```

`--phase waf` does the same for the beacon's WAF and rate rules. The deploy
of every build of main puts the redirect and response-header phases as
`lib/rules.mjs` generates them (site-deploy.yml, `apply_rules` on), so a rule
added there goes live with the deploy of the commit that adds it, and a rule
put by hand that `lib/rules.mjs` does not generate is taken off by the next
deploy. An apply by hand ahead of that deploy is held to the same code: run it
from a checkout of the commit that will be deployed.

wrangler prints "Read N files" counting folders as well as files; the limit
counts files, and stage.mjs prints that number.

## Quota

Only the beacon spends Worker requests, one per page view, plus the guard's
96 cron runs, of the 100 000 the account gets from 00:00 UTC.

- 80 %: a Cloudflare notification on the account (custom analytics over
  Workers invocations since 00:00 UTC, threshold 80 000) mails the maintainer.
  Nothing in GitHub reads the count.
- 95 %: the Worker `phonometry-quota-guard` (`guard/`, `lib/guard.mjs`) runs
  every 15 minutes from a Cron Trigger. It reads the day's count (GraphQL
  `workersInvocationsAdaptive`), the WAF rule `quota-guard-beacon` and the live
  version of `phonometry-docs`. At the threshold it deploys the assets-only
  half of the live version's pair (`/_v`, which no asset answers, costs
  nothing), then turns the rule on (the
  beacon is blocked before any Worker runs). The deploy goes first so that a
  run that fails between the two leaves a marked deploy the next run
  finishes, never the rule on above a deploy the guard did not make. After
  00:00 UTC it deploys the full half first, then turns the rule off. It keeps
  no state of its own: once tripped, the rule's last update carries the day.
  It switches back on only what it switched off itself: each deploy it makes
  says `quota guard: off|on at <count> of <threshold>`, and back on needs the
  live deployment to say `quota guard: off`. A rollback, an assets-only version
  deployed by hand, or `quota-switch.mjs --mode off` (which says `quota switch
  by hand`) stays as it is after 00:00 UTC, with a note in the log. Switching
  off does not ask: at the threshold it rolls whatever is live to assets only
  and turns the rule on. Beside an assets-only version already live that
  neither the guard nor `quota-switch.mjs` marked, it leaves the rule as it
  finds it (unless `MODE` pins off): that version runs no code, and a rule
  turned on beside it would have no one to turn it off after 00:00 UTC.
  It has no route, so no visitor request can reach the one Worker holding a
  token able to redeploy the site. Its variable `MODE` is `auto`; from 18 to 21
  November 2026 it ran as `dry-run` (log the decision, change nothing), 96
  runs a day without an error, before it was set to act. Without the secret
  `CF_GUARD_TOKEN` every run is dry. The token is an account token with
  Account Analytics Read and Workers Scripts Write on the account and Zone WAF
  Edit on phonometry.dev, stored only with
  `pnpm exec wrangler secret put CF_GUARD_TOKEN --config guard/wrangler.jsonc`.
- By hand, when the guard cannot act (no token yet, or a quota spent so fast
  that its cron stopped too): `node scripts/quota-switch.mjs --mode off` (or
  `on`, `auto`, `dry-run`, the default) with the account key. Off by hand stays
  off until `--mode on`, also over an off state the guard set: the same
  assets-only version is deployed again under `quota switch by hand`, so the
  guard no longer switches it back after 00:00 UTC.

Up to 15 minutes pass between runs, plus a few minutes of GraphQL lag: the 5 000
requests between 95 % and 100 % hold against any sustained rate under about 4
requests a second. Faster than that, the code paths answer 429 until 00:00 UTC
and pages are untouched.

`scripts/check-quota.mjs` reads the count by hand, per script, with the
projection to 00:00 UTC.

## Rolling back

A rollback of the deploy or of the zone rules holds only until the next
docs.yml run on main: that run deploys its build again and puts the rules as
the code generates them. Set the repository variable `SITE_DEPLOY_HOLD` to
`true` first (`gh variable set SITE_DEPLOY_HOLD --body true`), which skips the
job `deploy-site` of every run, or revert the commit on main; clear it
(`gh variable delete SITE_DEPLOY_HOLD`) once main carries the fix.

| What | How |
|---|---|
| A deploy | With `SITE_DEPLOY_HOLD` set (above), `pnpm exec wrangler rollback <version>` from this directory (the account comes from `wrangler.jsonc`), or delete the Custom Domain (phonometry.dev goes offline, nothing else changes). The guard leaves a rollback alone below the threshold; at the threshold it still rolls it to assets only, so set its `MODE` to `on` (or delete it) first to keep a version with code live whatever the count |
| Zone rules | With `SITE_DEPLOY_HOLD` set (above), PUT the `rules` of the file `apply-rules.mjs --apply` saved (each deploy keeps it as the artifact `zone-rules-before-<run id>`) |
| Zone records and settings | delete the records it reports as created; set each value back from the file it saved |
| The beacon | `node scripts/quota-switch.mjs --mode off`, or `pnpm exec wrangler versions deploy <assets-only version>@100`; the guard does not switch it back (only `--mode on`, or a deploy by hand, does) |
| The quota guard | `pnpm exec wrangler delete --config guard/wrangler.jsonc` (its schedule goes with it); delete its token |
| The WAF and rate rules | PUT the saved entrypoints back, as for the other rules (`--phase waf`) |
| Tokens and secrets | roll or delete the token; `gh secret delete` |

## First-deploy checks

1. A page answers 200 with no `x-robots-tag`, the security headers, an
   `etag` and its `Link` to the copy; the copy answers
   `text/markdown; charset=utf-8` with its canonical `Link` and one
   `Content-Type`; llms.txt and robots.txt answer `text/plain; charset=utf-8`;
   the Spanish API pages carry no `Link`.
2. A request with `Accept: text/markdown` gets the 302 with `Vary: Accept` and
   `Cache-Control: no-store`; a browser Accept does not.
3. Every retired address answers 301; one with a query string keeps it (if it
   does not, the pairs move to an account Bulk Redirects list, which runs before
   Workers and keeps the query).
4. `/nope/`, `/nope/index.md` and `/nope` answer 404 with
   the site's page, `text/html`, no `Link` and `Vary: Accept-Encoding`; a
   missing `_astro/` file is not cached for a year, a present one is.
5. A clip with a byte range: 302, then 206 from the clip host; and
   `node scripts/check-clip.mjs` plays clips in Chrome with no policy violation
   (curl cannot see a blocked clip).
6. `www.phonometry.dev/x?y` answers 301 to `phonometry.dev/x?y`, and
   `/signals?q=1` answers 301 to `/signals/?q=1`.
7. A page's bytes equal the build's file except the beacon element (staging
   holds this: `test/staging.test.mjs`).
9. A page view in a browser writes one `beacon` row; requests for pages,
   `_astro` files, Markdown copies, llms files and sitemaps do not move the
   day's Workers count (GraphQL); `GET /_v` answers the WAF's 403 without an
   invocation.
8. Whether `_headers` reach the `_redirects` responses (CORS on redirects).
