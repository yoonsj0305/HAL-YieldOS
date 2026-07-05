PYTHON ?= python

.PHONY: all test test-quick demo sweep sweep-large gen-large gen-robot gen-sat gen-all run-all validate clean help install

all: help

# ── Install ──────────────────────────────────────────────────────────────
install:
	$(PYTHON) -m pip install -e .

# ── Tests ───────────────────────────────────────────────────────────────
test:
	@echo "[YieldOS] Running tests..."
	$(PYTHON) -m pytest tests/ -v

test-quick:
	@echo "[YieldOS] Quick test..."
	$(PYTHON) -m pytest tests/ -q

# ── Sample runs ─────────────────────────────────────────────────────────
semfab:
	$(PYTHON) -m yieldos.cli.main semifab analyze \
		--input samples/semfab_tel_like \
		--out output/semfab_case_001

robot:
	$(PYTHON) -m yieldos.cli.main robot analyze \
		--input samples/robot_ooda/robot_telemetry.csv \
		--out output/robot_case_001

sat:
	$(PYTHON) -m yieldos.cli.main sat analyze \
		--input samples/satguard/satellite_telemetry.csv \
		--out output/sat_case_001

semiforge:
	$(PYTHON) -m yieldos.cli.main semiforge simulate \
		--config samples/semiforge_crossbar/config.json \
		--out output/semiforge_run_001 \
		--mc 30

# ── Sweep ───────────────────────────────────────────────────────────────
sweep:
	@echo "[YieldOS] SemiForge sweep (0%-40% defect rate)..."
	$(PYTHON) -m yieldos.cli.main semiforge sweep \
		--out output/sweep_001 \
		--rows 64 --cols 64 \
		--dist both \
		--mc 30

sweep-large:
	@echo "[YieldOS] SemiForge sweep 128x128 (higher precision)..."
	$(PYTHON) -m yieldos.cli.main semiforge sweep \
		--out output/sweep_128 \
		--rows 128 --cols 128 \
		--dist both \
		--mc 50

# ── Synthetic data generation ────────────────────────────────────────────
gen-large:
	@echo "[YieldOS] Generating large synthetic SemFab dataset (20 lots)..."
	$(PYTHON) -m yieldos.cli.main semifab gen \
		--out samples/semfab_large \
		--lots 20 \
		--wafers 5

gen-robot:
	@echo "[YieldOS] Generating large synthetic robot telemetry (500 rows)..."
	$(PYTHON) -m yieldos.cli.main robot gen \
		--out samples/robot_large \
		--samples 500

gen-sat:
	@echo "[YieldOS] Generating large synthetic satellite telemetry (500 rows)..."
	$(PYTHON) -m yieldos.cli.main sat gen \
		--out samples/sat_large \
		--samples 500

gen-all: gen-large gen-robot gen-sat

# ── Demo ────────────────────────────────────────────────────────────────
demo:
	@echo "[YieldOS] AI Tool API demo (all domains)..."
	$(PYTHON) demo_tool_api.py

run-demo:
	@echo "[YieldOS] Running full demo (all domains)..."
	$(PYTHON) scripts/run_demo.py

# ── Validate ────────────────────────────────────────────────────────────
validate:
	$(PYTHON) -m yieldos.cli.main validate --case output/semfab_case_001

# ── Run all domains ──────────────────────────────────────────────────────
run-all: semfab robot sat semiforge validate

# ── Clean ───────────────────────────────────────────────────────────────
clean:
	@echo "[YieldOS] Cleaning output..."
	$(PYTHON) -c "import shutil,os; [shutil.rmtree(f,True) for f in ['output/__pycache__']]; [os.remove(f) for f in __import__('glob').glob('**/*.pyc',recursive=True) if os.path.exists(f)]"
	-rm -rf output/semfab_case_001 output/robot_case_001 output/sat_case_001 output/semiforge_run_001 output/sweep_001 output/sweep_128

help:
	@echo ""
	@echo "HAL YieldOS v1.0 -- Read-Only Industrial Evidence Engine"
	@echo ""
	@echo "  make install     : pip install -e ."
	@echo "  make test        : Run all tests"
	@echo "  make semfab      : Analyze semfab sample"
	@echo "  make robot       : Analyze robot sample"
	@echo "  make sat         : Analyze satellite sample"
	@echo "  make semiforge   : Run SemiForge simulation"
	@echo "  make sweep       : SemiForge Y_func sweep (0-40% defect rate)"
	@echo "  make gen-large   : Generate 500+ row synthetic semfab dataset"
	@echo "  make gen-robot   : Generate 500-row synthetic robot telemetry"
	@echo "  make gen-sat     : Generate 500-row synthetic satellite telemetry"
	@echo "  make gen-all     : Generate all large synthetic datasets"
	@echo "  make demo        : AI Tool API demo (Token Idiot Index)"
	@echo "  make run-demo    : Full demo (all 4 domains + validate)"
	@echo "  make run-all     : Run all domains + validate"
	@echo "  make clean       : Remove generated output files"
	@echo ""
