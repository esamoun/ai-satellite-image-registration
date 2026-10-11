Int8 copies of exported RAFT files next to the float file each was made from, on the first 10 pairs of every chip, scenario and preset of the validation set (santerre, lyon, morvan, sete), seed 0: 360 pairs.

| method | file | MB | failed | EPE (px) | time (ms) | time, share of float | flow moved (px) | on the worst pair (px) | memory (MiB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| raft_ft_onnx | float | 21.5 | 0.0 % | 0.0854 | 913.3 |  |  |  | 87.6 |
| raft_ft_onnx_int8 | static | 7.1 | 0.0 % | 0.0889 | 552.5 | 0.60 | 0.0183 | 0.2053 | 100.2 |
| raft_ft_onnx_int8_dynamic | dynamic | 6.3 | 0.0 % | 0.0934 | 655.9 | 0.72 | 0.0353 | 0.1235 | 86.7 |
| raft_ft_r8_onnx | float | 21.3 | 0.0 % | 0.0878 | 691.4 |  |  |  | 85.0 |
| raft_ft_r8_onnx_int8 | static | 6.7 | 0.0 % | 0.0911 | 391.8 | 0.57 | 0.0194 | 0.2082 | 83.2 |
| raft_ft_r4_onnx | float | 21.2 | 0.0 % | 0.0963 | 463.9 |  |  |  | 83.4 |
| raft_ft_r4_onnx_int8 | static | 6.4 | 0.0 % | 0.1005 | 232.5 | 0.50 | 0.0243 | 0.1876 | 77.5 |
| raft_small_ft_onnx | float | 4.3 | 0.0 % | 0.1424 | 367.6 |  |  |  | 50.2 |
| raft_small_ft_onnx_int8 | static | 2.0 | 0.0 % | 0.1838 | 292.6 | 0.80 | 0.1066 | 0.2016 | 52.9 |
| raft_small_ft_onnx_int8_dynamic | dynamic | 1.9 | 0.0 % | 0.1998 | 332.9 | 0.91 | 0.1271 | 0.2185 | 50.0 |

EPE is the mean end-point error over the pairs not failed. Time is the median over the pairs; its share of float is that time over the float file's. Flow moved is the distance between the flow of the int8 file and of its float file, averaged over the valid pixels of a pair, then over the pairs; the worst pair is the one where it is largest. Memory is what calling the method adds to a process of its own (`satreg footprint`).

By preset:

| method | clean: EPE (px), failed | mild: EPE (px), failed | hard: EPE (px), failed |
|---|---:|---:|---:|
| raft_ft_onnx | 0.0422, 0 of 120 | 0.0492, 0 of 120 | 0.1647, 0 of 120 |
| raft_ft_onnx_int8 | 0.0451, 0 of 120 | 0.0516, 0 of 120 | 0.1699, 0 of 120 |
| raft_ft_onnx_int8_dynamic | 0.0502, 0 of 120 | 0.0554, 0 of 120 | 0.1745, 0 of 120 |
| raft_ft_r8_onnx | 0.0441, 0 of 120 | 0.0512, 0 of 120 | 0.1680, 0 of 120 |
| raft_ft_r8_onnx_int8 | 0.0471, 0 of 120 | 0.0533, 0 of 120 | 0.1729, 0 of 120 |
| raft_ft_r4_onnx | 0.0526, 0 of 120 | 0.0597, 0 of 120 | 0.1766, 0 of 120 |
| raft_ft_r4_onnx_int8 | 0.0560, 0 of 120 | 0.0624, 0 of 120 | 0.1831, 0 of 120 |
| raft_small_ft_onnx | 0.0833, 0 of 120 | 0.0973, 0 of 120 | 0.2464, 0 of 120 |
| raft_small_ft_onnx_int8 | 0.1360, 0 of 120 | 0.1450, 0 of 120 | 0.2703, 0 of 120 |
| raft_small_ft_onnx_int8_dynamic | 0.1466, 0 of 120 | 0.1564, 0 of 120 | 0.2964, 0 of 120 |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O, ONNX Runtime on the CPU. On every pair each float file runs, then its int8 copies: the times of a line and of its float file are read seconds apart. A pair's time is the median of 1 call(s), after 1 warm-up call(s) per method. Details in `context.json`.
