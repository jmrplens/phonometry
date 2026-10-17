# AGENTS.md

phonometry is a Python library of acoustics. Each method is implemented from
the text of its governing standard and verified in CI against that standard's
own tables and worked examples. This file is where AI coding agents working on
the repository start; it states no rule of its own, and points to the
documents that do.

## Layout

- `src/phonometry/<domain>/`: the library, one package per domain (`filters`,
  `signals`, `room`, `building`, `environment`, `vibration`, `underwater` and
  the rest). `_plot` holds the renderers behind `.plot()`, `_report` the
  `.report()` fiches, and `_internal` the shared helpers no user imports.
- `scripts/`: the generators (figures, diagrams, fiches, the API reference,
  `llms.txt`, the conformance report under `scripts/conformance/`) and the
  guards, `scripts/check_*.py`, that CI runs.
- `tests/`: the test suite.
- `docs/`: the plain-markdown mirror of the documentation that GitHub serves,
  and `docs/contributing/`, the contributor style guide.
- `site/`: the documentation website, built with pnpm.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e ".[full]"
```

## Before a pull request

```bash
ruff check .
ruff format --check .
mypy src scripts stub/src tests/static_typing
bandit -q -r src
zizmor --config .github/zizmor.yml .github/
pytest -n 8
make conformance
make api-docs
make llms
```

Then run the guards of the area you changed: each rule of the style guide
names the check that enforces it, a test that pytest runs, a script under
`scripts/`, a `make` target or a CI job. The last three commands above
regenerate committed files; [CONTRIBUTING.md](CONTRIBUTING.md) says what to
commit from them (sections 5 and 5a).

## What to read

1. [docs/contributing/index.md](docs/contributing/index.md): the style guide,
   every rule with its identifier and its check.
2. The page of the guide for the area you are changing.
3. [CONTRIBUTING.md](CONTRIBUTING.md) for the process: setup, gates, generated
   media, the conformance report, errata, releasing and pull requests.
