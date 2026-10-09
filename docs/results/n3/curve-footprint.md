What calling each method 10 times on one 256 px pair adds to the memory of a process that does nothing else: the rise of its resident high-water mark above the baseline, the mark with the method's runtime imported and the pair built. A lower bound on what the method touched, weights included, and not the memory of one call. Each method is read in 3 new processes: its line is the reading whose rise is the median, with the lowest and the highest rise beside it.

| method | rise (MiB) | lowest to highest (MiB) | after the first call (MiB) | whole process (MiB) | baseline (MiB) | last call that raised it | time (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| raft_r4_onnx | 81.4 | 81.4 to 83.4 | 56.4 | 269.0 | 187.6 | 2 of 10 | 396 |
| raft_r8_onnx | 83.9 | 83.7 to 85.0 | 58.8 | 271.6 | 187.7 | 2 of 10 | 613 |
| raft_onnx | 86.2 | 86.0 to 86.4 | 61.2 | 273.8 | 187.5 | 2 of 10 | 842 |
| raft_ft_r4_onnx | 81.4 | 81.3 to 81.4 | 56.3 | 269.0 | 187.7 | 2 of 10 | 385 |
| raft_ft_r8_onnx | 83.8 | 83.8 to 84.0 | 58.8 | 271.5 | 187.6 | 2 of 10 | 635 |
| raft_ft_onnx | 86.2 | 86.0 to 86.2 | 61.2 | 273.8 | 187.7 | 6 of 10 | 849 |
| raft_small_r4_onnx | 45.4 | 45.3 to 45.5 | 31.4 | 233.0 | 187.6 | 2 of 10 | 128 |
| raft_small_r8_onnx | 47.5 | 47.4 to 47.6 | 33.4 | 235.0 | 187.6 | 7 of 10 | 225 |
| raft_small_onnx | 49.6 | 49.5 to 49.7 | 35.6 | 237.3 | 187.7 | 2 of 10 | 328 |
| raft_small_ft_r4_onnx | 45.2 | 45.0 to 45.4 | 31.2 | 232.9 | 187.7 | 2 of 10 | 120 |
| raft_small_ft_r8_onnx | 47.5 | 47.5 to 48.4 | 33.5 | 235.1 | 187.6 | 2 of 10 | 235 |
| raft_small_ft_onnx | 49.6 | 49.4 to 49.6 | 35.6 | 237.1 | 187.5 | 2 of 10 | 336 |
| raft_r4 | 294.8 | 294.8 to 294.9 | 294.8 | 699.5 | 404.7 | 1 of 10 | 234 |
| raft_r8 | 295.1 | 295.0 to 296.5 | 294.9 | 699.9 | 404.8 | 2 of 10 | 302 |
| raft | 295.5 | 295.5 to 295.6 | 295.0 | 701.0 | 405.5 | 4 of 10 | 360 |
| raft_ft_r4 | 295.0 | 294.9 to 295.0 | 295.0 | 699.8 | 404.8 | 1 of 10 | 240 |
| raft_ft_r8 | 295.0 | 295.0 to 295.0 | 295.0 | 699.9 | 404.9 | 1 of 10 | 297 |
| raft_ft | 297.4 | 297.0 to 297.8 | 297.0 | 702.4 | 404.9 | 9 of 10 | 373 |
| raft_small_r4 | 79.9 | 79.7 to 79.9 | 79.8 | 484.7 | 404.9 | 2 of 10 | 52 |
| raft_small_r8 | 79.9 | 79.8 to 79.9 | 79.8 | 485.0 | 405.1 | 2 of 10 | 77 |
| raft_small | 83.8 | 83.5 to 83.9 | 81.9 | 489.4 | 405.6 | 2 of 10 | 103 |
| raft_small_ft_r4 | 79.9 | 79.8 to 80.0 | 79.8 | 485.0 | 405.1 | 3 of 10 | 52 |
| raft_small_ft_r8 | 83.7 | 83.5 to 83.8 | 79.6 | 489.0 | 405.3 | 4 of 10 | 76 |
| raft_small_ft | 83.7 | 83.6 to 83.9 | 81.7 | 488.2 | 404.5 | 4 of 10 | 102 |
| phase_correlation | 0.0 | 0.0 to 0.0 | 0.0 | 172.1 | 172.1 | 0 of 10 | 4 |
| sift_ransac | 12.2 | 12.1 to 12.9 | 11.3 | 184.4 | 172.2 | 10 of 10 | 34 |
| arosics | 8.3 | 8.3 to 8.4 | 8.2 | 301.9 | 293.6 | 2 of 10 | 17 |
