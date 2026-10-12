What calling each method 10 times on one 256 px pair adds to the memory of a process that does nothing else: the rise of its resident high-water mark above the baseline, the mark with the method's runtime imported and the pair built. A lower bound on what the method touched, weights included, and not the memory of one call. Each method is read in 3 new processes: its line is the reading whose rise is the median, with the lowest and the highest rise beside it.

| method | rise (MiB) | lowest to highest (MiB) | after the first call (MiB) | whole process (MiB) | baseline (MiB) | last call that raised it | time (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| raft_r4_onnx | 81.5 | 81.3 to 81.6 | 56.5 | 270.3 | 188.8 | 2 of 10 | 417 |
| raft_r8_onnx | 83.9 | 83.7 to 84.0 | 58.9 | 272.7 | 188.8 | 2 of 10 | 605 |
| raft_onnx | 86.1 | 85.9 to 86.3 | 61.1 | 275.0 | 188.8 | 2 of 10 | 845 |
| raft_ft_r4_onnx | 81.5 | 81.4 to 81.5 | 56.5 | 270.3 | 188.8 | 2 of 10 | 415 |
| raft_ft_r8_onnx | 83.8 | 83.8 to 83.9 | 58.8 | 272.5 | 188.7 | 2 of 10 | 635 |
| raft_ft_onnx | 86.4 | 86.2 to 92.9 | 61.4 | 275.2 | 188.8 | 2 of 10 | 857 |
| raft_small_r4_onnx | 45.3 | 45.3 to 45.3 | 31.2 | 234.1 | 188.8 | 2 of 10 | 122 |
| raft_small_r8_onnx | 47.3 | 47.2 to 47.4 | 33.2 | 236.2 | 189.0 | 2 of 10 | 222 |
| raft_small_onnx | 49.5 | 49.3 to 49.7 | 35.4 | 238.4 | 188.9 | 2 of 10 | 324 |
| raft_small_ft_r4_onnx | 45.4 | 45.3 to 45.4 | 31.3 | 234.2 | 188.8 | 4 of 10 | 123 |
| raft_small_ft_r8_onnx | 47.4 | 47.4 to 47.5 | 33.3 | 236.3 | 188.9 | 2 of 10 | 223 |
| raft_small_ft_onnx | 49.7 | 49.6 to 49.7 | 35.6 | 238.4 | 188.7 | 2 of 10 | 322 |
| raft_ft_r4_onnx_int8 | 77.6 | 77.6 to 77.7 | 64.6 | 266.5 | 188.9 | 2 of 10 | 200 |
| raft_ft_r8_onnx_int8 | 82.6 | 82.3 to 82.6 | 77.6 | 271.5 | 188.8 | 2 of 10 | 345 |
| raft_ft_onnx_int8 | 99.8 | 99.8 to 100.3 | 99.8 | 288.7 | 188.9 | 1 of 10 | 495 |
| raft_r4 | 294.6 | 294.5 to 294.7 | 294.6 | 700.7 | 406.1 | 1 of 10 | 235 |
| raft_r8 | 294.9 | 294.9 to 295.0 | 294.7 | 701.6 | 406.7 | 2 of 10 | 289 |
| raft | 294.9 | 294.8 to 294.9 | 294.9 | 701.0 | 406.1 | 1 of 10 | 360 |
| raft_ft_r4 | 294.8 | 294.8 to 295.0 | 294.8 | 700.8 | 405.9 | 1 of 10 | 231 |
| raft_ft_r8 | 294.8 | 294.8 to 294.9 | 294.8 | 700.9 | 406.1 | 1 of 10 | 290 |
| raft_ft | 296.9 | 296.7 to 296.9 | 296.9 | 703.3 | 406.4 | 1 of 10 | 355 |
| raft_small_r4 | 79.7 | 79.6 to 79.7 | 79.6 | 486.0 | 406.4 | 2 of 10 | 49 |
| raft_small_r8 | 79.6 | 79.4 to 79.6 | 79.5 | 485.7 | 406.1 | 2 of 10 | 75 |
| raft_small | 83.6 | 83.6 to 83.7 | 81.6 | 490.1 | 406.5 | 2 of 10 | 101 |
| raft_small_ft_r4 | 79.7 | 79.3 to 79.7 | 79.6 | 485.7 | 406.1 | 3 of 10 | 49 |
| raft_small_ft_r8 | 83.7 | 83.6 to 83.8 | 79.6 | 489.9 | 406.2 | 4 of 10 | 74 |
| raft_small_ft | 83.6 | 83.5 to 83.8 | 81.6 | 489.7 | 406.0 | 4 of 10 | 100 |
| phase_correlation | 0.0 | 0.0 to 0.0 | 0.0 | 173.5 | 173.5 | 0 of 10 | 4 |
| sift_ransac | 12.0 | 11.9 to 12.1 | 11.6 | 185.4 | 173.4 | 10 of 10 | 34 |
| arosics | 8.4 | 8.4 to 8.5 | 8.1 | 303.4 | 295.0 | 10 of 10 | 16 |
