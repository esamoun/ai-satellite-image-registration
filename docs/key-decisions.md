# Key decisions

This project compares classic and deep-learning methods for aligning two
Sentinel-2 images to a fraction of a pixel. Along the way I made a lot of
calls, and [the decision log](decisions.md) keeps every one of them with its
reasoning and its numbers. This page is the short version: the twelve that
shaped the project most. For each one, what I picked, what I turned down, and
why. Every section links to the full entry.

Drafted with Claude Code from the log, and reviewed by me.

## N2: classic against pretrained methods

### 1. Two sites stay hidden until the end

Of the six sites of the benchmark, two (a mountain and a desert) are kept back
for the final test in N3. In N2 they appear in no table at all: not in a separate one,
not flagged in the main one. N2 is where I tuned thresholds, presets and
variants, and anything I tune while looking at a site leaks into its score. A
separate table would only work if I trusted myself not to look. So the
benchmark refuses those two sites unless it gets an explicit
`--allow-held-out` flag, and the rule becomes something the code checks.

[Full entry, 2026-09-28](decisions.md#2026-09-28-held-out-sites-stay-out-of-every-n2-table)

### 2. Judging real pairs without a ground truth

On real image pairs nobody knows the true displacement, so I check consistency
instead. Take three dates A, B and C: going from A to B and then from B to C
should land where going straight from A to C does. The gap is the closure. A
triplet fails when one of its three registrations fails, and also when the loop
misses by more than 1 px. Without that second rule, a registration stuck on the
wrong peak would stay in the average, and the mean closure would stop saying
anything about sub-pixel accuracy. It is also the 1 px rule of the simulated
benchmark, so failure rates read the same way in both tables.

[Full entry, 2026-09-28](decisions.md#2026-09-28-a-triplet-fails-if-a-leg-fails-or-if-its-closure-exceeds-1-px)

### 3. One change detector for every method

The question here is what a leftover misalignment costs a change detector. So
after each method's correction, I count the pixels a simple detector flags as
changed. That detector has to be identical for every method, or part of the
gap between methods comes from the detector itself. It
flags a pixel when the difference is above 3 times the noise, after one gain
and offset per pair has put both images at the same level, the same for every
method. A fixed threshold would mean nothing across sites whose noise differs
by a factor of ten, and a percentile flags the same share of pixels whatever
the registration, which hides exactly what I want to measure.

[Full entry, 2026-09-28](decisions.md#2026-09-28-false-changes-are-counted-by-one-fixed-detector-at-3-sigma-of-the-noise)

## N3: RAFT fine-tuned on this data

### 4. What N3 had to prove, written before any training

N2 left pretrained RAFT with three weak spots: its accuracy on simulated pairs,
real pairs where the ground has changed, and red against near infrared. I made
the first one N3's target. It is what the spec asks for, it is the only one
with an exact ground truth, and a model aimed at all three at once would give a
result nobody could read. I wrote the success criterion before any training
code existed: on the 1,800 pairs of the two hidden sites, the fine-tuned model
must fail no more pairs than the pretrained one, and have a lower mean error on
the pairs neither fails. The bar is pretrained RAFT, not the classic methods,
because the question N3 can answer is what training on this data buys the same
architecture.

[Full entry, 2026-10-02](decisions.md#2026-10-02-what-n3-must-show-fine-tuned-raft-beats-pretrained-raft-on-the-held-out-sites)

### 5. Freezing everything before the final test

A hidden site stops being hidden the moment you make a choice knowing its
score. So the two sites were read exactly once, and before that run a dated
entry of the log froze everything it would use: the commit, the weights
and exported models by their SHA-256 hash, the points of the cost curve, the
configs.
I also timed the final cost curve on all 1,800 pairs rather than ten per cell,
so that the error and failure rate of each point come from the same pairs as
the criterion. Anyone can check the order from the dates of the log and of the
commits.

[Full entry, 2026-10-11](decisions.md#2026-10-11-the-freeze-what-the-final-evaluation-runs-on-the-held-out-sites-and-how-it-is-read),
and [the rule it applies](decisions.md#2026-10-02-the-held-out-sites-are-read-once-after-everything-is-frozen)

### 6. No model picked to deploy after seeing the results

My plan for the N3 write-up had a line on which point of the cost curve I
would deploy. I dropped it. The rule I set before training forbids any choice
made on the hidden sites' results, their cost figures included, and picking a
point after reading them would be exactly that. So
[the write-up](evaluation.md) describes what the curve shows for one
constraint at a time, and says the choice depends on the use and belongs on
the validation set. A first draft did name two points. Checking it against the
log caught that before anything was committed.

[Full entry, 2026-10-12](decisions.md#2026-10-12-the-n3-write-up-names-no-point-of-the-cost-curve-to-deploy)

### 7. Timing a laptop that slows down as it works

The laptop is an M1 without a fan. On a rested machine, RAFT large with 12
refinements under ONNX Runtime takes 630 to 640 ms a call; after two and a half
minutes of calls it is up to 860 to 880 ms. The curve shows the sustained
figure, not the rested one, because a benchmark is a long run and the rested
speed lasts a few calls: fine-tuned RAFT large is at 916 ms on the held-out
sites ([final evaluation, 2026-10-12](decisions.md#2026-10-12-the-final-evaluation-fine-tuned-raft-beats-the-pretrained-model-on-the-held-out-sites-and-its-closure-is-better)).
A first run came out slow because the
whole machine was slower for most of it, so I ran it again at night with
nothing else running and did not publish the first one. I also kept ONNX
Runtime's default settings, even though one trial made another setting look
faster: picking a setting from a result is what I was trying to avoid.

[Full entry, 2026-10-09](decisions.md#2026-10-09-the-cost-curve-on-the-m1s-cpu-onnx-runtime-is-19-to-35-times-slower-than-pytorch-and-adds-32-to-213-mib-less-to-a-process)

### 8. Compressing the model, and publishing what did not work

I quantized fine-tuned RAFT large to int8, so that most of its convolutions
compute on 8-bit integers instead of floats. Twenty-five of them stay in float,
the ones that read the flow, write its update or write the upsampling mask:
quantizing everything ONNX Runtime allows moved the flow by half a pixel.
Calibrated on 36 validation pairs, it cuts the time by 40 to 50 % for 0.003 to
0.004 px more error, and fails no pair. On RAFT small it does not pay: running
the float model with 8 refinements instead of 12 is faster and more accurate
than its int8 copy. I published that as a negative result, in the table, and
kept its files out of the release, since every file there is one a method
runs.

[Full entry, 2026-10-11](decisions.md#2026-10-11-static-int8-takes-40-to-50--off-raft-larges-time-under-onnx-runtime-for-0004-px-and-does-not-pay-on-raft-small)

### 9. Weights anyone can verify

The fine-tuned weights are files on a GitHub release, exactly as the training
saved them, and the code refuses any download whose SHA-256 is not the one it
has written in it. Release files can be replaced after publication, so the
release alone does not tell you which weights you got. The hash does, and it is
the same hash recorded next to the tables those weights produced. The ticket
said a benchmark should skip a model whose weights it cannot get; I made it
stop before the first pair instead, so a table can never be missing a method
without anyone noticing. Git LFS would need its client on every machine that
clones, and the Hugging Face hub would be a second account and a second place
where the weights could drift from the code.

[Full entry, 2026-10-07](decisions.md#2026-10-07-the-fine-tuned-weights-are-release-assets-pinned-by-their-sha-256-in-the-code)

## N4: a command, a demo, a container image

### 10. A command that registers your own images

Until N4, every command simulated its pairs or read a site's image series. To
show N4 I chose a command, `satreg register`, that aligns two images a reader
brings, rather than a replay of the benchmark. A replay proves the numbers come
back; it registers nothing of yours. The methods already took two arrays and
returned a displacement, so the command only reads and writes around them, and
no method had to change. It gives no score, because a pair you bring has no
ground truth.

[Full entry, 2026-10-12](decisions.md#2026-10-12-n4-is-shown-with-satreg-register-which-registers-a-supplied-pair)

### 11. Images on different map grids are refused

If the two images carry different georeferencing, `satreg register` stops and
tells you to put them on one grid first. I could have registered the raw pixels
with a warning, or reprojected one image onto the other's grid. But on two
grids, the same pixel in each file is two different places on the ground, and a
method would measure the gap between the grids with the misalignment on top.
Reprojecting would add a second resampler next to the simulator's, and a
reprojection shifts content by fractions of a pixel, the very size of what I
am measuring.

[Full entry, 2026-10-12](decisions.md#2026-10-12-two-files-on-different-map-grids-are-refused)

### 12. A light container image, without PyTorch

The container image runs three classic methods and the fine-tuned RAFT models
under ONNX Runtime, without PyTorch. I preferred that to a full container
image, or to shipping both. PyTorch alone takes 583 MB on my development
machine, and the container image only has to register a pair and run a small
benchmark, which the ONNX exports do without it. A full container image would
also need a system GDAL for AROSICS, and the deep-learning tables were
computed on a Kaggle GPU that a laptop's container does not have anyway; they
can still be reproduced outside it, with `make`. Light is relative, though:
the container image is about 940 MB on amd64.

[Full entry, 2026-10-13](decisions.md#2026-10-13-the-container-image-is-light-no-pytorch-the-classic-methods-and-fine-tuned-raft-under-onnx-runtime)
