.PHONY: install install-arosics install-dl install-roma install-onnx lint format test fetch benchmark n1 n2 n2-m1 n2-cost n2-bands n2-cycle n2-false-change n2-merge n2-bands-merge real-pairs check-presets cycle false-change fetch-train train-dataset train-pairs train-overfit validation validation-light validation-cycle ablation small onnx curve clean

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

# ONNX Runtime, which runs the exported RAFT models on the CPU without PyTorch,
# and onnx, which `satreg export` writes them with: exporting needs the dl
# extra too.
install-onnx:
	pip install -e ".[dev,onnx]"

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

# The twelve training and validation chips of configs/train-sites.toml (N3):
# their four dates, checked against the acceptance rule (docs/decisions.md).
fetch-train:
	satreg fetch-train

# The same chips, laid out as a data directory with Kaggle's dataset metadata,
# and zipped, ready to upload once (docs/kaggle.md).
TRAIN_DATASET = outputs/train-chips-dataset
TRAIN_ZIP = outputs/satreg-training-chips.zip

train-dataset:
	rm -rf $(TRAIN_DATASET) $(TRAIN_ZIP)
	satreg fetch-train --export $(TRAIN_DATASET)
	cp kaggle/dataset-metadata.json $(TRAIN_DATASET)/
	cd $(TRAIN_DATASET) && zip -qr $(abspath $(TRAIN_ZIP)) real chips.json

# A sample of the training pairs of configs/train-pairs.toml (N3): a contact
# sheet to look at before any training, and how fast pairs are made.
train-pairs:
	satreg train-pairs

# The overfit run of configs/train-overfit.toml (N3): RAFT large then small
# trained on the same 8 pairs for 300 steps, to check the training loop, not to
# make a model. About 9 minutes and 2 minutes on the M1. A run does not start
# over a checkpoint: remove outputs/train/ first, or pass --resume.
train-overfit:
	satreg train --config configs/train-overfit.toml
	satreg train --config configs/train-overfit.toml --model small

# The N3 validation set of configs/validation.toml: simulated pairs cut from the
# four validation chips and scored as the benchmark scores its own, its light
# version (the first pairs of every cell), and the closure of the real triplets
# of the twelve chips. What N3's choices are made on (docs/decisions.md). About
# 27 minutes, 3 minutes and 8 minutes on the M1 for pretrained RAFT.
validation:
	satreg validate --config configs/validation.toml

validation-light:
	satreg validate --config configs/validation.toml --light

validation-cycle:
	satreg validate-cycle --config configs/validation.toml

# The ablation (N3): the validation set and the real-triplet closure for
# pretrained RAFT and the two fine-tuned variants of configs/methods.toml,
# whose weights are the best.pt of the two Kaggle trainings (docs/kaggle.md),
# then the two read next to the pretrained model and the rule that chooses
# between them (docs/decisions.md). On the M1: 56 minutes for the validation
# set and 18 for the closure, on 2026-10-06, in a run a sleep interrupted.
# `satreg ablation` reads these three methods, a test checks the list, from
# validation/ and validation-cycle/ under the directory it is given.
ABLATION = outputs/ablation
ABLATION_METHODS = raft raft_ft_same_date raft_ft_cross_date

ablation:
	satreg validate --config configs/validation.toml --methods $(ABLATION_METHODS) --out $(ABLATION)/validation
	satreg validate-cycle --config configs/validation.toml --methods $(ABLATION_METHODS) --out $(ABLATION)/validation-cycle
	satreg ablation --out $(ABLATION)

# RAFT small fine-tuned (N3): the validation set and the real-triplet closure
# for RAFT small and RAFT large, each pretrained and fine-tuned with the pairs
# the ablation retained, then the fine-tuned small read next to the three
# others (docs/decisions.md). Its weights are the best.pt of the Kaggle
# training of configs/train-small.toml (docs/kaggle.md). The two RAFT large are
# scored again here, with the same code as the two small, and not read from
# outputs/ablation. On the M1: 54 minutes for the validation set and 17 for the
# closure, on 2026-10-06. `satreg small` reads these four methods, a test
# checks the list, from validation/ and validation-cycle/ under the directory
# it is given.
SMALL = outputs/small
SMALL_METHODS = raft_small raft_small_ft_cross_date raft raft_ft_cross_date

small:
	satreg validate --config configs/validation.toml --methods $(SMALL_METHODS) --out $(SMALL)/validation
	satreg validate-cycle --config configs/validation.toml --methods $(SMALL_METHODS) --out $(SMALL)/validation-cycle
	satreg small --out $(SMALL)

# RAFT exported to ONNX (N3): the large and the small model, pretrained and
# with the published fine-tuned weights, each with 4, 8 and 12 refinements,
# twelve files in outputs/onnx, each checked against PyTorch on one pair. Needs
# the dl and onnx extras. Half a minute on the M1.
onnx:
	satreg export

# The cost curve (N3): those twelve models scored under PyTorch on the full
# validation set, for what fewer refinements do to them; then under ONNX
# Runtime and under PyTorch on the light set and on the CPU
# (configs/curve.toml), with the classic methods, for their error and time;
# then what each adds to the memory of a process of its own; then the curve
# read from the four (docs/decisions.md). On the M1 CPU: one run at a time and
# nothing else running, as the times and the memory are read on it. A run of
# the PyTorch methods on a GPU is read as well if it is in $(CURVE)/gpu-light
# (docs/kaggle.md). `satreg curve` reads these methods, a test checks the
# lists, from the directories named here.
CURVE = outputs/curve
CURVE_TORCH = raft_r4 raft_r8 raft raft_ft_r4 raft_ft_r8 raft_ft raft_small_r4 raft_small_r8 raft_small raft_small_ft_r4 raft_small_ft_r8 raft_small_ft
CURVE_ONNX = raft_r4_onnx raft_r8_onnx raft_onnx raft_ft_r4_onnx raft_ft_r8_onnx raft_ft_onnx raft_small_r4_onnx raft_small_r8_onnx raft_small_onnx raft_small_ft_r4_onnx raft_small_ft_r8_onnx raft_small_ft_onnx
CURVE_REFERENCES = phase_correlation sift_ransac arosics

curve:
	satreg validate --config configs/validation.toml --methods $(CURVE_TORCH) --out $(CURVE)/validation
	satreg validate --config configs/curve.toml --light --out $(CURVE)/onnx
	satreg validate --config configs/curve.toml --light --methods $(CURVE_TORCH) --out $(CURVE)/torch
	satreg footprint --methods $(CURVE_ONNX) $(CURVE_TORCH) $(CURVE_REFERENCES) --out $(CURVE)/footprint
	satreg curve --out $(CURVE)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
