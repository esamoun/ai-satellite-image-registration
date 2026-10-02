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
