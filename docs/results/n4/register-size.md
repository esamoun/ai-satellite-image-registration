What registering one pair costs a process, by the side of the pair: a window of the beauce benchmark chip and the same window shifted by (1.37, -2.61) px, each method read in a new process at each size. Times: the first call, which loads the model, the median of the 2 calls after it, and the correction of the moving image. Memory: the rise of the process's highest physical footprint above its mark before the first call, after the calls and after the correction, then the whole process, with its resident high-water mark beside it. The error is that of this one clean pair: a check that the method still answers at that size, not a published accuracy.

| method | side (px) | first call (s) | call (s) | correction (s) | memory added by the calls (MiB) | with the correction (MiB) | whole process (MiB) | resident mark (MiB) | error on the pair (px) |
|---|---|---|---|---|---|---|---|---|---|
| phase_correlation | 256 | 0.00 | 0.00 | 0.04 | 3 | 32 | 148 | 209 | 0.010 |
| sift_ransac | 256 | 0.03 | 0.01 | 0.04 | 11 | 40 | 156 | 220 | 0.018 |
| arosics | 256 | 0.06 | 0.02 | 0.04 | 10 | 39 | 239 | 343 | 0.039 |
| lightglue | 256 | 1.40 | 0.14 | 0.04 | 411 | 424 | 540 | 659 | 0.070 |
| roma | 256 | 12.53 | 2.47 | 0.04 | 3897 | 3897 | 4013 | 2945 | 0.023 |
| raft_small_ft_onnx | 256 | 0.61 | 0.25 | 0.04 | 47 | 80 | 203 | 279 | 0.125 |
| raft_ft_r4_onnx | 256 | 0.44 | 0.35 | 0.04 | 81 | 113 | 236 | 312 | 0.043 |
| raft_ft_onnx_int8 | 256 | 0.87 | 0.39 | 0.04 | 97 | 130 | 253 | 329 | 0.036 |
| raft_ft_onnx | 256 | 0.99 | 0.71 | 0.04 | 85 | 117 | 240 | 316 | 0.036 |
| raft_ft | 256 | 0.52 | 0.37 | 0.04 | 292 | 302 | 617 | 725 | 0.036 |
| phase_correlation | 512 | 0.01 | 0.01 | 0.14 | 13 | 126 | 261 | 322 | 0.010 |
| sift_ransac | 512 | 0.04 | 0.04 | 0.14 | 52 | 163 | 298 | 362 | 0.010 |
| arosics | 512 | 0.05 | 0.02 | 0.13 | 13 | 136 | 356 | 460 | 0.044 |
| lightglue | 512 | 1.43 | 0.62 | 0.14 | 985 | 1031 | 1166 | 1285 | 0.014 |
| roma | 512 | 12.21 | 2.50 | 0.13 | 3894 | 3894 | 4029 | 2936 | 0.053 |
| raft_small_ft_onnx | 512 | 0.95 | 0.77 | 0.14 | 364 | 487 | 630 | 705 | 0.085 |
| raft_ft_r4_onnx | 512 | 1.31 | 1.25 | 0.14 | 405 | 526 | 668 | 744 | 0.044 |
| raft_ft_onnx_int8 | 512 | 1.49 | 1.03 | 0.14 | 386 | 512 | 654 | 730 | 0.033 |
| raft_ft_onnx | 512 | 2.59 | 2.36 | 0.14 | 411 | 533 | 675 | 751 | 0.035 |
| raft_ft | 512 | 2.11 | 1.98 | 0.13 | 1174 | 1175 | 1509 | 1617 | 0.035 |
| phase_correlation | 1024 | 0.05 | 0.05 | 0.71 | 56 | 470 | 670 | 730 | 0.010 |
| sift_ransac | 1024 | 0.22 | 0.21 | 0.71 | 215 | 629 | 829 | 892 | 0.006 |
| arosics | 1024 | 0.06 | 0.02 | 0.69 | 19 | 481 | 765 | 869 | 0.091 |
| lightglue | 1024 | 4.52 | 2.51 | 0.69 | 3206 | 3211 | 3411 | 3244 | 0.014 |
| roma | 1024 | 13.87 | 3.22 | 0.72 | 3862 | 3862 | 4062 | 2726 | 0.175 |
| raft_small_ft_onnx | 1024 | 3.89 | 4.53 | 0.84 | 4629 | 5082 | 5289 | 3086 | 0.070 |
| raft_ft_r4_onnx | 1024 | 6.27 | 7.24 | 1.16 | 4988 | 5452 | 5660 | 3774 | 0.037 |
| raft_ft_onnx_int8 | 1024 | 5.49 | 6.55 | 1.14 | 4888 | 5369 | 5576 | 3488 | 0.028 |
| raft_ft_onnx | 1024 | 11.71 | 12.42 | 0.85 | 4986 | 5468 | 5675 | 3243 | 0.026 |
| raft_ft | 1024 | 10.22 | 10.99 | 0.80 | 5033 | 5033 | 5432 | 3837 | 0.026 |
