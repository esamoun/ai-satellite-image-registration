Validation set: 100 pairs per chip, scenario and preset, seed 0, cut from the validation chips santerre, lyon, morvan, sete.

Over every chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all chips | translation | clean | raft | mps | 400 | 0.0 % | 0.0447 | 96.1 % | 100.0 % | 0.0 % | 138.3 | n/a |
| all chips | translation | clean | raft_ft_same_date | mps | 400 | 0.0 % | 0.0215 | 100.0 % | 100.0 % | 0.0 % | 139.9 | n/a |
| all chips | translation | clean | raft_ft_cross_date | mps | 400 | 0.0 % | 0.0303 | 99.7 % | 100.0 % | 0.0 % | 140.3 | n/a |
| all chips | translation | mild | raft | mps | 400 | 5.0 % | 0.0613 | 92.8 % | 99.9 % | 0.0 % | 138.6 | n/a |
| all chips | translation | mild | raft_ft_same_date | mps | 400 | 5.0 % | 0.0248 | 99.9 % | 100.0 % | 0.0 % | 140.1 | n/a |
| all chips | translation | mild | raft_ft_cross_date | mps | 400 | 5.0 % | 0.0350 | 99.0 % | 100.0 % | 0.0 % | 140.2 | n/a |
| all chips | translation | hard | raft | mps | 400 | 30.0 % | 0.2118 | 28.9 % | 95.4 % | 6.0 % | 138.9 | n/a |
| all chips | translation | hard | raft_ft_same_date | mps | 400 | 30.0 % | 0.0891 | 68.1 % | 99.9 % | 0.0 % | 140.5 | n/a |
| all chips | translation | hard | raft_ft_cross_date | mps | 400 | 30.0 % | 0.1139 | 51.5 % | 99.7 % | 0.0 % | 140.8 | n/a |
| all chips | affine | clean | raft | mps | 400 | 0.0 % | 0.0522 | 92.1 % | 100.0 % | 0.0 % | 137.9 | n/a |
| all chips | affine | clean | raft_ft_same_date | mps | 400 | 0.0 % | 0.0289 | 99.7 % | 100.0 % | 0.0 % | 140.2 | n/a |
| all chips | affine | clean | raft_ft_cross_date | mps | 400 | 0.0 % | 0.0364 | 98.6 % | 100.0 % | 0.0 % | 140.6 | n/a |
| all chips | affine | mild | raft | mps | 400 | 5.0 % | 0.0702 | 86.3 % | 99.9 % | 0.0 % | 138.7 | n/a |
| all chips | affine | mild | raft_ft_same_date | mps | 400 | 5.0 % | 0.0341 | 98.7 % | 100.0 % | 0.0 % | 140.1 | n/a |
| all chips | affine | mild | raft_ft_cross_date | mps | 400 | 5.0 % | 0.0429 | 96.3 % | 100.0 % | 0.0 % | 140.4 | n/a |
| all chips | affine | hard | raft | mps | 400 | 30.0 % | 0.2389 | 22.6 % | 93.6 % | 5.8 % | 139.0 | n/a |
| all chips | affine | hard | raft_ft_same_date | mps | 400 | 30.0 % | 0.1300 | 47.3 % | 99.0 % | 0.0 % | 140.6 | n/a |
| all chips | affine | hard | raft_ft_cross_date | mps | 400 | 30.0 % | 0.1469 | 38.3 % | 98.5 % | 0.0 % | 140.8 | n/a |
| all chips | dense | clean | raft | mps | 400 | 0.0 % | 0.0923 | 63.5 % | 100.0 % | 0.0 % | 139.8 | n/a |
| all chips | dense | clean | raft_ft_same_date | mps | 400 | 0.0 % | 0.0599 | 86.4 % | 100.0 % | 0.0 % | 137.8 | n/a |
| all chips | dense | clean | raft_ft_cross_date | mps | 400 | 0.0 % | 0.0703 | 79.0 % | 100.0 % | 0.0 % | 139.5 | n/a |
| all chips | dense | mild | raft | mps | 400 | 5.0 % | 0.1124 | 55.8 % | 99.9 % | 0.0 % | 137.9 | n/a |
| all chips | dense | mild | raft_ft_same_date | mps | 400 | 5.0 % | 0.0712 | 78.7 % | 100.0 % | 0.0 % | 139.0 | n/a |
| all chips | dense | mild | raft_ft_cross_date | mps | 400 | 5.0 % | 0.0818 | 71.4 % | 100.0 % | 0.0 % | 139.4 | n/a |
| all chips | dense | hard | raft | mps | 400 | 30.0 % | 0.2751 | 15.6 % | 90.2 % | 5.8 % | 138.0 | n/a |
| all chips | dense | hard | raft_ft_same_date | mps | 400 | 30.0 % | 0.1835 | 29.9 % | 96.7 % | 0.0 % | 139.4 | n/a |
| all chips | dense | hard | raft_ft_cross_date | mps | 400 | 30.0 % | 0.2013 | 24.7 % | 95.7 % | 0.0 % | 139.7 | n/a |

By chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | translation | clean | raft | mps | 100 | 0.0 % | 0.0367 | 97.7 % | 100.0 % | 0.0 % | 138.5 | n/a |
| santerre | translation | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0215 | 100.0 % | 100.0 % | 0.0 % | 140.3 | n/a |
| santerre | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0284 | 99.8 % | 100.0 % | 0.0 % | 140.1 | n/a |
| santerre | translation | mild | raft | mps | 100 | 5.0 % | 0.0698 | 94.0 % | 99.9 % | 0.0 % | 138.8 | n/a |
| santerre | translation | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0246 | 99.9 % | 100.0 % | 0.0 % | 140.3 | n/a |
| santerre | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0351 | 99.5 % | 100.0 % | 0.0 % | 140.4 | n/a |
| santerre | translation | hard | raft | mps | 100 | 30.0 % | 0.2422 | 20.3 % | 95.3 % | 3.0 % | 139.3 | n/a |
| santerre | translation | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.0902 | 62.4 % | 100.0 % | 0.0 % | 140.7 | n/a |
| santerre | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1115 | 50.0 % | 100.0 % | 0.0 % | 141.0 | n/a |
| santerre | affine | clean | raft | mps | 100 | 0.0 % | 0.0467 | 94.4 % | 100.0 % | 0.0 % | 138.0 | n/a |
| santerre | affine | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0291 | 99.8 % | 100.0 % | 0.0 % | 140.3 | n/a |
| santerre | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0358 | 98.7 % | 100.0 % | 0.0 % | 140.8 | n/a |
| santerre | affine | mild | raft | mps | 100 | 5.0 % | 0.0796 | 86.8 % | 99.8 % | 0.0 % | 138.8 | n/a |
| santerre | affine | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0346 | 99.1 % | 100.0 % | 0.0 % | 139.9 | n/a |
| santerre | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0441 | 96.7 % | 100.0 % | 0.0 % | 140.4 | n/a |
| santerre | affine | hard | raft | mps | 100 | 30.0 % | 0.2656 | 16.0 % | 93.4 % | 3.0 % | 139.3 | n/a |
| santerre | affine | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1278 | 41.4 % | 100.0 % | 0.0 % | 140.6 | n/a |
| santerre | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1460 | 34.3 % | 99.9 % | 0.0 % | 141.1 | n/a |
| santerre | dense | clean | raft | mps | 100 | 0.0 % | 0.0864 | 67.8 % | 100.0 % | 0.0 % | 140.0 | n/a |
| santerre | dense | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0607 | 85.8 % | 100.0 % | 0.0 % | 137.8 | n/a |
| santerre | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0707 | 79.0 % | 100.0 % | 0.0 % | 139.3 | n/a |
| santerre | dense | mild | raft | mps | 100 | 5.0 % | 0.1176 | 56.8 % | 99.8 % | 0.0 % | 138.3 | n/a |
| santerre | dense | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0738 | 77.3 % | 100.0 % | 0.0 % | 139.7 | n/a |
| santerre | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0847 | 69.6 % | 100.0 % | 0.0 % | 139.9 | n/a |
| santerre | dense | hard | raft | mps | 100 | 30.0 % | 0.2936 | 11.2 % | 89.3 % | 3.0 % | 138.6 | n/a |
| santerre | dense | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1813 | 26.7 % | 98.2 % | 0.0 % | 140.3 | n/a |
| santerre | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1976 | 22.5 % | 97.6 % | 0.0 % | 140.1 | n/a |
| lyon | translation | clean | raft | mps | 100 | 0.0 % | 0.0513 | 93.6 % | 100.0 % | 0.0 % | 138.0 | n/a |
| lyon | translation | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0215 | 100.0 % | 100.0 % | 0.0 % | 139.8 | n/a |
| lyon | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0302 | 99.7 % | 100.0 % | 0.0 % | 140.2 | n/a |
| lyon | translation | mild | raft | mps | 100 | 5.0 % | 0.0545 | 91.6 % | 100.0 % | 0.0 % | 138.1 | n/a |
| lyon | translation | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0237 | 100.0 % | 100.0 % | 0.0 % | 140.0 | n/a |
| lyon | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0335 | 99.3 % | 100.0 % | 0.0 % | 139.9 | n/a |
| lyon | translation | hard | raft | mps | 100 | 30.0 % | 0.1319 | 43.2 % | 99.8 % | 0.0 % | 138.6 | n/a |
| lyon | translation | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.0713 | 79.5 % | 100.0 % | 0.0 % | 140.3 | n/a |
| lyon | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.0918 | 63.0 % | 100.0 % | 0.0 % | 140.6 | n/a |
| lyon | affine | clean | raft | mps | 100 | 0.0 % | 0.0574 | 88.4 % | 100.0 % | 0.0 % | 137.7 | n/a |
| lyon | affine | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0289 | 99.8 % | 100.0 % | 0.0 % | 140.2 | n/a |
| lyon | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0357 | 98.8 % | 100.0 % | 0.0 % | 140.6 | n/a |
| lyon | affine | mild | raft | mps | 100 | 5.0 % | 0.0622 | 85.9 % | 100.0 % | 0.0 % | 138.8 | n/a |
| lyon | affine | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0318 | 99.5 % | 100.0 % | 0.0 % | 140.6 | n/a |
| lyon | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0405 | 97.3 % | 100.0 % | 0.0 % | 140.4 | n/a |
| lyon | affine | hard | raft | mps | 100 | 30.0 % | 0.1586 | 33.3 % | 99.3 % | 0.0 % | 138.6 | n/a |
| lyon | affine | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1004 | 58.8 % | 100.0 % | 0.0 % | 140.1 | n/a |
| lyon | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1125 | 49.8 % | 100.0 % | 0.0 % | 140.6 | n/a |
| lyon | dense | clean | raft | mps | 100 | 0.0 % | 0.1005 | 58.3 % | 100.0 % | 0.0 % | 139.9 | n/a |
| lyon | dense | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0583 | 87.5 % | 100.0 % | 0.0 % | 138.2 | n/a |
| lyon | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0671 | 81.1 % | 100.0 % | 0.0 % | 139.5 | n/a |
| lyon | dense | mild | raft | mps | 100 | 5.0 % | 0.1103 | 54.1 % | 100.0 % | 0.0 % | 137.9 | n/a |
| lyon | dense | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0665 | 81.3 % | 100.0 % | 0.0 % | 139.0 | n/a |
| lyon | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0756 | 75.3 % | 100.0 % | 0.0 % | 139.6 | n/a |
| lyon | dense | hard | raft | mps | 100 | 30.0 % | 0.2045 | 22.3 % | 96.7 % | 0.0 % | 137.5 | n/a |
| lyon | dense | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1497 | 36.9 % | 99.1 % | 0.0 % | 138.8 | n/a |
| lyon | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1633 | 31.2 % | 98.8 % | 0.0 % | 139.4 | n/a |
| morvan | translation | clean | raft | mps | 100 | 0.0 % | 0.0443 | 96.9 % | 100.0 % | 0.0 % | 139.0 | n/a |
| morvan | translation | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0211 | 100.0 % | 100.0 % | 0.0 % | 140.4 | n/a |
| morvan | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0287 | 99.9 % | 100.0 % | 0.0 % | 141.0 | n/a |
| morvan | translation | mild | raft | mps | 100 | 5.0 % | 0.0677 | 93.9 % | 99.9 % | 0.0 % | 138.9 | n/a |
| morvan | translation | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0248 | 100.0 % | 100.0 % | 0.0 % | 140.2 | n/a |
| morvan | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0329 | 99.6 % | 100.0 % | 0.0 % | 140.6 | n/a |
| morvan | translation | hard | raft | mps | 100 | 30.0 % | 0.2131 | 24.8 % | 95.8 % | 2.0 % | 139.2 | n/a |
| morvan | translation | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.0810 | 71.9 % | 99.9 % | 0.0 % | 140.6 | n/a |
| morvan | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1108 | 50.0 % | 99.9 % | 0.0 % | 141.3 | n/a |
| morvan | affine | clean | raft | mps | 100 | 0.0 % | 0.0511 | 94.2 % | 100.0 % | 0.0 % | 138.0 | n/a |
| morvan | affine | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0282 | 99.7 % | 100.0 % | 0.0 % | 140.8 | n/a |
| morvan | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0350 | 98.9 % | 100.0 % | 0.0 % | 141.1 | n/a |
| morvan | affine | mild | raft | mps | 100 | 5.0 % | 0.0766 | 88.2 % | 99.8 % | 0.0 % | 139.0 | n/a |
| morvan | affine | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0334 | 99.1 % | 100.0 % | 0.0 % | 140.4 | n/a |
| morvan | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0401 | 97.8 % | 100.0 % | 0.0 % | 140.5 | n/a |
| morvan | affine | hard | raft | mps | 100 | 30.0 % | 0.2410 | 20.2 % | 93.4 % | 2.0 % | 139.4 | n/a |
| morvan | affine | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1207 | 48.7 % | 99.8 % | 0.0 % | 141.3 | n/a |
| morvan | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1403 | 36.9 % | 99.4 % | 0.0 % | 140.7 | n/a |
| morvan | dense | clean | raft | mps | 100 | 0.0 % | 0.0895 | 65.4 % | 100.0 % | 0.0 % | 140.0 | n/a |
| morvan | dense | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0586 | 87.2 % | 100.0 % | 0.0 % | 138.2 | n/a |
| morvan | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0696 | 79.6 % | 100.0 % | 0.0 % | 140.2 | n/a |
| morvan | dense | mild | raft | mps | 100 | 5.0 % | 0.1129 | 58.0 % | 99.9 % | 0.0 % | 138.6 | n/a |
| morvan | dense | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0689 | 80.2 % | 100.0 % | 0.0 % | 139.7 | n/a |
| morvan | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0795 | 72.9 % | 100.0 % | 0.0 % | 139.9 | n/a |
| morvan | dense | hard | raft | mps | 100 | 30.0 % | 0.2755 | 14.9 % | 88.4 % | 2.0 % | 138.9 | n/a |
| morvan | dense | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1733 | 32.0 % | 97.3 % | 0.0 % | 140.2 | n/a |
| morvan | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1932 | 25.4 % | 96.8 % | 0.0 % | 140.3 | n/a |
| sete | translation | clean | raft | mps | 100 | 0.0 % | 0.0467 | 96.1 % | 100.0 % | 0.0 % | 137.7 | n/a |
| sete | translation | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0219 | 100.0 % | 100.0 % | 0.0 % | 139.1 | n/a |
| sete | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0340 | 99.4 % | 100.0 % | 0.0 % | 139.7 | n/a |
| sete | translation | mild | raft | mps | 100 | 5.0 % | 0.0532 | 91.7 % | 100.0 % | 0.0 % | 137.7 | n/a |
| sete | translation | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0261 | 99.7 % | 100.0 % | 0.0 % | 139.7 | n/a |
| sete | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0385 | 97.5 % | 100.0 % | 0.0 % | 139.7 | n/a |
| sete | translation | hard | raft | mps | 100 | 30.0 % | 0.2723 | 26.3 % | 89.8 % | 19.0 % | 138.5 | n/a |
| sete | translation | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1140 | 58.5 % | 99.5 % | 0.0 % | 140.1 | n/a |
| sete | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1417 | 43.0 % | 98.9 % | 0.0 % | 140.6 | n/a |
| sete | affine | clean | raft | mps | 100 | 0.0 % | 0.0537 | 91.4 % | 100.0 % | 0.0 % | 137.8 | n/a |
| sete | affine | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0294 | 99.6 % | 100.0 % | 0.0 % | 139.4 | n/a |
| sete | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0392 | 97.8 % | 100.0 % | 0.0 % | 140.2 | n/a |
| sete | affine | mild | raft | mps | 100 | 5.0 % | 0.0624 | 84.4 % | 100.0 % | 0.0 % | 138.3 | n/a |
| sete | affine | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0365 | 97.1 % | 100.0 % | 0.0 % | 139.8 | n/a |
| sete | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0469 | 93.2 % | 100.0 % | 0.0 % | 140.1 | n/a |
| sete | affine | hard | raft | mps | 100 | 30.0 % | 0.3028 | 20.4 % | 87.4 % | 18.0 % | 138.5 | n/a |
| sete | affine | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.1712 | 40.3 % | 96.2 % | 0.0 % | 140.2 | n/a |
| sete | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1886 | 32.1 % | 94.8 % | 0.0 % | 140.4 | n/a |
| sete | dense | clean | raft | mps | 100 | 0.0 % | 0.0929 | 62.4 % | 100.0 % | 0.0 % | 139.3 | n/a |
| sete | dense | clean | raft_ft_same_date | mps | 100 | 0.0 % | 0.0621 | 85.3 % | 100.0 % | 0.0 % | 137.2 | n/a |
| sete | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0740 | 76.3 % | 100.0 % | 0.0 % | 138.8 | n/a |
| sete | dense | mild | raft | mps | 100 | 5.0 % | 0.1087 | 54.3 % | 99.9 % | 0.0 % | 137.3 | n/a |
| sete | dense | mild | raft_ft_same_date | mps | 100 | 5.0 % | 0.0756 | 75.9 % | 100.0 % | 0.0 % | 138.4 | n/a |
| sete | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0874 | 67.8 % | 100.0 % | 0.0 % | 138.7 | n/a |
| sete | dense | hard | raft | mps | 100 | 30.0 % | 0.3390 | 13.4 % | 85.3 % | 18.0 % | 137.7 | n/a |
| sete | dense | hard | raft_ft_same_date | mps | 100 | 30.0 % | 0.2297 | 24.2 % | 92.0 % | 0.0 % | 139.1 | n/a |
| sete | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.2511 | 19.7 % | 89.5 % | 0.0 % | 139.1 | n/a |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 1 calls per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Details in `context.json`.

