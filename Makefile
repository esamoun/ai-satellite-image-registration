.PHONY: install install-arosics install-dl install-roma install-onnx lint format test fetch benchmark n1 n2 n2-m1 n2-cost n2-bands n2-cycle n2-false-change n2-merge n2-bands-merge real-pairs check-presets cycle false-change fetch-train train-dataset train-pairs train-overfit validation validation-light validation-cycle ablation small onnx curve int8 n3 n3-m1 n3-merge n3-cycle n3-final n3-bands n3-false-change n3-curve n3-dry demo clean

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

# The int8 copies of the fine-tuned ONNX files (N3). Needs `make onnx`
# for the float files, and the Mac on mains with nothing else running: the
# reading times each copy next to its float twin. About 2 minutes to quantize,
# 5 for the memory and 30 for the reading.
QUANTIZATION = outputs/quantization
INT8 = raft_ft_onnx_int8 raft_ft_onnx_int8_dynamic raft_ft_r8_onnx_int8 raft_ft_r4_onnx_int8 raft_small_ft_onnx_int8 raft_small_ft_onnx_int8_dynamic
INT8_FLOAT = raft_ft_onnx raft_ft_r8_onnx raft_ft_r4_onnx raft_small_ft_onnx

int8:
	satreg quantize --config configs/quantization.toml
	satreg footprint --methods $(INT8_FLOAT) $(INT8) --out $(QUANTIZATION)/footprint
	satreg int8 --config configs/quantization.toml

# The final evaluation of N3, published in docs/evaluation.md: the single read
# of the held-out sites (alps, libya4), after the freeze of docs/decisions.md.
# The M1 parts of configs/n3.toml, configs/n3-bands.toml and
# configs/n3-curve.toml, the merge with the GPU half of the simulated table
# (configs/n3-gpu.toml), and the verdict and the cost curve read from them.
# The GPU runs (configs/n3-gpu.toml, configs/n3-curve-gpu.toml) are made on
# Kaggle and downloaded to outputs/kaggle/ before `make n3` (docs/kaggle.md).
# --allow-held-out is given here, on each command that reads a held-out site,
# and nowhere else. Needs `make onnx` for the pretrained ONNX files. About 9
# hours on the M1, the cost curve being most of it: on mains with the lid open
# and nothing else running, as the times and the memory are read on it.
N3_GPU = outputs/kaggle/outputs/n3-gpu
N3_CURVE = outputs/n3-curve
N3_CURVE_GPU = outputs/kaggle/outputs/n3-curve-gpu
N3_INT8 = raft_ft_r4_onnx_int8 raft_ft_r8_onnx_int8 raft_ft_onnx_int8
N3_FOOTPRINT = $(CURVE_ONNX) $(N3_INT8) $(CURVE_TORCH) $(CURVE_REFERENCES)

n3: n3-m1 n3-merge n3-cycle n3-final n3-bands n3-false-change n3-curve

n3-m1:
	satreg benchmark --config configs/n3.toml --allow-held-out

n3-merge:
	satreg merge outputs/n3-m1 $(N3_GPU) --out outputs/n3

n3-cycle:
	satreg cycle --config configs/n3.toml --allow-held-out

n3-final:
	satreg final --table outputs/n3 --closure outputs/n3-cycle --out outputs/n3-final

n3-bands:
	satreg benchmark --config configs/n3-bands.toml

n3-false-change:
	satreg false-change --config configs/n3.toml --allow-held-out

n3-curve:
	satreg benchmark --config configs/n3-curve.toml --allow-held-out
	satreg benchmark --config configs/n3-curve.toml --allow-held-out --methods $(CURVE_TORCH) --out $(N3_CURVE)/torch
	satreg footprint --methods $(N3_FOOTPRINT) --out $(N3_CURVE)/footprint
	satreg curve --benchmark --gpu $(N3_CURVE_GPU) --out $(N3_CURVE)

# The rehearsal of `make n3`, before the freeze: every config and every
# command of the final evaluation on the four seen sites, two pairs a cell,
# without --allow-held-out, so that no command can read a held-out site. The
# GPU configs run here on $(N3_DRY_DEVICE). It checks that the commands run
# and read each other's tables: its numbers are not results, and nothing is
# chosen on them. About 55 minutes on the M1.
N3_DRY = outputs/n3-dry
N3_DRY_DEVICE = mps
N3_SEEN = beauce toulouse vosges marseille
N3_STAND_IN = vosges marseille
N3_DRY_SITES = $(addprefix --site ,$(N3_SEEN))
N3_DRY_CURVE_SITES = $(addprefix --site ,$(N3_STAND_IN))

n3-dry:
	satreg benchmark --config configs/n3.toml $(N3_DRY_SITES) --pairs 2 --repeats 1 --out $(N3_DRY)/n3-m1
	satreg benchmark --config configs/n3-gpu.toml $(N3_DRY_SITES) --pairs 2 --repeats 1 --device $(N3_DRY_DEVICE) --out $(N3_DRY)/n3-gpu
	satreg merge $(N3_DRY)/n3-m1 $(N3_DRY)/n3-gpu --out $(N3_DRY)/n3
	satreg cycle --config configs/n3.toml $(N3_DRY_SITES) --simulated-triplets 1 --out $(N3_DRY)/n3-cycle
	satreg final --table $(N3_DRY)/n3 --closure $(N3_DRY)/n3-cycle --rehearsal $(N3_STAND_IN) --out $(N3_DRY)/n3-final
	satreg benchmark --config configs/n3-bands.toml --pairs 2 --out $(N3_DRY)/n3-bands
	satreg false-change --config configs/n3.toml $(N3_DRY_SITES) --pairs 2 --out $(N3_DRY)/n3-false-change
	satreg benchmark --config configs/n3-curve.toml $(N3_DRY_CURVE_SITES) --pairs 2 --out $(N3_DRY)/n3-curve/onnx
	satreg benchmark --config configs/n3-curve.toml $(N3_DRY_CURVE_SITES) --pairs 2 --methods $(CURVE_TORCH) --out $(N3_DRY)/n3-curve/torch
	satreg benchmark --config configs/n3-curve-gpu.toml $(N3_DRY_CURVE_SITES) --pairs 2 --device $(N3_DRY_DEVICE) --out $(N3_DRY)/n3-curve-gpu
	satreg footprint --methods $(N3_FOOTPRINT) --calls 2 --processes 1 --out $(N3_DRY)/n3-curve/footprint
	satreg curve --benchmark --rehearsal --gpu $(N3_DRY)/n3-curve-gpu --out $(N3_DRY)/n3-curve

# The data of the demo page (docs/demo/) and the demo pairs as GeoTIFF
# (examples/), on the four seen sites: about 40 s on the M1. It needs the dl
# extra and the released weights, and reads no held-out site.
demo:
	satreg demo

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
