RAFT small fine-tuned on the first 8 pairs, over and over, of 256 px, from 8 chips (champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava): steps 1 to 300 of 300, batches of 2, on mps, in 101 s.

| steps | loss | EPE (px) | learning rate | s/step |
|---|---:|---:|---:|---:|
| 1-30 | 3.3795 | 1.3443 | 9.47e-05 | 0.36 |
| 31-60 | 0.4902 | 0.1196 | 8.42e-05 | 0.33 |
| 61-90 | 0.3101 | 0.0683 | 7.37e-05 | 0.33 |
| 91-120 | 0.2612 | 0.0535 | 6.32e-05 | 0.33 |
| 121-150 | 0.2247 | 0.0459 | 5.26e-05 | 0.33 |
| 151-180 | 0.2040 | 0.0389 | 4.21e-05 | 0.33 |
| 181-210 | 0.1796 | 0.0333 | 3.16e-05 | 0.33 |
| 211-240 | 0.1640 | 0.0278 | 2.11e-05 | 0.33 |
| 241-270 | 0.1449 | 0.0216 | 1.05e-05 | 0.33 |
| 271-300 | 0.1398 | 0.0194 | 4.00e-10 | 0.33 |

Mean end-point error on those 8 pairs, over the pixels of the loss mask, as at inference:

- pretrained weights: 6.2477 px (pair by pair: 0.111, 0.263, 0.153, 45.747, 0.140, 0.251, 0.236, 3.080)
- after step 300: 0.0183 px (pair by pair: 0.011, 0.013, 0.013, 0.022, 0.013, 0.016, 0.028, 0.030)

Checkpoint: outputs/train/raft_small_ft/checkpoint.pt, which the method raft_small_ft loads if that is its path in the methods config.

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O.