Light sets, the first pairs of every cell, next to the full set:

| pairs per cell | degradation | method | failures | full | EPE (px) | full | spread | gap (px) | full | spread |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | clean | raft | 0.0 % | 0.0 % | 0.0639 | 0.0631 | 0.0031 | n/a | n/a | n/a |
| 5 | clean | raft_ft_same_date | 0.0 % | 0.0 % | 0.0371 | 0.0368 | 0.0019 | -0.0268 | -0.0263 | 0.0028 |
| 5 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0440 | 0.0457 | 0.0025 | -0.0199 | -0.0174 | 0.0028 |
| 5 | mild | raft | 0.0 % | 0.0 % | 0.0762 | 0.0813 | 0.0121 | n/a | n/a | n/a |
| 5 | mild | raft_ft_same_date | 0.0 % | 0.0 % | 0.0461 | 0.0434 | 0.0025 | -0.0302 | -0.0379 | 0.0114 |
| 5 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0523 | 0.0532 | 0.0028 | -0.0239 | -0.0280 | 0.0115 |
| 5 | hard | raft | 18.3 % | 5.8 % | 0.2558 | 0.2420 | 0.0285 | n/a | n/a | n/a |
| 5 | hard | raft_ft_same_date | 0.0 % | 0.0 % | 0.1468 | 0.1342 | 0.0143 | -0.1343 | -0.1150 | 0.0231 |
| 5 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1736 | 0.1540 | 0.0151 | -0.1001 | -0.0965 | 0.0236 |
| 5 | all | raft | 6.1 % | 1.9 % | 0.1239 | 0.1265 | 0.0107 | n/a | n/a | n/a |
| 5 | all | raft_ft_same_date | 0.0 % | 0.0 % | 0.0766 | 0.0714 | 0.0051 | -0.0592 | -0.0587 | 0.0085 |
| 5 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0900 | 0.0843 | 0.0056 | -0.0446 | -0.0464 | 0.0085 |
| 10 | clean | raft | 0.0 % | 0.0 % | 0.0619 | 0.0631 | 0.0021 | n/a | n/a | n/a |
| 10 | clean | raft_ft_same_date | 0.0 % | 0.0 % | 0.0354 | 0.0368 | 0.0013 | -0.0265 | -0.0263 | 0.0019 |
| 10 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0422 | 0.0457 | 0.0017 | -0.0196 | -0.0174 | 0.0019 |
| 10 | mild | raft | 0.0 % | 0.0 % | 0.0728 | 0.0813 | 0.0079 | n/a | n/a | n/a |
| 10 | mild | raft_ft_same_date | 0.0 % | 0.0 % | 0.0418 | 0.0434 | 0.0017 | -0.0310 | -0.0379 | 0.0075 |
| 10 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0492 | 0.0532 | 0.0020 | -0.0236 | -0.0280 | 0.0076 |
| 10 | hard | raft | 11.7 % | 5.8 % | 0.2532 | 0.2420 | 0.0190 | n/a | n/a | n/a |
| 10 | hard | raft_ft_same_date | 0.0 % | 0.0 % | 0.1420 | 0.1342 | 0.0094 | -0.1255 | -0.1150 | 0.0155 |
| 10 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1647 | 0.1540 | 0.0101 | -0.0998 | -0.0965 | 0.0158 |
| 10 | all | raft | 3.9 % | 1.9 % | 0.1243 | 0.1265 | 0.0071 | n/a | n/a | n/a |
| 10 | all | raft_ft_same_date | 0.0 % | 0.0 % | 0.0731 | 0.0714 | 0.0033 | -0.0584 | -0.0587 | 0.0057 |
| 10 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0854 | 0.0843 | 0.0037 | -0.0456 | -0.0464 | 0.0058 |
| 20 | clean | raft | 0.0 % | 0.0 % | 0.0623 | 0.0631 | 0.0014 | n/a | n/a | n/a |
| 20 | clean | raft_ft_same_date | 0.0 % | 0.0 % | 0.0363 | 0.0368 | 0.0009 | -0.0260 | -0.0263 | 0.0013 |
| 20 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0428 | 0.0457 | 0.0012 | -0.0195 | -0.0174 | 0.0013 |
| 20 | mild | raft | 0.0 % | 0.0 % | 0.0781 | 0.0813 | 0.0054 | n/a | n/a | n/a |
| 20 | mild | raft_ft_same_date | 0.0 % | 0.0 % | 0.0427 | 0.0434 | 0.0012 | -0.0354 | -0.0379 | 0.0051 |
| 20 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0503 | 0.0532 | 0.0013 | -0.0278 | -0.0280 | 0.0052 |
| 20 | hard | raft | 7.9 % | 5.8 % | 0.2442 | 0.2420 | 0.0132 | n/a | n/a | n/a |
| 20 | hard | raft_ft_same_date | 0.0 % | 0.0 % | 0.1359 | 0.1342 | 0.0063 | -0.1172 | -0.1150 | 0.0107 |
| 20 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1569 | 0.1540 | 0.0070 | -0.0963 | -0.0965 | 0.0109 |
| 20 | all | raft | 2.6 % | 1.9 % | 0.1251 | 0.1265 | 0.0050 | n/a | n/a | n/a |
| 20 | all | raft_ft_same_date | 0.0 % | 0.0 % | 0.0716 | 0.0714 | 0.0023 | -0.0580 | -0.0587 | 0.0039 |
| 20 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0833 | 0.0843 | 0.0026 | -0.0466 | -0.0464 | 0.0040 |
| 50 | clean | raft | 0.0 % | 0.0 % | 0.0636 | 0.0631 | 0.0007 | n/a | n/a | n/a |
| 50 | clean | raft_ft_same_date | 0.0 % | 0.0 % | 0.0373 | 0.0368 | 0.0004 | -0.0263 | -0.0263 | 0.0006 |
| 50 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0455 | 0.0457 | 0.0006 | -0.0182 | -0.0174 | 0.0006 |
| 50 | mild | raft | 0.0 % | 0.0 % | 0.0810 | 0.0813 | 0.0026 | n/a | n/a | n/a |
| 50 | mild | raft_ft_same_date | 0.0 % | 0.0 % | 0.0441 | 0.0434 | 0.0006 | -0.0369 | -0.0379 | 0.0024 |
| 50 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0530 | 0.0532 | 0.0007 | -0.0280 | -0.0280 | 0.0025 |
| 50 | hard | raft | 6.7 % | 5.8 % | 0.2397 | 0.2420 | 0.0064 | n/a | n/a | n/a |
| 50 | hard | raft_ft_same_date | 0.0 % | 0.0 % | 0.1335 | 0.1342 | 0.0032 | -0.1150 | -0.1150 | 0.0053 |
| 50 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1513 | 0.1540 | 0.0034 | -0.0962 | -0.0965 | 0.0053 |
| 50 | all | raft | 2.2 % | 1.9 % | 0.1256 | 0.1265 | 0.0024 | n/a | n/a | n/a |
| 50 | all | raft_ft_same_date | 0.0 % | 0.0 % | 0.0717 | 0.0714 | 0.0012 | -0.0581 | -0.0587 | 0.0019 |
| 50 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0833 | 0.0843 | 0.0013 | -0.0464 | -0.0464 | 0.0019 |

Over every chip and scenario. EPE is the mean error over non-failed pairs; gap is the mean difference of error with raft over the pairs neither fails. Spread is the standard deviation of the figure over 1000 random sets of as many pair indices: how far a light set of that size strays from the full one.
