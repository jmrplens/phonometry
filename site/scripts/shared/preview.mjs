// Where the site's audits start `astro preview`, and the check for a server
// already on its port, shared by with-preview.mjs and lighthouse-audit.mjs.
//
// Given no host, Vite listens on `localhost` as the resolver orders it, and in
// a stock node:24 container that is ::1 first, while Node's own fetch there
// tries 127.0.0.1 alone: a runner polling `localhost` was refused until its
// ceiling and no audit ran. So the preview is pinned to the IPv4 loopback and
// polled there. A browser opening `localhost` may still reach either loopback,
// so a server already on the port is looked for on both.

/** The address the preview listens on and is polled at. */
export const PREVIEW_HOST = '127.0.0.1';

/**
 * The arguments that start `astro preview` on `port` as a server of the
 * runner's own: on the IPv4 loopback, and in the foreground. Under an AI
 * coding agent, which Astro 7 reads from the environment, `astro preview`
 * otherwise starts the server as a detached process with a lock file and
 * exits, so the runner stopped a process that had already ended, the server
 * outlived it, and the next audit found the port taken. `--ignore-lock` keeps
 * it a one-off server in the foreground.
 */
export const previewArgs = (port) => ['preview', '--port', String(port), '--host', PREVIEW_HOST, '--ignore-lock'];

/** Both loopbacks, as a URL writes them. */
const LOOPBACKS = ['127.0.0.1', '[::1]'];

/** The first loopback something already answers on at `port`, or null when neither does. */
export async function servedLoopback(port) {
  for (const loopback of LOOPBACKS) {
    try {
      await fetch(`http://${loopback}:${port}/`, { signal: AbortSignal.timeout(2000) });
      return loopback;
    } catch {
      // Nothing listening on this one.
    }
  }
  return null;
}
