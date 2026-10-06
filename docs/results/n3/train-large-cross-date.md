RAFT large fine-tuned on new pairs, of 256 px, from 8 chips (champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava): steps 1 to 10000 of 10000, batches of 8, on cuda, in 32230 s.

| steps | loss | EPE (px) | learning rate | s/step | pairs |
|---|---:|---:|---:|---:|---:|
| 1-1000 | 0.7900 | 0.2291 | 9.47e-05 | 3.24 | 72 % |
| 1001-2000 | 0.6084 | 0.1800 | 8.42e-05 | 3.19 | 71 % |
| 2001-3000 | 0.5843 | 0.1752 | 7.37e-05 | 3.24 | 72 % |
| 3001-4000 | 0.5474 | 0.1629 | 6.32e-05 | 3.26 | 72 % |
| 4001-5000 | 0.5548 | 0.1659 | 5.26e-05 | 3.25 | 72 % |
| 5001-6000 | 0.5101 | 0.1510 | 4.21e-05 | 3.23 | 72 % |
| 6001-7000 | 0.5105 | 0.1511 | 3.16e-05 | 3.23 | 72 % |
| 7001-8000 | 0.5258 | 0.1582 | 2.11e-05 | 3.12 | 71 % |
| 8001-9000 | 0.4823 | 0.1445 | 1.05e-05 | 3.24 | 72 % |
| 9001-10000 | 0.4915 | 0.1471 | 4.00e-10 | 3.22 | 72 % |

Speed of this session, over 9999 steps: 3.307 s per step (median), 2.5 pairs per second, 72 % of the time spent getting the pairs, with 3 worker process(es). Peak GPU memory, weights included: 4358 MiB.

Light validation set (360 pairs), every 500 steps; step 0 is the pretrained weights. The score is the mean error over every pair, a failed pair counting for 1 px; EPE is over non-failed pairs. A validation took 26 s on average.

| step | score (px) | clean: EPE (px) | failures | mild: EPE (px) | failures | hard: EPE (px) | failures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.1583 | 0.062 | 0.0 % | 0.073 | 0.0 % | 0.260 | 10.8 % |
| 500 | 0.1061 | 0.058 | 0.0 % | 0.065 | 0.0 % | 0.195 | 0.0 % |
| 1000 | 0.1065 | 0.059 | 0.0 % | 0.067 | 0.0 % | 0.194 | 0.0 % |
| 1500 | 0.1020 | 0.054 | 0.0 % | 0.063 | 0.0 % | 0.189 | 0.0 % |
| 2000 | 0.1006 | 0.062 | 0.0 % | 0.067 | 0.0 % | 0.172 | 0.0 % |
| 2500 | 0.0957 | 0.051 | 0.0 % | 0.058 | 0.0 % | 0.177 | 0.0 % |
| 3000 | 0.1033 | 0.056 | 0.0 % | 0.063 | 0.0 % | 0.192 | 0.0 % |
| 3500 | 0.0947 | 0.050 | 0.0 % | 0.056 | 0.0 % | 0.178 | 0.0 % |
| 4000 | 0.0976 | 0.055 | 0.0 % | 0.062 | 0.0 % | 0.176 | 0.0 % |
| 4500 | 0.0910 | 0.049 | 0.0 % | 0.056 | 0.0 % | 0.168 | 0.0 % |
| 5000 | 0.0959 | 0.049 | 0.0 % | 0.055 | 0.0 % | 0.184 | 0.0 % |
| 5500 | 0.1004 | 0.051 | 0.0 % | 0.059 | 0.0 % | 0.191 | 0.0 % |
| 6000 | 0.0907 | 0.047 | 0.0 % | 0.052 | 0.0 % | 0.172 | 0.0 % |
| 6500 | 0.0914 | 0.047 | 0.0 % | 0.055 | 0.0 % | 0.172 | 0.0 % |
| 7000 | 0.0897 | 0.046 | 0.0 % | 0.051 | 0.0 % | 0.172 | 0.0 % |
| 7500 | 0.0867 | 0.044 | 0.0 % | 0.051 | 0.0 % | 0.165 | 0.0 % |
| 8000 | 0.0876 | 0.043 | 0.0 % | 0.050 | 0.0 % | 0.170 | 0.0 % |
| 8500 (kept) | 0.0854 | 0.042 | 0.0 % | 0.049 | 0.0 % | 0.165 | 0.0 % |
| 9000 | 0.0884 | 0.043 | 0.0 % | 0.050 | 0.0 % | 0.173 | 0.0 % |
| 9500 | 0.0877 | 0.043 | 0.0 % | 0.049 | 0.0 % | 0.171 | 0.0 % |
| 10000 | 0.0868 | 0.042 | 0.0 % | 0.048 | 0.0 % | 0.170 | 0.0 % |

Kept: step 8500, score 0.0854 px, in /kaggle/working/outputs/train/large-cross-date/best.pt.

Checkpoint: /kaggle/working/outputs/train/large-cross-date/checkpoint.pt, which the method raft_ft loads if that is its path in the methods config.

Measured on Intel(R) Xeon(R) CPU @ 2.00GHz, 31 GiB, 4 CPUs, Linux-6.18.48+-x86_64-with-glibc2.39; GPU Tesla T4, 15 GiB, CUDA 12.8.
