// What a browser has to report for a clip of the preview to count as playing.
//
// curl sees a clip as a 302 and a 206 and stops there. A browser also holds
// the address a clip is redirected to against the page's
// Content-Security-Policy, and a host left out of `media-src` blocks every
// clip while curl still reports success. scripts/check-clip.mjs plays one
// clip in Chrome and hands what it saw to clipVerdict.

/** HTMLMediaElement.HAVE_FUTURE_DATA: enough data to play forward. */
export const HAVE_FUTURE_DATA = 3;

/**
 * The problems in what the browser reported, empty when the clip played.
 *
 * @param {object} seen
 * @param {{src: string, readyState: number, error: number | null, currentTime: number}[]} seen.videos
 *   Each clip tried: its address, readyState, MediaError code and position after playing.
 * @param {string[]} seen.violations Every Content-Security-Policy violation the page reported
 *   (securitypolicyviolation events and console messages that name the policy).
 * @returns {string[]} One line per problem.
 */
export function clipVerdict({ videos, violations }) {
	const problems = [];
	if (videos.length === 0) problems.push('the page has no <video> to play');
	for (const video of videos) {
		if (video.error !== null) problems.push(`${video.src}: MediaError code ${video.error}`);
		else if (video.readyState < HAVE_FUTURE_DATA) problems.push(`${video.src}: readyState ${video.readyState}, below ${HAVE_FUTURE_DATA}`);
		else if (!(video.currentTime > 0)) problems.push(`${video.src}: did not advance`);
	}
	for (const line of violations) problems.push(`Content-Security-Policy: ${line}`);
	return problems;
}
