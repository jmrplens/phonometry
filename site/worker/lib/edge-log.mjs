// cspell:words otros formado -- Spanish labels shared with the Telegraf Starlark (ua_class, referer host)
// The data point the Worker writes for each request it runs for: docs-edge's.
//
// Everything from NAMED_AGENTS to the end of logEdgeRequest is a VERBATIM
// copy of the logging block of docs-edge, the Worker in front of
// docs.jmrp.io (workers/docs-edge/worker.js in the jmrp.io repository),
// with `export` added to the four functions this Worker calls. Its blob
// layout is a contract with the maintainer's ingestion
// (scripts/ae-to-influx.mjs there, which reads phonometry.dev rows like
// docs.jmrp.io's): change it there first, then copy it here whole;
// test/edge-log.test.mjs compares the two texts when that repository is on
// the machine. requestClass strips the first path segment, which on both
// hosts is the base path /phonometry, so a row classifies the same on both.
// Do not reformat this file: the comparison is of the text.
/* eslint-disable */

const NAMED_AGENTS = [
  "GPTBot",
  "ChatGPT-User",
  "OAI-SearchBot",
  "ClaudeBot",
  "Claude-User",
  "Claude-SearchBot",
  "PerplexityBot",
  "Perplexity-User",
  "Google-Extended",
  "Googlebot",
  "bingbot",
  "DuckDuckBot",
  "Applebot",
  "Amazonbot",
  "Bytespider",
  "CCBot",
  "meta-externalagent",
  "facebookexternalhit",
  "AhrefsBot",
  "SemrushBot",
  "MJ12bot",
  "DotBot",
  "YandexBot",
  "PetalBot",
  "Timpibot",
  "archive.org_bot",
  "curl",
  "wget",
  "python-requests",
  "Go-http-client",
  "okhttp",
  // Added 2026-09-22. In the five days to that date "otros-bots" was the
  // largest bot bucket at the edge (2842 requests), which made the breakdown
  // useless; these are the names behind it, ordered by volume. Checked
  // against the 400 distinct user-agents of the preceding week: 31 rows move
  // out of "otros-bots"/"otros" and no already-named agent is renamed.
  // A name here is a label, never proof: the GCP scanner of that same round
  // wore most of these.
  "jscrawler",
  "DuckAssistBot",
  "PanguBot",
  "SERankingBacklinksBot",
  "ExaSearchBot",
  "cohere-ai",
  "KimiBot",
  "Kimi-SearchBot",
  "MoonshotBot",
  "DataForSeoBot",
  "Qwenbot",
  "Qwantbot",
  "Bravebot",
  "ChatGLM-Spider",
  "Baiduspider",
  "GrokBot",
  "xAI-Grok",
  "DeepSeekBot",
  "LinkupBot",
  "YiBot",
  "YouBot",
  "WhyNoIPv6Bot",
  "BrickBlueBot",
  "SeznamBot",
  "ShapBot",
  "Sogou",
  "MCP-Cloud-AboutBot",
  "Barkrowler",
];

/**
 * Request class (index1) for docs.jmrp.io. Every project site lives under
 * /<repo>/, so the class is decided on the path AFTER that first segment:
 * a project's /llms.txt, /_astro/ and sitemap classify exactly as jmrp.io's
 * do. Files at the host root (robots.txt, the hub sitemap, the IndexNow key)
 * keep their plain path.
 *
 * @param {string} fullPath - The request path, prefix included.
 * @returns {string} The class.
 */
export function requestClass(fullPath) {
  const m = /^\/[^/]+(\/.*)$/.exec(fullPath);
  const p = m ? m[1] : fullPath;
  if (p.endsWith(".md")) return "md-twin";
  if (p.endsWith(".txt") && p.includes("llms")) return "llms-txt";
  if (p.endsWith(".pdf")) return "pdf";
  if (p.endsWith(".xml")) return "feed-xml";
  if (
    p.startsWith("/_astro/") ||
    p.startsWith("/assets/") ||
    p.startsWith("/pagefind/")
  ) {
    return "asset";
  }
  if (p.endsWith("/") || !p.includes(".")) return "page";
  return "other";
}

