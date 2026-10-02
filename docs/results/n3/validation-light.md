Light validation set: 10 pairs per chip, scenario and preset, seed 0, cut from the validation chips santerre, lyon, morvan, sete. These are the first 10 pairs of every cell of the full set, which has 100.

Over every chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all chips | translation | clean | raft | mps | 40 | 0.0 % | 0.0455 | 96.4 % | 100.0 % | 0.0 % | 141.6 | n/a |
| all chips | translation | clean | raft_small | mps | 40 | 0.0 % | 0.1357 | 36.2 % | 99.8 % | 0.0 % | 60.0 | n/a |
| all chips | translation | mild | raft | mps | 40 | 5.0 % | 0.0531 | 94.1 % | 100.0 % | 0.0 % | 142.5 | n/a |
| all chips | translation | mild | raft_small | mps | 40 | 5.0 % | 0.1792 | 33.6 % | 99.0 % | 2.5 % | 59.3 | n/a |
| all chips | translation | hard | raft | mps | 40 | 30.0 % | 0.2211 | 26.8 % | 96.1 % | 12.5 % | 142.4 | n/a |
| all chips | translation | hard | raft_small | mps | 40 | 30.0 % | 0.4485 | 4.9 % | 69.9 % | 30.0 % | 59.5 | n/a |
| all chips | affine | clean | raft | mps | 40 | 0.0 % | 0.0520 | 92.0 % | 100.0 % | 0.0 % | 142.1 | n/a |
| all chips | affine | clean | raft_small | mps | 40 | 0.0 % | 0.1365 | 35.4 % | 99.8 % | 0.0 % | 59.1 | n/a |
| all chips | affine | mild | raft | mps | 40 | 5.0 % | 0.0640 | 88.2 % | 99.9 % | 0.0 % | 142.1 | n/a |
| all chips | affine | mild | raft_small | mps | 40 | 5.0 % | 0.1915 | 33.6 % | 99.0 % | 0.0 % | 59.5 | n/a |
| all chips | affine | hard | raft | mps | 40 | 30.0 % | 0.2433 | 20.4 % | 95.0 % | 12.5 % | 142.7 | n/a |
| all chips | affine | hard | raft_small | mps | 40 | 30.0 % | 0.4462 | 4.8 % | 69.9 % | 32.5 % | 59.7 | n/a |
| all chips | dense | clean | raft | mps | 40 | 0.0 % | 0.0881 | 65.4 % | 100.0 % | 0.0 % | 145.8 | n/a |
| all chips | dense | clean | raft_small | mps | 40 | 0.0 % | 0.1632 | 29.2 % | 99.0 % | 0.0 % | 57.9 | n/a |
| all chips | dense | mild | raft | mps | 40 | 5.0 % | 0.1014 | 60.0 % | 99.9 % | 0.0 % | 142.5 | n/a |
| all chips | dense | mild | raft_small | mps | 40 | 5.0 % | 0.2035 | 28.3 % | 97.9 % | 0.0 % | 58.7 | n/a |
| all chips | dense | hard | raft | mps | 40 | 30.0 % | 0.2939 | 15.2 % | 91.7 % | 10.0 % | 141.8 | n/a |
| all chips | dense | hard | raft_small | mps | 40 | 30.0 % | 0.4915 | 4.9 % | 66.5 % | 27.5 % | 58.6 | n/a |

By chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | translation | clean | raft | mps | 10 | 0.0 % | 0.0381 | 97.6 % | 100.0 % | 0.0 % | 141.7 | n/a |
| santerre | translation | clean | raft_small | mps | 10 | 0.0 % | 0.1183 | 46.6 % | 99.8 % | 0.0 % | 59.1 | n/a |
| santerre | translation | mild | raft | mps | 10 | 5.0 % | 0.0464 | 94.9 % | 100.0 % | 0.0 % | 142.7 | n/a |
| santerre | translation | mild | raft_small | mps | 10 | 5.0 % | 0.1819 | 43.2 % | 98.9 % | 10.0 % | 59.2 | n/a |
| santerre | translation | hard | raft | mps | 10 | 30.0 % | 0.1885 | 24.5 % | 98.6 % | 0.0 % | 142.4 | n/a |
| santerre | translation | hard | raft_small | mps | 10 | 30.0 % | 0.5098 | 3.4 % | 67.4 % | 20.0 % | 59.1 | n/a |
| santerre | affine | clean | raft | mps | 10 | 0.0 % | 0.0468 | 94.6 % | 100.0 % | 0.0 % | 140.4 | n/a |
| santerre | affine | clean | raft_small | mps | 10 | 0.0 % | 0.1185 | 46.8 % | 99.8 % | 0.0 % | 58.4 | n/a |
| santerre | affine | mild | raft | mps | 10 | 5.0 % | 0.0667 | 89.1 % | 99.8 % | 0.0 % | 141.5 | n/a |
| santerre | affine | mild | raft_small | mps | 10 | 5.0 % | 0.2414 | 37.8 % | 98.4 % | 0.0 % | 59.6 | n/a |
| santerre | affine | hard | raft | mps | 10 | 30.0 % | 0.2132 | 18.7 % | 98.3 % | 0.0 % | 143.5 | n/a |
| santerre | affine | hard | raft_small | mps | 10 | 30.0 % | 0.5303 | 2.9 % | 65.6 % | 20.0 % | 59.5 | n/a |
| santerre | dense | clean | raft | mps | 10 | 0.0 % | 0.0863 | 67.1 % | 100.0 % | 0.0 % | 145.0 | n/a |
| santerre | dense | clean | raft_small | mps | 10 | 0.0 % | 0.1461 | 35.4 % | 99.3 % | 0.0 % | 57.6 | n/a |
| santerre | dense | mild | raft | mps | 10 | 5.0 % | 0.1039 | 58.5 % | 99.9 % | 0.0 % | 142.8 | n/a |
| santerre | dense | mild | raft_small | mps | 10 | 5.0 % | 0.2207 | 32.4 % | 97.1 % | 0.0 % | 58.7 | n/a |
| santerre | dense | hard | raft | mps | 10 | 30.0 % | 0.2578 | 11.7 % | 94.0 % | 0.0 % | 141.8 | n/a |
| santerre | dense | hard | raft_small | mps | 10 | 30.0 % | 0.5396 | 3.9 % | 67.6 % | 20.0 % | 58.8 | n/a |
| lyon | translation | clean | raft | mps | 10 | 0.0 % | 0.0495 | 94.1 % | 100.0 % | 0.0 % | 141.9 | n/a |
| lyon | translation | clean | raft_small | mps | 10 | 0.0 % | 0.1583 | 25.8 % | 99.9 % | 0.0 % | 59.9 | n/a |
| lyon | translation | mild | raft | mps | 10 | 5.0 % | 0.0505 | 94.0 % | 100.0 % | 0.0 % | 142.4 | n/a |
| lyon | translation | mild | raft_small | mps | 10 | 5.0 % | 0.1494 | 28.8 % | 99.8 % | 0.0 % | 59.6 | n/a |
| lyon | translation | hard | raft | mps | 10 | 30.0 % | 0.1912 | 30.8 % | 99.7 % | 0.0 % | 142.1 | n/a |
| lyon | translation | hard | raft_small | mps | 10 | 30.0 % | 0.3500 | 6.8 % | 82.1 % | 0.0 % | 58.9 | n/a |
| lyon | affine | clean | raft | mps | 10 | 0.0 % | 0.0530 | 88.6 % | 100.0 % | 0.0 % | 142.3 | n/a |
| lyon | affine | clean | raft_small | mps | 10 | 0.0 % | 0.1556 | 26.2 % | 99.9 % | 0.0 % | 60.3 | n/a |
| lyon | affine | mild | raft | mps | 10 | 5.0 % | 0.0549 | 87.8 % | 100.0 % | 0.0 % | 142.6 | n/a |
| lyon | affine | mild | raft_small | mps | 10 | 5.0 % | 0.1465 | 30.8 % | 99.9 % | 0.0 % | 59.6 | n/a |
| lyon | affine | hard | raft | mps | 10 | 30.0 % | 0.2249 | 21.5 % | 99.1 % | 0.0 % | 142.5 | n/a |
| lyon | affine | hard | raft_small | mps | 10 | 30.0 % | 0.3533 | 7.6 % | 80.7 % | 0.0 % | 60.5 | n/a |
| lyon | dense | clean | raft | mps | 10 | 0.0 % | 0.0848 | 65.3 % | 100.0 % | 0.0 % | 146.7 | n/a |
| lyon | dense | clean | raft_small | mps | 10 | 0.0 % | 0.1796 | 24.6 % | 98.2 % | 0.0 % | 58.9 | n/a |
| lyon | dense | mild | raft | mps | 10 | 5.0 % | 0.0916 | 64.1 % | 100.0 % | 0.0 % | 141.8 | n/a |
| lyon | dense | mild | raft_small | mps | 10 | 5.0 % | 0.1790 | 25.4 % | 98.3 % | 0.0 % | 58.6 | n/a |
| lyon | dense | hard | raft | mps | 10 | 30.0 % | 0.2320 | 21.2 % | 96.4 % | 0.0 % | 142.2 | n/a |
| lyon | dense | hard | raft_small | mps | 10 | 30.0 % | 0.3572 | 7.2 % | 80.2 % | 0.0 % | 58.5 | n/a |
| morvan | translation | clean | raft | mps | 10 | 0.0 % | 0.0469 | 96.6 % | 100.0 % | 0.0 % | 142.1 | n/a |
| morvan | translation | clean | raft_small | mps | 10 | 0.0 % | 0.1375 | 33.4 % | 99.8 % | 0.0 % | 60.6 | n/a |
| morvan | translation | mild | raft | mps | 10 | 5.0 % | 0.0615 | 94.7 % | 99.9 % | 0.0 % | 142.6 | n/a |
| morvan | translation | mild | raft_small | mps | 10 | 5.0 % | 0.1952 | 34.5 % | 98.3 % | 0.0 % | 59.2 | n/a |
| morvan | translation | hard | raft | mps | 10 | 30.0 % | 0.2072 | 26.1 % | 93.0 % | 10.0 % | 142.6 | n/a |
| morvan | translation | hard | raft_small | mps | 10 | 30.0 % | 0.6065 | 1.7 % | 47.2 % | 40.0 % | 59.7 | n/a |
| morvan | affine | clean | raft | mps | 10 | 0.0 % | 0.0532 | 93.8 % | 100.0 % | 0.0 % | 140.4 | n/a |
| morvan | affine | clean | raft_small | mps | 10 | 0.0 % | 0.1411 | 31.4 % | 99.7 % | 0.0 % | 59.5 | n/a |
| morvan | affine | mild | raft | mps | 10 | 5.0 % | 0.0689 | 90.6 % | 99.9 % | 0.0 % | 142.5 | n/a |
| morvan | affine | mild | raft_small | mps | 10 | 5.0 % | 0.1866 | 36.4 % | 98.5 % | 0.0 % | 59.3 | n/a |
| morvan | affine | hard | raft | mps | 10 | 30.0 % | 0.2284 | 25.4 % | 91.0 % | 10.0 % | 143.2 | n/a |
| morvan | affine | hard | raft_small | mps | 10 | 30.0 % | 0.5666 | 2.4 % | 50.4 % | 50.0 % | 59.5 | n/a |
| morvan | dense | clean | raft | mps | 10 | 0.0 % | 0.0923 | 64.4 % | 100.0 % | 0.0 % | 145.8 | n/a |
| morvan | dense | clean | raft_small | mps | 10 | 0.0 % | 0.1681 | 26.4 % | 99.3 % | 0.0 % | 57.7 | n/a |
| morvan | dense | mild | raft | mps | 10 | 5.0 % | 0.1068 | 59.3 % | 99.9 % | 0.0 % | 142.5 | n/a |
| morvan | dense | mild | raft_small | mps | 10 | 5.0 % | 0.2110 | 28.6 % | 98.4 % | 0.0 % | 58.8 | n/a |
| morvan | dense | hard | raft | mps | 10 | 30.0 % | 0.2854 | 11.8 % | 88.6 % | 10.0 % | 141.8 | n/a |
| morvan | dense | hard | raft_small | mps | 10 | 30.0 % | 0.6984 | 1.7 % | 39.1 % | 30.0 % | 59.2 | n/a |
| sete | translation | clean | raft | mps | 10 | 0.0 % | 0.0474 | 97.3 % | 100.0 % | 0.0 % | 141.3 | n/a |
| sete | translation | clean | raft_small | mps | 10 | 0.0 % | 0.1287 | 38.9 % | 99.9 % | 0.0 % | 59.9 | n/a |
| sete | translation | mild | raft | mps | 10 | 5.0 % | 0.0538 | 93.0 % | 100.0 % | 0.0 % | 141.3 | n/a |
| sete | translation | mild | raft_small | mps | 10 | 5.0 % | 0.1905 | 28.9 % | 99.1 % | 0.0 % | 59.1 | n/a |
| sete | translation | hard | raft | mps | 10 | 30.0 % | 0.3458 | 25.2 % | 90.5 % | 40.0 % | 142.9 | n/a |
| sete | translation | hard | raft_small | mps | 10 | 30.0 % | 0.3353 | 7.7 % | 78.2 % | 60.0 % | 60.5 | n/a |
| sete | affine | clean | raft | mps | 10 | 0.0 % | 0.0551 | 91.0 % | 100.0 % | 0.0 % | 142.5 | n/a |
| sete | affine | clean | raft_small | mps | 10 | 0.0 % | 0.1307 | 37.1 % | 100.0 % | 0.0 % | 58.8 | n/a |
| sete | affine | mild | raft | mps | 10 | 5.0 % | 0.0654 | 85.1 % | 100.0 % | 0.0 % | 142.4 | n/a |
| sete | affine | mild | raft_small | mps | 10 | 5.0 % | 0.1915 | 29.3 % | 99.3 % | 0.0 % | 58.7 | n/a |
| sete | affine | hard | raft | mps | 10 | 30.0 % | 0.3467 | 13.9 % | 88.7 % | 40.0 % | 142.0 | n/a |
| sete | affine | hard | raft_small | mps | 10 | 30.0 % | 0.3594 | 5.0 % | 75.9 % | 60.0 % | 59.8 | n/a |
| sete | dense | clean | raft | mps | 10 | 0.0 % | 0.0892 | 64.8 % | 100.0 % | 0.0 % | 145.0 | n/a |
| sete | dense | clean | raft_small | mps | 10 | 0.0 % | 0.1591 | 30.4 % | 99.3 % | 0.0 % | 57.4 | n/a |
| sete | dense | mild | raft | mps | 10 | 5.0 % | 0.1033 | 58.4 % | 99.9 % | 0.0 % | 142.0 | n/a |
| sete | dense | mild | raft_small | mps | 10 | 5.0 % | 0.2034 | 26.8 % | 97.9 % | 0.0 % | 58.2 | n/a |
| sete | dense | hard | raft | mps | 10 | 30.0 % | 0.4451 | 16.2 % | 86.0 % | 30.0 % | 141.2 | n/a |
| sete | dense | hard | raft_small | mps | 10 | 30.0 % | 0.3687 | 7.0 % | 78.0 % | 60.0 % | 58.7 | n/a |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 1 calls per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Details in `context.json`.
