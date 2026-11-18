// The quota guard Worker (lib/guard.mjs says what it decides and why).
//
// It has no route and no fetch handler: only its Cron Trigger runs it, every
// 15 minutes (96 invocations a day, which count toward the same quota), so
// no visitor request can reach the one Worker that holds a token able to
// redeploy the site. The token is the secret CF_GUARD_TOKEN; without it every
// run is dry. MODE (a variable) is `dry-run` until the maintainer sets
// `auto`; `off` and `on` pin a state by hand. Each run logs one line per
// fact and action (Workers Logs, observability in guard/wrangler.jsonc).
import { reconcile } from '../../lib/guard.mjs';

export default {
	async scheduled(controller, env, ctx) {
		ctx.waitUntil(
			reconcile({ env, now: new Date(controller.scheduledTime) }).then((report) => {
				for (const line of report.lines) console.log(`[quota-guard] ${line}`);
			}),
		);
	},
};