/**
 * Substrings that mark a User-Agent as automated (blob 2 "bot"), matched
 * case-insensitively. Telegraf's clean_metrics.star keeps the same list in
 * UA_BOT_MARKS for nginx rows: change both together.
 */
const BOT_MARKS = [
  "bot",
  "crawl",
  "spider",
  "gpt",
  "claude",
  "perplexity",
  "bingpreview",
  "slurp",
  "grok",
  "externalhit",
  "curl",
  "wget",
  "python",
  "aiohttp",
  "go-http-client",
  "okhttp",
  "scrapy",
  "lychee",
  "camo",
  "rss",
  "validator",
  "checker",
  "webfetch",
  "notebooklm",
  "hunyuan",
  "turnitin",
];

/** Coarse UA class (blob 2): bot, browser or empty-ua. */
export function agentClass(ua) {
  if (!ua) return "empty-ua";
  // "grok" is here for xAI-Grok alone: its UA is
  // `Mozilla/5.0 (compatible; xAI-Grok/1.0; +https://x.ai/)`, which carries
  // none of the other markers, so blob2 called a crawler a browser while
  // blob4 named it correctly. Checked over the 400 distinct user-agents of
  // the week to 2026-09-22: exactly one of them changes class, that one.
  // Automated clients that name no crawler, added 2026-10-14: link
  // previewers (facebookexternalhit), HTTP libraries and CLIs (curl, wget,
  // python, aiohttp, go-http-client, okhttp, scrapy, got-style fetchers),
  // image proxies (github-camo, Tangled Camo), feed readers (FreshRSS, RSS
  // Guard), link checkers and validators (lychee, our own CI), and fetchers
  // that call themselves tools (WebFetch, NotebookLM, Hunyuan, Turnitin).
  // Over three days of the three edge datasets this moved 2012 requests out
  // of "browser" and no real browser family: the one "Chrome" that moved is
  // RSS Guard, a feed reader on QtWebEngine. Telegraf's clean_metrics.star
  // keeps the same list in UA_BOT_MARKS.
  const lower = ua.toLowerCase();
  if (BOT_MARKS.some((mark) => lower.includes(mark))) return "bot";
  // Every real Chrome, Edge and Opera sends "AppleWebKit/537.36 (KHTML, like
  // Gecko)". A UA that claims Chrome without it is a client in disguise: over
  // three days all five such UAs were scanners and minimal fetchers (the top
  // one, "...Win64; x64) Chrome/120.0.0.0", made 204 requests).
  if (ua.includes("Chrome/") && !ua.includes("AppleWebKit/")) return "bot";
  return "browser";
}

/** Browser families by UA marker, in the order the old regex chain tested them. */
const BROWSER_FAMILIES = [
  ["Edg/", "Edge"],
  ["OPR/", "Opera"],
  ["Firefox/", "Firefox"],
  ["Chrome/", "Chrome"],
  ["Safari/", "Safari"],
];

/** Named agent or family (blob 4), same vocabulary as before. */
export function agentName(ua, uaClass) {
  const lower = ua.toLowerCase();
  let bestPos = -1;
  let bestLen = 0;
  for (const name of NAMED_AGENTS) {
    const pos = lower.indexOf(name.toLowerCase());
    if (pos !== -1 && (bestPos === -1 || pos < bestPos)) {
      bestPos = pos;
      bestLen = name.length;
    }
  }
  if (bestPos !== -1) return ua.slice(bestPos, bestPos + bestLen);
  if (uaClass === "bot") return "otros-bots";
  const family = BROWSER_FAMILIES.find(([marker]) => ua.includes(marker));
  if (family) return family[1];
  return ua ? "otros" : "(sin-ua)";
}

/** Referer host when it is not this site; "(mal-formado)" when unparsable. */
function refererHost(referer, ownHost) {
  if (!referer) return "";
  try {
    const h = new URL(referer).hostname;
    return h === ownHost ? "" : h;
  } catch {
    return "(mal-formado)";
  }
}

