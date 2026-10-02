RAFT large fine-tuned on the first 8 pairs, over and over, of 256 px, from 8 chips (champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava): steps 1 to 300 of 300, batches of 2, on mps, in 541 s.

| steps | loss | EPE (px) | learning rate | s/step |
|---|---:|---:|---:|---:|
| 1-30 | 1.5723 | 0.6647 | 9.47e-05 | 1.81 |
| 31-60 | 0.2213 | 0.0566 | 8.42e-05 | 1.81 |
| 61-90 | 0.1572 | 0.0390 | 7.37e-05 | 1.79 |
| 91-120 | 0.1408 | 0.0354 | 6.32e-05 | 1.81 |
| 121-150 | 0.1150 | 0.0287 | 5.26e-05 | 1.81 |
| 151-180 | 0.0908 | 0.0208 | 4.21e-05 | 1.80 |
| 181-210 | 0.0748 | 0.0164 | 3.16e-05 | 1.80 |
| 211-240 | 0.0709 | 0.0150 | 2.11e-05 | 1.80 |
| 241-270 | 0.0582 | 0.0114 | 1.05e-05 | 1.80 |
| 271-300 | 0.0544 | 0.0099 | 4.00e-10 | 1.80 |

Mean end-point error on those 8 pairs, over the pixels of the loss mask, as at inference:

- pretrained weights: 4.2409 px (pair by pair: 0.041, 0.220, 0.065, 31.290, 0.065, 0.139, 0.143, 1.962)
- after step 300: 0.0090 px (pair by pair: 0.005, 0.007, 0.008, 0.010, 0.006, 0.008, 0.011, 0.018)

Checkpoint: outputs/train/raft_ft/checkpoint.pt, which the method raft_ft loads if that is its path in the methods config.

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O.
