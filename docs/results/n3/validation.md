Validation set: 100 pairs per chip, scenario and preset, seed 0, cut from the validation chips santerre, lyon, morvan, sete.

Over every chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all chips | translation | clean | raft | mps | 400 | 0.0 % | 0.0447 | 96.1 % | 100.0 % | 0.0 % | 136.7 | n/a |
| all chips | translation | clean | raft_small | mps | 400 | 0.0 % | 0.1289 | 40.7 % | 99.8 % | 0.0 % | 57.1 | n/a |
| all chips | translation | mild | raft | mps | 400 | 5.0 % | 0.0613 | 92.8 % | 99.9 % | 0.0 % | 137.0 | n/a |
| all chips | translation | mild | raft_small | mps | 400 | 5.0 % | 0.1656 | 35.9 % | 99.3 % | 0.5 % | 56.9 | n/a |
| all chips | translation | hard | raft | mps | 400 | 30.0 % | 0.2118 | 28.9 % | 95.4 % | 6.0 % | 137.0 | n/a |
| all chips | translation | hard | raft_small | mps | 400 | 30.0 % | 0.4720 | 5.5 % | 66.8 % | 27.3 % | 57.1 | n/a |
| all chips | affine | clean | raft | mps | 400 | 0.0 % | 0.0522 | 92.1 % | 100.0 % | 0.0 % | 136.6 | n/a |
| all chips | affine | clean | raft_small | mps | 400 | 0.0 % | 0.1304 | 40.1 % | 99.8 % | 0.0 % | 56.6 | n/a |
| all chips | affine | mild | raft | mps | 400 | 5.0 % | 0.0702 | 86.3 % | 99.9 % | 0.0 % | 136.8 | n/a |
| all chips | affine | mild | raft_small | mps | 400 | 5.0 % | 0.1701 | 35.2 % | 99.3 % | 0.2 % | 56.9 | n/a |
| all chips | affine | hard | raft | mps | 400 | 30.0 % | 0.2389 | 22.6 % | 93.6 % | 5.8 % | 137.1 | n/a |
| all chips | affine | hard | raft_small | mps | 400 | 30.0 % | 0.4777 | 5.2 % | 65.4 % | 27.8 % | 57.1 | n/a |
| all chips | dense | clean | raft | mps | 400 | 0.0 % | 0.0923 | 63.5 % | 100.0 % | 0.0 % | 141.1 | n/a |
| all chips | dense | clean | raft_small | mps | 400 | 0.0 % | 0.1631 | 29.4 % | 99.3 % | 0.0 % | 55.7 | n/a |
| all chips | dense | mild | raft | mps | 400 | 5.0 % | 0.1124 | 55.8 % | 99.9 % | 0.0 % | 136.5 | n/a |
| all chips | dense | mild | raft_small | mps | 400 | 5.0 % | 0.1919 | 26.0 % | 98.5 % | 0.5 % | 56.1 | n/a |
| all chips | dense | hard | raft | mps | 400 | 30.0 % | 0.2751 | 15.6 % | 90.2 % | 5.8 % | 136.7 | n/a |
| all chips | dense | hard | raft_small | mps | 400 | 30.0 % | 0.4967 | 4.8 % | 63.9 % | 25.8 % | 56.4 | n/a |

By chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | translation | clean | raft | mps | 100 | 0.0 % | 0.0367 | 97.7 % | 100.0 % | 0.0 % | 137.3 | n/a |
| santerre | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1135 | 50.6 % | 99.8 % | 0.0 % | 56.3 | n/a |
| santerre | translation | mild | raft | mps | 100 | 5.0 % | 0.0698 | 94.0 % | 99.9 % | 0.0 % | 137.5 | n/a |
| santerre | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1794 | 40.9 % | 99.0 % | 1.0 % | 56.5 | n/a |
| santerre | translation | hard | raft | mps | 100 | 30.0 % | 0.2422 | 20.3 % | 95.3 % | 3.0 % | 138.1 | n/a |
| santerre | translation | hard | raft_small | mps | 100 | 30.0 % | 0.5000 | 5.3 % | 65.4 % | 21.0 % | 57.0 | n/a |
| santerre | affine | clean | raft | mps | 100 | 0.0 % | 0.0467 | 94.4 % | 100.0 % | 0.0 % | 136.9 | n/a |
| santerre | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1148 | 49.8 % | 99.8 % | 0.0 % | 56.0 | n/a |
| santerre | affine | mild | raft | mps | 100 | 5.0 % | 0.0796 | 86.8 % | 99.8 % | 0.0 % | 137.4 | n/a |
| santerre | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1856 | 39.6 % | 99.0 % | 0.0 % | 56.3 | n/a |
| santerre | affine | hard | raft | mps | 100 | 30.0 % | 0.2656 | 16.0 % | 93.4 % | 3.0 % | 137.4 | n/a |
| santerre | affine | hard | raft_small | mps | 100 | 30.0 % | 0.5012 | 4.8 % | 63.5 % | 22.0 % | 56.6 | n/a |
| santerre | dense | clean | raft | mps | 100 | 0.0 % | 0.0864 | 67.8 % | 100.0 % | 0.0 % | 142.0 | n/a |
| santerre | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1460 | 36.0 % | 99.5 % | 0.0 % | 54.9 | n/a |
| santerre | dense | mild | raft | mps | 100 | 5.0 % | 0.1176 | 56.8 % | 99.8 % | 0.0 % | 136.6 | n/a |
| santerre | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1921 | 29.2 % | 98.4 % | 1.0 % | 55.6 | n/a |
| santerre | dense | hard | raft | mps | 100 | 30.0 % | 0.2936 | 11.2 % | 89.3 % | 3.0 % | 137.2 | n/a |
| santerre | dense | hard | raft_small | mps | 100 | 30.0 % | 0.5237 | 4.8 % | 61.6 % | 19.0 % | 56.3 | n/a |
| lyon | translation | clean | raft | mps | 100 | 0.0 % | 0.0513 | 93.6 % | 100.0 % | 0.0 % | 136.4 | n/a |
| lyon | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1544 | 27.0 % | 99.8 % | 0.0 % | 57.1 | n/a |
| lyon | translation | mild | raft | mps | 100 | 5.0 % | 0.0545 | 91.6 % | 100.0 % | 0.0 % | 136.7 | n/a |
| lyon | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1597 | 27.2 % | 99.7 % | 1.0 % | 56.8 | n/a |
| lyon | translation | hard | raft | mps | 100 | 30.0 % | 0.1319 | 43.2 % | 99.8 % | 0.0 % | 136.5 | n/a |
| lyon | translation | hard | raft_small | mps | 100 | 30.0 % | 0.3887 | 7.2 % | 75.8 % | 1.0 % | 57.1 | n/a |
| lyon | affine | clean | raft | mps | 100 | 0.0 % | 0.0574 | 88.4 % | 100.0 % | 0.0 % | 136.3 | n/a |
| lyon | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1546 | 27.9 % | 99.8 % | 0.0 % | 56.7 | n/a |
| lyon | affine | mild | raft | mps | 100 | 5.0 % | 0.0622 | 85.9 % | 100.0 % | 0.0 % | 136.4 | n/a |
| lyon | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1597 | 27.7 % | 99.7 % | 1.0 % | 56.8 | n/a |
| lyon | affine | hard | raft | mps | 100 | 30.0 % | 0.1586 | 33.3 % | 99.3 % | 0.0 % | 136.7 | n/a |
| lyon | affine | hard | raft_small | mps | 100 | 30.0 % | 0.3949 | 7.1 % | 75.2 % | 1.0 % | 57.0 | n/a |
| lyon | dense | clean | raft | mps | 100 | 0.0 % | 0.1005 | 58.3 % | 100.0 % | 0.0 % | 140.8 | n/a |
| lyon | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1875 | 22.1 % | 98.8 % | 0.0 % | 55.9 | n/a |
| lyon | dense | mild | raft | mps | 100 | 5.0 % | 0.1103 | 54.1 % | 100.0 % | 0.0 % | 136.0 | n/a |
| lyon | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1958 | 20.6 % | 98.6 % | 1.0 % | 56.2 | n/a |
| lyon | dense | hard | raft | mps | 100 | 30.0 % | 0.2045 | 22.3 % | 96.7 % | 0.0 % | 136.3 | n/a |
| lyon | dense | hard | raft_small | mps | 100 | 30.0 % | 0.4144 | 6.2 % | 73.0 % | 1.0 % | 56.3 | n/a |
| morvan | translation | clean | raft | mps | 100 | 0.0 % | 0.0443 | 96.9 % | 100.0 % | 0.0 % | 136.4 | n/a |
| morvan | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1240 | 43.2 % | 99.8 % | 0.0 % | 57.5 | n/a |
| morvan | translation | mild | raft | mps | 100 | 5.0 % | 0.0677 | 93.9 % | 99.9 % | 0.0 % | 136.7 | n/a |
| morvan | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1735 | 38.0 % | 99.0 % | 0.0 % | 57.1 | n/a |
| morvan | translation | hard | raft | mps | 100 | 30.0 % | 0.2131 | 24.8 % | 95.8 % | 2.0 % | 136.6 | n/a |
| morvan | translation | hard | raft_small | mps | 100 | 30.0 % | 0.5668 | 3.1 % | 55.4 % | 40.0 % | 57.1 | n/a |
| morvan | affine | clean | raft | mps | 100 | 0.0 % | 0.0511 | 94.2 % | 100.0 % | 0.0 % | 136.2 | n/a |
| morvan | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1267 | 41.9 % | 99.8 % | 0.0 % | 57.0 | n/a |
| morvan | affine | mild | raft | mps | 100 | 5.0 % | 0.0766 | 88.2 % | 99.8 % | 0.0 % | 136.5 | n/a |
| morvan | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1779 | 37.2 % | 99.0 % | 0.0 % | 57.1 | n/a |
| morvan | affine | hard | raft | mps | 100 | 30.0 % | 0.2410 | 20.2 % | 93.4 % | 2.0 % | 137.1 | n/a |
| morvan | affine | hard | raft_small | mps | 100 | 30.0 % | 0.5937 | 2.7 % | 52.0 % | 40.0 % | 57.4 | n/a |
| morvan | dense | clean | raft | mps | 100 | 0.0 % | 0.0895 | 65.4 % | 100.0 % | 0.0 % | 140.3 | n/a |
| morvan | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1579 | 30.5 % | 99.5 % | 0.0 % | 56.0 | n/a |
| morvan | dense | mild | raft | mps | 100 | 5.0 % | 0.1129 | 58.0 % | 99.9 % | 0.0 % | 136.4 | n/a |
| morvan | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1974 | 27.4 % | 98.6 % | 0.0 % | 56.3 | n/a |
| morvan | dense | hard | raft | mps | 100 | 30.0 % | 0.2755 | 14.9 % | 88.4 % | 2.0 % | 136.6 | n/a |
| morvan | dense | hard | raft_small | mps | 100 | 30.0 % | 0.6085 | 2.8 % | 51.5 % | 34.0 % | 56.5 | n/a |
| sete | translation | clean | raft | mps | 100 | 0.0 % | 0.0467 | 96.1 % | 100.0 % | 0.0 % | 138.2 | n/a |
| sete | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1237 | 41.8 % | 99.9 % | 0.0 % | 57.3 | n/a |
| sete | translation | mild | raft | mps | 100 | 5.0 % | 0.0532 | 91.7 % | 100.0 % | 0.0 % | 138.8 | n/a |
| sete | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1499 | 37.6 % | 99.6 % | 0.0 % | 57.1 | n/a |
| sete | translation | hard | raft | mps | 100 | 30.0 % | 0.2723 | 26.3 % | 89.8 % | 19.0 % | 140.6 | n/a |
| sete | translation | hard | raft_small | mps | 100 | 30.0 % | 0.4787 | 5.4 % | 65.0 % | 47.0 % | 57.2 | n/a |
| sete | affine | clean | raft | mps | 100 | 0.0 % | 0.0537 | 91.4 % | 100.0 % | 0.0 % | 138.1 | n/a |
| sete | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1256 | 41.0 % | 99.9 % | 0.0 % | 56.9 | n/a |
| sete | affine | mild | raft | mps | 100 | 5.0 % | 0.0624 | 84.4 % | 100.0 % | 0.0 % | 137.8 | n/a |
| sete | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1572 | 36.3 % | 99.5 % | 0.0 % | 57.6 | n/a |
| sete | affine | hard | raft | mps | 100 | 30.0 % | 0.3028 | 20.4 % | 87.4 % | 18.0 % | 139.4 | n/a |
| sete | affine | hard | raft_small | mps | 100 | 30.0 % | 0.4660 | 4.9 % | 65.2 % | 48.0 % | 57.3 | n/a |
| sete | dense | clean | raft | mps | 100 | 0.0 % | 0.0929 | 62.4 % | 100.0 % | 0.0 % | 143.8 | n/a |
| sete | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1609 | 29.1 % | 99.4 % | 0.0 % | 55.5 | n/a |
| sete | dense | mild | raft | mps | 100 | 5.0 % | 0.1087 | 54.3 % | 99.9 % | 0.0 % | 139.3 | n/a |
| sete | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1823 | 26.9 % | 98.6 % | 0.0 % | 56.5 | n/a |
| sete | dense | hard | raft | mps | 100 | 30.0 % | 0.3390 | 13.4 % | 85.3 % | 18.0 % | 138.4 | n/a |
| sete | dense | hard | raft_small | mps | 100 | 30.0 % | 0.4689 | 4.4 % | 65.6 % | 49.0 % | 56.5 | n/a |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 1 calls per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Details in `context.json`.

