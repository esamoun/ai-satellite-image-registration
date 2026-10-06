Validation set: 100 pairs per chip, scenario and preset, seed 0, cut from the validation chips santerre, lyon, morvan, sete.

Over every chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all chips | translation | clean | raft_small | mps | 400 | 0.0 % | 0.1289 | 40.7 % | 99.8 % | 0.0 % | 58.0 | n/a |
| all chips | translation | clean | raft_small_ft_cross_date | mps | 400 | 0.0 % | 0.0634 | 84.5 % | 100.0 % | 0.0 % | 57.0 | n/a |
| all chips | translation | clean | raft | mps | 400 | 0.0 % | 0.0447 | 96.1 % | 100.0 % | 0.0 % | 144.7 | n/a |
| all chips | translation | clean | raft_ft_cross_date | mps | 400 | 0.0 % | 0.0303 | 99.7 % | 100.0 % | 0.0 % | 147.7 | n/a |
| all chips | translation | mild | raft_small | mps | 400 | 5.0 % | 0.1656 | 35.9 % | 99.3 % | 0.5 % | 58.2 | n/a |
| all chips | translation | mild | raft_small_ft_cross_date | mps | 400 | 5.0 % | 0.0709 | 78.9 % | 100.0 % | 0.0 % | 57.0 | n/a |
| all chips | translation | mild | raft | mps | 400 | 5.0 % | 0.0613 | 92.8 % | 99.9 % | 0.0 % | 144.9 | n/a |
| all chips | translation | mild | raft_ft_cross_date | mps | 400 | 5.0 % | 0.0350 | 99.0 % | 100.0 % | 0.0 % | 147.0 | n/a |
| all chips | translation | hard | raft_small | mps | 400 | 30.0 % | 0.4720 | 5.5 % | 66.8 % | 27.3 % | 58.3 | n/a |
| all chips | translation | hard | raft_small_ft_cross_date | mps | 400 | 30.0 % | 0.1725 | 29.8 % | 97.8 % | 0.2 % | 57.3 | n/a |
| all chips | translation | hard | raft | mps | 400 | 30.0 % | 0.2118 | 28.9 % | 95.4 % | 6.0 % | 145.4 | n/a |
| all chips | translation | hard | raft_ft_cross_date | mps | 400 | 30.0 % | 0.1139 | 51.5 % | 99.7 % | 0.0 % | 147.7 | n/a |
| all chips | affine | clean | raft_small | mps | 400 | 0.0 % | 0.1304 | 40.1 % | 99.8 % | 0.0 % | 56.2 | n/a |
| all chips | affine | clean | raft_small_ft_cross_date | mps | 400 | 0.0 % | 0.0760 | 74.7 % | 100.0 % | 0.0 % | 56.3 | n/a |
| all chips | affine | clean | raft | mps | 400 | 0.0 % | 0.0522 | 92.1 % | 100.0 % | 0.0 % | 144.4 | n/a |
| all chips | affine | clean | raft_ft_cross_date | mps | 400 | 0.0 % | 0.0364 | 98.6 % | 100.0 % | 0.0 % | 148.3 | n/a |
| all chips | affine | mild | raft_small | mps | 400 | 5.0 % | 0.1701 | 35.2 % | 99.3 % | 0.2 % | 58.2 | n/a |
| all chips | affine | mild | raft_small_ft_cross_date | mps | 400 | 5.0 % | 0.0857 | 67.6 % | 100.0 % | 0.0 % | 57.3 | n/a |
| all chips | affine | mild | raft | mps | 400 | 5.0 % | 0.0702 | 86.3 % | 99.9 % | 0.0 % | 145.3 | n/a |
| all chips | affine | mild | raft_ft_cross_date | mps | 400 | 5.0 % | 0.0429 | 96.3 % | 100.0 % | 0.0 % | 147.8 | n/a |
| all chips | affine | hard | raft_small | mps | 400 | 30.0 % | 0.4777 | 5.2 % | 65.4 % | 27.8 % | 57.9 | n/a |
| all chips | affine | hard | raft_small_ft_cross_date | mps | 400 | 30.0 % | 0.2242 | 19.0 % | 94.7 % | 0.2 % | 57.4 | n/a |
| all chips | affine | hard | raft | mps | 400 | 30.0 % | 0.2389 | 22.6 % | 93.6 % | 5.8 % | 145.3 | n/a |
| all chips | affine | hard | raft_ft_cross_date | mps | 400 | 30.0 % | 0.1469 | 38.3 % | 98.5 % | 0.0 % | 148.1 | n/a |
| all chips | dense | clean | raft_small | mps | 400 | 0.0 % | 0.1631 | 29.4 % | 99.3 % | 0.0 % | 65.0 | n/a |
| all chips | dense | clean | raft_small_ft_cross_date | mps | 400 | 0.0 % | 0.1320 | 43.4 % | 99.7 % | 0.0 % | 54.5 | n/a |
| all chips | dense | clean | raft | mps | 400 | 0.0 % | 0.0923 | 63.5 % | 100.0 % | 0.0 % | 142.2 | n/a |
| all chips | dense | clean | raft_ft_cross_date | mps | 400 | 0.0 % | 0.0703 | 79.0 % | 100.0 % | 0.0 % | 146.6 | n/a |
| all chips | dense | mild | raft_small | mps | 400 | 5.0 % | 0.1919 | 26.0 % | 98.5 % | 0.5 % | 58.0 | n/a |
| all chips | dense | mild | raft_small_ft_cross_date | mps | 400 | 5.0 % | 0.1435 | 38.9 % | 99.5 % | 0.0 % | 56.5 | n/a |
| all chips | dense | mild | raft | mps | 400 | 5.0 % | 0.1124 | 55.8 % | 99.9 % | 0.0 % | 144.2 | n/a |
| all chips | dense | mild | raft_ft_cross_date | mps | 400 | 5.0 % | 0.0818 | 71.4 % | 100.0 % | 0.0 % | 146.8 | n/a |
| all chips | dense | hard | raft_small | mps | 400 | 30.0 % | 0.4967 | 4.8 % | 63.9 % | 25.8 % | 57.7 | n/a |
| all chips | dense | hard | raft_small_ft_cross_date | mps | 400 | 30.0 % | 0.2708 | 13.9 % | 89.5 % | 0.2 % | 56.4 | n/a |
| all chips | dense | hard | raft | mps | 400 | 30.0 % | 0.2751 | 15.6 % | 90.2 % | 5.8 % | 144.4 | n/a |
| all chips | dense | hard | raft_ft_cross_date | mps | 400 | 30.0 % | 0.2013 | 24.7 % | 95.7 % | 0.0 % | 147.1 | n/a |

By chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1135 | 50.6 % | 99.8 % | 0.0 % | 54.7 | n/a |
| santerre | translation | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0589 | 88.3 % | 100.0 % | 0.0 % | 52.8 | n/a |
| santerre | translation | clean | raft | mps | 100 | 0.0 % | 0.0367 | 97.7 % | 100.0 % | 0.0 % | 136.8 | n/a |
| santerre | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0284 | 99.8 % | 100.0 % | 0.0 % | 139.3 | n/a |
| santerre | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1794 | 40.9 % | 99.0 % | 1.0 % | 55.0 | n/a |
| santerre | translation | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0708 | 78.9 % | 100.0 % | 0.0 % | 53.1 | n/a |
| santerre | translation | mild | raft | mps | 100 | 5.0 % | 0.0698 | 94.0 % | 99.9 % | 0.0 % | 136.9 | n/a |
| santerre | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0351 | 99.5 % | 100.0 % | 0.0 % | 139.1 | n/a |
| santerre | translation | hard | raft_small | mps | 100 | 30.0 % | 0.5000 | 5.3 % | 65.4 % | 21.0 % | 54.8 | n/a |
| santerre | translation | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.1657 | 28.0 % | 99.9 % | 0.0 % | 53.2 | n/a |
| santerre | translation | hard | raft | mps | 100 | 30.0 % | 0.2422 | 20.3 % | 95.3 % | 3.0 % | 137.2 | n/a |
| santerre | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1115 | 50.0 % | 100.0 % | 0.0 % | 139.8 | n/a |
| santerre | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1148 | 49.8 % | 99.8 % | 0.0 % | 53.0 | n/a |
| santerre | affine | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0721 | 77.5 % | 100.0 % | 0.0 % | 52.2 | n/a |
| santerre | affine | clean | raft | mps | 100 | 0.0 % | 0.0467 | 94.4 % | 100.0 % | 0.0 % | 136.6 | n/a |
| santerre | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0358 | 98.7 % | 100.0 % | 0.0 % | 138.9 | n/a |
| santerre | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1856 | 39.6 % | 99.0 % | 0.0 % | 55.1 | n/a |
| santerre | affine | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0853 | 66.8 % | 100.0 % | 0.0 % | 53.5 | n/a |
| santerre | affine | mild | raft | mps | 100 | 5.0 % | 0.0796 | 86.8 % | 99.8 % | 0.0 % | 137.3 | n/a |
| santerre | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0441 | 96.7 % | 100.0 % | 0.0 % | 139.4 | n/a |
| santerre | affine | hard | raft_small | mps | 100 | 30.0 % | 0.5012 | 4.8 % | 63.5 % | 22.0 % | 55.0 | n/a |
| santerre | affine | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2198 | 16.6 % | 97.2 % | 0.0 % | 53.2 | n/a |
| santerre | affine | hard | raft | mps | 100 | 30.0 % | 0.2656 | 16.0 % | 93.4 % | 3.0 % | 137.2 | n/a |
| santerre | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1460 | 34.3 % | 99.9 % | 0.0 % | 139.6 | n/a |
| santerre | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1460 | 36.0 % | 99.5 % | 0.0 % | 64.5 | n/a |
| santerre | dense | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.1288 | 45.7 % | 99.8 % | 0.0 % | 54.2 | n/a |
| santerre | dense | clean | raft | mps | 100 | 0.0 % | 0.0864 | 67.8 % | 100.0 % | 0.0 % | 136.2 | n/a |
| santerre | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0707 | 79.0 % | 100.0 % | 0.0 % | 138.8 | n/a |
| santerre | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1921 | 29.2 % | 98.4 % | 1.0 % | 55.0 | n/a |
| santerre | dense | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.1441 | 38.7 % | 99.5 % | 0.0 % | 52.7 | n/a |
| santerre | dense | mild | raft | mps | 100 | 5.0 % | 0.1176 | 56.8 % | 99.8 % | 0.0 % | 136.7 | n/a |
| santerre | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0847 | 69.6 % | 100.0 % | 0.0 % | 138.9 | n/a |
| santerre | dense | hard | raft_small | mps | 100 | 30.0 % | 0.5237 | 4.8 % | 61.6 % | 19.0 % | 54.5 | n/a |
| santerre | dense | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2643 | 11.5 % | 91.6 % | 0.0 % | 52.9 | n/a |
| santerre | dense | hard | raft | mps | 100 | 30.0 % | 0.2936 | 11.2 % | 89.3 % | 3.0 % | 137.3 | n/a |
| santerre | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1976 | 22.5 % | 97.6 % | 0.0 % | 138.9 | n/a |
| lyon | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1544 | 27.0 % | 99.8 % | 0.0 % | 56.6 | n/a |
| lyon | translation | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0687 | 79.7 % | 100.0 % | 0.0 % | 55.4 | n/a |
| lyon | translation | clean | raft | mps | 100 | 0.0 % | 0.0513 | 93.6 % | 100.0 % | 0.0 % | 140.4 | n/a |
| lyon | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0302 | 99.7 % | 100.0 % | 0.0 % | 141.4 | n/a |
| lyon | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1597 | 27.2 % | 99.7 % | 1.0 % | 56.4 | n/a |
| lyon | translation | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0730 | 76.7 % | 100.0 % | 0.0 % | 55.1 | n/a |
| lyon | translation | mild | raft | mps | 100 | 5.0 % | 0.0545 | 91.6 % | 100.0 % | 0.0 % | 139.1 | n/a |
| lyon | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0335 | 99.3 % | 100.0 % | 0.0 % | 141.4 | n/a |
| lyon | translation | hard | raft_small | mps | 100 | 30.0 % | 0.3887 | 7.2 % | 75.8 % | 1.0 % | 56.5 | n/a |
| lyon | translation | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.1357 | 38.2 % | 99.8 % | 0.0 % | 55.3 | n/a |
| lyon | translation | hard | raft | mps | 100 | 30.0 % | 0.1319 | 43.2 % | 99.8 % | 0.0 % | 139.9 | n/a |
| lyon | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.0918 | 63.0 % | 100.0 % | 0.0 % | 141.7 | n/a |
| lyon | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1546 | 27.9 % | 99.8 % | 0.0 % | 54.8 | n/a |
| lyon | affine | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0791 | 72.3 % | 100.0 % | 0.0 % | 54.4 | n/a |
| lyon | affine | clean | raft | mps | 100 | 0.0 % | 0.0574 | 88.4 % | 100.0 % | 0.0 % | 139.7 | n/a |
| lyon | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0357 | 98.8 % | 100.0 % | 0.0 % | 141.9 | n/a |
| lyon | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1597 | 27.7 % | 99.7 % | 1.0 % | 56.6 | n/a |
| lyon | affine | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0841 | 69.0 % | 100.0 % | 0.0 % | 54.3 | n/a |
| lyon | affine | mild | raft | mps | 100 | 5.0 % | 0.0622 | 85.9 % | 100.0 % | 0.0 % | 139.1 | n/a |
| lyon | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0405 | 97.3 % | 100.0 % | 0.0 % | 141.5 | n/a |
| lyon | affine | hard | raft_small | mps | 100 | 30.0 % | 0.3949 | 7.1 % | 75.2 % | 1.0 % | 56.1 | n/a |
| lyon | affine | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.1772 | 24.8 % | 99.1 % | 0.0 % | 54.9 | n/a |
| lyon | affine | hard | raft | mps | 100 | 30.0 % | 0.1586 | 33.3 % | 99.3 % | 0.0 % | 139.3 | n/a |
| lyon | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1125 | 49.8 % | 100.0 % | 0.0 % | 142.9 | n/a |
| lyon | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1875 | 22.1 % | 98.8 % | 0.0 % | 65.4 | n/a |
| lyon | dense | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.1329 | 42.1 % | 99.7 % | 0.0 % | 54.1 | n/a |
| lyon | dense | clean | raft | mps | 100 | 0.0 % | 0.1005 | 58.3 % | 100.0 % | 0.0 % | 138.6 | n/a |
| lyon | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0671 | 81.1 % | 100.0 % | 0.0 % | 141.4 | n/a |
| lyon | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1958 | 20.6 % | 98.6 % | 1.0 % | 57.0 | n/a |
| lyon | dense | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.1409 | 38.6 % | 99.6 % | 0.0 % | 55.0 | n/a |
| lyon | dense | mild | raft | mps | 100 | 5.0 % | 0.1103 | 54.1 % | 100.0 % | 0.0 % | 140.9 | n/a |
| lyon | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0756 | 75.3 % | 100.0 % | 0.0 % | 141.4 | n/a |
| lyon | dense | hard | raft_small | mps | 100 | 30.0 % | 0.4144 | 6.2 % | 73.0 % | 1.0 % | 55.5 | n/a |
| lyon | dense | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2261 | 17.7 % | 95.3 % | 0.0 % | 55.1 | n/a |
| lyon | dense | hard | raft | mps | 100 | 30.0 % | 0.2045 | 22.3 % | 96.7 % | 0.0 % | 139.1 | n/a |
| lyon | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1633 | 31.2 % | 98.8 % | 0.0 % | 142.1 | n/a |
| morvan | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1240 | 43.2 % | 99.8 % | 0.0 % | 59.2 | n/a |
| morvan | translation | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0592 | 87.0 % | 100.0 % | 0.0 % | 57.8 | n/a |
| morvan | translation | clean | raft | mps | 100 | 0.0 % | 0.0443 | 96.9 % | 100.0 % | 0.0 % | 146.5 | n/a |
| morvan | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0287 | 99.9 % | 100.0 % | 0.0 % | 149.4 | n/a |
| morvan | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1735 | 38.0 % | 99.0 % | 0.0 % | 59.5 | n/a |
| morvan | translation | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0677 | 81.1 % | 100.0 % | 0.0 % | 57.7 | n/a |
| morvan | translation | mild | raft | mps | 100 | 5.0 % | 0.0677 | 93.9 % | 99.9 % | 0.0 % | 145.9 | n/a |
| morvan | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0329 | 99.6 % | 100.0 % | 0.0 % | 148.6 | n/a |
| morvan | translation | hard | raft_small | mps | 100 | 30.0 % | 0.5668 | 3.1 % | 55.4 % | 40.0 % | 59.1 | n/a |
| morvan | translation | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.1680 | 26.6 % | 99.6 % | 0.0 % | 58.3 | n/a |
| morvan | translation | hard | raft | mps | 100 | 30.0 % | 0.2131 | 24.8 % | 95.8 % | 2.0 % | 146.5 | n/a |
| morvan | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1108 | 50.0 % | 99.9 % | 0.0 % | 149.4 | n/a |
| morvan | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1267 | 41.9 % | 99.8 % | 0.0 % | 57.4 | n/a |
| morvan | affine | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0719 | 77.9 % | 100.0 % | 0.0 % | 56.8 | n/a |
| morvan | affine | clean | raft | mps | 100 | 0.0 % | 0.0511 | 94.2 % | 100.0 % | 0.0 % | 145.5 | n/a |
| morvan | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0350 | 98.9 % | 100.0 % | 0.0 % | 149.1 | n/a |
| morvan | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1779 | 37.2 % | 99.0 % | 0.0 % | 59.6 | n/a |
| morvan | affine | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0826 | 69.5 % | 100.0 % | 0.0 % | 58.4 | n/a |
| morvan | affine | mild | raft | mps | 100 | 5.0 % | 0.0766 | 88.2 % | 99.8 % | 0.0 % | 147.1 | n/a |
| morvan | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0401 | 97.8 % | 100.0 % | 0.0 % | 148.9 | n/a |
| morvan | affine | hard | raft_small | mps | 100 | 30.0 % | 0.5937 | 2.7 % | 52.0 % | 40.0 % | 58.8 | n/a |
| morvan | affine | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2242 | 18.8 % | 95.0 % | 0.0 % | 58.2 | n/a |
| morvan | affine | hard | raft | mps | 100 | 30.0 % | 0.2410 | 20.2 % | 93.4 % | 2.0 % | 146.3 | n/a |
| morvan | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1403 | 36.9 % | 99.4 % | 0.0 % | 149.4 | n/a |
| morvan | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1579 | 30.5 % | 99.5 % | 0.0 % | 65.0 | n/a |
| morvan | dense | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.1293 | 44.3 % | 99.8 % | 0.0 % | 54.1 | n/a |
| morvan | dense | clean | raft | mps | 100 | 0.0 % | 0.0895 | 65.4 % | 100.0 % | 0.0 % | 143.2 | n/a |
| morvan | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0696 | 79.6 % | 100.0 % | 0.0 % | 147.3 | n/a |
| morvan | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1974 | 27.4 % | 98.6 % | 0.0 % | 58.7 | n/a |
| morvan | dense | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.1407 | 40.5 % | 99.6 % | 0.0 % | 57.1 | n/a |
| morvan | dense | mild | raft | mps | 100 | 5.0 % | 0.1129 | 58.0 % | 99.9 % | 0.0 % | 145.4 | n/a |
| morvan | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0795 | 72.9 % | 100.0 % | 0.0 % | 147.3 | n/a |
| morvan | dense | hard | raft_small | mps | 100 | 30.0 % | 0.6085 | 2.8 % | 51.5 % | 34.0 % | 58.4 | n/a |
| morvan | dense | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2724 | 12.9 % | 89.8 % | 0.0 % | 57.1 | n/a |
| morvan | dense | hard | raft | mps | 100 | 30.0 % | 0.2755 | 14.9 % | 88.4 % | 2.0 % | 145.6 | n/a |
| morvan | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1932 | 25.4 % | 96.8 % | 0.0 % | 148.8 | n/a |
| sete | translation | clean | raft_small | mps | 100 | 0.0 % | 0.1237 | 41.8 % | 99.9 % | 0.0 % | 64.4 | n/a |
| sete | translation | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0670 | 83.1 % | 100.0 % | 0.0 % | 63.4 | n/a |
| sete | translation | clean | raft | mps | 100 | 0.0 % | 0.0467 | 96.1 % | 100.0 % | 0.0 % | 161.8 | n/a |
| sete | translation | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0340 | 99.4 % | 100.0 % | 0.0 % | 166.4 | n/a |
| sete | translation | mild | raft_small | mps | 100 | 5.0 % | 0.1499 | 37.6 % | 99.6 % | 0.0 % | 65.5 | n/a |
| sete | translation | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0722 | 79.1 % | 100.0 % | 0.0 % | 64.3 | n/a |
| sete | translation | mild | raft | mps | 100 | 5.0 % | 0.0532 | 91.7 % | 100.0 % | 0.0 % | 164.0 | n/a |
| sete | translation | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0385 | 97.5 % | 100.0 % | 0.0 % | 167.8 | n/a |
| sete | translation | hard | raft_small | mps | 100 | 30.0 % | 0.4787 | 5.4 % | 65.0 % | 47.0 % | 66.5 | n/a |
| sete | translation | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2211 | 26.3 % | 91.8 % | 1.0 % | 65.3 | n/a |
| sete | translation | hard | raft | mps | 100 | 30.0 % | 0.2723 | 26.3 % | 89.8 % | 19.0 % | 165.4 | n/a |
| sete | translation | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1417 | 43.0 % | 98.9 % | 0.0 % | 170.0 | n/a |
| sete | affine | clean | raft_small | mps | 100 | 0.0 % | 0.1256 | 41.0 % | 99.9 % | 0.0 % | 64.2 | n/a |
| sete | affine | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.0808 | 71.3 % | 100.0 % | 0.0 % | 64.5 | n/a |
| sete | affine | clean | raft | mps | 100 | 0.0 % | 0.0537 | 91.4 % | 100.0 % | 0.0 % | 166.0 | n/a |
| sete | affine | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0392 | 97.8 % | 100.0 % | 0.0 % | 169.6 | n/a |
| sete | affine | mild | raft_small | mps | 100 | 5.0 % | 0.1572 | 36.3 % | 99.5 % | 0.0 % | 66.4 | n/a |
| sete | affine | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.0906 | 65.1 % | 100.0 % | 0.0 % | 65.1 | n/a |
| sete | affine | mild | raft | mps | 100 | 5.0 % | 0.0624 | 84.4 % | 100.0 % | 0.0 % | 166.3 | n/a |
| sete | affine | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0469 | 93.2 % | 100.0 % | 0.0 % | 168.7 | n/a |
| sete | affine | hard | raft_small | mps | 100 | 30.0 % | 0.4660 | 4.9 % | 65.2 % | 48.0 % | 66.3 | n/a |
| sete | affine | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.2760 | 15.8 % | 87.3 % | 1.0 % | 65.1 | n/a |
| sete | affine | hard | raft | mps | 100 | 30.0 % | 0.3028 | 20.4 % | 87.4 % | 18.0 % | 165.1 | n/a |
| sete | affine | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.1886 | 32.1 % | 94.8 % | 0.0 % | 168.7 | n/a |
| sete | dense | clean | raft_small | mps | 100 | 0.0 % | 0.1609 | 29.1 % | 99.4 % | 0.0 % | 65.2 | n/a |
| sete | dense | clean | raft_small_ft_cross_date | mps | 100 | 0.0 % | 0.1369 | 41.5 % | 99.7 % | 0.0 % | 55.9 | n/a |
| sete | dense | clean | raft | mps | 100 | 0.0 % | 0.0929 | 62.4 % | 100.0 % | 0.0 % | 148.9 | n/a |
| sete | dense | clean | raft_ft_cross_date | mps | 100 | 0.0 % | 0.0740 | 76.3 % | 100.0 % | 0.0 % | 155.8 | n/a |
| sete | dense | mild | raft_small | mps | 100 | 5.0 % | 0.1823 | 26.9 % | 98.6 % | 0.0 % | 62.1 | n/a |
| sete | dense | mild | raft_small_ft_cross_date | mps | 100 | 5.0 % | 0.1483 | 37.9 % | 99.3 % | 0.0 % | 60.3 | n/a |
| sete | dense | mild | raft | mps | 100 | 5.0 % | 0.1087 | 54.3 % | 99.9 % | 0.0 % | 153.9 | n/a |
| sete | dense | mild | raft_ft_cross_date | mps | 100 | 5.0 % | 0.0874 | 67.8 % | 100.0 % | 0.0 % | 158.3 | n/a |
| sete | dense | hard | raft_small | mps | 100 | 30.0 % | 0.4689 | 4.4 % | 65.6 % | 49.0 % | 62.8 | n/a |
| sete | dense | hard | raft_small_ft_cross_date | mps | 100 | 30.0 % | 0.3210 | 13.5 % | 81.1 % | 1.0 % | 61.3 | n/a |
| sete | dense | hard | raft | mps | 100 | 30.0 % | 0.3390 | 13.4 % | 85.3 % | 18.0 % | 157.0 | n/a |
| sete | dense | hard | raft_ft_cross_date | mps | 100 | 30.0 % | 0.2511 | 19.7 % | 89.5 % | 0.0 % | 162.8 | n/a |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 1 calls per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Details in `context.json`.

