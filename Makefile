.PHONY: install install-arosics install-dl install-roma lint format test fetch benchmark n1 n2 n2-m1 n2-cost n2-bands n2-cycle n2-false-change n2-merge n2-bands-merge real-pairs check-presets cycle false-change clean

install:
	pip install -e ".[dev]"

# GDAL's bindings must match the system GDAL (brew install gdal), so they are
# pinned to it before AROSICS pulls them in.
install-arosics:
	pip install "gdal==$$(gdal-config --version)"
	pip install -e ".[dev,arosics]"

# PyTorch, then the pretrained weights, downloaded once to PyTorch's cache
# (~/.cache/torch unless TORCH_HOME says otherwise), outside the repository.
install-dl:
	pip install -e ".[dev,dl]"
	python -c "from satreg.methods import lightglue, raft; print(*raft.fetch_weights(), *lightglue.fetch_weights(), sep='\n')"

# RoMa on top of the dl extra. romatch is installed without the dependencies it
# declares: it would pull opencv-python over opencv-python-headless, and training
# and benchmarking packages that inference never imports (see docs/decisions.md).
# The weights (1.7 GB) go to PyTorch's cache.
install-roma: install-dl
	pip install -e ".[dev,dl,roma]"
	pip install --no-deps "romatch==0.1.2"
	python -c "from satreg.methods import roma; print(*roma.fetch_weights(), sep='\n')"

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff check --fix src tests
	ruff format src tests

test:
	pytest -q

fetch:
	satreg fetch

benchmark:
	satreg benchmark

# The N1 results table, published in docs/evaluation.md.
n1:
	satreg benchmark --config configs/n1.toml

# The N2 results, published in docs/evaluation.md: the M1 parts of
# configs/n2.toml, configs/n2-cost.toml and configs/n2-bands.toml, then the
# merges with the GPU halves of the simulated and inter-band tables
# (configs/n2-gpu.toml, configs/n2-bands-gpu.toml). Those halves run on Kaggle
# and are downloaded to outputs/kaggle/ (docs/kaggle.md). About 6 hours on the
# M1, RoMa's rows in cycle consistency and false change being most of it: keep
# it plugged in with the lid open.
N2_GPU = outputs/kaggle/outputs/n2-gpu
N2_BANDS_GPU = outputs/kaggle/outputs/n2-bands-gpu

n2: n2-m1 n2-cost n2-bands n2-cycle n2-false-change n2-merge n2-bands-merge

n2-m1:
	satreg benchmark --config configs/n2.toml

n2-cost:
	satreg benchmark --config configs/n2-cost.toml

n2-bands:
	satreg benchmark --config configs/n2-bands.toml

n2-cycle:
	satreg cycle --config configs/n2.toml

n2-false-change:
	satreg false-change --config configs/n2.toml

n2-merge:
	satreg merge outputs/n2-m1 $(N2_GPU) --out outputs/n2

n2-bands-merge:
	satreg merge outputs/n2-bands-m1 $(N2_BANDS_GPU) --out outputs/n2-bands

# The real multi-temporal pairs of configs/real.toml, and the presets measured
# next to them (docs/decisions.md).
real-pairs:
	satreg real-pairs

check-presets:
	satreg check-presets

cycle:
	satreg cycle

false-change:
	satreg false-change

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
