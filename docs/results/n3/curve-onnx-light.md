Light validation set: 10 pairs per chip, scenario and preset, seed 0, cut from the validation chips santerre, lyon, morvan, sete. These are the first 10 pairs of every cell of the full set, which has 100.

Over every chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all chips | translation | clean | raft_r4_onnx | cpu | 40 | 0.0 % | 0.0577 | 89.9 % | 100.0 % | 0.0 % | 446.2 | n/a |
| all chips | translation | clean | raft_r8_onnx | cpu | 40 | 0.0 % | 0.0474 | 95.6 % | 100.0 % | 0.0 % | 675.4 | n/a |
| all chips | translation | clean | raft_onnx | cpu | 40 | 0.0 % | 0.0455 | 96.4 % | 100.0 % | 0.0 % | 906.1 | n/a |
| all chips | translation | clean | raft_ft_r4_onnx | cpu | 40 | 0.0 % | 0.0376 | 98.2 % | 100.0 % | 0.0 % | 463.5 | n/a |
| all chips | translation | clean | raft_ft_r8_onnx | cpu | 40 | 0.0 % | 0.0295 | 99.6 % | 100.0 % | 0.0 % | 716.2 | n/a |
| all chips | translation | clean | raft_ft_onnx | cpu | 40 | 0.0 % | 0.0280 | 99.7 % | 100.0 % | 0.0 % | 965.9 | n/a |
| all chips | translation | clean | raft_small_r4_onnx | cpu | 40 | 0.0 % | 0.1792 | 24.2 % | 98.8 % | 0.0 % | 144.7 | n/a |
| all chips | translation | clean | raft_small_r8_onnx | cpu | 40 | 0.0 % | 0.1427 | 34.2 % | 99.7 % | 0.0 % | 262.1 | n/a |
| all chips | translation | clean | raft_small_onnx | cpu | 40 | 0.0 % | 0.1357 | 36.2 % | 99.8 % | 0.0 % | 372.6 | n/a |
| all chips | translation | clean | raft_small_ft_r4_onnx | cpu | 40 | 0.0 % | 0.0772 | 74.0 % | 100.0 % | 0.0 % | 139.6 | n/a |
| all chips | translation | clean | raft_small_ft_r8_onnx | cpu | 40 | 0.0 % | 0.0627 | 85.3 % | 100.0 % | 0.0 % | 251.4 | n/a |
| all chips | translation | clean | raft_small_ft_onnx | cpu | 40 | 0.0 % | 0.0603 | 87.9 % | 100.0 % | 0.0 % | 358.2 | n/a |
| all chips | translation | clean | phase_correlation | cpu | 40 | 0.0 % | 0.0186 | 100.0 % | 100.0 % | 0.0 % | 5.3 | 6.5 |
| all chips | translation | clean | sift_ransac | cpu | 40 | 0.0 % | 0.0260 | 95.8 % | 98.8 % | 0.0 % | 22.5 | 1.9 |
| all chips | translation | clean | arosics | cpu | 40 | 0.0 % | 0.0222 | 97.5 % | 100.0 % | 0.0 % | 19.8 | 10.0 |
| all chips | translation | mild | raft_r4_onnx | cpu | 40 | 5.0 % | 0.0739 | 82.3 % | 99.8 % | 0.0 % | 447.0 | n/a |
| all chips | translation | mild | raft_r8_onnx | cpu | 40 | 5.0 % | 0.0567 | 92.8 % | 99.9 % | 0.0 % | 675.3 | n/a |
| all chips | translation | mild | raft_onnx | cpu | 40 | 5.0 % | 0.0531 | 94.1 % | 100.0 % | 0.0 % | 904.8 | n/a |
| all chips | translation | mild | raft_ft_r4_onnx | cpu | 40 | 5.0 % | 0.0418 | 95.5 % | 100.0 % | 0.0 % | 465.6 | n/a |
| all chips | translation | mild | raft_ft_r8_onnx | cpu | 40 | 5.0 % | 0.0336 | 97.9 % | 100.0 % | 0.0 % | 712.7 | n/a |
| all chips | translation | mild | raft_ft_onnx | cpu | 40 | 5.0 % | 0.0320 | 98.6 % | 100.0 % | 0.0 % | 963.1 | n/a |
| all chips | translation | mild | raft_small_r4_onnx | cpu | 40 | 5.0 % | 0.2599 | 19.2 % | 94.6 % | 0.0 % | 144.5 | n/a |
| all chips | translation | mild | raft_small_r8_onnx | cpu | 40 | 5.0 % | 0.2001 | 30.0 % | 98.5 % | 0.0 % | 260.6 | n/a |
| all chips | translation | mild | raft_small_onnx | cpu | 40 | 5.0 % | 0.1792 | 33.6 % | 99.0 % | 2.5 % | 375.8 | n/a |
| all chips | translation | mild | raft_small_ft_r4_onnx | cpu | 40 | 5.0 % | 0.0927 | 62.7 % | 99.9 % | 0.0 % | 142.2 | n/a |
| all chips | translation | mild | raft_small_ft_r8_onnx | cpu | 40 | 5.0 % | 0.0756 | 76.2 % | 100.0 % | 0.0 % | 251.8 | n/a |
| all chips | translation | mild | raft_small_ft_onnx | cpu | 40 | 5.0 % | 0.0716 | 78.7 % | 100.0 % | 0.0 % | 360.7 | n/a |
| all chips | translation | mild | phase_correlation | cpu | 40 | 5.0 % | 0.0237 | 100.0 % | 100.0 % | 0.0 % | 5.2 | 6.5 |
| all chips | translation | mild | sift_ransac | cpu | 40 | 5.0 % | 0.0444 | 93.3 % | 98.4 % | 0.0 % | 22.7 | 1.9 |
| all chips | translation | mild | arosics | cpu | 40 | 5.0 % | 0.0719 | 75.0 % | 100.0 % | 0.0 % | 19.6 | 10.0 |
| all chips | translation | hard | raft_r4_onnx | cpu | 40 | 30.0 % | 0.4543 | 11.7 % | 78.2 % | 27.5 % | 444.2 | n/a |
| all chips | translation | hard | raft_r8_onnx | cpu | 40 | 30.0 % | 0.2305 | 24.0 % | 94.8 % | 15.0 % | 676.0 | n/a |
| all chips | translation | hard | raft_onnx | cpu | 40 | 30.0 % | 0.2211 | 26.8 % | 96.1 % | 12.5 % | 906.0 | n/a |
| all chips | translation | hard | raft_ft_r4_onnx | cpu | 40 | 30.0 % | 0.1484 | 40.9 % | 97.8 % | 0.0 % | 466.0 | n/a |
| all chips | translation | hard | raft_ft_r8_onnx | cpu | 40 | 30.0 % | 0.1293 | 45.5 % | 100.0 % | 0.0 % | 716.4 | n/a |
| all chips | translation | hard | raft_ft_onnx | cpu | 40 | 30.0 % | 0.1266 | 45.9 % | 99.9 % | 0.0 % | 964.0 | n/a |
| all chips | translation | hard | raft_small_r4_onnx | cpu | 40 | 30.0 % | 0.8341 | 9.0 % | 65.3 % | 97.5 % | 144.2 | n/a |
| all chips | translation | hard | raft_small_r8_onnx | cpu | 40 | 30.0 % | 0.5072 | 6.2 % | 63.4 % | 47.5 % | 259.3 | n/a |
| all chips | translation | hard | raft_small_onnx | cpu | 40 | 30.0 % | 0.4485 | 4.9 % | 69.9 % | 30.0 % | 369.5 | n/a |
| all chips | translation | hard | raft_small_ft_r4_onnx | cpu | 40 | 30.0 % | 0.2959 | 13.7 % | 85.7 % | 5.0 % | 139.6 | n/a |
| all chips | translation | hard | raft_small_ft_r8_onnx | cpu | 40 | 30.0 % | 0.2131 | 27.4 % | 92.9 % | 0.0 % | 252.0 | n/a |
| all chips | translation | hard | raft_small_ft_onnx | cpu | 40 | 30.0 % | 0.2037 | 30.3 % | 94.0 % | 0.0 % | 357.3 | n/a |
| all chips | translation | hard | phase_correlation | cpu | 40 | 30.0 % | 0.2211 | 15.8 % | 92.1 % | 5.0 % | 5.2 | 6.5 |
| all chips | translation | hard | sift_ransac | cpu | 40 | 30.0 % | 0.3557 | 12.8 % | 77.9 % | 50.0 % | 19.1 | 1.9 |
| all chips | translation | hard | arosics | cpu | 40 | 30.0 % | 0.3153 | 5.6 % | 83.3 % | 55.0 % | 19.1 | 10.0 |
| all chips | affine | clean | raft_r4_onnx | cpu | 40 | 0.0 % | 0.0620 | 85.9 % | 100.0 % | 0.0 % | 445.8 | n/a |
| all chips | affine | clean | raft_r8_onnx | cpu | 40 | 0.0 % | 0.0541 | 91.3 % | 100.0 % | 0.0 % | 674.0 | n/a |
| all chips | affine | clean | raft_onnx | cpu | 40 | 0.0 % | 0.0520 | 92.0 % | 100.0 % | 0.0 % | 909.7 | n/a |
| all chips | affine | clean | raft_ft_r4_onnx | cpu | 40 | 0.0 % | 0.0445 | 95.4 % | 100.0 % | 0.0 % | 465.8 | n/a |
| all chips | affine | clean | raft_ft_r8_onnx | cpu | 40 | 0.0 % | 0.0359 | 98.6 % | 100.0 % | 0.0 % | 713.6 | n/a |
| all chips | affine | clean | raft_ft_onnx | cpu | 40 | 0.0 % | 0.0336 | 99.0 % | 100.0 % | 0.0 % | 962.7 | n/a |
| all chips | affine | clean | raft_small_r4_onnx | cpu | 40 | 0.0 % | 0.1788 | 23.9 % | 98.9 % | 0.0 % | 144.3 | n/a |
| all chips | affine | clean | raft_small_r8_onnx | cpu | 40 | 0.0 % | 0.1430 | 34.1 % | 99.7 % | 0.0 % | 260.2 | n/a |
| all chips | affine | clean | raft_small_onnx | cpu | 40 | 0.0 % | 0.1365 | 35.4 % | 99.8 % | 0.0 % | 375.4 | n/a |
| all chips | affine | clean | raft_small_ft_r4_onnx | cpu | 40 | 0.0 % | 0.0854 | 68.7 % | 100.0 % | 0.0 % | 139.9 | n/a |
| all chips | affine | clean | raft_small_ft_r8_onnx | cpu | 40 | 0.0 % | 0.0740 | 77.0 % | 100.0 % | 0.0 % | 250.3 | n/a |
| all chips | affine | clean | raft_small_ft_onnx | cpu | 40 | 0.0 % | 0.0680 | 81.1 % | 100.0 % | 0.0 % | 358.7 | n/a |
| all chips | affine | clean | phase_correlation | cpu | 40 | 0.0 % | 0.2159 | 21.4 % | 96.5 % | 0.0 % | 5.2 | 6.5 |
| all chips | affine | clean | sift_ransac | cpu | 40 | 0.0 % | 0.0349 | 95.4 % | 98.4 % | 0.0 % | 23.1 | 1.9 |
| all chips | affine | clean | arosics | cpu | 40 | 0.0 % | 0.2099 | 21.8 % | 97.9 % | 2.5 % | 19.7 | 10.0 |
| all chips | affine | mild | raft_r4_onnx | cpu | 40 | 5.0 % | 0.0801 | 78.0 % | 99.8 % | 0.0 % | 444.8 | n/a |
| all chips | affine | mild | raft_r8_onnx | cpu | 40 | 5.0 % | 0.0662 | 86.6 % | 99.9 % | 0.0 % | 675.0 | n/a |
| all chips | affine | mild | raft_onnx | cpu | 40 | 5.0 % | 0.0640 | 88.2 % | 99.9 % | 0.0 % | 904.9 | n/a |
| all chips | affine | mild | raft_ft_r4_onnx | cpu | 40 | 5.0 % | 0.0507 | 91.3 % | 100.0 % | 0.0 % | 463.5 | n/a |
| all chips | affine | mild | raft_ft_r8_onnx | cpu | 40 | 5.0 % | 0.0420 | 94.7 % | 100.0 % | 0.0 % | 713.8 | n/a |
| all chips | affine | mild | raft_ft_onnx | cpu | 40 | 5.0 % | 0.0397 | 95.9 % | 100.0 % | 0.0 % | 964.7 | n/a |
| all chips | affine | mild | raft_small_r4_onnx | cpu | 40 | 5.0 % | 0.2571 | 19.5 % | 94.6 % | 0.0 % | 144.2 | n/a |
| all chips | affine | mild | raft_small_r8_onnx | cpu | 40 | 5.0 % | 0.1935 | 30.6 % | 98.5 % | 0.0 % | 259.7 | n/a |
| all chips | affine | mild | raft_small_onnx | cpu | 40 | 5.0 % | 0.1915 | 33.6 % | 99.0 % | 0.0 % | 373.9 | n/a |
| all chips | affine | mild | raft_small_ft_r4_onnx | cpu | 40 | 5.0 % | 0.0989 | 58.6 % | 99.9 % | 0.0 % | 139.0 | n/a |
| all chips | affine | mild | raft_small_ft_r8_onnx | cpu | 40 | 5.0 % | 0.0884 | 65.7 % | 100.0 % | 0.0 % | 253.6 | n/a |
| all chips | affine | mild | raft_small_ft_onnx | cpu | 40 | 5.0 % | 0.0826 | 70.5 % | 100.0 % | 0.0 % | 358.5 | n/a |
| all chips | affine | mild | phase_correlation | cpu | 40 | 5.0 % | 0.2166 | 21.4 % | 96.6 % | 0.0 % | 5.3 | 6.5 |
| all chips | affine | mild | sift_ransac | cpu | 40 | 5.0 % | 0.0388 | 93.8 % | 99.3 % | 0.0 % | 22.5 | 1.9 |
| all chips | affine | mild | arosics | cpu | 40 | 5.0 % | 0.2226 | 18.0 % | 97.1 % | 2.5 % | 19.6 | 10.0 |
| all chips | affine | hard | raft_r4_onnx | cpu | 40 | 30.0 % | 0.4611 | 11.2 % | 77.7 % | 27.5 % | 449.8 | n/a |
| all chips | affine | hard | raft_r8_onnx | cpu | 40 | 30.0 % | 0.2499 | 20.1 % | 93.9 % | 15.0 % | 678.4 | n/a |
| all chips | affine | hard | raft_onnx | cpu | 40 | 30.0 % | 0.2433 | 20.4 % | 95.0 % | 12.5 % | 908.9 | n/a |
| all chips | affine | hard | raft_ft_r4_onnx | cpu | 40 | 30.0 % | 0.1757 | 29.5 % | 97.7 % | 0.0 % | 466.6 | n/a |
| all chips | affine | hard | raft_ft_r8_onnx | cpu | 40 | 30.0 % | 0.1699 | 29.4 % | 98.1 % | 0.0 % | 714.8 | n/a |
| all chips | affine | hard | raft_ft_onnx | cpu | 40 | 30.0 % | 0.1639 | 32.1 % | 98.3 % | 0.0 % | 961.1 | n/a |
| all chips | affine | hard | raft_small_r4_onnx | cpu | 40 | 30.0 % | 0.8002 | 8.5 % | 65.0 % | 97.5 % | 145.1 | n/a |
| all chips | affine | hard | raft_small_r8_onnx | cpu | 40 | 30.0 % | 0.5067 | 6.3 % | 62.8 % | 47.5 % | 260.4 | n/a |
| all chips | affine | hard | raft_small_onnx | cpu | 40 | 30.0 % | 0.4462 | 4.8 % | 69.9 % | 32.5 % | 374.0 | n/a |
| all chips | affine | hard | raft_small_ft_r4_onnx | cpu | 40 | 30.0 % | 0.3028 | 13.6 % | 84.9 % | 5.0 % | 140.2 | n/a |
| all chips | affine | hard | raft_small_ft_r8_onnx | cpu | 40 | 30.0 % | 0.2496 | 20.2 % | 91.0 % | 0.0 % | 253.3 | n/a |
| all chips | affine | hard | raft_small_ft_onnx | cpu | 40 | 30.0 % | 0.2484 | 19.7 % | 91.2 % | 0.0 % | 362.0 | n/a |
| all chips | affine | hard | phase_correlation | cpu | 40 | 30.0 % | 0.3434 | 6.6 % | 82.0 % | 5.0 % | 5.3 | 6.5 |
| all chips | affine | hard | sift_ransac | cpu | 40 | 30.0 % | 0.3339 | 16.0 % | 78.2 % | 52.5 % | 19.5 | 1.9 |
| all chips | affine | hard | arosics | cpu | 40 | 30.0 % | 0.3798 | 5.7 % | 73.9 % | 55.0 % | 19.1 | 10.0 |
| all chips | dense | clean | raft_r4_onnx | cpu | 40 | 0.0 % | 0.0896 | 65.4 % | 100.0 % | 0.0 % | 440.8 | n/a |
| all chips | dense | clean | raft_r8_onnx | cpu | 40 | 0.0 % | 0.0895 | 64.6 % | 100.0 % | 0.0 % | 672.2 | n/a |
| all chips | dense | clean | raft_onnx | cpu | 40 | 0.0 % | 0.0881 | 65.4 % | 100.0 % | 0.0 % | 901.6 | n/a |
| all chips | dense | clean | raft_ft_r4_onnx | cpu | 40 | 0.0 % | 0.0758 | 74.9 % | 100.0 % | 0.0 % | 461.9 | n/a |
| all chips | dense | clean | raft_ft_r8_onnx | cpu | 40 | 0.0 % | 0.0669 | 80.9 % | 100.0 % | 0.0 % | 700.4 | n/a |
| all chips | dense | clean | raft_ft_onnx | cpu | 40 | 0.0 % | 0.0650 | 82.1 % | 100.0 % | 0.0 % | 964.6 | n/a |
| all chips | dense | clean | raft_small_r4_onnx | cpu | 40 | 0.0 % | 0.1915 | 21.8 % | 98.4 % | 0.0 % | 145.2 | n/a |
| all chips | dense | clean | raft_small_r8_onnx | cpu | 40 | 0.0 % | 0.1664 | 28.6 % | 99.0 % | 0.0 % | 263.2 | n/a |
| all chips | dense | clean | raft_small_onnx | cpu | 40 | 0.0 % | 0.1632 | 29.2 % | 99.0 % | 0.0 % | 381.3 | n/a |
| all chips | dense | clean | raft_small_ft_r4_onnx | cpu | 40 | 0.0 % | 0.1271 | 45.4 % | 99.7 % | 0.0 % | 143.1 | n/a |
| all chips | dense | clean | raft_small_ft_r8_onnx | cpu | 40 | 0.0 % | 0.1251 | 48.4 % | 99.6 % | 0.0 % | 258.4 | n/a |
| all chips | dense | clean | raft_small_ft_onnx | cpu | 40 | 0.0 % | 0.1218 | 50.7 % | 99.6 % | 0.0 % | 363.2 | n/a |
| all chips | dense | clean | phase_correlation | cpu | 40 | 0.0 % | 0.2734 | 12.9 % | 90.3 % | 0.0 % | 5.4 | 6.5 |
| all chips | dense | clean | sift_ransac | cpu | 40 | 0.0 % | 0.1532 | 51.9 % | 95.6 % | 0.0 % | 23.2 | 1.9 |
| all chips | dense | clean | arosics | cpu | 40 | 0.0 % | 0.2767 | 12.8 % | 89.6 % | 2.5 % | 19.7 | 10.0 |
| all chips | dense | mild | raft_r4_onnx | cpu | 40 | 5.0 % | 0.1055 | 58.4 % | 99.8 % | 0.0 % | 447.5 | n/a |
| all chips | dense | mild | raft_r8_onnx | cpu | 40 | 5.0 % | 0.1026 | 59.1 % | 99.9 % | 0.0 % | 675.6 | n/a |
| all chips | dense | mild | raft_onnx | cpu | 40 | 5.0 % | 0.1014 | 60.0 % | 99.9 % | 0.0 % | 904.2 | n/a |
| all chips | dense | mild | raft_ft_r4_onnx | cpu | 40 | 5.0 % | 0.0867 | 69.0 % | 99.9 % | 0.0 % | 462.2 | n/a |
| all chips | dense | mild | raft_ft_r8_onnx | cpu | 40 | 5.0 % | 0.0780 | 74.5 % | 99.9 % | 0.0 % | 703.3 | n/a |
| all chips | dense | mild | raft_ft_onnx | cpu | 40 | 5.0 % | 0.0761 | 76.2 % | 100.0 % | 0.0 % | 964.5 | n/a |
| all chips | dense | mild | raft_small_r4_onnx | cpu | 40 | 5.0 % | 0.2575 | 19.1 % | 94.5 % | 0.0 % | 144.4 | n/a |
| all chips | dense | mild | raft_small_r8_onnx | cpu | 40 | 5.0 % | 0.2071 | 27.7 % | 97.6 % | 0.0 % | 262.3 | n/a |
| all chips | dense | mild | raft_small_onnx | cpu | 40 | 5.0 % | 0.2035 | 28.3 % | 97.9 % | 0.0 % | 376.6 | n/a |
| all chips | dense | mild | raft_small_ft_r4_onnx | cpu | 40 | 5.0 % | 0.1420 | 38.6 % | 99.4 % | 0.0 % | 142.6 | n/a |
| all chips | dense | mild | raft_small_ft_r8_onnx | cpu | 40 | 5.0 % | 0.1408 | 41.1 % | 99.3 % | 0.0 % | 253.8 | n/a |
| all chips | dense | mild | raft_small_ft_onnx | cpu | 40 | 5.0 % | 0.1377 | 42.6 % | 99.3 % | 0.0 % | 360.0 | n/a |
| all chips | dense | mild | phase_correlation | cpu | 40 | 5.0 % | 0.2738 | 12.7 % | 90.3 % | 0.0 % | 5.2 | 6.5 |
| all chips | dense | mild | sift_ransac | cpu | 40 | 5.0 % | 0.1439 | 52.3 % | 96.0 % | 0.0 % | 22.4 | 1.9 |
| all chips | dense | mild | arosics | cpu | 40 | 5.0 % | 0.2820 | 12.7 % | 88.9 % | 2.5 % | 19.4 | 10.0 |
| all chips | dense | hard | raft_r4_onnx | cpu | 40 | 30.0 % | 0.4551 | 10.8 % | 80.1 % | 20.0 % | 445.7 | n/a |
| all chips | dense | hard | raft_r8_onnx | cpu | 40 | 30.0 % | 0.2831 | 16.0 % | 91.7 % | 12.5 % | 677.0 | n/a |
| all chips | dense | hard | raft_onnx | cpu | 40 | 30.0 % | 0.2939 | 15.2 % | 91.7 % | 10.0 % | 906.9 | n/a |
| all chips | dense | hard | raft_ft_r4_onnx | cpu | 40 | 30.0 % | 0.2057 | 22.7 % | 96.5 % | 0.0 % | 463.3 | n/a |
| all chips | dense | hard | raft_ft_r8_onnx | cpu | 40 | 30.0 % | 0.2049 | 21.6 % | 96.2 % | 0.0 % | 713.1 | n/a |
| all chips | dense | hard | raft_ft_onnx | cpu | 40 | 30.0 % | 0.2035 | 22.8 % | 95.8 % | 0.0 % | 965.6 | n/a |
| all chips | dense | hard | raft_small_r4_onnx | cpu | 40 | 30.0 % | 0.5355 | 5.7 % | 60.8 % | 92.5 % | 144.3 | n/a |
| all chips | dense | hard | raft_small_r8_onnx | cpu | 40 | 30.0 % | 0.5055 | 6.5 % | 63.9 % | 45.0 % | 261.1 | n/a |
| all chips | dense | hard | raft_small_onnx | cpu | 40 | 30.0 % | 0.4915 | 4.9 % | 66.5 % | 27.5 % | 374.4 | n/a |
| all chips | dense | hard | raft_small_ft_r4_onnx | cpu | 40 | 30.0 % | 0.3100 | 13.7 % | 84.6 % | 5.0 % | 141.6 | n/a |
| all chips | dense | hard | raft_small_ft_r8_onnx | cpu | 40 | 30.0 % | 0.2857 | 17.1 % | 86.6 % | 0.0 % | 253.6 | n/a |
| all chips | dense | hard | raft_small_ft_onnx | cpu | 40 | 30.0 % | 0.2871 | 17.1 % | 86.1 % | 0.0 % | 359.8 | n/a |
| all chips | dense | hard | phase_correlation | cpu | 40 | 30.0 % | 0.3764 | 6.1 % | 76.1 % | 5.0 % | 5.4 | 6.5 |
| all chips | dense | hard | sift_ransac | cpu | 40 | 30.0 % | 0.3237 | 18.1 % | 79.9 % | 50.0 % | 19.4 | 1.9 |
| all chips | dense | hard | arosics | cpu | 40 | 30.0 % | 0.4035 | 4.8 % | 72.5 % | 57.5 % | 18.8 | 10.0 |

By chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | translation | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0569 | 90.3 % | 100.0 % | 0.0 % | 442.2 | n/a |
| santerre | translation | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0412 | 96.8 % | 100.0 % | 0.0 % | 663.6 | n/a |
| santerre | translation | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0381 | 97.6 % | 100.0 % | 0.0 % | 883.0 | n/a |
| santerre | translation | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0372 | 98.0 % | 100.0 % | 0.0 % | 453.4 | n/a |
| santerre | translation | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0293 | 99.4 % | 100.0 % | 0.0 % | 688.4 | n/a |
| santerre | translation | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0273 | 99.7 % | 100.0 % | 0.0 % | 942.0 | n/a |
| santerre | translation | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1698 | 26.0 % | 98.7 % | 0.0 % | 144.0 | n/a |
| santerre | translation | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1278 | 42.0 % | 99.7 % | 0.0 % | 260.6 | n/a |
| santerre | translation | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1183 | 46.6 % | 99.8 % | 0.0 % | 361.9 | n/a |
| santerre | translation | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0776 | 73.6 % | 100.0 % | 0.0 % | 135.7 | n/a |
| santerre | translation | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0571 | 90.7 % | 100.0 % | 0.0 % | 249.4 | n/a |
| santerre | translation | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0546 | 91.6 % | 100.0 % | 0.0 % | 354.5 | n/a |
| santerre | translation | clean | phase_correlation | cpu | 10 | 0.0 % | 0.0273 | 100.0 % | 100.0 % | 0.0 % | 5.2 | 6.5 |
| santerre | translation | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0141 | 100.0 % | 100.0 % | 0.0 % | 20.0 | 1.8 |
| santerre | translation | clean | arosics | cpu | 10 | 0.0 % | 0.0402 | 90.0 % | 100.0 % | 0.0 % | 19.4 | 10.0 |
| santerre | translation | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0929 | 76.1 % | 99.3 % | 0.0 % | 433.7 | n/a |
| santerre | translation | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0560 | 93.1 % | 99.8 % | 0.0 % | 657.5 | n/a |
| santerre | translation | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0464 | 94.9 % | 100.0 % | 0.0 % | 882.4 | n/a |
| santerre | translation | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0443 | 96.3 % | 100.0 % | 0.0 % | 453.7 | n/a |
| santerre | translation | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0348 | 99.4 % | 100.0 % | 0.0 % | 685.7 | n/a |
| santerre | translation | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0317 | 99.6 % | 100.0 % | 0.0 % | 925.3 | n/a |
| santerre | translation | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.3164 | 18.0 % | 92.6 % | 0.0 % | 141.8 | n/a |
| santerre | translation | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2282 | 34.0 % | 98.0 % | 0.0 % | 258.4 | n/a |
| santerre | translation | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1819 | 43.2 % | 98.9 % | 10.0 % | 363.0 | n/a |
| santerre | translation | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.1063 | 54.4 % | 99.7 % | 0.0 % | 136.7 | n/a |
| santerre | translation | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0833 | 74.7 % | 100.0 % | 0.0 % | 246.7 | n/a |
| santerre | translation | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0807 | 76.0 % | 100.0 % | 0.0 % | 351.4 | n/a |
| santerre | translation | mild | phase_correlation | cpu | 10 | 5.0 % | 0.0432 | 100.0 % | 100.0 % | 0.0 % | 5.1 | 6.5 |
| santerre | translation | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0384 | 96.0 % | 100.0 % | 0.0 % | 19.8 | 1.8 |
| santerre | translation | mild | arosics | cpu | 10 | 5.0 % | 0.1165 | 40.0 % | 100.0 % | 0.0 % | 19.2 | 10.0 |
| santerre | translation | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.5421 | 7.2 % | 71.2 % | 10.0 % | 437.0 | n/a |
| santerre | translation | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2444 | 19.9 % | 94.9 % | 0.0 % | 660.6 | n/a |
| santerre | translation | hard | raft_onnx | cpu | 10 | 30.0 % | 0.1885 | 24.5 % | 98.6 % | 0.0 % | 894.9 | n/a |
| santerre | translation | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1303 | 41.4 % | 100.0 % | 0.0 % | 454.0 | n/a |
| santerre | translation | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1138 | 48.6 % | 100.0 % | 0.0 % | 688.2 | n/a |
| santerre | translation | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1132 | 48.9 % | 100.0 % | 0.0 % | 932.5 | n/a |
| santerre | translation | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 141.8 | n/a |
| santerre | translation | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.6109 | 1.7 % | 53.3 % | 50.0 % | 250.3 | n/a |
| santerre | translation | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.5098 | 3.4 % | 67.4 % | 20.0 % | 357.8 | n/a |
| santerre | translation | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2699 | 15.2 % | 89.0 % | 0.0 % | 137.3 | n/a |
| santerre | translation | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1510 | 34.0 % | 99.9 % | 0.0 % | 247.5 | n/a |
| santerre | translation | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.1399 | 37.6 % | 100.0 % | 0.0 % | 351.4 | n/a |
| santerre | translation | hard | phase_correlation | cpu | 10 | 30.0 % | 0.3575 | 11.1 % | 77.8 % | 10.0 % | 5.2 | 6.5 |
| santerre | translation | hard | sift_ransac | cpu | 10 | 30.0 % | 0.5519 | 6.1 % | 54.4 % | 80.0 % | 18.6 | 1.8 |
| santerre | translation | hard | arosics | cpu | 10 | 30.0 % | 0.3720 | 0.0 % | 66.7 % | 70.0 % | 19.2 | 10.0 |
| santerre | affine | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0608 | 87.1 % | 100.0 % | 0.0 % | 439.3 | n/a |
| santerre | affine | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0496 | 93.4 % | 100.0 % | 0.0 % | 659.3 | n/a |
| santerre | affine | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0468 | 94.6 % | 100.0 % | 0.0 % | 883.1 | n/a |
| santerre | affine | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0418 | 97.1 % | 100.0 % | 0.0 % | 450.0 | n/a |
| santerre | affine | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0353 | 98.5 % | 100.0 % | 0.0 % | 695.1 | n/a |
| santerre | affine | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0350 | 98.7 % | 100.0 % | 0.0 % | 942.5 | n/a |
| santerre | affine | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1685 | 26.2 % | 98.7 % | 0.0 % | 143.2 | n/a |
| santerre | affine | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1280 | 42.6 % | 99.7 % | 0.0 % | 255.9 | n/a |
| santerre | affine | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1185 | 46.8 % | 99.8 % | 0.0 % | 369.1 | n/a |
| santerre | affine | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0850 | 69.7 % | 100.0 % | 0.0 % | 136.8 | n/a |
| santerre | affine | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0689 | 80.6 % | 100.0 % | 0.0 % | 247.1 | n/a |
| santerre | affine | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0634 | 84.3 % | 100.0 % | 0.0 % | 357.2 | n/a |
| santerre | affine | clean | phase_correlation | cpu | 10 | 0.0 % | 0.1911 | 24.9 % | 97.2 % | 0.0 % | 5.2 | 6.5 |
| santerre | affine | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0148 | 100.0 % | 100.0 % | 0.0 % | 20.1 | 1.8 |
| santerre | affine | clean | arosics | cpu | 10 | 0.0 % | 0.1939 | 23.9 % | 97.5 % | 0.0 % | 19.4 | 10.0 |
| santerre | affine | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.1025 | 72.9 % | 99.3 % | 0.0 % | 440.6 | n/a |
| santerre | affine | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0709 | 87.3 % | 99.8 % | 0.0 % | 663.3 | n/a |
| santerre | affine | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0667 | 89.1 % | 99.8 % | 0.0 % | 885.0 | n/a |
| santerre | affine | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0506 | 93.8 % | 100.0 % | 0.0 % | 454.0 | n/a |
| santerre | affine | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0439 | 96.1 % | 100.0 % | 0.0 % | 694.7 | n/a |
| santerre | affine | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0411 | 97.8 % | 100.0 % | 0.0 % | 941.9 | n/a |
| santerre | affine | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.3150 | 17.1 % | 92.6 % | 0.0 % | 141.2 | n/a |
| santerre | affine | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2069 | 31.7 % | 98.0 % | 0.0 % | 256.0 | n/a |
| santerre | affine | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.2414 | 37.8 % | 98.4 % | 0.0 % | 357.7 | n/a |
| santerre | affine | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.1114 | 52.1 % | 99.8 % | 0.0 % | 138.5 | n/a |
| santerre | affine | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0966 | 60.2 % | 100.0 % | 0.0 % | 247.4 | n/a |
| santerre | affine | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0915 | 65.2 % | 100.0 % | 0.0 % | 359.3 | n/a |
| santerre | affine | mild | phase_correlation | cpu | 10 | 5.0 % | 0.1943 | 24.3 % | 97.1 % | 0.0 % | 5.1 | 6.5 |
| santerre | affine | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0317 | 100.0 % | 100.0 % | 0.0 % | 20.2 | 1.8 |
| santerre | affine | mild | arosics | cpu | 10 | 5.0 % | 0.2202 | 15.3 % | 95.7 % | 0.0 % | 19.4 | 10.0 |
| santerre | affine | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.5459 | 6.9 % | 70.5 % | 10.0 % | 440.8 | n/a |
| santerre | affine | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2571 | 18.7 % | 94.9 % | 0.0 % | 663.5 | n/a |
| santerre | affine | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2132 | 18.7 % | 98.3 % | 0.0 % | 893.7 | n/a |
| santerre | affine | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1624 | 28.2 % | 99.6 % | 0.0 % | 450.2 | n/a |
| santerre | affine | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1488 | 31.4 % | 100.0 % | 0.0 % | 681.9 | n/a |
| santerre | affine | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1451 | 33.6 % | 100.0 % | 0.0 % | 948.3 | n/a |
| santerre | affine | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 143.8 | n/a |
| santerre | affine | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.6345 | 1.6 % | 52.2 % | 50.0 % | 260.5 | n/a |
| santerre | affine | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.5303 | 2.9 % | 65.6 % | 20.0 % | 372.1 | n/a |
| santerre | affine | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2853 | 13.7 % | 87.1 % | 0.0 % | 138.6 | n/a |
| santerre | affine | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1880 | 24.8 % | 98.9 % | 0.0 % | 252.9 | n/a |
| santerre | affine | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.1754 | 28.5 % | 99.8 % | 0.0 % | 358.5 | n/a |
| santerre | affine | hard | phase_correlation | cpu | 10 | 30.0 % | 0.4256 | 3.2 % | 72.6 % | 10.0 % | 5.2 | 6.5 |
| santerre | affine | hard | sift_ransac | cpu | 10 | 30.0 % | 0.6071 | 1.9 % | 37.0 % | 90.0 % | 18.3 | 1.8 |
| santerre | affine | hard | arosics | cpu | 10 | 30.0 % | 0.4122 | 2.8 % | 76.3 % | 70.0 % | 19.2 | 10.0 |
| santerre | dense | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0866 | 67.9 % | 100.0 % | 0.0 % | 435.3 | n/a |
| santerre | dense | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0874 | 66.6 % | 100.0 % | 0.0 % | 663.0 | n/a |
| santerre | dense | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0863 | 67.1 % | 100.0 % | 0.0 % | 882.0 | n/a |
| santerre | dense | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0805 | 71.5 % | 100.0 % | 0.0 % | 447.9 | n/a |
| santerre | dense | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0735 | 77.0 % | 100.0 % | 0.0 % | 678.0 | n/a |
| santerre | dense | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0711 | 78.4 % | 100.0 % | 0.0 % | 930.3 | n/a |
| santerre | dense | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1826 | 23.0 % | 98.4 % | 0.0 % | 141.9 | n/a |
| santerre | dense | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1525 | 32.6 % | 99.2 % | 0.0 % | 256.6 | n/a |
| santerre | dense | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1461 | 35.4 % | 99.3 % | 0.0 % | 369.4 | n/a |
| santerre | dense | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.1258 | 44.4 % | 100.0 % | 0.0 % | 140.8 | n/a |
| santerre | dense | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.1227 | 49.1 % | 99.9 % | 0.0 % | 247.1 | n/a |
| santerre | dense | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.1209 | 50.1 % | 99.8 % | 0.0 % | 358.3 | n/a |
| santerre | dense | clean | phase_correlation | cpu | 10 | 0.0 % | 0.2363 | 17.4 % | 92.8 % | 0.0 % | 5.1 | 6.5 |
| santerre | dense | clean | sift_ransac | cpu | 10 | 0.0 % | 0.1267 | 50.4 % | 98.7 % | 0.0 % | 20.0 | 1.8 |
| santerre | dense | clean | arosics | cpu | 10 | 0.0 % | 0.2469 | 15.3 % | 92.3 % | 0.0 % | 19.5 | 10.0 |
| santerre | dense | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.1184 | 54.1 % | 99.3 % | 0.0 % | 441.8 | n/a |
| santerre | dense | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.1055 | 58.0 % | 99.9 % | 0.0 % | 662.1 | n/a |
| santerre | dense | mild | raft_onnx | cpu | 10 | 5.0 % | 0.1039 | 58.5 % | 99.9 % | 0.0 % | 886.7 | n/a |
| santerre | dense | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0930 | 66.1 % | 100.0 % | 0.0 % | 450.2 | n/a |
| santerre | dense | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0852 | 71.0 % | 99.9 % | 0.0 % | 685.8 | n/a |
| santerre | dense | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0821 | 72.6 % | 100.0 % | 0.0 % | 945.1 | n/a |
| santerre | dense | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.3150 | 16.6 % | 92.7 % | 0.0 % | 141.1 | n/a |
| santerre | dense | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2164 | 29.3 % | 96.6 % | 0.0 % | 254.4 | n/a |
| santerre | dense | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.2207 | 32.4 % | 97.1 % | 0.0 % | 361.5 | n/a |
| santerre | dense | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.1509 | 33.5 % | 99.5 % | 0.0 % | 138.1 | n/a |
| santerre | dense | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.1488 | 36.8 % | 99.5 % | 0.0 % | 248.2 | n/a |
| santerre | dense | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.1456 | 36.9 % | 99.5 % | 0.0 % | 356.3 | n/a |
| santerre | dense | mild | phase_correlation | cpu | 10 | 5.0 % | 0.2375 | 17.4 % | 92.6 % | 0.0 % | 5.2 | 6.5 |
| santerre | dense | mild | sift_ransac | cpu | 10 | 5.0 % | 0.1370 | 47.7 % | 98.6 % | 0.0 % | 20.1 | 1.8 |
| santerre | dense | mild | arosics | cpu | 10 | 5.0 % | 0.2536 | 17.6 % | 90.9 % | 0.0 % | 19.3 | 10.0 |
| santerre | dense | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.5302 | 6.5 % | 73.3 % | 0.0 % | 440.6 | n/a |
| santerre | dense | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2856 | 10.2 % | 91.3 % | 0.0 % | 666.5 | n/a |
| santerre | dense | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2578 | 11.7 % | 94.0 % | 0.0 % | 900.3 | n/a |
| santerre | dense | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1940 | 24.2 % | 97.8 % | 0.0 % | 450.5 | n/a |
| santerre | dense | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1902 | 19.4 % | 98.9 % | 0.0 % | 697.9 | n/a |
| santerre | dense | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1888 | 19.8 % | 99.1 % | 0.0 % | 943.6 | n/a |
| santerre | dense | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 141.9 | n/a |
| santerre | dense | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.5952 | 3.2 % | 53.9 % | 50.0 % | 255.7 | n/a |
| santerre | dense | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.5396 | 3.9 % | 67.6 % | 20.0 % | 363.4 | n/a |
| santerre | dense | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2913 | 12.3 % | 87.7 % | 0.0 % | 137.1 | n/a |
| santerre | dense | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2268 | 17.8 % | 94.4 % | 0.0 % | 249.9 | n/a |
| santerre | dense | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.2202 | 21.1 % | 94.9 % | 0.0 % | 359.4 | n/a |
| santerre | dense | hard | phase_correlation | cpu | 10 | 30.0 % | 0.4298 | 6.5 % | 64.4 % | 10.0 % | 5.2 | 6.5 |
| santerre | dense | hard | sift_ransac | cpu | 10 | 30.0 % | 0.4733 | 7.9 % | 58.1 % | 80.0 % | 18.7 | 1.8 |
| santerre | dense | hard | arosics | cpu | 10 | 30.0 % | 0.4329 | 1.1 % | 67.3 % | 80.0 % | 18.7 | 10.0 |
| lyon | translation | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0586 | 89.7 % | 100.0 % | 0.0 % | 445.5 | n/a |
| lyon | translation | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0511 | 93.7 % | 100.0 % | 0.0 % | 680.7 | n/a |
| lyon | translation | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0495 | 94.1 % | 100.0 % | 0.0 % | 900.0 | n/a |
| lyon | translation | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0337 | 99.3 % | 100.0 % | 0.0 % | 462.1 | n/a |
| lyon | translation | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0264 | 100.0 % | 100.0 % | 0.0 % | 713.6 | n/a |
| lyon | translation | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0244 | 100.0 % | 100.0 % | 0.0 % | 970.7 | n/a |
| lyon | translation | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1892 | 18.4 % | 99.0 % | 0.0 % | 145.1 | n/a |
| lyon | translation | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1633 | 24.4 % | 99.8 % | 0.0 % | 262.0 | n/a |
| lyon | translation | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1583 | 25.8 % | 99.9 % | 0.0 % | 375.7 | n/a |
| lyon | translation | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0835 | 68.4 % | 100.0 % | 0.0 % | 142.4 | n/a |
| lyon | translation | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0744 | 77.6 % | 100.0 % | 0.0 % | 253.7 | n/a |
| lyon | translation | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0710 | 79.7 % | 100.0 % | 0.0 % | 359.4 | n/a |
| lyon | translation | clean | phase_correlation | cpu | 10 | 0.0 % | 0.0117 | 100.0 % | 100.0 % | 0.0 % | 5.5 | 6.5 |
| lyon | translation | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0067 | 100.0 % | 100.0 % | 0.0 % | 31.8 | 2.2 |
| lyon | translation | clean | arosics | cpu | 10 | 0.0 % | 0.0105 | 100.0 % | 100.0 % | 0.0 % | 20.0 | 10.0 |
| lyon | translation | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0611 | 86.9 % | 100.0 % | 0.0 % | 449.1 | n/a |
| lyon | translation | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0515 | 93.6 % | 100.0 % | 0.0 % | 673.8 | n/a |
| lyon | translation | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0505 | 94.0 % | 100.0 % | 0.0 % | 906.8 | n/a |
| lyon | translation | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0352 | 98.0 % | 100.0 % | 0.0 % | 466.3 | n/a |
| lyon | translation | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0280 | 99.4 % | 100.0 % | 0.0 % | 719.9 | n/a |
| lyon | translation | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0261 | 99.6 % | 100.0 % | 0.0 % | 961.4 | n/a |
| lyon | translation | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.1952 | 19.2 % | 97.8 % | 0.0 % | 145.1 | n/a |
| lyon | translation | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.1563 | 27.8 % | 99.7 % | 0.0 % | 259.4 | n/a |
| lyon | translation | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1494 | 28.8 % | 99.8 % | 0.0 % | 375.6 | n/a |
| lyon | translation | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0895 | 64.3 % | 100.0 % | 0.0 % | 142.5 | n/a |
| lyon | translation | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0786 | 71.7 % | 100.0 % | 0.0 % | 254.4 | n/a |
| lyon | translation | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0747 | 73.9 % | 100.0 % | 0.0 % | 362.8 | n/a |
| lyon | translation | mild | phase_correlation | cpu | 10 | 5.0 % | 0.0126 | 100.0 % | 100.0 % | 0.0 % | 5.5 | 6.5 |
| lyon | translation | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0083 | 100.0 % | 100.0 % | 0.0 % | 32.4 | 2.2 |
| lyon | translation | mild | arosics | cpu | 10 | 5.0 % | 0.0193 | 100.0 % | 100.0 % | 0.0 % | 19.8 | 10.0 |
| lyon | translation | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.3031 | 14.8 % | 90.9 % | 0.0 % | 444.7 | n/a |
| lyon | translation | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2040 | 28.7 % | 99.1 % | 0.0 % | 682.0 | n/a |
| lyon | translation | hard | raft_onnx | cpu | 10 | 30.0 % | 0.1912 | 30.8 % | 99.7 % | 0.0 % | 905.3 | n/a |
| lyon | translation | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1250 | 51.1 % | 98.3 % | 0.0 % | 471.8 | n/a |
| lyon | translation | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1173 | 49.4 % | 100.0 % | 0.0 % | 717.0 | n/a |
| lyon | translation | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1132 | 50.2 % | 100.0 % | 0.0 % | 967.2 | n/a |
| lyon | translation | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 144.4 | n/a |
| lyon | translation | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.4567 | 6.8 % | 69.3 % | 0.0 % | 260.2 | n/a |
| lyon | translation | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.3500 | 6.8 % | 82.1 % | 0.0 % | 366.1 | n/a |
| lyon | translation | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2389 | 14.9 % | 93.2 % | 0.0 % | 138.4 | n/a |
| lyon | translation | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1498 | 32.6 % | 100.0 % | 0.0 % | 252.7 | n/a |
| lyon | translation | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.1376 | 36.5 % | 100.0 % | 0.0 % | 357.3 | n/a |
| lyon | translation | hard | phase_correlation | cpu | 10 | 30.0 % | 0.1386 | 20.0 % | 100.0 % | 0.0 % | 5.2 | 6.5 |
| lyon | translation | hard | sift_ransac | cpu | 10 | 30.0 % | 0.3611 | 9.2 % | 78.6 % | 30.0 % | 22.0 | 2.2 |
| lyon | translation | hard | arosics | cpu | 10 | 30.0 % | 0.2023 | 16.7 % | 100.0 % | 40.0 % | 19.0 | 10.0 |
| lyon | affine | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0620 | 84.9 % | 100.0 % | 0.0 % | 447.9 | n/a |
| lyon | affine | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0558 | 88.3 % | 100.0 % | 0.0 % | 674.6 | n/a |
| lyon | affine | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0530 | 88.6 % | 100.0 % | 0.0 % | 907.4 | n/a |
| lyon | affine | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0429 | 95.4 % | 100.0 % | 0.0 % | 470.9 | n/a |
| lyon | affine | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0343 | 98.3 % | 100.0 % | 0.0 % | 713.6 | n/a |
| lyon | affine | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0309 | 99.1 % | 100.0 % | 0.0 % | 965.5 | n/a |
| lyon | affine | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1875 | 18.7 % | 99.0 % | 0.0 % | 144.4 | n/a |
| lyon | affine | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1600 | 25.9 % | 99.8 % | 0.0 % | 260.1 | n/a |
| lyon | affine | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1556 | 26.2 % | 99.9 % | 0.0 % | 372.4 | n/a |
| lyon | affine | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0913 | 63.8 % | 100.0 % | 0.0 % | 139.9 | n/a |
| lyon | affine | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0838 | 69.8 % | 100.0 % | 0.0 % | 249.7 | n/a |
| lyon | affine | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0768 | 73.6 % | 100.0 % | 0.0 % | 356.2 | n/a |
| lyon | affine | clean | phase_correlation | cpu | 10 | 0.0 % | 0.2300 | 15.6 % | 98.3 % | 0.0 % | 5.5 | 6.5 |
| lyon | affine | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0050 | 100.0 % | 100.0 % | 0.0 % | 31.9 | 2.2 |
| lyon | affine | clean | arosics | cpu | 10 | 0.0 % | 0.2293 | 15.5 % | 98.5 % | 0.0 % | 19.7 | 10.0 |
| lyon | affine | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0656 | 81.8 % | 100.0 % | 0.0 % | 450.3 | n/a |
| lyon | affine | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0574 | 86.9 % | 100.0 % | 0.0 % | 682.0 | n/a |
| lyon | affine | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0549 | 87.8 % | 100.0 % | 0.0 % | 902.0 | n/a |
| lyon | affine | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0472 | 92.7 % | 100.0 % | 0.0 % | 469.7 | n/a |
| lyon | affine | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0371 | 96.6 % | 100.0 % | 0.0 % | 724.6 | n/a |
| lyon | affine | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0352 | 96.6 % | 100.0 % | 0.0 % | 967.5 | n/a |
| lyon | affine | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.1933 | 20.3 % | 97.7 % | 0.0 % | 145.3 | n/a |
| lyon | affine | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.1534 | 29.6 % | 99.8 % | 0.0 % | 259.5 | n/a |
| lyon | affine | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1465 | 30.9 % | 99.9 % | 0.0 % | 374.0 | n/a |
| lyon | affine | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0976 | 60.0 % | 100.0 % | 0.0 % | 139.0 | n/a |
| lyon | affine | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0896 | 65.3 % | 100.0 % | 0.0 % | 254.2 | n/a |
| lyon | affine | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0849 | 67.8 % | 100.0 % | 0.0 % | 356.5 | n/a |
| lyon | affine | mild | phase_correlation | cpu | 10 | 5.0 % | 0.2299 | 15.6 % | 98.5 % | 0.0 % | 5.5 | 6.5 |
| lyon | affine | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0096 | 100.0 % | 100.0 % | 0.0 % | 32.4 | 2.2 |
| lyon | affine | mild | arosics | cpu | 10 | 5.0 % | 0.2300 | 15.5 % | 98.4 % | 0.0 % | 19.6 | 10.0 |
| lyon | affine | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.3135 | 14.4 % | 90.0 % | 0.0 % | 445.7 | n/a |
| lyon | affine | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2266 | 22.2 % | 98.9 % | 0.0 % | 677.3 | n/a |
| lyon | affine | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2249 | 21.5 % | 99.1 % | 0.0 % | 916.4 | n/a |
| lyon | affine | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1544 | 36.3 % | 98.2 % | 0.0 % | 468.5 | n/a |
| lyon | affine | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1440 | 33.0 % | 99.8 % | 0.0 % | 717.7 | n/a |
| lyon | affine | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1335 | 39.1 % | 99.9 % | 0.0 % | 965.0 | n/a |
| lyon | affine | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 145.9 | n/a |
| lyon | affine | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.4466 | 7.3 % | 68.7 % | 0.0 % | 260.5 | n/a |
| lyon | affine | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.3533 | 7.6 % | 80.7 % | 0.0 % | 369.2 | n/a |
| lyon | affine | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2335 | 18.4 % | 93.8 % | 0.0 % | 140.5 | n/a |
| lyon | affine | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1731 | 30.9 % | 98.9 % | 0.0 % | 251.0 | n/a |
| lyon | affine | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.1678 | 30.8 % | 99.5 % | 0.0 % | 359.6 | n/a |
| lyon | affine | hard | phase_correlation | cpu | 10 | 30.0 % | 0.2800 | 8.1 % | 92.0 % | 0.0 % | 5.6 | 6.5 |
| lyon | affine | hard | sift_ransac | cpu | 10 | 30.0 % | 0.3801 | 10.8 % | 72.7 % | 20.0 % | 22.3 | 2.2 |
| lyon | affine | hard | arosics | cpu | 10 | 30.0 % | 0.3023 | 12.2 % | 85.3 % | 40.0 % | 19.1 | 10.0 |
| lyon | dense | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0913 | 64.1 % | 100.0 % | 0.0 % | 441.9 | n/a |
| lyon | dense | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0874 | 63.8 % | 100.0 % | 0.0 % | 677.1 | n/a |
| lyon | dense | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0848 | 65.3 % | 100.0 % | 0.0 % | 904.7 | n/a |
| lyon | dense | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0644 | 82.9 % | 100.0 % | 0.0 % | 464.4 | n/a |
| lyon | dense | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0586 | 87.0 % | 100.0 % | 0.0 % | 706.9 | n/a |
| lyon | dense | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0577 | 87.7 % | 100.0 % | 0.0 % | 968.6 | n/a |
| lyon | dense | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1986 | 18.7 % | 98.1 % | 0.0 % | 146.1 | n/a |
| lyon | dense | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1806 | 24.5 % | 98.2 % | 0.0 % | 264.7 | n/a |
| lyon | dense | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1796 | 24.6 % | 98.2 % | 0.0 % | 378.9 | n/a |
| lyon | dense | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.1253 | 45.6 % | 99.4 % | 0.0 % | 143.9 | n/a |
| lyon | dense | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.1206 | 49.3 % | 99.2 % | 0.0 % | 260.1 | n/a |
| lyon | dense | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.1140 | 54.1 % | 99.2 % | 0.0 % | 362.6 | n/a |
| lyon | dense | clean | phase_correlation | cpu | 10 | 0.0 % | 0.2717 | 12.1 % | 91.9 % | 0.0 % | 5.4 | 6.5 |
| lyon | dense | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0945 | 71.0 % | 98.7 % | 0.0 % | 31.7 | 2.2 |
| lyon | dense | clean | arosics | cpu | 10 | 0.0 % | 0.2784 | 13.5 % | 90.1 % | 0.0 % | 19.8 | 10.0 |
| lyon | dense | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0982 | 61.3 % | 100.0 % | 0.0 % | 446.0 | n/a |
| lyon | dense | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0947 | 62.7 % | 100.0 % | 0.0 % | 675.0 | n/a |
| lyon | dense | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0916 | 64.1 % | 100.0 % | 0.0 % | 908.4 | n/a |
| lyon | dense | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0726 | 77.2 % | 100.0 % | 0.0 % | 465.7 | n/a |
| lyon | dense | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0639 | 82.7 % | 100.0 % | 0.0 % | 720.7 | n/a |
| lyon | dense | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0637 | 83.3 % | 100.0 % | 0.0 % | 967.7 | n/a |
| lyon | dense | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2072 | 19.9 % | 97.0 % | 0.0 % | 145.5 | n/a |
| lyon | dense | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.1820 | 26.7 % | 98.3 % | 0.0 % | 264.8 | n/a |
| lyon | dense | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1790 | 25.4 % | 98.3 % | 0.0 % | 376.4 | n/a |
| lyon | dense | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.1340 | 42.5 % | 99.3 % | 0.0 % | 143.4 | n/a |
| lyon | dense | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.1308 | 46.0 % | 99.0 % | 0.0 % | 251.0 | n/a |
| lyon | dense | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.1261 | 47.5 % | 99.1 % | 0.0 % | 357.0 | n/a |
| lyon | dense | mild | phase_correlation | cpu | 10 | 5.0 % | 0.2720 | 11.8 % | 91.7 % | 0.0 % | 5.2 | 6.5 |
| lyon | dense | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0940 | 71.6 % | 98.6 % | 0.0 % | 32.0 | 2.2 |
| lyon | dense | mild | arosics | cpu | 10 | 5.0 % | 0.2816 | 13.5 % | 89.7 % | 0.0 % | 19.8 | 10.0 |
| lyon | dense | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.2647 | 13.8 % | 94.4 % | 0.0 % | 443.3 | n/a |
| lyon | dense | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2287 | 22.5 % | 97.3 % | 0.0 % | 675.8 | n/a |
| lyon | dense | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2320 | 21.2 % | 96.4 % | 0.0 % | 897.0 | n/a |
| lyon | dense | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1773 | 28.0 % | 98.6 % | 0.0 % | 460.8 | n/a |
| lyon | dense | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1716 | 27.3 % | 98.9 % | 0.0 % | 711.9 | n/a |
| lyon | dense | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1712 | 28.9 % | 98.7 % | 0.0 % | 966.3 | n/a |
| lyon | dense | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | 0.4706 | 4.5 % | 62.2 % | 90.0 % | 144.3 | n/a |
| lyon | dense | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.4178 | 8.9 % | 71.7 % | 0.0 % | 263.5 | n/a |
| lyon | dense | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.3572 | 7.2 % | 80.2 % | 0.0 % | 375.2 | n/a |
| lyon | dense | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2421 | 19.2 % | 92.9 % | 0.0 % | 142.9 | n/a |
| lyon | dense | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2126 | 25.4 % | 96.1 % | 0.0 % | 258.8 | n/a |
| lyon | dense | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.2173 | 24.8 % | 95.8 % | 0.0 % | 359.3 | n/a |
| lyon | dense | hard | phase_correlation | cpu | 10 | 30.0 % | 0.3135 | 7.7 % | 86.5 % | 0.0 % | 5.3 | 6.5 |
| lyon | dense | hard | sift_ransac | cpu | 10 | 30.0 % | 0.2882 | 20.5 % | 82.5 % | 20.0 % | 21.7 | 2.2 |
| lyon | dense | hard | arosics | cpu | 10 | 30.0 % | 0.3540 | 11.1 % | 77.9 % | 40.0 % | 18.9 | 10.0 |
| morvan | translation | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0591 | 89.1 % | 100.0 % | 0.0 % | 448.9 | n/a |
| morvan | translation | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0481 | 95.7 % | 100.0 % | 0.0 % | 681.1 | n/a |
| morvan | translation | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0469 | 96.6 % | 100.0 % | 0.0 % | 913.2 | n/a |
| morvan | translation | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0368 | 99.0 % | 100.0 % | 0.0 % | 464.1 | n/a |
| morvan | translation | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0280 | 100.0 % | 100.0 % | 0.0 % | 717.8 | n/a |
| morvan | translation | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0268 | 100.0 % | 100.0 % | 0.0 % | 965.0 | n/a |
| morvan | translation | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1955 | 19.6 % | 98.8 % | 0.0 % | 145.8 | n/a |
| morvan | translation | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1459 | 30.7 % | 99.7 % | 0.0 % | 262.7 | n/a |
| morvan | translation | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1375 | 33.4 % | 99.8 % | 0.0 % | 377.4 | n/a |
| morvan | translation | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0723 | 78.4 % | 100.0 % | 0.0 % | 143.0 | n/a |
| morvan | translation | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0546 | 90.3 % | 100.0 % | 0.0 % | 255.5 | n/a |
| morvan | translation | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0516 | 94.6 % | 100.0 % | 0.0 % | 368.6 | n/a |
| morvan | translation | clean | phase_correlation | cpu | 10 | 0.0 % | 0.0168 | 100.0 % | 100.0 % | 0.0 % | 5.6 | 6.5 |
| morvan | translation | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0126 | 100.0 % | 100.0 % | 0.0 % | 21.8 | 1.8 |
| morvan | translation | clean | arosics | cpu | 10 | 0.0 % | 0.0222 | 100.0 % | 100.0 % | 0.0 % | 19.9 | 10.0 |
| morvan | translation | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0757 | 81.1 % | 99.9 % | 0.0 % | 450.9 | n/a |
| morvan | translation | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0633 | 93.4 % | 99.9 % | 0.0 % | 681.1 | n/a |
| morvan | translation | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0615 | 94.7 % | 99.9 % | 0.0 % | 905.6 | n/a |
| morvan | translation | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0396 | 97.5 % | 100.0 % | 0.0 % | 467.8 | n/a |
| morvan | translation | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0317 | 99.3 % | 100.0 % | 0.0 % | 721.9 | n/a |
| morvan | translation | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0307 | 99.9 % | 100.0 % | 0.0 % | 973.2 | n/a |
| morvan | translation | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2897 | 16.6 % | 93.5 % | 0.0 % | 149.0 | n/a |
| morvan | translation | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2135 | 28.9 % | 97.6 % | 0.0 % | 264.9 | n/a |
| morvan | translation | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1952 | 34.5 % | 98.3 % | 0.0 % | 383.6 | n/a |
| morvan | translation | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0836 | 70.0 % | 100.0 % | 0.0 % | 145.8 | n/a |
| morvan | translation | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0606 | 85.5 % | 100.0 % | 0.0 % | 259.9 | n/a |
| morvan | translation | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0568 | 87.2 % | 100.0 % | 0.0 % | 372.8 | n/a |
| morvan | translation | mild | phase_correlation | cpu | 10 | 5.0 % | 0.0205 | 100.0 % | 100.0 % | 0.0 % | 5.6 | 6.5 |
| morvan | translation | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0195 | 100.0 % | 100.0 % | 0.0 % | 22.5 | 1.8 |
| morvan | translation | mild | arosics | cpu | 10 | 5.0 % | 0.0594 | 90.0 % | 100.0 % | 0.0 % | 19.7 | 10.0 |
| morvan | translation | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.5988 | 10.3 % | 68.5 % | 30.0 % | 446.8 | n/a |
| morvan | translation | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2407 | 23.1 % | 89.8 % | 10.0 % | 680.5 | n/a |
| morvan | translation | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2072 | 26.1 % | 93.0 % | 10.0 % | 907.3 | n/a |
| morvan | translation | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1321 | 39.4 % | 100.0 % | 0.0 % | 461.6 | n/a |
| morvan | translation | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1047 | 53.2 % | 100.0 % | 0.0 % | 722.6 | n/a |
| morvan | translation | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1032 | 53.5 % | 100.0 % | 0.0 % | 972.7 | n/a |
| morvan | translation | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 145.4 | n/a |
| morvan | translation | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.7168 | 6.1 % | 40.5 % | 80.0 % | 261.4 | n/a |
| morvan | translation | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.6065 | 1.7 % | 47.2 % | 40.0 % | 376.1 | n/a |
| morvan | translation | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.3365 | 8.7 % | 82.0 % | 0.0 % | 143.6 | n/a |
| morvan | translation | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2134 | 13.6 % | 99.6 % | 0.0 % | 255.9 | n/a |
| morvan | translation | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.2150 | 14.3 % | 98.4 % | 0.0 % | 361.0 | n/a |
| morvan | translation | hard | phase_correlation | cpu | 10 | 30.0 % | 0.2123 | 10.0 % | 90.0 % | 0.0 % | 5.3 | 6.5 |
| morvan | translation | hard | sift_ransac | cpu | 10 | 30.0 % | 0.2860 | 13.3 % | 86.0 % | 30.0 % | 19.1 | 1.8 |
| morvan | translation | hard | arosics | cpu | 10 | 30.0 % | 0.4417 | 0.0 % | 60.0 % | 50.0 % | 19.3 | 10.0 |
| morvan | affine | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0639 | 85.8 % | 100.0 % | 0.0 % | 448.2 | n/a |
| morvan | affine | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0549 | 92.5 % | 100.0 % | 0.0 % | 680.5 | n/a |
| morvan | affine | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0532 | 93.8 % | 100.0 % | 0.0 % | 917.4 | n/a |
| morvan | affine | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0436 | 96.2 % | 100.0 % | 0.0 % | 463.8 | n/a |
| morvan | affine | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0334 | 99.7 % | 100.0 % | 0.0 % | 716.6 | n/a |
| morvan | affine | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0315 | 99.8 % | 100.0 % | 0.0 % | 968.4 | n/a |
| morvan | affine | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1964 | 19.9 % | 98.6 % | 0.0 % | 147.6 | n/a |
| morvan | affine | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1488 | 30.2 % | 99.5 % | 0.0 % | 261.4 | n/a |
| morvan | affine | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1411 | 31.4 % | 99.7 % | 0.0 % | 377.3 | n/a |
| morvan | affine | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0844 | 70.2 % | 100.0 % | 0.0 % | 143.7 | n/a |
| morvan | affine | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0716 | 80.5 % | 100.0 % | 0.0 % | 256.2 | n/a |
| morvan | affine | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0666 | 84.4 % | 100.0 % | 0.0 % | 358.6 | n/a |
| morvan | affine | clean | phase_correlation | cpu | 10 | 0.0 % | 0.2347 | 21.5 % | 95.1 % | 0.0 % | 5.4 | 6.5 |
| morvan | affine | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0116 | 100.0 % | 100.0 % | 0.0 % | 22.1 | 1.8 |
| morvan | affine | clean | arosics | cpu | 10 | 0.0 % | 0.2279 | 21.3 % | 97.3 % | 0.0 % | 19.6 | 10.0 |
| morvan | affine | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0810 | 77.5 % | 99.9 % | 0.0 % | 445.7 | n/a |
| morvan | affine | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0704 | 87.9 % | 99.9 % | 0.0 % | 676.4 | n/a |
| morvan | affine | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0689 | 90.6 % | 99.9 % | 0.0 % | 912.7 | n/a |
| morvan | affine | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0471 | 94.1 % | 100.0 % | 0.0 % | 464.6 | n/a |
| morvan | affine | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0363 | 98.3 % | 100.0 % | 0.0 % | 714.8 | n/a |
| morvan | affine | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0345 | 99.5 % | 100.0 % | 0.0 % | 967.9 | n/a |
| morvan | affine | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2826 | 17.7 % | 93.2 % | 0.0 % | 144.3 | n/a |
| morvan | affine | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2113 | 31.3 % | 97.7 % | 0.0 % | 262.9 | n/a |
| morvan | affine | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1866 | 36.4 % | 98.5 % | 0.0 % | 377.3 | n/a |
| morvan | affine | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0920 | 62.4 % | 100.0 % | 0.0 % | 144.2 | n/a |
| morvan | affine | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0782 | 70.6 % | 100.0 % | 0.0 % | 256.4 | n/a |
| morvan | affine | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0734 | 76.6 % | 100.0 % | 0.0 % | 360.5 | n/a |
| morvan | affine | mild | phase_correlation | cpu | 10 | 5.0 % | 0.2342 | 21.9 % | 95.1 % | 0.0 % | 5.7 | 6.5 |
| morvan | affine | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0213 | 99.0 % | 100.0 % | 0.0 % | 23.0 | 1.8 |
| morvan | affine | mild | arosics | cpu | 10 | 5.0 % | 0.2373 | 20.1 % | 96.2 % | 0.0 % | 19.5 | 10.0 |
| morvan | affine | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.6006 | 10.1 % | 68.4 % | 30.0 % | 451.3 | n/a |
| morvan | affine | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2514 | 20.9 % | 88.6 % | 10.0 % | 679.9 | n/a |
| morvan | affine | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2284 | 25.4 % | 91.0 % | 10.0 % | 907.9 | n/a |
| morvan | affine | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1487 | 32.2 % | 99.9 % | 0.0 % | 473.5 | n/a |
| morvan | affine | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1414 | 32.7 % | 100.0 % | 0.0 % | 718.2 | n/a |
| morvan | affine | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1377 | 34.0 % | 100.0 % | 0.0 % | 970.2 | n/a |
| morvan | affine | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 145.4 | n/a |
| morvan | affine | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.6769 | 6.6 % | 42.9 % | 80.0 % | 260.9 | n/a |
| morvan | affine | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.5666 | 2.4 % | 50.4 % | 50.0 % | 372.5 | n/a |
| morvan | affine | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.3404 | 8.8 % | 82.1 % | 0.0 % | 139.4 | n/a |
| morvan | affine | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2597 | 11.9 % | 92.2 % | 0.0 % | 257.9 | n/a |
| morvan | affine | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.2729 | 8.9 % | 90.9 % | 0.0 % | 360.3 | n/a |
| morvan | affine | hard | phase_correlation | cpu | 10 | 30.0 % | 0.3968 | 5.0 % | 72.2 % | 0.0 % | 5.3 | 6.5 |
| morvan | affine | hard | sift_ransac | cpu | 10 | 30.0 % | 0.2829 | 24.4 % | 83.6 % | 30.0 % | 19.2 | 1.8 |
| morvan | affine | hard | arosics | cpu | 10 | 30.0 % | 0.4703 | 1.3 % | 55.5 % | 50.0 % | 19.1 | 10.0 |
| morvan | dense | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0906 | 64.8 % | 100.0 % | 0.0 % | 443.5 | n/a |
| morvan | dense | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0930 | 63.7 % | 100.0 % | 0.0 % | 675.7 | n/a |
| morvan | dense | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0923 | 64.4 % | 100.0 % | 0.0 % | 908.2 | n/a |
| morvan | dense | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0790 | 72.9 % | 100.0 % | 0.0 % | 462.2 | n/a |
| morvan | dense | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0663 | 81.4 % | 100.0 % | 0.0 % | 699.6 | n/a |
| morvan | dense | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0649 | 82.7 % | 100.0 % | 0.0 % | 966.5 | n/a |
| morvan | dense | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.2078 | 17.8 % | 98.3 % | 0.0 % | 147.2 | n/a |
| morvan | dense | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1726 | 25.4 % | 99.3 % | 0.0 % | 263.2 | n/a |
| morvan | dense | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1681 | 26.4 % | 99.3 % | 0.0 % | 383.1 | n/a |
| morvan | dense | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.1291 | 44.9 % | 99.8 % | 0.0 % | 144.2 | n/a |
| morvan | dense | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.1280 | 46.6 % | 99.8 % | 0.0 % | 261.5 | n/a |
| morvan | dense | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.1256 | 48.5 % | 99.8 % | 0.0 % | 368.1 | n/a |
| morvan | dense | clean | phase_correlation | cpu | 10 | 0.0 % | 0.3064 | 7.7 % | 86.7 % | 0.0 % | 5.5 | 6.5 |
| morvan | dense | clean | sift_ransac | cpu | 10 | 0.0 % | 0.1555 | 48.4 % | 95.1 % | 0.0 % | 23.6 | 1.8 |
| morvan | dense | clean | arosics | cpu | 10 | 0.0 % | 0.3093 | 9.2 % | 86.6 % | 0.0 % | 19.5 | 10.0 |
| morvan | dense | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.1039 | 59.3 % | 99.9 % | 0.0 % | 449.3 | n/a |
| morvan | dense | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.1067 | 58.5 % | 99.9 % | 0.0 % | 675.0 | n/a |
| morvan | dense | mild | raft_onnx | cpu | 10 | 5.0 % | 0.1068 | 59.3 % | 99.9 % | 0.0 % | 898.2 | n/a |
| morvan | dense | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0859 | 67.6 % | 100.0 % | 0.0 % | 465.9 | n/a |
| morvan | dense | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0766 | 73.7 % | 100.0 % | 0.0 % | 712.8 | n/a |
| morvan | dense | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0729 | 77.1 % | 100.0 % | 0.0 % | 964.4 | n/a |
| morvan | dense | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2692 | 17.5 % | 94.0 % | 0.0 % | 145.9 | n/a |
| morvan | dense | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2216 | 25.9 % | 97.9 % | 0.0 % | 263.8 | n/a |
| morvan | dense | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.2110 | 28.6 % | 98.4 % | 0.0 % | 381.8 | n/a |
| morvan | dense | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.1387 | 39.1 % | 99.8 % | 0.0 % | 143.6 | n/a |
| morvan | dense | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.1392 | 40.6 % | 99.8 % | 0.0 % | 258.3 | n/a |
| morvan | dense | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.1364 | 43.4 % | 99.8 % | 0.0 % | 365.1 | n/a |
| morvan | dense | mild | phase_correlation | cpu | 10 | 5.0 % | 0.3059 | 7.3 % | 86.9 % | 0.0 % | 5.5 | 6.5 |
| morvan | dense | mild | sift_ransac | cpu | 10 | 5.0 % | 0.1465 | 49.6 % | 96.3 % | 0.0 % | 22.0 | 1.8 |
| morvan | dense | mild | arosics | cpu | 10 | 5.0 % | 0.3124 | 9.1 % | 85.6 % | 0.0 % | 19.0 | 10.0 |
| morvan | dense | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.5566 | 10.8 % | 71.9 % | 30.0 % | 448.8 | n/a |
| morvan | dense | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2908 | 13.6 % | 86.6 % | 10.0 % | 679.1 | n/a |
| morvan | dense | hard | raft_onnx | cpu | 10 | 30.0 % | 0.2854 | 11.8 % | 88.6 % | 10.0 % | 901.6 | n/a |
| morvan | dense | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.1958 | 20.6 % | 97.5 % | 0.0 % | 463.4 | n/a |
| morvan | dense | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1942 | 22.6 % | 97.5 % | 0.0 % | 710.4 | n/a |
| morvan | dense | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1910 | 24.7 % | 97.7 % | 0.0 % | 968.3 | n/a |
| morvan | dense | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 147.8 | n/a |
| morvan | dense | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.8261 | 3.3 % | 36.1 % | 70.0 % | 264.2 | n/a |
| morvan | dense | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.6984 | 1.7 % | 39.1 % | 30.0 % | 379.7 | n/a |
| morvan | dense | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.3472 | 9.6 % | 82.1 % | 0.0 % | 143.0 | n/a |
| morvan | dense | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2946 | 12.8 % | 88.7 % | 0.0 % | 257.1 | n/a |
| morvan | dense | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.3080 | 11.7 % | 84.7 % | 0.0 % | 359.3 | n/a |
| morvan | dense | hard | phase_correlation | cpu | 10 | 30.0 % | 0.4545 | 3.3 % | 63.1 % | 0.0 % | 5.6 | 6.5 |
| morvan | dense | hard | sift_ransac | cpu | 10 | 30.0 % | 0.3281 | 24.4 % | 81.3 % | 40.0 % | 19.7 | 1.8 |
| morvan | dense | hard | arosics | cpu | 10 | 30.0 % | 0.4894 | 1.7 % | 58.3 % | 50.0 % | 19.3 | 10.0 |
| sete | translation | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0562 | 90.4 % | 100.0 % | 0.0 % | 449.5 | n/a |
| sete | translation | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0492 | 96.0 % | 100.0 % | 0.0 % | 676.7 | n/a |
| sete | translation | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0474 | 97.3 % | 100.0 % | 0.0 % | 922.8 | n/a |
| sete | translation | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0425 | 96.4 % | 100.0 % | 0.0 % | 477.3 | n/a |
| sete | translation | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0344 | 98.9 % | 100.0 % | 0.0 % | 725.4 | n/a |
| sete | translation | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0338 | 99.2 % | 100.0 % | 0.0 % | 965.3 | n/a |
| sete | translation | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1624 | 32.8 % | 98.8 % | 0.0 % | 144.0 | n/a |
| sete | translation | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1340 | 39.6 % | 99.7 % | 0.0 % | 261.8 | n/a |
| sete | translation | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1287 | 38.9 % | 99.9 % | 0.0 % | 370.8 | n/a |
| sete | translation | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0754 | 75.6 % | 100.0 % | 0.0 % | 138.5 | n/a |
| sete | translation | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0647 | 82.7 % | 100.0 % | 0.0 % | 249.6 | n/a |
| sete | translation | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0638 | 85.8 % | 100.0 % | 0.0 % | 356.7 | n/a |
| sete | translation | clean | phase_correlation | cpu | 10 | 0.0 % | 0.0186 | 100.0 % | 100.0 % | 0.0 % | 5.2 | 6.5 |
| sete | translation | clean | sift_ransac | cpu | 10 | 0.0 % | 0.0705 | 83.4 % | 95.3 % | 0.0 % | 22.4 | 1.9 |
| sete | translation | clean | arosics | cpu | 10 | 0.0 % | 0.0159 | 100.0 % | 100.0 % | 0.0 % | 19.5 | 10.0 |
| sete | translation | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0659 | 84.9 % | 100.0 % | 0.0 % | 446.7 | n/a |
| sete | translation | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0558 | 91.3 % | 100.0 % | 0.0 % | 678.8 | n/a |
| sete | translation | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0538 | 93.0 % | 100.0 % | 0.0 % | 916.2 | n/a |
| sete | translation | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0480 | 90.2 % | 100.0 % | 0.0 % | 468.1 | n/a |
| sete | translation | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0399 | 93.5 % | 100.0 % | 0.0 % | 721.1 | n/a |
| sete | translation | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0394 | 95.3 % | 100.0 % | 0.0 % | 968.8 | n/a |
| sete | translation | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2383 | 22.9 % | 94.4 % | 0.0 % | 143.8 | n/a |
| sete | translation | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2022 | 29.2 % | 98.4 % | 0.0 % | 260.0 | n/a |
| sete | translation | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1905 | 28.9 % | 99.1 % | 0.0 % | 376.1 | n/a |
| sete | translation | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0913 | 61.9 % | 100.0 % | 0.0 % | 141.3 | n/a |
| sete | translation | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0800 | 72.9 % | 100.0 % | 0.0 % | 251.5 | n/a |
| sete | translation | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0744 | 77.7 % | 100.0 % | 0.0 % | 360.9 | n/a |
| sete | translation | mild | phase_correlation | cpu | 10 | 5.0 % | 0.0186 | 100.0 % | 100.0 % | 0.0 % | 5.2 | 6.5 |
| sete | translation | mild | sift_ransac | cpu | 10 | 5.0 % | 0.1115 | 77.2 % | 93.8 % | 0.0 % | 23.0 | 1.9 |
| sete | translation | mild | arosics | cpu | 10 | 5.0 % | 0.0926 | 70.0 % | 100.0 % | 0.0 % | 19.4 | 10.0 |
| sete | translation | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.3581 | 18.5 % | 79.8 % | 70.0 % | 452.7 | n/a |
| sete | translation | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2378 | 24.5 % | 94.9 % | 50.0 % | 682.2 | n/a |
| sete | translation | hard | raft_onnx | cpu | 10 | 30.0 % | 0.3459 | 25.2 % | 90.5 % | 40.0 % | 906.2 | n/a |
| sete | translation | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2063 | 31.6 % | 92.9 % | 0.0 % | 468.1 | n/a |
| sete | translation | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.1815 | 30.7 % | 100.0 % | 0.0 % | 718.8 | n/a |
| sete | translation | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.1770 | 31.2 % | 99.5 % | 0.0 % | 957.6 | n/a |
| sete | translation | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | 0.8341 | 9.0 % | 65.3 % | 90.0 % | 144.6 | n/a |
| sete | translation | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.3993 | 10.2 % | 72.7 % | 60.0 % | 260.1 | n/a |
| sete | translation | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.3353 | 7.7 % | 78.2 % | 60.0 % | 376.5 | n/a |
| sete | translation | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.3491 | 16.7 % | 76.6 % | 20.0 % | 142.4 | n/a |
| sete | translation | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.3382 | 29.5 % | 72.3 % | 0.0 % | 256.1 | n/a |
| sete | translation | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.3225 | 32.9 % | 77.6 % | 0.0 % | 358.8 | n/a |
| sete | translation | hard | phase_correlation | cpu | 10 | 30.0 % | 0.1861 | 22.2 % | 100.0 % | 10.0 % | 5.4 | 6.5 |
| sete | translation | hard | sift_ransac | cpu | 10 | 30.0 % | 0.3703 | 21.8 % | 74.3 % | 60.0 % | 18.2 | 1.8 |
| sete | translation | hard | arosics | cpu | 10 | 30.0 % | 0.2843 | 0.0 % | 100.0 % | 60.0 % | 12.7 | 6.9 |
| sete | affine | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0614 | 85.9 % | 100.0 % | 0.0 % | 446.7 | n/a |
| sete | affine | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0562 | 91.0 % | 100.0 % | 0.0 % | 675.6 | n/a |
| sete | affine | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0551 | 91.0 % | 100.0 % | 0.0 % | 913.4 | n/a |
| sete | affine | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0498 | 92.7 % | 100.0 % | 0.0 % | 473.3 | n/a |
| sete | affine | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0407 | 97.8 % | 100.0 % | 0.0 % | 719.1 | n/a |
| sete | affine | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0372 | 98.4 % | 100.0 % | 0.0 % | 964.7 | n/a |
| sete | affine | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1630 | 30.7 % | 99.0 % | 0.0 % | 144.4 | n/a |
| sete | affine | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1352 | 37.8 % | 99.8 % | 0.0 % | 260.6 | n/a |
| sete | affine | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1307 | 37.1 % | 100.0 % | 0.0 % | 377.7 | n/a |
| sete | affine | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0809 | 71.1 % | 100.0 % | 0.0 % | 142.6 | n/a |
| sete | affine | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0717 | 77.1 % | 100.0 % | 0.0 % | 250.6 | n/a |
| sete | affine | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.0651 | 82.1 % | 100.0 % | 0.0 % | 360.3 | n/a |
| sete | affine | clean | phase_correlation | cpu | 10 | 0.0 % | 0.2079 | 23.9 % | 95.5 % | 0.0 % | 5.3 | 6.5 |
| sete | affine | clean | sift_ransac | cpu | 10 | 0.0 % | 0.1081 | 81.8 % | 93.4 % | 0.0 % | 22.8 | 1.9 |
| sete | affine | clean | arosics | cpu | 10 | 0.0 % | 0.1861 | 27.1 % | 98.2 % | 10.0 % | 19.7 | 10.0 |
| sete | affine | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.0713 | 79.9 % | 100.0 % | 0.0 % | 446.9 | n/a |
| sete | affine | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.0662 | 84.2 % | 100.0 % | 0.0 % | 679.2 | n/a |
| sete | affine | mild | raft_onnx | cpu | 10 | 5.0 % | 0.0654 | 85.1 % | 100.0 % | 0.0 % | 926.1 | n/a |
| sete | affine | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0580 | 84.6 % | 100.0 % | 0.0 % | 470.0 | n/a |
| sete | affine | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0508 | 87.7 % | 100.0 % | 0.0 % | 717.9 | n/a |
| sete | affine | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0479 | 89.5 % | 100.0 % | 0.0 % | 967.6 | n/a |
| sete | affine | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2375 | 22.8 % | 94.8 % | 0.0 % | 144.1 | n/a |
| sete | affine | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2024 | 29.8 % | 98.6 % | 0.0 % | 259.7 | n/a |
| sete | affine | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.1915 | 29.3 % | 99.3 % | 0.0 % | 372.3 | n/a |
| sete | affine | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0945 | 60.0 % | 100.0 % | 0.0 % | 140.3 | n/a |
| sete | affine | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0891 | 66.5 % | 100.0 % | 0.0 % | 255.3 | n/a |
| sete | affine | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.0806 | 72.2 % | 100.0 % | 0.0 % | 359.2 | n/a |
| sete | affine | mild | phase_correlation | cpu | 10 | 5.0 % | 0.2079 | 23.8 % | 95.5 % | 0.0 % | 5.5 | 6.5 |
| sete | affine | mild | sift_ransac | cpu | 10 | 5.0 % | 0.0927 | 76.4 % | 97.1 % | 0.0 % | 22.5 | 1.9 |
| sete | affine | mild | arosics | cpu | 10 | 5.0 % | 0.2007 | 21.5 % | 98.0 % | 10.0 % | 19.7 | 10.0 |
| sete | affine | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.3730 | 16.0 % | 80.1 % | 70.0 % | 451.9 | n/a |
| sete | affine | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.2796 | 17.4 % | 91.5 % | 50.0 % | 684.7 | n/a |
| sete | affine | hard | raft_onnx | cpu | 10 | 30.0 % | 0.3466 | 13.9 % | 88.7 % | 40.0 % | 913.4 | n/a |
| sete | affine | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2372 | 21.4 % | 93.1 % | 0.0 % | 470.2 | n/a |
| sete | affine | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2455 | 20.4 % | 92.8 % | 0.0 % | 725.4 | n/a |
| sete | affine | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.2393 | 21.6 % | 93.1 % | 0.0 % | 962.5 | n/a |
| sete | affine | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | 0.8002 | 8.5 % | 65.0 % | 90.0 % | 145.0 | n/a |
| sete | affine | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.4120 | 9.4 % | 71.5 % | 60.0 % | 260.0 | n/a |
| sete | affine | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.3594 | 5.0 % | 75.9 % | 60.0 % | 376.8 | n/a |
| sete | affine | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.3644 | 13.4 % | 74.7 % | 20.0 % | 142.2 | n/a |
| sete | affine | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.3776 | 13.3 % | 73.8 % | 0.0 % | 255.2 | n/a |
| sete | affine | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.3776 | 10.3 % | 74.4 % | 0.0 % | 370.1 | n/a |
| sete | affine | hard | phase_correlation | cpu | 10 | 30.0 % | 0.2724 | 10.1 % | 91.3 % | 10.0 % | 5.6 | 6.5 |
| sete | affine | hard | sift_ransac | cpu | 10 | 30.0 % | 0.2388 | 14.6 % | 93.8 % | 70.0 % | 18.9 | 1.8 |
| sete | affine | hard | arosics | cpu | 10 | 30.0 % | 0.3584 | 3.8 % | 78.2 % | 60.0 % | 19.1 | 10.0 |
| sete | dense | clean | raft_r4_onnx | cpu | 10 | 0.0 % | 0.0898 | 65.0 % | 100.0 % | 0.0 % | 443.9 | n/a |
| sete | dense | clean | raft_r8_onnx | cpu | 10 | 0.0 % | 0.0901 | 64.4 % | 100.0 % | 0.0 % | 672.2 | n/a |
| sete | dense | clean | raft_onnx | cpu | 10 | 0.0 % | 0.0892 | 64.8 % | 100.0 % | 0.0 % | 906.4 | n/a |
| sete | dense | clean | raft_ft_r4_onnx | cpu | 10 | 0.0 % | 0.0794 | 72.3 % | 100.0 % | 0.0 % | 467.4 | n/a |
| sete | dense | clean | raft_ft_r8_onnx | cpu | 10 | 0.0 % | 0.0691 | 78.0 % | 100.0 % | 0.0 % | 718.9 | n/a |
| sete | dense | clean | raft_ft_onnx | cpu | 10 | 0.0 % | 0.0665 | 79.7 % | 100.0 % | 0.0 % | 967.4 | n/a |
| sete | dense | clean | raft_small_r4_onnx | cpu | 10 | 0.0 % | 0.1772 | 27.8 % | 98.8 % | 0.0 % | 145.0 | n/a |
| sete | dense | clean | raft_small_r8_onnx | cpu | 10 | 0.0 % | 0.1598 | 32.1 % | 99.2 % | 0.0 % | 263.9 | n/a |
| sete | dense | clean | raft_small_onnx | cpu | 10 | 0.0 % | 0.1591 | 30.4 % | 99.3 % | 0.0 % | 380.0 | n/a |
| sete | dense | clean | raft_small_ft_r4_onnx | cpu | 10 | 0.0 % | 0.1282 | 46.7 % | 99.7 % | 0.0 % | 143.9 | n/a |
| sete | dense | clean | raft_small_ft_r8_onnx | cpu | 10 | 0.0 % | 0.1289 | 48.8 % | 99.5 % | 0.0 % | 258.4 | n/a |
| sete | dense | clean | raft_small_ft_onnx | cpu | 10 | 0.0 % | 0.1265 | 50.0 % | 99.6 % | 0.0 % | 363.5 | n/a |
| sete | dense | clean | phase_correlation | cpu | 10 | 0.0 % | 0.2792 | 14.5 % | 89.7 % | 0.0 % | 5.5 | 6.5 |
| sete | dense | clean | sift_ransac | cpu | 10 | 0.0 % | 0.2359 | 37.6 % | 90.0 % | 0.0 % | 22.1 | 1.9 |
| sete | dense | clean | arosics | cpu | 10 | 0.0 % | 0.2718 | 13.1 % | 89.3 % | 10.0 % | 19.7 | 10.0 |
| sete | dense | mild | raft_r4_onnx | cpu | 10 | 5.0 % | 0.1016 | 59.0 % | 100.0 % | 0.0 % | 453.1 | n/a |
| sete | dense | mild | raft_r8_onnx | cpu | 10 | 5.0 % | 0.1034 | 57.3 % | 100.0 % | 0.0 % | 682.9 | n/a |
| sete | dense | mild | raft_onnx | cpu | 10 | 5.0 % | 0.1033 | 58.4 % | 99.9 % | 0.0 % | 910.8 | n/a |
| sete | dense | mild | raft_ft_r4_onnx | cpu | 10 | 5.0 % | 0.0955 | 65.3 % | 99.7 % | 0.0 % | 461.8 | n/a |
| sete | dense | mild | raft_ft_r8_onnx | cpu | 10 | 5.0 % | 0.0864 | 70.5 % | 99.7 % | 0.0 % | 703.3 | n/a |
| sete | dense | mild | raft_ft_onnx | cpu | 10 | 5.0 % | 0.0854 | 71.6 % | 99.9 % | 0.0 % | 970.3 | n/a |
| sete | dense | mild | raft_small_r4_onnx | cpu | 10 | 5.0 % | 0.2386 | 22.3 % | 94.2 % | 0.0 % | 144.6 | n/a |
| sete | dense | mild | raft_small_r8_onnx | cpu | 10 | 5.0 % | 0.2084 | 28.8 % | 97.7 % | 0.0 % | 262.4 | n/a |
| sete | dense | mild | raft_small_onnx | cpu | 10 | 5.0 % | 0.2034 | 26.8 % | 97.9 % | 0.0 % | 377.0 | n/a |
| sete | dense | mild | raft_small_ft_r4_onnx | cpu | 10 | 5.0 % | 0.1446 | 39.4 % | 99.1 % | 0.0 % | 143.5 | n/a |
| sete | dense | mild | raft_small_ft_r8_onnx | cpu | 10 | 5.0 % | 0.1446 | 41.2 % | 99.0 % | 0.0 % | 255.7 | n/a |
| sete | dense | mild | raft_small_ft_onnx | cpu | 10 | 5.0 % | 0.1428 | 42.5 % | 99.0 % | 0.0 % | 363.1 | n/a |
| sete | dense | mild | phase_correlation | cpu | 10 | 5.0 % | 0.2796 | 14.4 % | 89.9 % | 0.0 % | 5.5 | 6.5 |
| sete | dense | mild | sift_ransac | cpu | 10 | 5.0 % | 0.1980 | 40.4 % | 90.5 % | 0.0 % | 22.7 | 1.9 |
| sete | dense | mild | arosics | cpu | 10 | 5.0 % | 0.2801 | 10.4 % | 89.3 % | 10.0 % | 19.5 | 10.0 |
| sete | dense | hard | raft_r4_onnx | cpu | 10 | 30.0 % | 0.5437 | 13.7 % | 76.7 % | 50.0 % | 457.7 | n/a |
| sete | dense | hard | raft_r8_onnx | cpu | 10 | 30.0 % | 0.3579 | 18.3 % | 90.6 % | 40.0 % | 682.5 | n/a |
| sete | dense | hard | raft_onnx | cpu | 10 | 30.0 % | 0.4450 | 16.2 % | 86.0 % | 30.0 % | 916.0 | n/a |
| sete | dense | hard | raft_ft_r4_onnx | cpu | 10 | 30.0 % | 0.2558 | 17.9 % | 92.0 % | 0.0 % | 475.9 | n/a |
| sete | dense | hard | raft_ft_r8_onnx | cpu | 10 | 30.0 % | 0.2634 | 17.1 % | 89.3 % | 0.0 % | 728.0 | n/a |
| sete | dense | hard | raft_ft_onnx | cpu | 10 | 30.0 % | 0.2628 | 17.8 % | 87.8 % | 0.0 % | 970.1 | n/a |
| sete | dense | hard | raft_small_r4_onnx | cpu | 10 | 30.0 % | 0.5680 | 6.3 % | 60.1 % | 80.0 % | 142.8 | n/a |
| sete | dense | hard | raft_small_r8_onnx | cpu | 10 | 30.0 % | 0.3724 | 7.3 % | 77.5 % | 60.0 % | 256.7 | n/a |
| sete | dense | hard | raft_small_onnx | cpu | 10 | 30.0 % | 0.3687 | 7.0 % | 78.0 % | 60.0 % | 366.2 | n/a |
| sete | dense | hard | raft_small_ft_r4_onnx | cpu | 10 | 30.0 % | 0.3715 | 13.6 % | 73.5 % | 20.0 % | 141.2 | n/a |
| sete | dense | hard | raft_small_ft_r8_onnx | cpu | 10 | 30.0 % | 0.4087 | 12.5 % | 67.0 % | 0.0 % | 254.6 | n/a |
| sete | dense | hard | raft_small_ft_onnx | cpu | 10 | 30.0 % | 0.4027 | 10.8 % | 68.8 % | 0.0 % | 361.1 | n/a |
| sete | dense | hard | phase_correlation | cpu | 10 | 30.0 % | 0.3062 | 7.1 % | 90.8 % | 10.0 % | 5.3 | 6.5 |
| sete | dense | hard | sift_ransac | cpu | 10 | 30.0 % | 0.3135 | 8.9 % | 83.7 % | 60.0 % | 17.9 | 1.8 |
| sete | dense | hard | arosics | cpu | 10 | 30.0 % | 0.3556 | 1.2 % | 84.7 % | 60.0 % | 18.8 | 10.0 |

Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. Time is the median of 3 calls per pair, after 1 warm-up call(s) per method; memory is not measured call by call, as no counter sees what ONNX Runtime allocates (its memory is read in a process of its own, by satreg footprint) for raft_r4_onnx, raft_r8_onnx, raft_onnx, raft_ft_r4_onnx, raft_ft_r8_onnx, raft_ft_onnx, raft_small_r4_onnx, raft_small_r8_onnx, raft_small_onnx, raft_small_ft_r4_onnx, raft_small_ft_r8_onnx, raft_small_ft_onnx; the peak traced by tracemalloc, which misses native allocations for phase_correlation, sift_ransac, arosics. Details in `context.json`.
