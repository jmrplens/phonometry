<!-- Written by `make llms` from site/src/content/docs/start/privacy.md: edit that page and its Spanish twin, then run `make llms`. -->

← [Documentation index](../README.md) · Published at https://phonometry.dev/start/privacy/

# Privacy

This site sets no cookies, shows no ads, loads nothing from another company's
servers and follows nobody from site to site. It does count page views and it
does see requests, and this page lists every field that is kept, where, and for
how long, so that you can check each claim against the site itself.

## Who runs it

I do: José Manuel Requena Plens, who maintains phonometry (see
[About](about.md)). There is no company and nobody else with access to
these records. Cloudflare serves the site and processes requests on my behalf;
its own handling is described in the
[Cloudflare privacy policy](https://www.cloudflare.com/privacypolicy/).

## Page views

After a page has loaded, a small script in it sends one report to `/_v` on
phonometry.dev itself, never to another host. The report holds the page
address and the first 128 characters of its query string, the referrer (up to
512 characters), how you arrived (a link, a reload, the back button or a
prerender), how long the page took to load, your screen size, window size and
pixel ratio, your browser's language and time zone, whether the browser says it
is driven by automation, and whether the page was the "not found" page. It sets
no cookie, assigns no identifier and keeps nothing between pages, so nothing in
the report links one visit to the next or follows you to another site. The row
it becomes does hold your IP address and User-Agent (next paragraph), which stay
the same while your connection and browser do, so two rows can be matched by
them; no profile is built from them, as the end of this section says.

That report reaches a small Worker of mine at Cloudflare, which stores it as one
row together with what the request itself carries: your IP address, your full
User-Agent, the languages your browser accepts, the Sec-Fetch headers it sends,
and what Cloudflare associates with your address (country, region, city, postal
code, time zone, continent, approximate coordinates, network operator), plus
the Cloudflare data centre that answered, the round-trip time of your
connection, and the HTTP and TLS versions used. To stop a flood, a Cloudflare
rule turns away more than ten reports from one address in ten seconds before
they reach the Worker, and the Worker marks as over the limit, while still
storing it, every report beyond 30 in a minute from one address; neither counter
is stored anywhere.

The rows live in a Cloudflare Analytics Engine dataset that Cloudflare keeps
for about ninety days. Every five minutes they are copied into my own
monitoring database, where they are kept for one year and then deleted.
Cloudflare keeps no execution log of this Worker: its logs are switched off.

These numbers tell me which pages are read and which ones answer "not found",
so that I know what to keep up to date and what to fix. That is their only use.
They are not combined with anything else, not used to build profiles of readers
and not shared with anyone.

## Requests

Cloudflare serves every file of the site, so it sees every request, including
the ones no browser makes: crawlers and agents that read the Markdown copies,
the llms files and the sitemaps run no script and send no page-view report. For
its own analytics Cloudflare records, for each request, the time, your IP
address, the path and query asked for, the User-Agent, the network and country
it comes from, the method and the response status (Cloudflare keeps them for
31 days). Every five minutes the records of the files agents read (the Markdown
copies, the llms files, the sitemaps, robots.txt and the files under
`/.well-known/`) are copied into the same monitoring database as the page
views, where they are kept for one year and then deleted, so that I can see
which files crawlers fetch.

## Cookies and storage

No response from this site carries a `Set-Cookie` header. What the site keeps
on your device is short, and none of it is ever sent anywhere:

- in `localStorage`, your colour theme, your language once you choose one, the
  fact that you dismissed the suggestion to switch language, and which tab you
  picked in a group of tabs (for example `pip` or `conda`), so the same tab
  opens on the next page;
- in `sessionStorage`, only while the tab is open, the state of the side
  navigation.

The suggestion to read a page in the other language compares the languages your
browser advertises with the page's own, entirely in your browser.

## Other hosts

Every file a page loads comes from phonometry.dev, or, for the video clips,
from media.phonometry.dev, the site's own host for them. A Content Security
Policy holds pages to that: scripts, styles, fonts and images are accepted from
this origin only. The search box runs in your browser: its index is downloaded
from this site, and what you type is never sent anywhere.

If your browser blocks something on a page (a Content Security Policy
violation), it may send a short report naming the page address, the referrer
and the resource it blocked to `jmrp.io/csp-report`, my own server, where it is
handled as the [jmrp.io privacy page](https://jmrp.io/privacy/) describes. Those
reports exist so that a broken page is noticed the same day.

A link to another site (GitHub, PyPI, a standard's publisher) takes you to that
site, and from then on its own policy applies.

## Signals your browser sends

[`/.well-known/gpc.json`](https://phonometry.dev/.well-known/gpc.json) declares that this site
honours Global Privacy Control. Nothing here is sold or shared for advertising,
so the signal has nothing to turn off; the file states that in the form a
browser can read.

## No ads, no affiliates

There is no advertising, no affiliate link, no sponsored content and no mailing
list. The [support page](support.md) lists ways to help the project; its
links are ordinary links that set nothing and measure nothing.

## Your data

You can ask me what is held about you, or ask me to delete it. Nothing here
holds a name or an account, so to find your rows I need the IP address you used
and roughly when. Write to `mail@jmrp.io`. Security reports have their own
channel: [`/.well-known/security.txt`](https://phonometry.dev/.well-known/security.txt) and the
project's
[security policy](https://github.com/jmrplens/phonometry/security/policy).
