# Virtual environment detection
VENV = .venv
BIN = $(VENV)/bin

# If venv doesn't exist, use system binaries
ifeq (,$(wildcard $(VENV)))
    PYTHON = python3
    RUFF = ruff
    MYPY = mypy
    BANDIT = bandit
    PNPM = pnpm
else
    PYTHON = $(BIN)/python3
    RUFF = $(BIN)/ruff
    MYPY = $(BIN)/mypy
    BANDIT = $(BIN)/bandit
    PNPM = pnpm
endif

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .

lint:
	$(RUFF) check .
	$(MYPY) src scripts

format:
	$(RUFF) check --fix .
	$(RUFF) format .

security:
	$(BANDIT) -r src

snyk:
	@echo "Running Snyk..."
	@if [ -f .env ]; then export $$(cat .env | xargs) && $(PNPM) exec snyk test --all-projects; else $(PNPM) exec snyk test --all-projects; fi

sonar:
	@echo "Running SonarQube Scanner..."
	@if [ -f .env ]; then export $$(cat .env | xargs) && $(PNPM) exec sonar-scanner; else $(PNPM) exec sonar-scanner; fi

graphs:
	$(PYTHON) scripts/generate_graphs.py
	$(PYTHON) scripts/generate_diagrams.py

# Regenerate the fallback social-preview card (site/public/og-image.png).
# Kept out of `graphs`/CI so the committed designed asset is not clobbered on
# every build; run manually to refresh it deterministically when needed.
og:
	$(PYTHON) -c "import sys; sys.path.insert(0, 'scripts'); import generate_graphs as g; g.generate_og_image()"

llms:
	$(PYTHON) scripts/gen_llms.py

# Regenerate the committed, versioned numerical conformance report. The
# --file-header flag prepends the "do not hand-edit" note; the body is exactly
# what the CI PR-comment harness computes. CI fails if this drifts (see the
# `conformance` job in python-app.yml).
conformance:
	$(PYTHON) scripts/conformance_report.py --file-header > docs/CONFORMANCE.md

# Optional convenience: install a git pre-commit hook that regenerates
# docs/CONFORMANCE.md when the library source or the report generator changes.
# The CI staleness check is the enforcement; this only saves a round-trip.
install-hooks:
	@mkdir -p .git/hooks
	@cp hooks/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Installed .git/hooks/pre-commit (regenerates docs/CONFORMANCE.md when src/scripts change)."

test:
	$(PYTHON) -m pytest tests/

coverage:
	$(PYTHON) -m pytest --cov=src/phonometry --cov-report=term-missing tests/

check: lint security test

.PHONY: install lint format security snyk sonar graphs og llms conformance \
	install-hooks test coverage check