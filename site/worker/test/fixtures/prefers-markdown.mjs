// prefersMarkdown: a VERBATIM copy of the function in
// /var/www/jmrp.io/workers/docs-edge/markdown-negotiation.js (jmrp.io
// repository, 2026-11-17), the negotiation docs.jmrp.io runs today. The
// preview approximates it with a zone redirect rule, and
// test/negotiation.test.mjs holds the two side by side so every place they
// disagree is listed. When the jmrp.io checkout is present, that test also
// fails if this copy and the original differ.
/* eslint-disable */
function prefersMarkdown(accept) {
  if (!accept) return false;
  // [specificity, q]; specificity 2 = exact type, 1 = `type/*`, 0 = `*` + `/*`.
  let markdown = null;
  let html = null;
  const better = (a, b) =>
    b === null || a[0] > b[0] || (a[0] === b[0] && a[1] > b[1]);
  for (const part of accept.split(",")) {
    const segments = part.trim().split(";");
    const type = segments[0].trim().toLowerCase();
    if (!type) continue;
    // `q=.8` (no leading zero) is legal in the wild, hence `\d*` plus the
    // non-empty guard: an unparseable `q=` leaves the default of 1.
    // The outer whitespace goes to trim(), not to the pattern: `\s*` on both
    // sides of a group that can match empty backtracks in quadratic time on
    // `q=`, a run of spaces and any other character (64 KB of them: 6 s).
    // trim() strips exactly what `\s` matches, so every result is unchanged.
    let q = 1;
    for (const parameter of segments.slice(1)) {
      const match = /^q\s*=\s*(\d*(?:\.\d+)?)$/i.exec(parameter.trim());
      if (match && match[1] !== "") q = Number.parseFloat(match[1]);
    }
    if (!Number.isFinite(q) || q < 0) q = 0;
    if (q === 0) continue; // "not acceptable": no vote at all
    if (type === "text/markdown") {
      if (better([2, q], markdown)) markdown = [2, q];
    } else if (type === "text/html" || type === "application/xhtml+xml") {
      if (better([2, q], html)) html = [2, q];
    } else if (type === "text/*") {
      if (better([1, q], html)) html = [1, q];
    } else if (type === "*/*") {
      if (better([0, q], html)) html = [0, q];
    }
  }
  if (markdown === null) return false;
  if (html === null) return true;
  return !better(html, markdown); // ties go to markdown
}
/* eslint-enable */

export { prefersMarkdown };
