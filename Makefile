.PHONY: install install-arosics install-dl install-roma lint format test fetch benchmark n1 real-pairs check-presets clean

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

# The real multi-temporal pairs of configs/real.toml, and the presets measured
# next to them (docs/decisions.md).
real-pairs:
	satreg real-pairs

check-presets:
	satreg check-presets

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
