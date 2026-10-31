# Security policy

## What this project is

phonometry is a scientific Python library. It computes acoustic, vibration and
psychoacoustic quantities from arrays and files you hand it, inside your own
process. It runs no service, opens no socket, holds no credentials, and never
executes code derived from what you pass it: it calls its own code and its
declared dependencies, nothing else. That shapes what a vulnerability can be
here, so this policy is written for this library rather than copied from a
generic template.

## Supported versions

Fixes ship forward. There are no backports: a security fix is released as a new
version from `main`, and the remedy for any older version is to upgrade.

| Version | Supported |
| :--- | :--- |
| Latest 3.x release | Yes |
| Earlier 3.x releases | Upgrade to the latest 3.x |
| 2.x and earlier, including `PyOctaveBand` | No |

The `PyOctaveBand` package on PyPI is a stub that only redirects to
`phonometry` and receives no fixes.

Supported interpreters and platforms are whatever the test matrix in
[`.github/workflows/python-app.yml`](.github/workflows/python-app.yml)
exercises, at the time of writing Python 3.12, 3.13 and 3.14 on Ubuntu, macOS
and Windows. That workflow is the authority, not this paragraph. A report that
reproduces only outside the matrix is handled as an ordinary bug.

## Reporting a vulnerability

Report privately through GitHub, with **Security > Report a vulnerability**, or
directly at
[github.com/jmrplens/phonometry/security/advisories/new](https://github.com/jmrplens/phonometry/security/advisories/new).
That opens a private advisory visible only to you and the maintainers, and keeps
the report, the fix and any CVE in one place.

If private reporting is not available to you, write to `mail@jmrp.io`, the
maintainer address already published in [`CITATION.cff`](CITATION.cff) and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), with `phonometry security` in the
subject. Please do not use a public issue, a discussion or a pull request for a
suspected vulnerability.

A useful report states the version and interpreter, a minimal reproduction, the
input that triggers the behaviour, and what an attacker gains. If a standard is
involved, cite the clause or table by number rather than pasting the text.
Standards are copyrighted.

### What to expect

This library is maintained by one person alongside research work, so these are
commitments I can keep rather than an enterprise service level:

| Step | Target |
| :--- | :--- |
| Acknowledgement that the report arrived | 5 working days |
| First assessment: accepted, more information needed, or out of scope | 15 working days |
| Release containing the fix, once accepted | with the next release, sooner if the impact warrants it |

If the acknowledgement window passes in silence, add a comment on the advisory.
It means the notification was missed, not that the report was dismissed.

## Coordinated disclosure

I work to coordinated disclosure. Please give me a chance to publish a fixed
release before going public. In return I keep the advisory updated while it is
open, credit you unless you would rather stay anonymous, and publish the advisory
(with a CVE where GitHub assigns one) once the fixed version is on PyPI.

Ninety days from acknowledgement is a reasonable ceiling. If a fix is going to
take longer than that I will say so on the advisory instead of letting it go
quiet.

## Scope

### Treated as a vulnerability

- **Untrusted input reaching a computation.** Measurement arrays, samples
  decoded elsewhere and passed in, and above all the file readers: the aircraft
  noise module reads ANP CSV exports from a directory you point it at. If a
  crafted file causes anything worse than a clean exception, for example
  unbounded memory growth, a path that escapes the directory it was given, or an
  attempt to execute what was read, that is a vulnerability.
- **Deserialisation.** The library deliberately never unpickles, evaluates or
  imports anything derived from input. A code path that does is a defect worth
  reporting even without a working exploit.
- **Supply chain.** Anything that can place code into a published artefact: the
  release workflow, the contents of the built wheel or sdist, package data
  reaching outside the package, or a dependency declaration that resolves
  somewhere unexpected.
- **Repository automation.** A workflow in this repository that can be made to
  run attacker-controlled code, leak a secret, or escalate its token
  permissions.

### Not treated as a vulnerability