Light sets, the first pairs of every cell, next to the full set:

| pairs per cell | degradation | method | failures | full | EPE (px) | full | spread | gap (px) | full | spread |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | clean | raft_small | 0.0 % | 0.0 % | 0.1470 | 0.1408 | 0.0082 | n/a | n/a | n/a |
| 5 | clean | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.0844 | 0.0905 | 0.0051 | -0.0626 | -0.0503 | 0.0080 |
| 5 | clean | raft | 0.0 % | 0.0 % | 0.0639 | 0.0631 | 0.0031 | -0.0831 | -0.0777 | 0.0080 |
| 5 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0440 | 0.0457 | 0.0025 | -0.1030 | -0.0951 | 0.0083 |
| 5 | mild | raft_small | 1.7 % | 0.4 % | 0.2004 | 0.1759 | 0.0195 | n/a | n/a | n/a |
| 5 | mild | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.1041 | 0.1000 | 0.0059 | -0.0956 | -0.0758 | 0.0197 |
| 5 | mild | raft | 0.0 % | 0.0 % | 0.0762 | 0.0813 | 0.0121 | -0.1237 | -0.0946 | 0.0198 |
| 5 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0523 | 0.0532 | 0.0028 | -0.1478 | -0.1227 | 0.0195 |
| 5 | hard | raft_small | 36.7 % | 26.9 % | 0.5179 | 0.4823 | 0.0396 | n/a | n/a | n/a |
| 5 | hard | raft_small_ft_cross_date | 0.0 % | 0.2 % | 0.2825 | 0.2225 | 0.0230 | -0.3194 | -0.2857 | 0.0391 |
| 5 | hard | raft | 18.3 % | 5.8 % | 0.2558 | 0.2420 | 0.0285 | -0.2609 | -0.2728 | 0.0369 |
| 5 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1736 | 0.1540 | 0.0151 | -0.3614 | -0.3467 | 0.0383 |
| 5 | all | raft_small | 12.8 % | 9.1 % | 0.2568 | 0.2451 | 0.0161 | n/a | n/a | n/a |
| 5 | all | raft_small_ft_cross_date | 0.0 % | 0.1 % | 0.1570 | 0.1376 | 0.0089 | -0.1371 | -0.1227 | 0.0152 |
| 5 | all | raft | 6.1 % | 1.9 % | 0.1239 | 0.1265 | 0.0107 | -0.1399 | -0.1356 | 0.0142 |
| 5 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0900 | 0.0843 | 0.0056 | -0.1824 | -0.1726 | 0.0149 |
| 10 | clean | raft_small | 0.0 % | 0.0 % | 0.1451 | 0.1408 | 0.0055 | n/a | n/a | n/a |
| 10 | clean | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.0833 | 0.0905 | 0.0034 | -0.0618 | -0.0503 | 0.0054 |
| 10 | clean | raft | 0.0 % | 0.0 % | 0.0619 | 0.0631 | 0.0021 | -0.0833 | -0.0777 | 0.0053 |
| 10 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0422 | 0.0457 | 0.0017 | -0.1029 | -0.0951 | 0.0057 |
| 10 | mild | raft_small | 0.8 % | 0.4 % | 0.1915 | 0.1759 | 0.0137 | n/a | n/a | n/a |
| 10 | mild | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.0973 | 0.1000 | 0.0039 | -0.0939 | -0.0758 | 0.0137 |
| 10 | mild | raft | 0.0 % | 0.0 % | 0.0728 | 0.0813 | 0.0079 | -0.1185 | -0.0946 | 0.0140 |
| 10 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0492 | 0.0532 | 0.0020 | -0.1422 | -0.1227 | 0.0136 |
| 10 | hard | raft_small | 30.0 % | 26.9 % | 0.4626 | 0.4823 | 0.0283 | n/a | n/a | n/a |
| 10 | hard | raft_small_ft_cross_date | 0.0 % | 0.2 % | 0.2464 | 0.2225 | 0.0152 | -0.2757 | -0.2857 | 0.0269 |
| 10 | hard | raft | 11.7 % | 5.8 % | 0.2532 | 0.2420 | 0.0190 | -0.2366 | -0.2728 | 0.0261 |
| 10 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1647 | 0.1540 | 0.0101 | -0.3201 | -0.3467 | 0.0270 |
| 10 | all | raft_small | 10.3 % | 9.1 % | 0.2448 | 0.2451 | 0.0113 | n/a | n/a | n/a |
| 10 | all | raft_small_ft_cross_date | 0.0 % | 0.1 % | 0.1424 | 0.1376 | 0.0059 | -0.1292 | -0.1227 | 0.0105 |
| 10 | all | raft | 3.9 % | 1.9 % | 0.1243 | 0.1265 | 0.0071 | -0.1348 | -0.1356 | 0.0098 |
| 10 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0854 | 0.0843 | 0.0037 | -0.1738 | -0.1726 | 0.0104 |
| 20 | clean | raft_small | 0.0 % | 0.0 % | 0.1424 | 0.1408 | 0.0037 | n/a | n/a | n/a |
| 20 | clean | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.0892 | 0.0905 | 0.0023 | -0.0532 | -0.0503 | 0.0036 |
| 20 | clean | raft | 0.0 % | 0.0 % | 0.0623 | 0.0631 | 0.0014 | -0.0801 | -0.0777 | 0.0036 |
| 20 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0428 | 0.0457 | 0.0012 | -0.0996 | -0.0951 | 0.0038 |
| 20 | mild | raft_small | 0.4 % | 0.4 % | 0.1833 | 0.1759 | 0.0091 | n/a | n/a | n/a |
| 20 | mild | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.1001 | 0.1000 | 0.0027 | -0.0830 | -0.0758 | 0.0091 |
| 20 | mild | raft | 0.0 % | 0.0 % | 0.0781 | 0.0813 | 0.0054 | -0.1051 | -0.0946 | 0.0094 |
| 20 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0503 | 0.0532 | 0.0013 | -0.1330 | -0.1227 | 0.0091 |
| 20 | hard | raft_small | 30.8 % | 26.9 % | 0.4580 | 0.4823 | 0.0184 | n/a | n/a | n/a |
| 20 | hard | raft_small_ft_cross_date | 0.0 % | 0.2 % | 0.2372 | 0.2225 | 0.0102 | -0.2592 | -0.2857 | 0.0176 |
| 20 | hard | raft | 7.9 % | 5.8 % | 0.2442 | 0.2420 | 0.0132 | -0.2441 | -0.2728 | 0.0179 |
| 20 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1569 | 0.1540 | 0.0070 | -0.3214 | -0.3467 | 0.0175 |
| 20 | all | raft_small | 10.4 % | 9.1 % | 0.2388 | 0.2451 | 0.0077 | n/a | n/a | n/a |
| 20 | all | raft_small_ft_cross_date | 0.0 % | 0.1 % | 0.1422 | 0.1376 | 0.0040 | -0.1173 | -0.1227 | 0.0070 |
| 20 | all | raft | 2.6 % | 1.9 % | 0.1251 | 0.1265 | 0.0050 | -0.1308 | -0.1356 | 0.0066 |
| 20 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0833 | 0.0843 | 0.0026 | -0.1690 | -0.1726 | 0.0070 |
| 50 | clean | raft_small | 0.0 % | 0.0 % | 0.1417 | 0.1408 | 0.0018 | n/a | n/a | n/a |
| 50 | clean | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.0912 | 0.0905 | 0.0012 | -0.0506 | -0.0503 | 0.0018 |
| 50 | clean | raft | 0.0 % | 0.0 % | 0.0636 | 0.0631 | 0.0007 | -0.0781 | -0.0777 | 0.0018 |
| 50 | clean | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0455 | 0.0457 | 0.0006 | -0.0963 | -0.0951 | 0.0019 |
| 50 | mild | raft_small | 0.2 % | 0.4 % | 0.1799 | 0.1759 | 0.0047 | n/a | n/a | n/a |
| 50 | mild | raft_small_ft_cross_date | 0.0 % | 0.0 % | 0.1018 | 0.1000 | 0.0014 | -0.0780 | -0.0758 | 0.0048 |
| 50 | mild | raft | 0.0 % | 0.0 % | 0.0810 | 0.0813 | 0.0026 | -0.0988 | -0.0946 | 0.0046 |
| 50 | mild | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0530 | 0.0532 | 0.0007 | -0.1269 | -0.1227 | 0.0047 |
| 50 | hard | raft_small | 29.7 % | 26.9 % | 0.4736 | 0.4823 | 0.0094 | n/a | n/a | n/a |
| 50 | hard | raft_small_ft_cross_date | 0.0 % | 0.2 % | 0.2232 | 0.2225 | 0.0053 | -0.2786 | -0.2857 | 0.0089 |
| 50 | hard | raft | 6.7 % | 5.8 % | 0.2397 | 0.2420 | 0.0064 | -0.2664 | -0.2728 | 0.0088 |
| 50 | hard | raft_ft_cross_date | 0.0 % | 0.0 % | 0.1513 | 0.1540 | 0.0034 | -0.3393 | -0.3467 | 0.0090 |
| 50 | all | raft_small | 9.9 % | 9.1 % | 0.2422 | 0.2451 | 0.0039 | n/a | n/a | n/a |
| 50 | all | raft_small_ft_cross_date | 0.0 % | 0.1 % | 0.1387 | 0.1376 | 0.0020 | -0.1201 | -0.1227 | 0.0036 |
| 50 | all | raft | 2.2 % | 1.9 % | 0.1256 | 0.1265 | 0.0024 | -0.1342 | -0.1356 | 0.0034 |
| 50 | all | raft_ft_cross_date | 0.0 % | 0.0 % | 0.0833 | 0.0843 | 0.0013 | -0.1708 | -0.1726 | 0.0036 |

Over every chip and scenario. EPE is the mean error over non-failed pairs; gap is the mean difference of error with raft_small over the pairs neither fails. Spread is the standard deviation of the figure over 1000 random sets of as many pair indices: how far a light set of that size strays from the full one.
