| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| beauce | translation | clean | phase_correlation | cpu | 20 | 0.0 % | 0.0227 | 100.0 % | 100.0 % | 0.0 % | 4.8 | 6.5 |
| beauce | translation | clean | phase_correlation_hann | cpu | 20 | 0.0 % | 0.0038 | 100.0 % | 100.0 % | 0.0 % | 7.6 | 8.0 |
| beauce | translation | clean | sift_ransac | cpu | 20 | 0.0 % | 0.0226 | 100.0 % | 100.0 % | 0.0 % | 15.8 | 1.7 |
| beauce | translation | clean | raft_ft_onnx | cpu | 20 | 0.0 % | 0.0341 | 99.7 % | 100.0 % | 0.0 % | 839.2 | n/a |
| beauce | translation | clean | raft_ft_r8_onnx | cpu | 20 | 0.0 % | 0.0364 | 99.3 % | 100.0 % | 0.0 % | 635.1 | n/a |
| beauce | translation | clean | raft_ft_r4_onnx | cpu | 20 | 0.0 % | 0.0427 | 96.9 % | 100.0 % | 0.0 % | 421.9 | n/a |
| beauce | translation | clean | raft_small_ft_onnx | cpu | 20 | 0.0 % | 0.0690 | 78.0 % | 100.0 % | 0.0 % | 336.3 | n/a |
| beauce | translation | clean | raft_small_ft_r8_onnx | cpu | 20 | 0.0 % | 0.0686 | 79.2 % | 100.0 % | 0.0 % | 229.9 | n/a |
| beauce | translation | clean | raft_small_ft_r4_onnx | cpu | 20 | 0.0 % | 0.0890 | 64.0 % | 100.0 % | 0.0 % | 127.1 | n/a |
| beauce | translation | clean | raft_ft_onnx_int8 | cpu | 20 | 0.0 % | 0.0368 | 98.9 % | 100.0 % | 0.0 % | 495.9 | n/a |
| beauce | translation | clean | raft_ft_r8_onnx_int8 | cpu | 20 | 0.0 % | 0.0393 | 98.2 % | 100.0 % | 0.0 % | 358.2 | n/a |
| beauce | translation | clean | raft_ft_r4_onnx_int8 | cpu | 20 | 0.0 % | 0.0463 | 95.8 % | 100.0 % | 0.0 % | 204.5 | n/a |
| beauce | translation | hard | phase_correlation | cpu | 20 | 30.0 % | 0.4405 | 5.0 % | 65.0 % | 0.0 % | 4.7 | 6.5 |
| beauce | translation | hard | phase_correlation_hann | cpu | 20 | 30.0 % | 0.4817 | 0.0 % | 72.2 % | 10.0 % | 7.2 | 8.0 |
| beauce | translation | hard | sift_ransac | cpu | 20 | 30.0 % | 0.3816 | 17.5 % | 75.3 % | 75.0 % | 15.7 | 1.7 |
| beauce | translation | hard | raft_ft_onnx | cpu | 20 | 30.0 % | 0.1194 | 47.8 % | 100.0 % | 0.0 % | 838.0 | n/a |
| beauce | translation | hard | raft_ft_r8_onnx | cpu | 20 | 30.0 % | 0.1194 | 48.0 % | 100.0 % | 0.0 % | 631.1 | n/a |
| beauce | translation | hard | raft_ft_r4_onnx | cpu | 20 | 30.0 % | 0.1352 | 41.0 % | 99.8 % | 0.0 % | 425.2 | n/a |
| beauce | translation | hard | raft_small_ft_onnx | cpu | 20 | 30.0 % | 0.1578 | 32.0 % | 100.0 % | 0.0 % | 340.3 | n/a |
| beauce | translation | hard | raft_small_ft_r8_onnx | cpu | 20 | 30.0 % | 0.1631 | 31.4 % | 99.7 % | 0.0 % | 231.2 | n/a |
| beauce | translation | hard | raft_small_ft_r4_onnx | cpu | 20 | 30.0 % | 0.2662 | 15.0 % | 91.2 % | 0.0 % | 128.5 | n/a |
| beauce | translation | hard | raft_ft_onnx_int8 | cpu | 20 | 30.0 % | 0.1209 | 45.1 % | 100.0 % | 0.0 % | 496.9 | n/a |
| beauce | translation | hard | raft_ft_r8_onnx_int8 | cpu | 20 | 30.0 % | 0.1207 | 44.6 % | 100.0 % | 0.0 % | 350.8 | n/a |
| beauce | translation | hard | raft_ft_r4_onnx_int8 | cpu | 20 | 30.0 % | 0.1393 | 37.2 % | 99.9 % | 0.0 % | 205.9 | n/a |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 3 calls per pair, after 1 warm-up call(s) per method; memory is the peak traced by tracemalloc, which misses native allocations for phase_correlation, phase_correlation_hann, sift_ransac; not measured call by call, as no counter sees what ONNX Runtime allocates (its memory is read in a process of its own, by satreg footprint) for raft_ft_onnx, raft_ft_r8_onnx, raft_ft_r4_onnx, raft_small_ft_onnx, raft_small_ft_r8_onnx, raft_small_ft_r4_onnx, raft_ft_onnx_int8, raft_ft_r8_onnx_int8, raft_ft_r4_onnx_int8. Details in `context.json`.