/** Blob 20: the long tail of request/response facts, "|"-joined (see layout). */
function miscBag(cf, h, rh) {
  return [
    cf.region ?? "",
    cf.regionCode ?? "",
    cf.tlsCipher ?? "",
    cf.continent ?? "",
    cf.timezone ?? "",
    h("sec-fetch-dest"),
    h("sec-fetch-mode"),
    h("sec-fetch-site"),
    String(cf.botManagement?.verifiedBot ?? ""),
    h("cf-ray"),
    rh("content-type").slice(0, 60),
    h("accept-encoding").slice(0, 40),
    String(cf.isEUCountry ?? ""),
    cf.postalCode ?? "",
  ].join("|");
}

/**
 * Writes ONE Analytics Engine datapoint for a request, at the exit of every
 * path so it carries the final status and the edge-cache verdict. Never in
 * the serving path: a failed write must not cost a page view.
 *
 * Blob layout is an API contract with scripts/ae-to-influx.mjs and the daily
 * report (append, never reorder). Blobs 1-13 are the original record; 14-20
 * and doubles 3-9 were appended on 2026-09-05 to capture everything the
 * edge knows, so filtering can happen locally instead of here:
 *   1 path · 2 uaClass · 3 country · 4 agent · 5 referer host · 6 colo
 *   7 city · 8 ASN org · 9 http protocol · 10 TLS version · 11 status
 *   12 cache verdict · 13 Accept (64) · 14 method · 15 full User-Agent (256)
 *   16 client IP · 17 Accept-Language (64) · 18 full referer (200)
 *   19 query string (128, no "?") · 20 misc, "|"-joined in this order:
 *      region|regionCode|tlsCipher|continent|timezone|sec-fetch-dest|
 *      sec-fetch-mode|sec-fetch-site|verifiedBot|cf-ray|response
 *      content-type|accept-encoding|isEUCountry|postalCode
 * Doubles: 1 latitude · 2 longitude · 3 ASN · 4 client TCP RTT (ms)
 *   5 response Content-Length · 6 response Age · 7 worker time (ms)
 *   8 bot score (0 without Bot Management) · 9 request time (ms epoch)
 * Analytics Engine caps a datapoint at 20 blobs and 5 KB of blob data; the
 * truncations keep the worst case under 2 KB.
 *
 * @param {object} args - env, request, url, startedAt, status, cacheStatus, response.
 */
export function logEdgeRequest({
  env,
  request,
  url,
  startedAt,
  status,
  cacheStatus,
  response,
}) {
  try {
    const p = url.pathname;
    const ua = request.headers.get("user-agent") ?? "";
    const uaClass = agentClass(ua);
    const cf = request.cf ?? {};
    const h = (name) => request.headers.get(name) ?? "";
    const rh = (name) => response?.headers.get(name) ?? "";
    const misc = miscBag(cf, h, rh);
    env.REQS?.writeDataPoint({
      indexes: [requestClass(p)],
      blobs: [
        p.slice(0, 256),
        uaClass,
        cf.country ?? "",
        agentName(ua, uaClass).slice(0, 60),
        refererHost(h("referer"), url.hostname).slice(0, 120),
        cf.colo ?? "",
        String(cf.city ?? "").slice(0, 60),
        String(cf.asOrganization ?? "").slice(0, 80),
        cf.httpProtocol ?? "",
        cf.tlsVersion ?? "",
        String(status),
        cacheStatus ?? "",
        h("accept").slice(0, 64),
        request.method,
        ua.slice(0, 256),
        h("cf-connecting-ip"),
        h("accept-language").slice(0, 64),
        h("referer").slice(0, 200),
        url.search.slice(1, 129),
        misc.slice(0, 400),
      ],
      doubles: [
        Number.parseFloat(cf.latitude) || 0,
        Number.parseFloat(cf.longitude) || 0,
        Number(cf.asn) || 0,
        Number(cf.clientTcpRtt) || 0,
        Number(rh("content-length")) || 0,
        Number(rh("age")) || 0,
        Date.now() - startedAt,
        Number(cf.botManagement?.score) || 0,
        startedAt,
      ],
    });
  } catch {
    // Analytics must never break serving.
  }
}
