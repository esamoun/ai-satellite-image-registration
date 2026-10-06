RAFT large fine-tuned on new pairs, of 256 px, from 8 chips (champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava): steps 1 to 10000 of 10000, batches of 8, on cuda, in 29578 s.

| steps | loss | EPE (px) | learning rate | s/step | pairs |
|---|---:|---:|---:|---:|---:|
| 1-1000 | 0.3316 | 0.1011 | 9.47e-05 | 2.95 | 69 % |
| 1001-2000 | 0.2635 | 0.0768 | 8.42e-05 | 2.92 | 68 % |
| 2001-3000 | 0.2565 | 0.0748 | 7.37e-05 | 2.99 | 69 % |
| 3001-4000 | 0.2430 | 0.0709 | 6.32e-05 | 2.99 | 69 % |
| 4001-5000 | 0.2347 | 0.0688 | 5.26e-05 | 2.99 | 69 % |
| 5001-6000 | 0.2263 | 0.0663 | 4.21e-05 | 2.96 | 69 % |
| 6001-7000 | 0.2203 | 0.0643 | 3.16e-05 | 2.97 | 69 % |
| 7001-8000 | 0.2143 | 0.0630 | 2.11e-05 | 2.87 | 68 % |
| 8001-9000 | 0.2089 | 0.0613 | 1.05e-05 | 2.97 | 69 % |
| 9001-10000 | 0.2070 | 0.0603 | 4.00e-10 | 2.96 | 69 % |

Speed of this session, over 9999 steps: 3.046 s per step (median), 2.7 pairs per second, 69 % of the time spent getting the pairs, with 3 worker process(es). Peak GPU memory, weights included: 4357 MiB.

Light validation set (360 pairs), every 500 steps; step 0 is the pretrained weights. The score is the mean error over every pair, a failed pair counting for 1 px; EPE is over non-failed pairs. A validation took 24 s on average.

| step | score (px) | clean: EPE (px) | failures | mild: EPE (px) | failures | hard: EPE (px) | failures |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.1583 | 0.062 | 0.0 % | 0.073 | 0.0 % | 0.260 | 10.8 % |
| 500 | 0.1057 | 0.054 | 0.0 % | 0.060 | 0.0 % | 0.203 | 0.0 % |
| 1000 | 0.0949 | 0.049 | 0.0 % | 0.056 | 0.0 % | 0.180 | 0.0 % |
| 1500 | 0.0931 | 0.048 | 0.0 % | 0.056 | 0.0 % | 0.175 | 0.0 % |
| 2000 | 0.0951 | 0.047 | 0.0 % | 0.053 | 0.0 % | 0.185 | 0.0 % |
| 2500 | 0.0949 | 0.047 | 0.0 % | 0.056 | 0.0 % | 0.182 | 0.0 % |
| 3000 | 0.0900 | 0.044 | 0.0 % | 0.051 | 0.0 % | 0.175 | 0.0 % |
| 3500 | 0.0886 | 0.047 | 0.0 % | 0.053 | 0.0 % | 0.166 | 0.0 % |
| 4000 | 0.0884 | 0.045 | 0.0 % | 0.052 | 0.0 % | 0.169 | 0.0 % |
| 4500 | 0.0799 | 0.043 | 0.0 % | 0.048 | 0.0 % | 0.149 | 0.0 % |
| 5000 | 0.0830 | 0.042 | 0.0 % | 0.049 | 0.0 % | 0.158 | 0.0 % |
| 5500 | 0.0818 | 0.042 | 0.0 % | 0.048 | 0.0 % | 0.155 | 0.0 % |
| 6000 | 0.0789 | 0.040 | 0.0 % | 0.046 | 0.0 % | 0.151 | 0.0 % |
| 6500 | 0.0794 | 0.041 | 0.0 % | 0.048 | 0.0 % | 0.149 | 0.0 % |
| 7000 | 0.0784 | 0.039 | 0.0 % | 0.045 | 0.0 % | 0.151 | 0.0 % |
| 7500 | 0.0747 | 0.038 | 0.0 % | 0.044 | 0.0 % | 0.142 | 0.0 % |
| 8000 | 0.0737 | 0.037 | 0.0 % | 0.044 | 0.0 % | 0.140 | 0.0 % |
| 8500 | 0.0743 | 0.037 | 0.0 % | 0.044 | 0.0 % | 0.142 | 0.0 % |
| 9000 | 0.0739 | 0.036 | 0.0 % | 0.043 | 0.0 % | 0.142 | 0.0 % |
| 9500 | 0.0743 | 0.036 | 0.0 % | 0.043 | 0.0 % | 0.144 | 0.0 % |
| 10000 (kept) | 0.0731 | 0.035 | 0.0 % | 0.042 | 0.0 % | 0.142 | 0.0 % |

Kept: step 10000, score 0.0731 px, in /kaggle/working/outputs/train/large-same-date/best.pt.

Checkpoint: /kaggle/working/outputs/train/large-same-date/checkpoint.pt, which the method raft_ft loads if that is its path in the methods config.

Measured on Intel(R) Xeon(R) CPU @ 2.00GHz, 31 GiB, 4 CPUs, Linux-6.18.48+-x86_64-with-glibc2.39; GPU Tesla T4, 15 GiB, CUDA 12.8.