Light sets, the first pairs of every cell, next to the full set:

| pairs per cell | degradation | method | failures | full | EPE (px) | full | spread | gap (px) | full | spread |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | clean | raft | 0.0 % | 0.0 % | 0.0639 | 0.0631 | 0.0031 | n/a | n/a | n/a |
| 5 | clean | raft_small | 0.0 % | 0.0 % | 0.1470 | 0.1408 | 0.0082 | +0.0831 | +0.0777 | 0.0080 |
| 5 | mild | raft | 0.0 % | 0.0 % | 0.0762 | 0.0813 | 0.0121 | n/a | n/a | n/a |
| 5 | mild | raft_small | 1.7 % | 0.4 % | 0.2004 | 0.1759 | 0.0195 | +0.1237 | +0.0946 | 0.0198 |
| 5 | hard | raft | 18.3 % | 5.8 % | 0.2558 | 0.2420 | 0.0285 | n/a | n/a | n/a |
| 5 | hard | raft_small | 36.7 % | 26.9 % | 0.5179 | 0.4823 | 0.0396 | +0.2609 | +0.2728 | 0.0369 |
| 5 | all | raft | 6.1 % | 1.9 % | 0.1239 | 0.1265 | 0.0107 | n/a | n/a | n/a |
| 5 | all | raft_small | 12.8 % | 9.1 % | 0.2568 | 0.2451 | 0.0161 | +0.1399 | +0.1356 | 0.0142 |
| 10 | clean | raft | 0.0 % | 0.0 % | 0.0619 | 0.0631 | 0.0021 | n/a | n/a | n/a |
| 10 | clean | raft_small | 0.0 % | 0.0 % | 0.1451 | 0.1408 | 0.0055 | +0.0833 | +0.0777 | 0.0053 |
| 10 | mild | raft | 0.0 % | 0.0 % | 0.0728 | 0.0813 | 0.0079 | n/a | n/a | n/a |
| 10 | mild | raft_small | 0.8 % | 0.4 % | 0.1915 | 0.1759 | 0.0137 | +0.1185 | +0.0946 | 0.0140 |
| 10 | hard | raft | 11.7 % | 5.8 % | 0.2532 | 0.2420 | 0.0190 | n/a | n/a | n/a |
| 10 | hard | raft_small | 30.0 % | 26.9 % | 0.4626 | 0.4823 | 0.0283 | +0.2366 | +0.2728 | 0.0261 |
| 10 | all | raft | 3.9 % | 1.9 % | 0.1243 | 0.1265 | 0.0071 | n/a | n/a | n/a |
| 10 | all | raft_small | 10.3 % | 9.1 % | 0.2448 | 0.2451 | 0.0113 | +0.1348 | +0.1356 | 0.0098 |
| 20 | clean | raft | 0.0 % | 0.0 % | 0.0623 | 0.0631 | 0.0014 | n/a | n/a | n/a |
| 20 | clean | raft_small | 0.0 % | 0.0 % | 0.1424 | 0.1408 | 0.0037 | +0.0801 | +0.0777 | 0.0036 |
| 20 | mild | raft | 0.0 % | 0.0 % | 0.0781 | 0.0813 | 0.0054 | n/a | n/a | n/a |
| 20 | mild | raft_small | 0.4 % | 0.4 % | 0.1833 | 0.1759 | 0.0091 | +0.1051 | +0.0946 | 0.0094 |
| 20 | hard | raft | 7.9 % | 5.8 % | 0.2442 | 0.2420 | 0.0132 | n/a | n/a | n/a |
| 20 | hard | raft_small | 30.8 % | 26.9 % | 0.4580 | 0.4823 | 0.0184 | +0.2441 | +0.2728 | 0.0179 |
| 20 | all | raft | 2.6 % | 1.9 % | 0.1251 | 0.1265 | 0.0050 | n/a | n/a | n/a |
| 20 | all | raft_small | 10.4 % | 9.1 % | 0.2388 | 0.2451 | 0.0077 | +0.1308 | +0.1356 | 0.0066 |
| 50 | clean | raft | 0.0 % | 0.0 % | 0.0636 | 0.0631 | 0.0007 | n/a | n/a | n/a |
| 50 | clean | raft_small | 0.0 % | 0.0 % | 0.1417 | 0.1408 | 0.0018 | +0.0781 | +0.0777 | 0.0018 |
| 50 | mild | raft | 0.0 % | 0.0 % | 0.0810 | 0.0813 | 0.0026 | n/a | n/a | n/a |
| 50 | mild | raft_small | 0.2 % | 0.4 % | 0.1799 | 0.1759 | 0.0047 | +0.0988 | +0.0946 | 0.0046 |
| 50 | hard | raft | 6.7 % | 5.8 % | 0.2397 | 0.2420 | 0.0064 | n/a | n/a | n/a |
| 50 | hard | raft_small | 29.7 % | 26.9 % | 0.4736 | 0.4823 | 0.0094 | +0.2664 | +0.2728 | 0.0088 |
| 50 | all | raft | 2.2 % | 1.9 % | 0.1256 | 0.1265 | 0.0024 | n/a | n/a | n/a |
| 50 | all | raft_small | 9.9 % | 9.1 % | 0.2422 | 0.2451 | 0.0039 | +0.1342 | +0.1356 | 0.0034 |

Over every chip and scenario. EPE is the mean error over non-failed pairs; gap is the mean difference of error with raft over the pairs neither fails. Spread is the standard deviation of the figure over 1000 random sets of as many pair indices: how far a light set of that size strays from the full one.