- **A value that disagrees with a standard.** This is the failure mode that
  matters most in this library, and it is a conformance defect, not a security
  issue. Once the disagreement has been established, usually in
  [Standards & conformance](https://github.com/jmrplens/phonometry/discussions/categories/standards-conformance),
  file it with the
  [conformance defect form](https://github.com/jmrplens/phonometry/issues/new?template=02-conformance-defect.yml).
  It is handled with the same seriousness as a security report, in public, where
  the numbers can be checked.
- **A defect in the published standard itself.** Misprints and worked examples
  that contradict their own normative text are recorded in
  [`docs/ERRATA.md`](docs/ERRATA.md) with the evidence and the reading the
  library implements. Those entries are documentation, never security
  advisories.
- **Resource exhaustion you asked for**, such as requesting a transform over an
  array that does not fit in memory. The library computes what it is told to
  compute.
- **Results from inputs outside the validity range of a method**, for instance a
  temperature or a frequency beyond what the standard covers. The guides state
  the ranges; a missing range check is a bug report.
- **Vulnerabilities in numpy, scipy, matplotlib, reportlab or any other
  dependency.** Report those upstream. If phonometry uses the dependency in a way
  that exposes users to it, that use is in scope here.
- **Scanner output with no demonstrated impact**, and hardening suggestions with
  no exploit path. Both are welcome as ordinary issues.

## What already runs

Rather than describe a process I do not have, here is the tooling that runs on
every pull request and on `main`:

- **CodeQL** default setup, weekly and on change, over the Python,
  JavaScript/TypeScript and GitHub Actions code.
- **bandit** over `src/` in the `quality` job. Any finding fails the build,
  including Low severity, so the source stays clean of `assert` in library code,
  unreviewed subprocess use and hardcoded secrets.
- **GitGuardian** secret scanning on every pull request.
- **Dependabot** security and version updates for pip, npm and GitHub Actions,
  grouped weekly, each proposed three days after it is published rather than
  the morning it appears.
- **zizmor** over everything under `.github/` in the `quality` job: a workflow
  that expands untrusted input into a shell, grants a token it does not need,
  leaves its token in `.git` or uses an action with a published advisory
  fails the build.
- **Snyk** through the `snyk` target in the `Makefile`, for an on-demand
  dependency audit.

Workflows declare `contents: read` at the top level and widen permissions only
on the individual jobs that need them; the release workflow grants nothing at
the top level at all.

## Verifying a release

Every release from 4.0.0 on is built, checked and published by
`.github/workflows/release.yml`, run by a push to `main` on a runner GitHub
hosts. It is uploaded to PyPI through trusted publishing: no token is stored
anywhere, and PyPI attaches to each file a
[PEP 740](https://peps.python.org/pep-0740/) attestation, which the file's
page on PyPI shows under Provenance. The GitHub Release carries the same wheel
and sdist, a checksum file, `phonometry-<version>.sha256`, and a CycloneDX
SBOM, `phonometry-<version>.cdx.json`, of what `pip install phonometry`
resolved on the day. GitHub keeps a build provenance attestation for each of
those four files, and an SBOM attestation that ties the SBOM to the wheel.

The signing is keyless, so there is no key file to fetch or to trust: each
attestation is signed with a short-lived Sigstore certificate issued to the
run of the workflow, and a verification checks the identity that certificate
names.

- Issuer: `https://token.actions.githubusercontent.com`.
- Identity: `https://github.com/jmrplens/phonometry/.github/workflows/release.yml@refs/heads/main`.
- Runner: one GitHub hosts, never a self-hosted one.
- On PyPI, the trusted publisher of phonometry: owner `jmrplens`, repository
  `phonometry`, workflow `release.yml`, no environment.

To check that a file is one this repository's release workflow built:

```bash
# The wheel, the sdist, the checksum file or the SBOM, from PyPI or the GitHub Release.
gh attestation verify phonometry-4.0.0-py3-none-any.whl --repo jmrplens/phonometry \
    --signer-workflow jmrplens/phonometry/.github/workflows/release.yml \
    --source-ref refs/heads/main --deny-self-hosted-runners

# The SBOM attestation, made for the wheel.
gh attestation verify phonometry-4.0.0-py3-none-any.whl --repo jmrplens/phonometry \
    --predicate-type https://cyclonedx.org/bom \
    --signer-workflow jmrplens/phonometry/.github/workflows/release.yml \
    --source-ref refs/heads/main --deny-self-hosted-runners

# The PEP 740 attestation PyPI serves, without downloading anything first.
python -m pip install pypi-attestations
python -m pypi_attestations verify pypi --repository https://github.com/jmrplens/phonometry \
    pypi:phonometry-4.0.0-py3-none-any.whl

# The files of the GitHub Release against the checksum file it carries.
sha256sum --check phonometry-4.0.0.sha256
```

The signed source of a release is its sdist: the source the wheel was built
from, attested like the wheel. The "Source code" archives GitHub offers on
every release are made from the tag when they are downloaded and carry no
signature, and neither does the zip Zenodo keeps, which is made from one of
them.

The SBOM lists the runtime dependencies at the versions the release resolved
(`numpy` and `scipy`); the optional extras are not in it, because a plain
install does not bring them.

Integrity of the numbers is gated too, which matters more here than in most
libraries: `docs/CONFORMANCE.md` is regenerated in CI from the library's own
computations against reference values and the build fails if the committed
report drifts, so a change that quietly moves a standards-conformant result
cannot reach a release unnoticed.

## Rebuilding a release

Every release from 4.0.0 on rebuilds from its tag to the bytes PyPI and the
GitHub Release hold, on Linux and on macOS. The release workflow builds every
release twice before it publishes and refuses one whose builds differ, and
once it has published it clones the tag on macOS, rebuilds it as below and
compares the files with PyPI's; a rehearsal does the same with the commit it
builds and its own files, and so does every pull request. To rebuild one
yourself, with Python 3.13, which the release builds with:

```bash
git clone --depth 1 --branch v4.0.0 --config core.autocrlf=false \
    https://github.com/jmrplens/phonometry.git
cd phonometry
python3.13 -m venv ../phonometry-build
../phonometry-build/bin/python -m pip install -r requirements-release.txt
../phonometry-build/bin/python scripts/build_release.py --outdir ../rebuilt --check-pypi
```

`scripts/build_release.py` builds the sdist with the setuptools that
`requirements-release.txt` pins, without build isolation, and with every
time stamp set to the commit's. It writes the sdist again without the time of
the build, the builder's user or the checkout's modes, builds the wheel from
that sdist under umask 022, and compares both files with the digests PyPI
publishes for the version; `--check phonometry-4.0.0.sha256` compares them
with the release's checksum file instead. It refuses a checkout that differs
from its commit, and an environment in which another package installs a
setuptools plugin that could change what is packed, which is why the build
gets a virtual environment of its own. `core.autocrlf=false` keeps the files
as the commit holds them, and `.gitattributes` checks out every file the sdist
carries with LF whatever `core.autocrlf` or `core.eol` the cloner has set.

The script refuses to build on Windows, where the operating system reaches
the bytes: zipfile records the system that wrote each member of the wheel,
setuptools gives the wheel's modules the mode Windows reports, and it writes
the sdist's `PKG-INFO` and `setup.cfg` with CRLF. On Windows, run the commands
above inside WSL, from a clone made in WSL's own filesystem (under `~`, not
under `/mnt/c`, where the files carry no Unix modes and every one of them
looks executable).

The compressed bytes of both files come from the zlib that Python is linked
against. The release compares a build on Linux with one on macOS; a Python
linked against another implementation of it, such as zlib-ng, compresses the
same files to other bytes.

## Credit

Reporters are credited in the published advisory and in the changelog entry for
the release that carries the fix, unless they ask not to be.
