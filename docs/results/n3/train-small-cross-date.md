RAFT small fine-tuned on new pairs, of 256 px, from 8 chips (champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava): steps 1 to 10000 of 10000, batches of 8, on cuda, in 32797 s.

| steps | loss | EPE (px) | learning rate | s/step | pairs |
|---|---:|---:|---:|---:|---:|
| 1-1000 | 1.5208 | 0.4216 | 9.47e-05 | 3.21 | 89 % |
| 1001-2000 | 1.0072 | 0.2830 | 8.42e-05 | 3.27 | 89 % |
| 2001-3000 | 0.9717 | 0.2759 | 7.37e-05 | 3.32 | 89 % |
| 3001-4000 | 0.9098 | 0.2557 | 6.32e-05 | 3.34 | 90 % |
| 4001-5000 | 0.9134 | 0.2582 | 5.26e-05 | 3.33 | 90 % |
| 5001-6000 | 0.8515 | 0.2389 | 4.21e-05 | 3.31 | 89 % |
| 6001-7000 | 0.8624 | 0.2429 | 3.16e-05 | 3.27 | 90 % |
| 7001-8000 | 0.8561 | 0.2437 | 2.11e-05 | 3.17 | 89 % |
| 8001-9000 | 0.8173 | 0.2313 | 1.05e-05 | 3.28 | 90 % |
| 9001-10000 | 0.8229 | 0.2337 | 4.00e-10 | 3.29 | 90 % |

Speed of this session, over 9999 steps: 3.405 s per step (median), 2.4 pairs per second, 89 % of the time spent getting the pairs, with 3 worker process(es). Peak GPU memory, weights included: 1883 MiB.

Light validation set (360 pairs), every 500 steps; step 0 is the pretrained weights. The score is the mean error over every pair, a failed pair counting for 1 px; EPE is over non-failed pairs. A validation took 23 s on average.

| step | score (px) | clean: EPE (px) | failures | mild: EPE (px) | failures | hard: EPE (px) | failures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.3224 | 0.145 | 0.0 % | 0.191 | 0.8 % | 0.463 | 30.0 % |
| 500 | 0.2370 | 0.128 | 0.0 % | 0.135 | 0.0 % | 0.419 | 5.0 % |
| 1000 | 0.1885 | 0.113 | 0.0 % | 0.124 | 0.0 % | 0.293 | 5.0 % |
| 1500 | 0.1797 | 0.103 | 0.0 % | 0.114 | 0.0 % | 0.322 | 0.0 % |
| 2000 | 0.1946 | 0.109 | 0.0 % | 0.117 | 0.0 % | 0.352 | 0.8 % |
| 2500 | 0.1635 | 0.096 | 0.0 % | 0.109 | 0.0 % | 0.273 | 1.7 % |
| 3000 | 0.1624 | 0.098 | 0.0 % | 0.110 | 0.0 % | 0.273 | 0.8 % |
| 3500 | 0.1699 | 0.107 | 0.0 % | 0.121 | 0.0 % | 0.281 | 0.0 % |
| 4000 | 0.1572 | 0.096 | 0.0 % | 0.107 | 0.0 % | 0.269 | 0.0 % |
| 4500 | 0.1636 | 0.095 | 0.0 % | 0.108 | 0.0 % | 0.287 | 0.0 % |
| 5000 | 0.1477 | 0.088 | 0.0 % | 0.100 | 0.0 % | 0.254 | 0.0 % |
| 5500 | 0.1515 | 0.090 | 0.0 % | 0.104 | 0.0 % | 0.242 | 2.5 % |
| 6000 | 0.1472 | 0.089 | 0.0 % | 0.101 | 0.0 % | 0.233 | 2.5 % |
| 6500 | 0.1500 | 0.089 | 0.0 % | 0.101 | 0.0 % | 0.260 | 0.0 % |
| 7000 | 0.1509 | 0.087 | 0.0 % | 0.100 | 0.0 % | 0.265 | 0.0 % |
| 7500 | 0.1491 | 0.089 | 0.0 % | 0.103 | 0.0 % | 0.255 | 0.0 % |
| 8000 (kept) | 0.1424 | 0.083 | 0.0 % | 0.097 | 0.0 % | 0.246 | 0.0 % |
| 8500 | 0.1436 | 0.085 | 0.0 % | 0.100 | 0.0 % | 0.246 | 0.0 % |
| 9000 | 0.1469 | 0.084 | 0.0 % | 0.097 | 0.0 % | 0.259 | 0.0 % |
| 9500 | 0.1425 | 0.083 | 0.0 % | 0.097 | 0.0 % | 0.247 | 0.0 % |
| 10000 | 0.1426 | 0.083 | 0.0 % | 0.097 | 0.0 % | 0.247 | 0.0 % |

Kept: step 8000, score 0.1424 px, in /kaggle/working/outputs/train/small-cross-date/best.pt.

Checkpoint: /kaggle/working/outputs/train/small-cross-date/checkpoint.pt, which the method raft_small_ft loads if that is its path in the methods config.

Measured on Intel(R) Xeon(R) CPU @ 2.00GHz, 31 GiB, 4 CPUs, Linux-6.18.48+-x86_64-with-glibc2.39; GPU Tesla T4, 15 GiB, CUDA 12.8.
