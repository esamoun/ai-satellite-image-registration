What calling each method 10 times on one 256 px pair adds to the memory of a process that does nothing else: the rise of its resident high-water mark above the baseline, the mark with the method's runtime imported and the pair built. A lower bound on what the method touched, weights included, and not the memory of one call. Each method is read in 3 new processes: its line is the reading whose rise is the median, with the lowest and the highest rise beside it.

| method | rise (MiB) | lowest to highest (MiB) | after the first call (MiB) | whole process (MiB) | baseline (MiB) | last call that raised it | time (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| raft_ft_onnx | 87.6 | 87.5 to 96.7 | 61.3 | 275.8 | 188.2 | 2 of 10 | 829 |
| raft_ft_r8_onnx | 85.0 | 83.9 to 85.0 | 58.7 | 273.4 | 188.4 | 10 of 10 | 544 |
| raft_ft_r4_onnx | 83.4 | 82.9 to 83.7 | 56.6 | 271.7 | 188.3 | 10 of 10 | 438 |
| raft_small_ft_onnx | 50.2 | 49.2 to 50.3 | 35.2 | 238.8 | 188.6 | 7 of 10 | 308 |
| raft_ft_onnx_int8 | 100.2 | 100.1 to 100.9 | 100.2 | 288.5 | 188.3 | 1 of 10 | 497 |
| raft_ft_onnx_int8_dynamic | 86.7 | 86.6 to 87.7 | 68.9 | 275.0 | 188.4 | 2 of 10 | 559 |
| raft_ft_r8_onnx_int8 | 83.2 | 82.5 to 84.8 | 77.8 | 271.6 | 188.3 | 9 of 10 | 360 |
| raft_ft_r4_onnx_int8 | 77.5 | 77.3 to 77.8 | 64.4 | 265.9 | 188.4 | 2 of 10 | 209 |
| raft_small_ft_onnx_int8 | 52.9 | 51.6 to 53.5 | 49.9 | 241.2 | 188.3 | 2 of 10 | 270 |
| raft_small_ft_onnx_int8_dynamic | 50.0 | 49.9 to 51.6 | 36.7 | 238.3 | 188.3 | 4 of 10 | 283 |
