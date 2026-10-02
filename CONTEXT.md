# Satellite image registration benchmark

Measures how well classic and deep-learning methods recover the displacement
between two satellite images, on accuracy and compute cost. This glossary fixes
the words the code, the configs and the docs use.

## Language

### Images

**Site**:
A named place with one landscape type (open fields, urban, forest, coast,
mountain, desert).
_Avoid_: Area, location, zone

**Chip**:
A square image cut from one Sentinel-2 scene around a site's centre.
_Avoid_: Tile, patch, scene

**Benchmark chip**:
A chip that test pairs are cut from. No network is ever trained on its pixels.
_Avoid_: Test chip, N2 chip

**Training chip**:
A chip that training pairs are cut from. It shares no pixel with a benchmark
chip.

**Validation chip**:
A chip fetched like a training chip and set aside whole from training, one per
landscape type. It shares no pixel with a benchmark chip or a training chip.

**Window**:
A square cut from a chip, the size a method registers.
_Avoid_: Crop, patch

**Pair**:
A reference image and a moving image of the same window, whose displacement a
method estimates.

**Simulated pair**:
A pair whose moving image is made by applying a known displacement, so its
ground truth is known.
_Avoid_: Synthetic pair

**Same-date pair**:
A simulated pair whose two images come from one date. Its ground truth is exact.

**Cross-date pair**:
A simulated pair whose reference and moving images come from two dates of the
same chip. Its ground truth carries the residual misregistration between the
two dates.
_Avoid_: Multi-temporal pair (which also names real pairs)

**Loss mask**:
The pixels of a training pair the training loss may use: those whose true
position stays inside the moving image and that no opaque cloud covers, on
either image. On a cross-date pair, the pixels the scene classification hides
on either date are left out too.
_Avoid_: Valid mask (the benchmark's, which keeps cloud pixels for a global
motion)

**Real pair**:
Two dates of the same window with no displacement applied and no ground truth.

### Sites and evaluation

**Seen site**:
A site whose landscape type is among the training chips, measured on its
benchmark chip. Its pixels were not trained on; its landscape was.
_Avoid_: Training site, in-sample site

**Held-out site**:
A site whose landscape type is in no training or validation chip, and whose rows
no choice may be made on.
_Avoid_: Test site, unseen site

**Validation set**:
The fixed pairs cut from the validation chips, on which checkpoints and settings
are chosen.
_Avoid_: Dev set, test set

**Light validation set**:
The first pairs of every cell of the validation set, scored during a training.
Checkpoints are compared on it; what is kept is confirmed on the validation set.

**Final evaluation**:
The single read of the held-out sites, made once training, checkpoint, export
and quantization are frozen.

### Methods

**Pretrained method**:
A network used with its published weights, with no training on this project's
data.
_Avoid_: Off-the-shelf, zero-shot

**Fine-tuned model**:
A pretrained network trained further on this project's simulated pairs.
_Avoid_: Retrained, custom model

**Checkpoint**:
The file a training writes: the network's weights, with what resuming the
training needs and the configuration it ran with. A fine-tuned method loads its
weights from it.
_Avoid_: Snapshot, model file

**Selection score**:
The figure the validations of one training are compared on: the mean error over
the pairs of the light validation set, a failed pair counting for the failure
threshold. Lower is better.
_Avoid_: Validation loss, best metric

**Kept checkpoint**:
The weights of the validation with the lowest selection score, saved apart from
the checkpoint the training resumes from.
_Avoid_: Best model, final checkpoint

**Timing run**:
A few hundred steps on the training GPU, which measure how long a step takes
before the step budget is set. Its checkpoint is not a model to report.
_Avoid_: Benchmark run, dry run

**Step budget**:
The number of steps a training gets, fixed from the timing run before any real
training.
_Avoid_: Epochs, training length

**Overfit run**:
A short training on a few pairs seen over and over, which checks that the
training loop learns. Its checkpoint is not a model to report.
_Avoid_: Smoke training, toy training
