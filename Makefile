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
	$(MYPY) src

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

test:
	$(PYTHON) -m pytest tests/

coverage:
	$(PYTHON) -m pytest --cov=src/phonometry --cov-report=term-missing tests/

check: lint security test