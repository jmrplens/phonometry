// What counts as a clip that plays: the verdict scripts/check-clip.mjs applies
// to what Chrome reports, on the shapes the preview produced before and after
// its pages allowed the clip host.
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { HAVE_FUTURE_DATA, clipVerdict } from '../lib/clip-check.mjs';

const src = 'https://phonometry.dev/phonometry/media/anim_bearing_load_zone.webm';

test('a clip that loaded and moved on, with no violation, passes', () => {
	assert.deepEqual(clipVerdict({ videos: [{ src, readyState: 4, error: null, currentTime: 3.9 }], violations: [] }), []);
});

test('what the preview reported while the policy blocked the redirect fails twice over', () => {
	const problems = clipVerdict({
		videos: [{ src, readyState: 0, error: 4, currentTime: 0 }],
		violations: ["media-src blocked https://docs.jmrp.io/phonometry/media/anim_bearing_load_zone.webm"],
	});
	assert.equal(problems.length, 2);
	assert.match(problems[0], /MediaError code 4/);
	assert.match(problems[1], /^Content-Security-Policy: media-src blocked https:\/\/docs\.jmrp\.io/);
});

test('a violation fails even when the clip played (one policy can be looser than the other)', () => {
	assert.equal(clipVerdict({ videos: [{ src, readyState: 4, error: null, currentTime: 2 }], violations: ['x'] }).length, 1);
});

test('too little data, a clip that never advanced, or no clip at all fails', () => {
	assert.match(clipVerdict({ videos: [{ src, readyState: HAVE_FUTURE_DATA - 1, error: null, currentTime: 0 }], violations: [] })[0], /readyState 2/);
	assert.match(clipVerdict({ videos: [{ src, readyState: 4, error: null, currentTime: 0 }], violations: [] })[0], /did not advance/);
	assert.deepEqual(clipVerdict({ videos: [], violations: [] }), ['the page has no <video> to play']);
	assert.equal(HAVE_FUTURE_DATA, 3);
});
