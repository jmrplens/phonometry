/**
 * The one reading of a PEP 440 version the site makes: whether it is a
 * pre-release. src/data/repo-stats.mjs reads VERSION through it.
 *
 * @module
 */

/**
 * Whether a version string is a pre-release by PEP 440: it carries a
 * pre-release segment (an alpha, a beta or a release candidate, in any of the
 * spellings PEP 440 normalises) or a development segment, which pip installs
 * only when asked to. A final release and a post-release are not. The same
 * reading as packaging's `Version.is_prerelease`, which scripts/generate_llms.py
 * uses; src/data/pep440-pre-releases.json is the table both are tested on.
 *
 * @param {string} text
 * @returns {boolean}
 */
export function isPreRelease(text) {
  const parsed =
    /^v?\d+(?:\.\d+)*(?<pre>[-_.]?(?:a|b|c|rc|alpha|beta|pre|preview)[-_.]?\d*)?(?:-\d+|[-_.]?(?:post|rev|r)[-_.]?\d*)?(?<dev>[-_.]?dev[-_.]?\d*)?(?:\+[a-z0-9]+(?:[-_.][a-z0-9]+)*)?$/i.exec(
      text.trim(),
    );
  if (parsed === null) throw new Error(`"${text}" is not a PEP 440 version`);
  return parsed.groups?.pre !== undefined || parsed.groups?.dev !== undefined;
}
