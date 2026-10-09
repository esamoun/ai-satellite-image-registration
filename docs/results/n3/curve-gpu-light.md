Light validation set: 10 pairs per chip, scenario and preset, seed 0, cut from the validation chips santerre, lyon, morvan, sete. These are the first 10 pairs of every cell of the full set, which has 100.

Over every chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all chips | translation | clean | raft_r4 | cuda | 40 | 0.0 % | 0.0577 | 89.9 % | 100.0 % | 0.0 % | 22.7 | 43.4 |
| all chips | translation | clean | raft_r8 | cuda | 40 | 0.0 % | 0.0474 | 95.6 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| all chips | translation | clean | raft | cuda | 40 | 0.0 % | 0.0455 | 96.4 % | 100.0 % | 0.0 % | 46.5 | 43.4 |
| all chips | translation | clean | raft_ft_r4 | cuda | 40 | 0.0 % | 0.0376 | 98.2 % | 100.0 % | 0.0 % | 23.4 | 43.4 |
| all chips | translation | clean | raft_ft_r8 | cuda | 40 | 0.0 % | 0.0295 | 99.6 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| all chips | translation | clean | raft_ft | cuda | 40 | 0.0 % | 0.0280 | 99.7 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| all chips | translation | clean | raft_small_r4 | cuda | 40 | 0.0 % | 0.1792 | 24.2 % | 98.8 % | 0.0 % | 17.1 | 20.4 |
| all chips | translation | clean | raft_small_r8 | cuda | 40 | 0.0 % | 0.1427 | 34.2 % | 99.7 % | 0.0 % | 24.3 | 20.4 |
| all chips | translation | clean | raft_small | cuda | 40 | 0.0 % | 0.1357 | 36.2 % | 99.8 % | 0.0 % | 31.7 | 20.4 |
| all chips | translation | clean | raft_small_ft_r4 | cuda | 40 | 0.0 % | 0.0772 | 74.0 % | 100.0 % | 0.0 % | 17.1 | 20.0 |
| all chips | translation | clean | raft_small_ft_r8 | cuda | 40 | 0.0 % | 0.0627 | 85.3 % | 100.0 % | 0.0 % | 24.4 | 20.0 |
| all chips | translation | clean | raft_small_ft | cuda | 40 | 0.0 % | 0.0603 | 87.9 % | 100.0 % | 0.0 % | 32.0 | 20.0 |
| all chips | translation | mild | raft_r4 | cuda | 40 | 5.0 % | 0.0739 | 82.3 % | 99.8 % | 0.0 % | 22.4 | 43.4 |
| all chips | translation | mild | raft_r8 | cuda | 40 | 5.0 % | 0.0567 | 92.8 % | 99.9 % | 0.0 % | 35.0 | 43.4 |
| all chips | translation | mild | raft | cuda | 40 | 5.0 % | 0.0531 | 94.1 % | 100.0 % | 0.0 % | 46.5 | 43.4 |
| all chips | translation | mild | raft_ft_r4 | cuda | 40 | 5.0 % | 0.0418 | 95.5 % | 100.0 % | 0.0 % | 23.1 | 43.4 |
| all chips | translation | mild | raft_ft_r8 | cuda | 40 | 5.0 % | 0.0336 | 97.9 % | 100.0 % | 0.0 % | 34.7 | 43.4 |
| all chips | translation | mild | raft_ft | cuda | 40 | 5.0 % | 0.0320 | 98.6 % | 100.0 % | 0.0 % | 46.5 | 43.4 |
| all chips | translation | mild | raft_small_r4 | cuda | 40 | 5.0 % | 0.2599 | 19.2 % | 94.6 % | 0.0 % | 17.2 | 20.4 |
| all chips | translation | mild | raft_small_r8 | cuda | 40 | 5.0 % | 0.2001 | 30.0 % | 98.5 % | 0.0 % | 24.5 | 20.4 |
| all chips | translation | mild | raft_small | cuda | 40 | 5.0 % | 0.1792 | 33.6 % | 99.0 % | 2.5 % | 31.8 | 20.4 |
| all chips | translation | mild | raft_small_ft_r4 | cuda | 40 | 5.0 % | 0.0927 | 62.7 % | 99.9 % | 0.0 % | 17.3 | 20.0 |
| all chips | translation | mild | raft_small_ft_r8 | cuda | 40 | 5.0 % | 0.0756 | 76.2 % | 100.0 % | 0.0 % | 24.4 | 20.0 |
| all chips | translation | mild | raft_small_ft | cuda | 40 | 5.0 % | 0.0716 | 78.7 % | 100.0 % | 0.0 % | 31.7 | 20.0 |
| all chips | translation | hard | raft_r4 | cuda | 40 | 30.0 % | 0.4543 | 11.7 % | 78.2 % | 27.5 % | 22.6 | 43.4 |
| all chips | translation | hard | raft_r8 | cuda | 40 | 30.0 % | 0.2305 | 24.0 % | 94.8 % | 15.0 % | 35.0 | 43.4 |
| all chips | translation | hard | raft | cuda | 40 | 30.0 % | 0.2211 | 26.8 % | 96.1 % | 12.5 % | 46.6 | 43.4 |
| all chips | translation | hard | raft_ft_r4 | cuda | 40 | 30.0 % | 0.1484 | 40.9 % | 97.8 % | 0.0 % | 23.1 | 43.4 |
| all chips | translation | hard | raft_ft_r8 | cuda | 40 | 30.0 % | 0.1293 | 45.5 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| all chips | translation | hard | raft_ft | cuda | 40 | 30.0 % | 0.1266 | 45.9 % | 99.9 % | 0.0 % | 46.4 | 43.4 |
| all chips | translation | hard | raft_small_r4 | cuda | 40 | 30.0 % | 0.8341 | 9.0 % | 65.3 % | 97.5 % | 17.2 | 20.4 |
| all chips | translation | hard | raft_small_r8 | cuda | 40 | 30.0 % | 0.5072 | 6.2 % | 63.4 % | 47.5 % | 24.0 | 20.4 |
| all chips | translation | hard | raft_small | cuda | 40 | 30.0 % | 0.4485 | 4.9 % | 69.9 % | 30.0 % | 31.7 | 20.4 |
| all chips | translation | hard | raft_small_ft_r4 | cuda | 40 | 30.0 % | 0.2959 | 13.7 % | 85.7 % | 5.0 % | 16.8 | 20.0 |
| all chips | translation | hard | raft_small_ft_r8 | cuda | 40 | 30.0 % | 0.2131 | 27.4 % | 92.9 % | 0.0 % | 24.1 | 20.0 |
| all chips | translation | hard | raft_small_ft | cuda | 40 | 30.0 % | 0.2037 | 30.3 % | 94.0 % | 0.0 % | 31.9 | 20.0 |
| all chips | affine | clean | raft_r4 | cuda | 40 | 0.0 % | 0.0620 | 85.9 % | 100.0 % | 0.0 % | 25.9 | 43.4 |
| all chips | affine | clean | raft_r8 | cuda | 40 | 0.0 % | 0.0541 | 91.3 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| all chips | affine | clean | raft | cuda | 40 | 0.0 % | 0.0520 | 92.0 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| all chips | affine | clean | raft_ft_r4 | cuda | 40 | 0.0 % | 0.0445 | 95.4 % | 100.0 % | 0.0 % | 23.3 | 43.4 |
| all chips | affine | clean | raft_ft_r8 | cuda | 40 | 0.0 % | 0.0359 | 98.6 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| all chips | affine | clean | raft_ft | cuda | 40 | 0.0 % | 0.0336 | 99.0 % | 100.0 % | 0.0 % | 46.7 | 43.4 |
| all chips | affine | clean | raft_small_r4 | cuda | 40 | 0.0 % | 0.1788 | 23.9 % | 98.9 % | 0.0 % | 17.2 | 20.4 |
| all chips | affine | clean | raft_small_r8 | cuda | 40 | 0.0 % | 0.1430 | 34.1 % | 99.7 % | 0.0 % | 24.5 | 20.4 |
| all chips | affine | clean | raft_small | cuda | 40 | 0.0 % | 0.1365 | 35.4 % | 99.8 % | 0.0 % | 32.0 | 20.4 |
| all chips | affine | clean | raft_small_ft_r4 | cuda | 40 | 0.0 % | 0.0854 | 68.7 % | 100.0 % | 0.0 % | 17.2 | 20.0 |
| all chips | affine | clean | raft_small_ft_r8 | cuda | 40 | 0.0 % | 0.0740 | 77.0 % | 100.0 % | 0.0 % | 24.7 | 20.0 |
| all chips | affine | clean | raft_small_ft | cuda | 40 | 0.0 % | 0.0680 | 81.1 % | 100.0 % | 0.0 % | 32.3 | 20.0 |
| all chips | affine | mild | raft_r4 | cuda | 40 | 5.0 % | 0.0801 | 78.0 % | 99.8 % | 0.0 % | 22.5 | 43.4 |
| all chips | affine | mild | raft_r8 | cuda | 40 | 5.0 % | 0.0662 | 86.6 % | 99.9 % | 0.0 % | 34.8 | 43.4 |
| all chips | affine | mild | raft | cuda | 40 | 5.0 % | 0.0640 | 88.2 % | 99.9 % | 0.0 % | 46.5 | 43.4 |
| all chips | affine | mild | raft_ft_r4 | cuda | 40 | 5.0 % | 0.0507 | 91.3 % | 100.0 % | 0.0 % | 23.4 | 43.4 |
| all chips | affine | mild | raft_ft_r8 | cuda | 40 | 5.0 % | 0.0420 | 94.7 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| all chips | affine | mild | raft_ft | cuda | 40 | 5.0 % | 0.0397 | 95.9 % | 100.0 % | 0.0 % | 46.3 | 43.4 |
| all chips | affine | mild | raft_small_r4 | cuda | 40 | 5.0 % | 0.2571 | 19.5 % | 94.6 % | 0.0 % | 17.1 | 20.4 |
| all chips | affine | mild | raft_small_r8 | cuda | 40 | 5.0 % | 0.1935 | 30.6 % | 98.5 % | 0.0 % | 24.4 | 20.4 |
| all chips | affine | mild | raft_small | cuda | 40 | 5.0 % | 0.1915 | 33.6 % | 99.0 % | 0.0 % | 32.0 | 20.4 |
| all chips | affine | mild | raft_small_ft_r4 | cuda | 40 | 5.0 % | 0.0989 | 58.6 % | 99.9 % | 0.0 % | 17.1 | 20.0 |
| all chips | affine | mild | raft_small_ft_r8 | cuda | 40 | 5.0 % | 0.0884 | 65.7 % | 100.0 % | 0.0 % | 24.5 | 20.0 |
| all chips | affine | mild | raft_small_ft | cuda | 40 | 5.0 % | 0.0826 | 70.5 % | 100.0 % | 0.0 % | 31.7 | 20.0 |
| all chips | affine | hard | raft_r4 | cuda | 40 | 30.0 % | 0.4611 | 11.2 % | 77.7 % | 27.5 % | 22.7 | 43.4 |
| all chips | affine | hard | raft_r8 | cuda | 40 | 30.0 % | 0.2499 | 20.1 % | 93.9 % | 15.0 % | 35.1 | 43.4 |
| all chips | affine | hard | raft | cuda | 40 | 30.0 % | 0.2644 | 20.2 % | 93.7 % | 10.0 % | 46.8 | 43.4 |
| all chips | affine | hard | raft_ft_r4 | cuda | 40 | 30.0 % | 0.1757 | 29.5 % | 97.7 % | 0.0 % | 23.3 | 43.4 |
| all chips | affine | hard | raft_ft_r8 | cuda | 40 | 30.0 % | 0.1699 | 29.4 % | 98.1 % | 0.0 % | 34.8 | 43.4 |
| all chips | affine | hard | raft_ft | cuda | 40 | 30.0 % | 0.1639 | 32.1 % | 98.3 % | 0.0 % | 46.7 | 43.4 |
| all chips | affine | hard | raft_small_r4 | cuda | 40 | 30.0 % | 0.8002 | 8.5 % | 65.0 % | 97.5 % | 17.2 | 20.4 |
| all chips | affine | hard | raft_small_r8 | cuda | 40 | 30.0 % | 0.5067 | 6.3 % | 62.8 % | 47.5 % | 24.5 | 20.4 |
| all chips | affine | hard | raft_small | cuda | 40 | 30.0 % | 0.4462 | 4.8 % | 69.9 % | 32.5 % | 31.8 | 20.4 |
| all chips | affine | hard | raft_small_ft_r4 | cuda | 40 | 30.0 % | 0.3028 | 13.6 % | 84.9 % | 5.0 % | 17.2 | 20.0 |
| all chips | affine | hard | raft_small_ft_r8 | cuda | 40 | 30.0 % | 0.2496 | 20.2 % | 91.0 % | 0.0 % | 24.5 | 20.0 |
| all chips | affine | hard | raft_small_ft | cuda | 40 | 30.0 % | 0.2484 | 19.7 % | 91.2 % | 0.0 % | 31.8 | 20.0 |
| all chips | dense | clean | raft_r4 | cuda | 40 | 0.0 % | 0.0896 | 65.4 % | 100.0 % | 0.0 % | 39.2 | 43.4 |
| all chips | dense | clean | raft_r8 | cuda | 40 | 0.0 % | 0.0895 | 64.6 % | 100.0 % | 0.0 % | 45.6 | 43.4 |
| all chips | dense | clean | raft | cuda | 40 | 0.0 % | 0.0881 | 65.4 % | 100.0 % | 0.0 % | 48.3 | 43.4 |
| all chips | dense | clean | raft_ft_r4 | cuda | 40 | 0.0 % | 0.0758 | 74.9 % | 100.0 % | 0.0 % | 23.2 | 43.4 |
| all chips | dense | clean | raft_ft_r8 | cuda | 40 | 0.0 % | 0.0669 | 80.9 % | 100.0 % | 0.0 % | 34.7 | 43.4 |
| all chips | dense | clean | raft_ft | cuda | 40 | 0.0 % | 0.0650 | 82.1 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| all chips | dense | clean | raft_small_r4 | cuda | 40 | 0.0 % | 0.1915 | 21.8 % | 98.4 % | 0.0 % | 17.4 | 20.4 |
| all chips | dense | clean | raft_small_r8 | cuda | 40 | 0.0 % | 0.1664 | 28.6 % | 99.0 % | 0.0 % | 24.4 | 20.4 |
| all chips | dense | clean | raft_small | cuda | 40 | 0.0 % | 0.1632 | 29.2 % | 99.0 % | 0.0 % | 32.2 | 20.4 |
| all chips | dense | clean | raft_small_ft_r4 | cuda | 40 | 0.0 % | 0.1271 | 45.4 % | 99.7 % | 0.0 % | 17.2 | 20.0 |
| all chips | dense | clean | raft_small_ft_r8 | cuda | 40 | 0.0 % | 0.1251 | 48.4 % | 99.6 % | 0.0 % | 24.5 | 20.0 |
| all chips | dense | clean | raft_small_ft | cuda | 40 | 0.0 % | 0.1218 | 50.7 % | 99.6 % | 0.0 % | 31.7 | 20.0 |
| all chips | dense | mild | raft_r4 | cuda | 40 | 5.0 % | 0.1055 | 58.4 % | 99.8 % | 0.0 % | 22.3 | 43.4 |
| all chips | dense | mild | raft_r8 | cuda | 40 | 5.0 % | 0.1026 | 59.1 % | 99.9 % | 0.0 % | 34.9 | 43.4 |
| all chips | dense | mild | raft | cuda | 40 | 5.0 % | 0.1014 | 60.0 % | 99.9 % | 0.0 % | 46.4 | 43.4 |
| all chips | dense | mild | raft_ft_r4 | cuda | 40 | 5.0 % | 0.0867 | 69.0 % | 99.9 % | 0.0 % | 23.0 | 43.4 |
| all chips | dense | mild | raft_ft_r8 | cuda | 40 | 5.0 % | 0.0780 | 74.5 % | 99.9 % | 0.0 % | 34.7 | 43.4 |
| all chips | dense | mild | raft_ft | cuda | 40 | 5.0 % | 0.0761 | 76.2 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| all chips | dense | mild | raft_small_r4 | cuda | 40 | 5.0 % | 0.2575 | 19.1 % | 94.5 % | 0.0 % | 17.1 | 20.4 |
| all chips | dense | mild | raft_small_r8 | cuda | 40 | 5.0 % | 0.2071 | 27.7 % | 97.6 % | 0.0 % | 24.4 | 20.4 |
| all chips | dense | mild | raft_small | cuda | 40 | 5.0 % | 0.2035 | 28.3 % | 97.9 % | 0.0 % | 31.7 | 20.4 |
| all chips | dense | mild | raft_small_ft_r4 | cuda | 40 | 5.0 % | 0.1420 | 38.6 % | 99.4 % | 0.0 % | 17.0 | 20.0 |
| all chips | dense | mild | raft_small_ft_r8 | cuda | 40 | 5.0 % | 0.1408 | 41.1 % | 99.3 % | 0.0 % | 24.4 | 20.0 |
| all chips | dense | mild | raft_small_ft | cuda | 40 | 5.0 % | 0.1377 | 42.6 % | 99.3 % | 0.0 % | 31.9 | 20.0 |
| all chips | dense | hard | raft_r4 | cuda | 40 | 30.0 % | 0.4551 | 10.8 % | 80.1 % | 20.0 % | 22.7 | 43.4 |
| all chips | dense | hard | raft_r8 | cuda | 40 | 30.0 % | 0.2831 | 16.0 % | 91.7 % | 12.5 % | 34.9 | 43.4 |
| all chips | dense | hard | raft | cuda | 40 | 30.0 % | 0.2939 | 15.2 % | 91.7 % | 10.0 % | 46.5 | 43.4 |
| all chips | dense | hard | raft_ft_r4 | cuda | 40 | 30.0 % | 0.2057 | 22.7 % | 96.5 % | 0.0 % | 23.0 | 43.4 |
| all chips | dense | hard | raft_ft_r8 | cuda | 40 | 30.0 % | 0.2049 | 21.6 % | 96.2 % | 0.0 % | 34.9 | 43.4 |
| all chips | dense | hard | raft_ft | cuda | 40 | 30.0 % | 0.2035 | 22.8 % | 95.8 % | 0.0 % | 46.4 | 43.4 |
| all chips | dense | hard | raft_small_r4 | cuda | 40 | 30.0 % | 0.5355 | 5.7 % | 60.8 % | 92.5 % | 17.4 | 20.4 |
| all chips | dense | hard | raft_small_r8 | cuda | 40 | 30.0 % | 0.5055 | 6.5 % | 63.9 % | 45.0 % | 24.4 | 20.4 |
| all chips | dense | hard | raft_small | cuda | 40 | 30.0 % | 0.4915 | 4.9 % | 66.5 % | 27.5 % | 31.8 | 20.4 |
| all chips | dense | hard | raft_small_ft_r4 | cuda | 40 | 30.0 % | 0.3100 | 13.7 % | 84.6 % | 5.0 % | 17.1 | 20.0 |
| all chips | dense | hard | raft_small_ft_r8 | cuda | 40 | 30.0 % | 0.2857 | 17.1 % | 86.6 % | 0.0 % | 24.1 | 20.0 |
| all chips | dense | hard | raft_small_ft | cuda | 40 | 30.0 % | 0.2871 | 17.1 % | 86.1 % | 0.0 % | 31.9 | 20.0 |

By chip:

| site | scenario | degradation | method | device | pairs | clouds | EPE (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | translation | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0569 | 90.3 % | 100.0 % | 0.0 % | 22.4 | 43.4 |
| santerre | translation | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0412 | 96.8 % | 100.0 % | 0.0 % | 35.0 | 43.4 |
| santerre | translation | clean | raft | cuda | 10 | 0.0 % | 0.0381 | 97.6 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| santerre | translation | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0372 | 98.0 % | 100.0 % | 0.0 % | 23.2 | 43.4 |
| santerre | translation | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0293 | 99.4 % | 100.0 % | 0.0 % | 34.3 | 43.4 |
| santerre | translation | clean | raft_ft | cuda | 10 | 0.0 % | 0.0273 | 99.7 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| santerre | translation | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1698 | 26.0 % | 98.7 % | 0.0 % | 17.3 | 20.4 |
| santerre | translation | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1278 | 42.0 % | 99.7 % | 0.0 % | 24.5 | 20.4 |
| santerre | translation | clean | raft_small | cuda | 10 | 0.0 % | 0.1183 | 46.6 % | 99.8 % | 0.0 % | 31.9 | 20.4 |
| santerre | translation | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0776 | 73.6 % | 100.0 % | 0.0 % | 17.1 | 20.0 |
| santerre | translation | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0571 | 90.7 % | 100.0 % | 0.0 % | 24.6 | 20.0 |
| santerre | translation | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0546 | 91.6 % | 100.0 % | 0.0 % | 32.1 | 20.0 |
| santerre | translation | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0929 | 76.1 % | 99.3 % | 0.0 % | 22.3 | 43.4 |
| santerre | translation | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0560 | 93.1 % | 99.8 % | 0.0 % | 34.4 | 43.4 |
| santerre | translation | mild | raft | cuda | 10 | 5.0 % | 0.0464 | 94.9 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| santerre | translation | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0443 | 96.3 % | 100.0 % | 0.0 % | 22.8 | 43.4 |
| santerre | translation | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0348 | 99.4 % | 100.0 % | 0.0 % | 34.2 | 43.4 |
| santerre | translation | mild | raft_ft | cuda | 10 | 5.0 % | 0.0317 | 99.6 % | 100.0 % | 0.0 % | 45.7 | 43.4 |
| santerre | translation | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.3164 | 18.0 % | 92.6 % | 0.0 % | 17.4 | 20.4 |
| santerre | translation | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2282 | 34.0 % | 98.0 % | 0.0 % | 24.9 | 20.4 |
| santerre | translation | mild | raft_small | cuda | 10 | 5.0 % | 0.1819 | 43.2 % | 98.9 % | 10.0 % | 32.8 | 20.4 |
| santerre | translation | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.1063 | 54.4 % | 99.7 % | 0.0 % | 17.4 | 20.0 |
| santerre | translation | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0833 | 74.7 % | 100.0 % | 0.0 % | 24.7 | 20.0 |
| santerre | translation | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0807 | 76.0 % | 100.0 % | 0.0 % | 32.3 | 20.0 |
| santerre | translation | hard | raft_r4 | cuda | 10 | 30.0 % | 0.5421 | 7.2 % | 71.2 % | 10.0 % | 22.7 | 43.4 |
| santerre | translation | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2444 | 19.9 % | 94.9 % | 0.0 % | 34.8 | 43.4 |
| santerre | translation | hard | raft | cuda | 10 | 30.0 % | 0.1885 | 24.5 % | 98.6 % | 0.0 % | 46.0 | 43.4 |
| santerre | translation | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1303 | 41.4 % | 100.0 % | 0.0 % | 22.8 | 43.4 |
| santerre | translation | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1138 | 48.6 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| santerre | translation | hard | raft_ft | cuda | 10 | 30.0 % | 0.1132 | 48.9 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| santerre | translation | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.4 | 20.4 |
| santerre | translation | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.6109 | 1.7 % | 53.3 % | 50.0 % | 24.9 | 20.4 |
| santerre | translation | hard | raft_small | cuda | 10 | 30.0 % | 0.5098 | 3.4 % | 67.4 % | 20.0 % | 32.5 | 20.4 |
| santerre | translation | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.2699 | 15.2 % | 89.0 % | 0.0 % | 17.1 | 20.0 |
| santerre | translation | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.1510 | 34.0 % | 99.9 % | 0.0 % | 25.1 | 20.0 |
| santerre | translation | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.1399 | 37.6 % | 100.0 % | 0.0 % | 32.8 | 20.0 |
| santerre | affine | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0608 | 87.1 % | 100.0 % | 0.0 % | 26.2 | 43.4 |
| santerre | affine | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0496 | 93.4 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| santerre | affine | clean | raft | cuda | 10 | 0.0 % | 0.0468 | 94.6 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| santerre | affine | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0418 | 97.1 % | 100.0 % | 0.0 % | 23.0 | 43.4 |
| santerre | affine | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0353 | 98.5 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| santerre | affine | clean | raft_ft | cuda | 10 | 0.0 % | 0.0350 | 98.7 % | 100.0 % | 0.0 % | 46.2 | 43.4 |
| santerre | affine | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1685 | 26.2 % | 98.7 % | 0.0 % | 17.5 | 20.4 |
| santerre | affine | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1280 | 42.6 % | 99.7 % | 0.0 % | 24.7 | 20.4 |
| santerre | affine | clean | raft_small | cuda | 10 | 0.0 % | 0.1185 | 46.8 % | 99.8 % | 0.0 % | 32.6 | 20.4 |
| santerre | affine | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0850 | 69.7 % | 100.0 % | 0.0 % | 17.4 | 20.0 |
| santerre | affine | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0689 | 80.6 % | 100.0 % | 0.0 % | 25.5 | 20.0 |
| santerre | affine | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0634 | 84.3 % | 100.0 % | 0.0 % | 32.9 | 20.0 |
| santerre | affine | mild | raft_r4 | cuda | 10 | 5.0 % | 0.1025 | 72.9 % | 99.3 % | 0.0 % | 22.5 | 43.4 |
| santerre | affine | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0709 | 87.4 % | 99.8 % | 0.0 % | 34.8 | 43.4 |
| santerre | affine | mild | raft | cuda | 10 | 5.0 % | 0.0667 | 89.1 % | 99.8 % | 0.0 % | 46.3 | 43.4 |
| santerre | affine | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0506 | 93.8 % | 100.0 % | 0.0 % | 23.0 | 43.4 |
| santerre | affine | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0439 | 96.1 % | 100.0 % | 0.0 % | 34.6 | 43.4 |
| santerre | affine | mild | raft_ft | cuda | 10 | 5.0 % | 0.0411 | 97.8 % | 100.0 % | 0.0 % | 46.2 | 43.4 |
| santerre | affine | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.3150 | 17.1 % | 92.6 % | 0.0 % | 17.3 | 20.4 |
| santerre | affine | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2069 | 31.7 % | 98.0 % | 0.0 % | 25.0 | 20.4 |
| santerre | affine | mild | raft_small | cuda | 10 | 5.0 % | 0.2414 | 37.8 % | 98.4 % | 0.0 % | 33.2 | 20.4 |
| santerre | affine | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.1114 | 52.1 % | 99.8 % | 0.0 % | 17.4 | 20.0 |
| santerre | affine | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0966 | 60.2 % | 100.0 % | 0.0 % | 24.8 | 20.0 |
| santerre | affine | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0915 | 65.2 % | 100.0 % | 0.0 % | 32.3 | 20.0 |
| santerre | affine | hard | raft_r4 | cuda | 10 | 30.0 % | 0.5459 | 6.9 % | 70.5 % | 10.0 % | 23.3 | 43.4 |
| santerre | affine | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2571 | 18.7 % | 94.9 % | 0.0 % | 34.6 | 43.4 |
| santerre | affine | hard | raft | cuda | 10 | 30.0 % | 0.2132 | 18.7 % | 98.3 % | 0.0 % | 46.7 | 43.4 |
| santerre | affine | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1624 | 28.2 % | 99.6 % | 0.0 % | 23.0 | 43.4 |
| santerre | affine | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1488 | 31.4 % | 100.0 % | 0.0 % | 34.5 | 43.4 |
| santerre | affine | hard | raft_ft | cuda | 10 | 30.0 % | 0.1451 | 33.6 % | 100.0 % | 0.0 % | 46.5 | 43.4 |
| santerre | affine | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.4 | 20.4 |
| santerre | affine | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.6345 | 1.6 % | 52.2 % | 50.0 % | 25.3 | 20.4 |
| santerre | affine | hard | raft_small | cuda | 10 | 30.0 % | 0.5303 | 2.9 % | 65.6 % | 20.0 % | 32.5 | 20.4 |
| santerre | affine | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.2853 | 13.7 % | 87.1 % | 0.0 % | 17.5 | 20.0 |
| santerre | affine | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.1880 | 24.8 % | 98.9 % | 0.0 % | 25.3 | 20.0 |
| santerre | affine | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.1754 | 28.5 % | 99.8 % | 0.0 % | 32.7 | 20.0 |
| santerre | dense | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0866 | 67.9 % | 100.0 % | 0.0 % | 39.0 | 43.4 |
| santerre | dense | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0874 | 66.6 % | 100.0 % | 0.0 % | 48.5 | 43.4 |
| santerre | dense | clean | raft | cuda | 10 | 0.0 % | 0.0863 | 67.1 % | 100.0 % | 0.0 % | 48.5 | 43.4 |
| santerre | dense | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0805 | 71.5 % | 100.0 % | 0.0 % | 23.0 | 43.4 |
| santerre | dense | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0735 | 77.0 % | 100.0 % | 0.0 % | 34.4 | 43.4 |
| santerre | dense | clean | raft_ft | cuda | 10 | 0.0 % | 0.0711 | 78.4 % | 100.0 % | 0.0 % | 46.5 | 43.4 |
| santerre | dense | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1826 | 23.0 % | 98.4 % | 0.0 % | 17.2 | 20.4 |
| santerre | dense | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1525 | 32.6 % | 99.2 % | 0.0 % | 24.8 | 20.4 |
| santerre | dense | clean | raft_small | cuda | 10 | 0.0 % | 0.1461 | 35.4 % | 99.3 % | 0.0 % | 32.9 | 20.4 |
| santerre | dense | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.1258 | 44.4 % | 100.0 % | 0.0 % | 17.4 | 20.0 |
| santerre | dense | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.1227 | 49.1 % | 99.9 % | 0.0 % | 25.0 | 20.0 |
| santerre | dense | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.1209 | 50.1 % | 99.8 % | 0.0 % | 32.1 | 20.0 |
| santerre | dense | mild | raft_r4 | cuda | 10 | 5.0 % | 0.1184 | 54.1 % | 99.3 % | 0.0 % | 22.1 | 43.4 |
| santerre | dense | mild | raft_r8 | cuda | 10 | 5.0 % | 0.1055 | 58.0 % | 99.9 % | 0.0 % | 34.6 | 43.4 |
| santerre | dense | mild | raft | cuda | 10 | 5.0 % | 0.1039 | 58.5 % | 99.9 % | 0.0 % | 46.2 | 43.4 |
| santerre | dense | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0930 | 66.1 % | 100.0 % | 0.0 % | 23.2 | 43.4 |
| santerre | dense | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0852 | 71.0 % | 99.9 % | 0.0 % | 34.4 | 43.4 |
| santerre | dense | mild | raft_ft | cuda | 10 | 5.0 % | 0.0821 | 72.6 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| santerre | dense | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.3150 | 16.6 % | 92.7 % | 0.0 % | 17.1 | 20.4 |
| santerre | dense | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2164 | 29.3 % | 96.6 % | 0.0 % | 24.6 | 20.4 |
| santerre | dense | mild | raft_small | cuda | 10 | 5.0 % | 0.2207 | 32.4 % | 97.1 % | 0.0 % | 32.4 | 20.4 |
| santerre | dense | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.1509 | 33.5 % | 99.5 % | 0.0 % | 17.2 | 20.0 |
| santerre | dense | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.1488 | 36.8 % | 99.5 % | 0.0 % | 24.7 | 20.0 |
| santerre | dense | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.1456 | 36.9 % | 99.5 % | 0.0 % | 32.3 | 20.0 |
| santerre | dense | hard | raft_r4 | cuda | 10 | 30.0 % | 0.5302 | 6.5 % | 73.3 % | 0.0 % | 23.1 | 43.4 |
| santerre | dense | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2856 | 10.2 % | 91.3 % | 0.0 % | 34.6 | 43.4 |
| santerre | dense | hard | raft | cuda | 10 | 30.0 % | 0.2578 | 11.7 % | 94.0 % | 0.0 % | 46.4 | 43.4 |
| santerre | dense | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1940 | 24.2 % | 97.8 % | 0.0 % | 23.1 | 43.4 |
| santerre | dense | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1902 | 19.4 % | 98.9 % | 0.0 % | 35.0 | 43.4 |
| santerre | dense | hard | raft_ft | cuda | 10 | 30.0 % | 0.1888 | 19.8 % | 99.1 % | 0.0 % | 46.6 | 43.4 |
| santerre | dense | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.4 | 20.4 |
| santerre | dense | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.5952 | 3.2 % | 53.9 % | 50.0 % | 24.8 | 20.4 |
| santerre | dense | hard | raft_small | cuda | 10 | 30.0 % | 0.5396 | 3.9 % | 67.6 % | 20.0 % | 32.3 | 20.4 |
| santerre | dense | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.2913 | 12.3 % | 87.7 % | 0.0 % | 17.2 | 20.0 |
| santerre | dense | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.2268 | 17.8 % | 94.4 % | 0.0 % | 24.6 | 20.0 |
| santerre | dense | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.2202 | 21.1 % | 94.9 % | 0.0 % | 32.5 | 20.0 |
| lyon | translation | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0586 | 89.7 % | 100.0 % | 0.0 % | 23.1 | 43.4 |
| lyon | translation | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0511 | 93.7 % | 100.0 % | 0.0 % | 35.6 | 43.4 |
| lyon | translation | clean | raft | cuda | 10 | 0.0 % | 0.0495 | 94.1 % | 100.0 % | 0.0 % | 47.0 | 43.4 |
| lyon | translation | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0337 | 99.3 % | 100.0 % | 0.0 % | 23.7 | 43.4 |
| lyon | translation | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0264 | 100.0 % | 100.0 % | 0.0 % | 35.4 | 43.4 |
| lyon | translation | clean | raft_ft | cuda | 10 | 0.0 % | 0.0244 | 100.0 % | 100.0 % | 0.0 % | 46.7 | 43.4 |
| lyon | translation | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1892 | 18.4 % | 99.0 % | 0.0 % | 17.4 | 20.4 |
| lyon | translation | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1633 | 24.4 % | 99.8 % | 0.0 % | 24.5 | 20.4 |
| lyon | translation | clean | raft_small | cuda | 10 | 0.0 % | 0.1583 | 25.8 % | 99.9 % | 0.0 % | 32.1 | 20.4 |
| lyon | translation | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0835 | 68.4 % | 100.0 % | 0.0 % | 17.3 | 20.0 |
| lyon | translation | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0744 | 77.6 % | 100.0 % | 0.0 % | 24.7 | 20.0 |
| lyon | translation | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0710 | 79.7 % | 100.0 % | 0.0 % | 32.4 | 20.0 |
| lyon | translation | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0611 | 86.9 % | 100.0 % | 0.0 % | 22.9 | 43.4 |
| lyon | translation | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0515 | 93.6 % | 100.0 % | 0.0 % | 35.2 | 43.4 |
| lyon | translation | mild | raft | cuda | 10 | 5.0 % | 0.0505 | 94.0 % | 100.0 % | 0.0 % | 46.8 | 43.4 |
| lyon | translation | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0352 | 98.0 % | 100.0 % | 0.0 % | 23.6 | 43.4 |
| lyon | translation | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0280 | 99.4 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| lyon | translation | mild | raft_ft | cuda | 10 | 5.0 % | 0.0261 | 99.6 % | 100.0 % | 0.0 % | 46.9 | 43.4 |
| lyon | translation | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.1952 | 19.2 % | 97.8 % | 0.0 % | 17.5 | 20.4 |
| lyon | translation | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.1563 | 27.8 % | 99.7 % | 0.0 % | 25.3 | 20.4 |
| lyon | translation | mild | raft_small | cuda | 10 | 5.0 % | 0.1494 | 28.8 % | 99.8 % | 0.0 % | 32.4 | 20.4 |
| lyon | translation | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.0895 | 64.3 % | 100.0 % | 0.0 % | 17.5 | 20.0 |
| lyon | translation | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0786 | 71.7 % | 100.0 % | 0.0 % | 24.5 | 20.0 |
| lyon | translation | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0747 | 73.9 % | 100.0 % | 0.0 % | 31.9 | 20.0 |
| lyon | translation | hard | raft_r4 | cuda | 10 | 30.0 % | 0.3031 | 14.8 % | 90.9 % | 0.0 % | 22.5 | 43.4 |
| lyon | translation | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2040 | 28.7 % | 99.1 % | 0.0 % | 35.1 | 43.4 |
| lyon | translation | hard | raft | cuda | 10 | 30.0 % | 0.1912 | 30.8 % | 99.7 % | 0.0 % | 46.9 | 43.4 |
| lyon | translation | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1250 | 51.1 % | 98.3 % | 0.0 % | 23.2 | 43.4 |
| lyon | translation | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1173 | 49.4 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| lyon | translation | hard | raft_ft | cuda | 10 | 30.0 % | 0.1132 | 50.2 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| lyon | translation | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.1 | 20.4 |
| lyon | translation | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.4567 | 6.8 % | 69.3 % | 0.0 % | 23.9 | 20.4 |
| lyon | translation | hard | raft_small | cuda | 10 | 30.0 % | 0.3500 | 6.8 % | 82.1 % | 0.0 % | 31.7 | 20.4 |
| lyon | translation | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.2389 | 14.9 % | 93.2 % | 0.0 % | 16.9 | 20.0 |
| lyon | translation | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.1498 | 32.6 % | 100.0 % | 0.0 % | 24.1 | 20.0 |
| lyon | translation | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.1376 | 36.5 % | 100.0 % | 0.0 % | 32.0 | 20.0 |
| lyon | affine | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0620 | 84.9 % | 100.0 % | 0.0 % | 26.3 | 43.4 |
| lyon | affine | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0558 | 88.3 % | 100.0 % | 0.0 % | 35.8 | 43.4 |
| lyon | affine | clean | raft | cuda | 10 | 0.0 % | 0.0530 | 88.6 % | 100.0 % | 0.0 % | 47.0 | 43.4 |
| lyon | affine | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0429 | 95.4 % | 100.0 % | 0.0 % | 23.6 | 43.4 |
| lyon | affine | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0343 | 98.3 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| lyon | affine | clean | raft_ft | cuda | 10 | 0.0 % | 0.0309 | 99.1 % | 100.0 % | 0.0 % | 47.1 | 43.4 |
| lyon | affine | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1875 | 18.7 % | 99.0 % | 0.0 % | 17.6 | 20.4 |
| lyon | affine | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1600 | 25.9 % | 99.8 % | 0.0 % | 24.8 | 20.4 |
| lyon | affine | clean | raft_small | cuda | 10 | 0.0 % | 0.1556 | 26.2 % | 99.9 % | 0.0 % | 32.2 | 20.4 |
| lyon | affine | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0913 | 63.8 % | 100.0 % | 0.0 % | 17.2 | 20.0 |
| lyon | affine | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0838 | 69.8 % | 100.0 % | 0.0 % | 24.5 | 20.0 |
| lyon | affine | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0768 | 73.6 % | 100.0 % | 0.0 % | 32.1 | 20.0 |
| lyon | affine | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0656 | 81.8 % | 100.0 % | 0.0 % | 22.6 | 43.4 |
| lyon | affine | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0574 | 86.9 % | 100.0 % | 0.0 % | 35.2 | 43.4 |
| lyon | affine | mild | raft | cuda | 10 | 5.0 % | 0.0549 | 87.8 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| lyon | affine | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0472 | 92.7 % | 100.0 % | 0.0 % | 23.5 | 43.4 |
| lyon | affine | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0371 | 96.6 % | 100.0 % | 0.0 % | 35.2 | 43.4 |
| lyon | affine | mild | raft_ft | cuda | 10 | 5.0 % | 0.0352 | 96.6 % | 100.0 % | 0.0 % | 46.8 | 43.4 |
| lyon | affine | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.1933 | 20.3 % | 97.7 % | 0.0 % | 17.3 | 20.4 |
| lyon | affine | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.1534 | 29.6 % | 99.8 % | 0.0 % | 24.7 | 20.4 |
| lyon | affine | mild | raft_small | cuda | 10 | 5.0 % | 0.1465 | 30.8 % | 99.9 % | 0.0 % | 31.9 | 20.4 |
| lyon | affine | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.0976 | 60.0 % | 100.0 % | 0.0 % | 17.3 | 20.0 |
| lyon | affine | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0896 | 65.3 % | 100.0 % | 0.0 % | 24.4 | 20.0 |
| lyon | affine | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0849 | 67.8 % | 100.0 % | 0.0 % | 31.9 | 20.0 |
| lyon | affine | hard | raft_r4 | cuda | 10 | 30.0 % | 0.3135 | 14.4 % | 90.0 % | 0.0 % | 22.8 | 43.4 |
| lyon | affine | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2266 | 22.2 % | 98.9 % | 0.0 % | 35.3 | 43.4 |
| lyon | affine | hard | raft | cuda | 10 | 30.0 % | 0.2249 | 21.5 % | 99.1 % | 0.0 % | 47.0 | 43.4 |
| lyon | affine | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1544 | 36.3 % | 98.2 % | 0.0 % | 23.4 | 43.4 |
| lyon | affine | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1440 | 33.0 % | 99.8 % | 0.0 % | 34.9 | 43.4 |
| lyon | affine | hard | raft_ft | cuda | 10 | 30.0 % | 0.1335 | 39.2 % | 99.9 % | 0.0 % | 46.7 | 43.4 |
| lyon | affine | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.3 | 20.4 |
| lyon | affine | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.4466 | 7.3 % | 68.7 % | 0.0 % | 24.6 | 20.4 |
| lyon | affine | hard | raft_small | cuda | 10 | 30.0 % | 0.3533 | 7.6 % | 80.7 % | 0.0 % | 31.8 | 20.4 |
| lyon | affine | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.2335 | 18.4 % | 93.8 % | 0.0 % | 17.2 | 20.0 |
| lyon | affine | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.1731 | 30.9 % | 98.9 % | 0.0 % | 24.7 | 20.0 |
| lyon | affine | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.1678 | 30.8 % | 99.5 % | 0.0 % | 31.8 | 20.0 |
| lyon | dense | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0913 | 64.1 % | 100.0 % | 0.0 % | 39.6 | 43.4 |
| lyon | dense | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0874 | 63.8 % | 100.0 % | 0.0 % | 44.4 | 43.4 |
| lyon | dense | clean | raft | cuda | 10 | 0.0 % | 0.0848 | 65.3 % | 100.0 % | 0.0 % | 49.0 | 43.4 |
| lyon | dense | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0644 | 82.9 % | 100.0 % | 0.0 % | 23.5 | 43.4 |
| lyon | dense | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0586 | 87.0 % | 100.0 % | 0.0 % | 34.7 | 43.4 |
| lyon | dense | clean | raft_ft | cuda | 10 | 0.0 % | 0.0577 | 87.7 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| lyon | dense | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1986 | 18.7 % | 98.1 % | 0.0 % | 17.4 | 20.4 |
| lyon | dense | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1806 | 24.5 % | 98.2 % | 0.0 % | 24.5 | 20.4 |
| lyon | dense | clean | raft_small | cuda | 10 | 0.0 % | 0.1796 | 24.6 % | 98.2 % | 0.0 % | 32.3 | 20.4 |
| lyon | dense | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.1253 | 45.6 % | 99.4 % | 0.0 % | 17.3 | 20.0 |
| lyon | dense | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.1206 | 49.3 % | 99.2 % | 0.0 % | 24.8 | 20.0 |
| lyon | dense | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.1140 | 54.1 % | 99.2 % | 0.0 % | 31.9 | 20.0 |
| lyon | dense | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0982 | 61.3 % | 100.0 % | 0.0 % | 22.6 | 43.4 |
| lyon | dense | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0947 | 62.7 % | 100.0 % | 0.0 % | 35.3 | 43.4 |
| lyon | dense | mild | raft | cuda | 10 | 5.0 % | 0.0916 | 64.1 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| lyon | dense | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0726 | 77.2 % | 100.0 % | 0.0 % | 23.1 | 43.4 |
| lyon | dense | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0639 | 82.7 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| lyon | dense | mild | raft_ft | cuda | 10 | 5.0 % | 0.0637 | 83.3 % | 100.0 % | 0.0 % | 47.0 | 43.4 |
| lyon | dense | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2072 | 19.9 % | 97.0 % | 0.0 % | 17.7 | 20.4 |
| lyon | dense | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.1820 | 26.7 % | 98.3 % | 0.0 % | 24.8 | 20.4 |
| lyon | dense | mild | raft_small | cuda | 10 | 5.0 % | 0.1790 | 25.4 % | 98.3 % | 0.0 % | 32.3 | 20.4 |
| lyon | dense | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.1340 | 42.5 % | 99.3 % | 0.0 % | 17.4 | 20.0 |
| lyon | dense | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.1308 | 46.0 % | 99.0 % | 0.0 % | 24.7 | 20.0 |
| lyon | dense | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.1261 | 47.5 % | 99.1 % | 0.0 % | 32.0 | 20.0 |
| lyon | dense | hard | raft_r4 | cuda | 10 | 30.0 % | 0.2647 | 13.8 % | 94.4 % | 0.0 % | 22.7 | 43.4 |
| lyon | dense | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2287 | 22.5 % | 97.3 % | 0.0 % | 35.0 | 43.4 |
| lyon | dense | hard | raft | cuda | 10 | 30.0 % | 0.2320 | 21.2 % | 96.4 % | 0.0 % | 46.7 | 43.4 |
| lyon | dense | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1773 | 28.0 % | 98.6 % | 0.0 % | 23.1 | 43.4 |
| lyon | dense | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1716 | 27.3 % | 98.9 % | 0.0 % | 34.9 | 43.4 |
| lyon | dense | hard | raft_ft | cuda | 10 | 30.0 % | 0.1712 | 28.9 % | 98.7 % | 0.0 % | 46.8 | 43.4 |
| lyon | dense | hard | raft_small_r4 | cuda | 10 | 30.0 % | 0.4706 | 4.5 % | 62.2 % | 90.0 % | 18.0 | 20.4 |
| lyon | dense | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.4178 | 8.9 % | 71.7 % | 0.0 % | 24.5 | 20.4 |
| lyon | dense | hard | raft_small | cuda | 10 | 30.0 % | 0.3572 | 7.2 % | 80.2 % | 0.0 % | 31.9 | 20.4 |
| lyon | dense | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.2421 | 19.2 % | 92.9 % | 0.0 % | 17.2 | 20.0 |
| lyon | dense | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.2126 | 25.4 % | 96.1 % | 0.0 % | 24.1 | 20.0 |
| lyon | dense | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.2173 | 24.8 % | 95.8 % | 0.0 % | 32.2 | 20.0 |
| morvan | translation | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0591 | 89.1 % | 100.0 % | 0.0 % | 23.0 | 43.4 |
| morvan | translation | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0481 | 95.7 % | 100.0 % | 0.0 % | 35.0 | 43.4 |
| morvan | translation | clean | raft | cuda | 10 | 0.0 % | 0.0469 | 96.6 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| morvan | translation | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0368 | 99.0 % | 100.0 % | 0.0 % | 23.4 | 43.4 |
| morvan | translation | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0280 | 100.0 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| morvan | translation | clean | raft_ft | cuda | 10 | 0.0 % | 0.0268 | 100.0 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| morvan | translation | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1955 | 19.6 % | 98.8 % | 0.0 % | 16.9 | 20.4 |
| morvan | translation | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1459 | 30.7 % | 99.7 % | 0.0 % | 24.3 | 20.4 |
| morvan | translation | clean | raft_small | cuda | 10 | 0.0 % | 0.1375 | 33.4 % | 99.8 % | 0.0 % | 31.2 | 20.4 |
| morvan | translation | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0723 | 78.4 % | 100.0 % | 0.0 % | 17.1 | 20.0 |
| morvan | translation | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0546 | 90.3 % | 100.0 % | 0.0 % | 23.9 | 20.0 |
| morvan | translation | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0516 | 94.6 % | 100.0 % | 0.0 % | 31.5 | 20.0 |
| morvan | translation | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0757 | 81.1 % | 99.9 % | 0.0 % | 22.5 | 43.4 |
| morvan | translation | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0633 | 93.4 % | 99.9 % | 0.0 % | 34.8 | 43.4 |
| morvan | translation | mild | raft | cuda | 10 | 5.0 % | 0.0615 | 94.7 % | 99.9 % | 0.0 % | 46.5 | 43.4 |
| morvan | translation | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0396 | 97.5 % | 100.0 % | 0.0 % | 23.1 | 43.4 |
| morvan | translation | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0317 | 99.3 % | 100.0 % | 0.0 % | 34.8 | 43.4 |
| morvan | translation | mild | raft_ft | cuda | 10 | 5.0 % | 0.0307 | 99.9 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| morvan | translation | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2897 | 16.6 % | 93.5 % | 0.0 % | 17.3 | 20.4 |
| morvan | translation | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2135 | 28.9 % | 97.6 % | 0.0 % | 24.0 | 20.4 |
| morvan | translation | mild | raft_small | cuda | 10 | 5.0 % | 0.1952 | 34.5 % | 98.3 % | 0.0 % | 31.3 | 20.4 |
| morvan | translation | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.0836 | 70.0 % | 100.0 % | 0.0 % | 16.9 | 20.0 |
| morvan | translation | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0606 | 85.5 % | 100.0 % | 0.0 % | 23.9 | 20.0 |
| morvan | translation | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0568 | 87.2 % | 100.0 % | 0.0 % | 31.1 | 20.0 |
| morvan | translation | hard | raft_r4 | cuda | 10 | 30.0 % | 0.5988 | 10.3 % | 68.5 % | 30.0 % | 22.5 | 43.4 |
| morvan | translation | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2407 | 23.1 % | 89.8 % | 10.0 % | 34.8 | 43.4 |
| morvan | translation | hard | raft | cuda | 10 | 30.0 % | 0.2072 | 26.1 % | 93.0 % | 10.0 % | 46.8 | 43.4 |
| morvan | translation | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1321 | 39.4 % | 100.0 % | 0.0 % | 23.2 | 43.4 |
| morvan | translation | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1047 | 53.2 % | 100.0 % | 0.0 % | 35.0 | 43.4 |
| morvan | translation | hard | raft_ft | cuda | 10 | 30.0 % | 0.1032 | 53.5 % | 100.0 % | 0.0 % | 46.5 | 43.4 |
| morvan | translation | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.2 | 20.4 |
| morvan | translation | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.7168 | 6.1 % | 40.5 % | 80.0 % | 24.0 | 20.4 |
| morvan | translation | hard | raft_small | cuda | 10 | 30.0 % | 0.6065 | 1.7 % | 47.2 % | 40.0 % | 32.0 | 20.4 |
| morvan | translation | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.3365 | 8.7 % | 82.0 % | 0.0 % | 16.7 | 20.0 |
| morvan | translation | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.2134 | 13.6 % | 99.6 % | 0.0 % | 24.1 | 20.0 |
| morvan | translation | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.2150 | 14.3 % | 98.4 % | 0.0 % | 31.4 | 20.0 |
| morvan | affine | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0639 | 85.8 % | 100.0 % | 0.0 % | 25.7 | 43.4 |
| morvan | affine | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0549 | 92.5 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| morvan | affine | clean | raft | cuda | 10 | 0.0 % | 0.0532 | 93.8 % | 100.0 % | 0.0 % | 46.7 | 43.4 |
| morvan | affine | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0436 | 96.2 % | 100.0 % | 0.0 % | 23.5 | 43.4 |
| morvan | affine | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0334 | 99.7 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| morvan | affine | clean | raft_ft | cuda | 10 | 0.0 % | 0.0315 | 99.8 % | 100.0 % | 0.0 % | 46.7 | 43.4 |
| morvan | affine | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1964 | 19.9 % | 98.6 % | 0.0 % | 16.9 | 20.4 |
| morvan | affine | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1488 | 30.2 % | 99.5 % | 0.0 % | 24.4 | 20.4 |
| morvan | affine | clean | raft_small | cuda | 10 | 0.0 % | 0.1411 | 31.4 % | 99.7 % | 0.0 % | 31.6 | 20.4 |
| morvan | affine | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0844 | 70.2 % | 100.0 % | 0.0 % | 17.0 | 20.0 |
| morvan | affine | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0716 | 80.5 % | 100.0 % | 0.0 % | 24.3 | 20.0 |
| morvan | affine | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0666 | 84.4 % | 100.0 % | 0.0 % | 31.4 | 20.0 |
| morvan | affine | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0810 | 77.5 % | 99.9 % | 0.0 % | 22.4 | 43.4 |
| morvan | affine | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0704 | 87.9 % | 99.9 % | 0.0 % | 34.5 | 43.4 |
| morvan | affine | mild | raft | cuda | 10 | 5.0 % | 0.0689 | 90.6 % | 99.9 % | 0.0 % | 46.5 | 43.4 |
| morvan | affine | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0471 | 94.1 % | 100.0 % | 0.0 % | 23.2 | 43.4 |
| morvan | affine | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0363 | 98.3 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| morvan | affine | mild | raft_ft | cuda | 10 | 5.0 % | 0.0345 | 99.5 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| morvan | affine | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2826 | 17.7 % | 93.2 % | 0.0 % | 16.7 | 20.4 |
| morvan | affine | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2113 | 31.3 % | 97.7 % | 0.0 % | 24.1 | 20.4 |
| morvan | affine | mild | raft_small | cuda | 10 | 5.0 % | 0.1866 | 36.4 % | 98.5 % | 0.0 % | 31.4 | 20.4 |
| morvan | affine | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.0920 | 62.4 % | 100.0 % | 0.0 % | 16.8 | 20.0 |
| morvan | affine | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0782 | 70.6 % | 100.0 % | 0.0 % | 24.2 | 20.0 |
| morvan | affine | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0734 | 76.6 % | 100.0 % | 0.0 % | 31.1 | 20.0 |
| morvan | affine | hard | raft_r4 | cuda | 10 | 30.0 % | 0.6006 | 10.1 % | 68.4 % | 30.0 % | 22.5 | 43.4 |
| morvan | affine | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2514 | 20.9 % | 88.6 % | 10.0 % | 35.2 | 43.4 |
| morvan | affine | hard | raft | cuda | 10 | 30.0 % | 0.2284 | 25.4 % | 91.0 % | 10.0 % | 46.8 | 43.4 |
| morvan | affine | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1487 | 32.2 % | 99.9 % | 0.0 % | 23.3 | 43.4 |
| morvan | affine | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1414 | 32.7 % | 100.0 % | 0.0 % | 35.1 | 43.4 |
| morvan | affine | hard | raft_ft | cuda | 10 | 30.0 % | 0.1377 | 34.0 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| morvan | affine | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.2 | 20.4 |
| morvan | affine | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.6769 | 6.6 % | 42.9 % | 80.0 % | 24.0 | 20.4 |
| morvan | affine | hard | raft_small | cuda | 10 | 30.0 % | 0.5666 | 2.4 % | 50.4 % | 50.0 % | 31.2 | 20.4 |
| morvan | affine | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.3404 | 8.8 % | 82.1 % | 0.0 % | 17.1 | 20.0 |
| morvan | affine | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.2597 | 11.9 % | 92.2 % | 0.0 % | 23.7 | 20.0 |
| morvan | affine | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.2729 | 8.9 % | 90.9 % | 0.0 % | 31.5 | 20.0 |
| morvan | dense | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0906 | 64.8 % | 100.0 % | 0.0 % | 39.0 | 43.4 |
| morvan | dense | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0930 | 63.7 % | 100.0 % | 0.0 % | 50.9 | 43.4 |
| morvan | dense | clean | raft | cuda | 10 | 0.0 % | 0.0923 | 64.4 % | 100.0 % | 0.0 % | 47.4 | 43.4 |
| morvan | dense | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0790 | 72.9 % | 100.0 % | 0.0 % | 23.3 | 43.4 |
| morvan | dense | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0663 | 81.4 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| morvan | dense | clean | raft_ft | cuda | 10 | 0.0 % | 0.0649 | 82.7 % | 100.0 % | 0.0 % | 46.3 | 43.4 |
| morvan | dense | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.2078 | 17.8 % | 98.3 % | 0.0 % | 17.3 | 20.4 |
| morvan | dense | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1726 | 25.4 % | 99.3 % | 0.0 % | 23.6 | 20.4 |
| morvan | dense | clean | raft_small | cuda | 10 | 0.0 % | 0.1681 | 26.4 % | 99.3 % | 0.0 % | 30.7 | 20.4 |
| morvan | dense | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.1291 | 44.9 % | 99.8 % | 0.0 % | 16.7 | 20.0 |
| morvan | dense | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.1280 | 46.6 % | 99.8 % | 0.0 % | 23.8 | 20.0 |
| morvan | dense | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.1256 | 48.5 % | 99.8 % | 0.0 % | 31.1 | 20.0 |
| morvan | dense | mild | raft_r4 | cuda | 10 | 5.0 % | 0.1039 | 59.3 % | 99.9 % | 0.0 % | 22.5 | 43.4 |
| morvan | dense | mild | raft_r8 | cuda | 10 | 5.0 % | 0.1067 | 58.5 % | 99.9 % | 0.0 % | 35.0 | 43.4 |
| morvan | dense | mild | raft | cuda | 10 | 5.0 % | 0.1068 | 59.3 % | 99.9 % | 0.0 % | 46.6 | 43.4 |
| morvan | dense | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0859 | 67.6 % | 100.0 % | 0.0 % | 23.0 | 43.4 |
| morvan | dense | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0766 | 73.7 % | 100.0 % | 0.0 % | 34.7 | 43.4 |
| morvan | dense | mild | raft_ft | cuda | 10 | 5.0 % | 0.0729 | 77.1 % | 100.0 % | 0.0 % | 46.2 | 43.4 |
| morvan | dense | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2692 | 17.5 % | 94.0 % | 0.0 % | 16.6 | 20.4 |
| morvan | dense | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2216 | 25.9 % | 97.9 % | 0.0 % | 23.5 | 20.4 |
| morvan | dense | mild | raft_small | cuda | 10 | 5.0 % | 0.2110 | 28.6 % | 98.4 % | 0.0 % | 31.1 | 20.4 |
| morvan | dense | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.1387 | 39.1 % | 99.8 % | 0.0 % | 16.7 | 20.0 |
| morvan | dense | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.1392 | 40.6 % | 99.8 % | 0.0 % | 23.7 | 20.0 |
| morvan | dense | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.1364 | 43.4 % | 99.8 % | 0.0 % | 31.4 | 20.0 |
| morvan | dense | hard | raft_r4 | cuda | 10 | 30.0 % | 0.5566 | 10.8 % | 71.9 % | 30.0 % | 22.7 | 43.4 |
| morvan | dense | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2908 | 13.6 % | 86.6 % | 10.0 % | 34.8 | 43.4 |
| morvan | dense | hard | raft | cuda | 10 | 30.0 % | 0.2854 | 11.8 % | 88.6 % | 10.0 % | 46.5 | 43.4 |
| morvan | dense | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.1958 | 20.6 % | 97.5 % | 0.0 % | 23.1 | 43.4 |
| morvan | dense | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1942 | 22.6 % | 97.5 % | 0.0 % | 34.7 | 43.4 |
| morvan | dense | hard | raft_ft | cuda | 10 | 30.0 % | 0.1910 | 24.7 % | 97.7 % | 0.0 % | 46.3 | 43.4 |
| morvan | dense | hard | raft_small_r4 | cuda | 10 | 30.0 % | n/a | n/a | n/a | 100.0 % | 17.2 | 20.4 |
| morvan | dense | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.8261 | 3.3 % | 36.1 % | 70.0 % | 24.1 | 20.4 |
| morvan | dense | hard | raft_small | cuda | 10 | 30.0 % | 0.6984 | 1.7 % | 39.1 % | 30.0 % | 30.9 | 20.4 |
| morvan | dense | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.3472 | 9.6 % | 82.1 % | 0.0 % | 16.7 | 20.0 |
| morvan | dense | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.2946 | 12.8 % | 88.7 % | 0.0 % | 23.9 | 20.0 |
| morvan | dense | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.3080 | 11.7 % | 84.7 % | 0.0 % | 31.3 | 20.0 |
| sete | translation | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0562 | 90.4 % | 100.0 % | 0.0 % | 22.8 | 43.4 |
| sete | translation | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0492 | 96.0 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| sete | translation | clean | raft | cuda | 10 | 0.0 % | 0.0474 | 97.3 % | 100.0 % | 0.0 % | 46.6 | 43.4 |
| sete | translation | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0425 | 96.4 % | 100.0 % | 0.0 % | 23.2 | 43.4 |
| sete | translation | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0344 | 98.9 % | 100.0 % | 0.0 % | 34.4 | 43.4 |
| sete | translation | clean | raft_ft | cuda | 10 | 0.0 % | 0.0338 | 99.2 % | 100.0 % | 0.0 % | 46.2 | 43.4 |
| sete | translation | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1624 | 32.8 % | 98.8 % | 0.0 % | 16.2 | 20.4 |
| sete | translation | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1340 | 39.6 % | 99.7 % | 0.0 % | 23.3 | 20.4 |
| sete | translation | clean | raft_small | cuda | 10 | 0.0 % | 0.1287 | 38.9 % | 99.9 % | 0.0 % | 31.2 | 20.4 |
| sete | translation | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0754 | 75.6 % | 100.0 % | 0.0 % | 16.3 | 20.0 |
| sete | translation | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0647 | 82.7 % | 100.0 % | 0.0 % | 23.1 | 20.0 |
| sete | translation | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0638 | 85.8 % | 100.0 % | 0.0 % | 31.5 | 20.0 |
| sete | translation | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0659 | 84.9 % | 100.0 % | 0.0 % | 22.1 | 43.4 |
| sete | translation | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0558 | 91.3 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| sete | translation | mild | raft | cuda | 10 | 5.0 % | 0.0538 | 93.0 % | 100.0 % | 0.0 % | 46.2 | 43.4 |
| sete | translation | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0480 | 90.2 % | 100.0 % | 0.0 % | 22.9 | 43.4 |
| sete | translation | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0399 | 93.5 % | 100.0 % | 0.0 % | 34.4 | 43.4 |
| sete | translation | mild | raft_ft | cuda | 10 | 5.0 % | 0.0394 | 95.3 % | 100.0 % | 0.0 % | 46.0 | 43.4 |
| sete | translation | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2383 | 22.9 % | 94.4 % | 0.0 % | 16.1 | 20.4 |
| sete | translation | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2022 | 29.2 % | 98.4 % | 0.0 % | 23.1 | 20.4 |
| sete | translation | mild | raft_small | cuda | 10 | 5.0 % | 0.1905 | 28.9 % | 99.1 % | 0.0 % | 30.3 | 20.4 |
| sete | translation | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.0913 | 61.9 % | 100.0 % | 0.0 % | 16.2 | 20.0 |
| sete | translation | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0800 | 72.9 % | 100.0 % | 0.0 % | 22.7 | 20.0 |
| sete | translation | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0744 | 77.7 % | 100.0 % | 0.0 % | 29.9 | 20.0 |
| sete | translation | hard | raft_r4 | cuda | 10 | 30.0 % | 0.3581 | 18.5 % | 79.8 % | 70.0 % | 22.3 | 43.4 |
| sete | translation | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2378 | 24.5 % | 94.9 % | 50.0 % | 34.8 | 43.4 |
| sete | translation | hard | raft | cuda | 10 | 30.0 % | 0.3459 | 25.2 % | 90.5 % | 40.0 % | 46.2 | 43.4 |
| sete | translation | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.2063 | 31.6 % | 92.9 % | 0.0 % | 23.1 | 43.4 |
| sete | translation | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.1815 | 30.7 % | 100.0 % | 0.0 % | 34.5 | 43.4 |
| sete | translation | hard | raft_ft | cuda | 10 | 30.0 % | 0.1770 | 31.2 % | 99.5 % | 0.0 % | 46.1 | 43.4 |
| sete | translation | hard | raft_small_r4 | cuda | 10 | 30.0 % | 0.8341 | 9.0 % | 65.3 % | 90.0 % | 17.0 | 20.4 |
| sete | translation | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.3993 | 10.2 % | 72.7 % | 60.0 % | 23.6 | 20.4 |
| sete | translation | hard | raft_small | cuda | 10 | 30.0 % | 0.3353 | 7.7 % | 78.2 % | 60.0 % | 30.4 | 20.4 |
| sete | translation | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.3491 | 16.7 % | 76.6 % | 20.0 % | 16.7 | 20.0 |
| sete | translation | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.3382 | 29.5 % | 72.3 % | 0.0 % | 22.9 | 20.0 |
| sete | translation | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.3225 | 32.9 % | 77.6 % | 0.0 % | 30.2 | 20.0 |
| sete | affine | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0614 | 85.9 % | 100.0 % | 0.0 % | 25.3 | 43.4 |
| sete | affine | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0562 | 91.0 % | 100.0 % | 0.0 % | 34.9 | 43.4 |
| sete | affine | clean | raft | cuda | 10 | 0.0 % | 0.0551 | 91.0 % | 100.0 % | 0.0 % | 46.7 | 43.4 |
| sete | affine | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0498 | 92.7 % | 100.0 % | 0.0 % | 22.9 | 43.4 |
| sete | affine | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0407 | 97.8 % | 100.0 % | 0.0 % | 34.4 | 43.4 |
| sete | affine | clean | raft_ft | cuda | 10 | 0.0 % | 0.0372 | 98.4 % | 100.0 % | 0.0 % | 46.4 | 43.4 |
| sete | affine | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1630 | 30.7 % | 99.0 % | 0.0 % | 16.5 | 20.4 |
| sete | affine | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1352 | 37.8 % | 99.8 % | 0.0 % | 23.7 | 20.4 |
| sete | affine | clean | raft_small | cuda | 10 | 0.0 % | 0.1307 | 37.1 % | 100.0 % | 0.0 % | 30.7 | 20.4 |
| sete | affine | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.0809 | 71.1 % | 100.0 % | 0.0 % | 16.6 | 20.0 |
| sete | affine | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.0717 | 77.1 % | 100.0 % | 0.0 % | 23.5 | 20.0 |
| sete | affine | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.0651 | 82.1 % | 100.0 % | 0.0 % | 32.8 | 20.0 |
| sete | affine | mild | raft_r4 | cuda | 10 | 5.0 % | 0.0713 | 79.9 % | 100.0 % | 0.0 % | 22.1 | 43.4 |
| sete | affine | mild | raft_r8 | cuda | 10 | 5.0 % | 0.0662 | 84.2 % | 100.0 % | 0.0 % | 34.6 | 43.4 |
| sete | affine | mild | raft | cuda | 10 | 5.0 % | 0.0654 | 85.1 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| sete | affine | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0580 | 84.6 % | 100.0 % | 0.0 % | 23.3 | 43.4 |
| sete | affine | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0508 | 87.7 % | 100.0 % | 0.0 % | 34.3 | 43.4 |
| sete | affine | mild | raft_ft | cuda | 10 | 5.0 % | 0.0479 | 89.5 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| sete | affine | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2375 | 22.8 % | 94.8 % | 0.0 % | 16.2 | 20.4 |
| sete | affine | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2024 | 29.8 % | 98.6 % | 0.0 % | 23.4 | 20.4 |
| sete | affine | mild | raft_small | cuda | 10 | 5.0 % | 0.1915 | 29.3 % | 99.3 % | 0.0 % | 30.4 | 20.4 |
| sete | affine | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.0945 | 60.0 % | 100.0 % | 0.0 % | 16.8 | 20.0 |
| sete | affine | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.0891 | 66.5 % | 100.0 % | 0.0 % | 23.8 | 20.0 |
| sete | affine | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.0806 | 72.2 % | 100.0 % | 0.0 % | 30.8 | 20.0 |
| sete | affine | hard | raft_r4 | cuda | 10 | 30.0 % | 0.3730 | 16.0 % | 80.1 % | 70.0 % | 22.3 | 43.4 |
| sete | affine | hard | raft_r8 | cuda | 10 | 30.0 % | 0.2797 | 17.4 % | 91.5 % | 50.0 % | 34.8 | 43.4 |
| sete | affine | hard | raft | cuda | 10 | 30.0 % | 0.4400 | 13.8 % | 83.2 % | 30.0 % | 46.5 | 43.4 |
| sete | affine | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.2372 | 21.4 % | 93.1 % | 0.0 % | 23.1 | 43.4 |
| sete | affine | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.2455 | 20.4 % | 92.8 % | 0.0 % | 34.8 | 43.4 |
| sete | affine | hard | raft_ft | cuda | 10 | 30.0 % | 0.2393 | 21.6 % | 93.1 % | 0.0 % | 46.3 | 43.4 |
| sete | affine | hard | raft_small_r4 | cuda | 10 | 30.0 % | 0.8002 | 8.5 % | 65.0 % | 90.0 % | 16.4 | 20.4 |
| sete | affine | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.4120 | 9.4 % | 71.5 % | 60.0 % | 23.9 | 20.4 |
| sete | affine | hard | raft_small | cuda | 10 | 30.0 % | 0.3594 | 5.0 % | 75.9 % | 60.0 % | 31.1 | 20.4 |
| sete | affine | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.3644 | 13.4 % | 74.7 % | 20.0 % | 16.6 | 20.0 |
| sete | affine | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.3776 | 13.3 % | 73.8 % | 0.0 % | 23.0 | 20.0 |
| sete | affine | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.3776 | 10.3 % | 74.4 % | 0.0 % | 30.2 | 20.0 |
| sete | dense | clean | raft_r4 | cuda | 10 | 0.0 % | 0.0898 | 65.0 % | 100.0 % | 0.0 % | 38.9 | 43.4 |
| sete | dense | clean | raft_r8 | cuda | 10 | 0.0 % | 0.0901 | 64.4 % | 100.0 % | 0.0 % | 41.9 | 43.4 |
| sete | dense | clean | raft | cuda | 10 | 0.0 % | 0.0892 | 64.8 % | 100.0 % | 0.0 % | 48.6 | 43.4 |
| sete | dense | clean | raft_ft_r4 | cuda | 10 | 0.0 % | 0.0794 | 72.3 % | 100.0 % | 0.0 % | 23.0 | 43.4 |
| sete | dense | clean | raft_ft_r8 | cuda | 10 | 0.0 % | 0.0691 | 78.0 % | 100.0 % | 0.0 % | 35.0 | 43.4 |
| sete | dense | clean | raft_ft | cuda | 10 | 0.0 % | 0.0665 | 79.7 % | 100.0 % | 0.0 % | 46.1 | 43.4 |
| sete | dense | clean | raft_small_r4 | cuda | 10 | 0.0 % | 0.1772 | 27.8 % | 98.8 % | 0.0 % | 17.4 | 20.4 |
| sete | dense | clean | raft_small_r8 | cuda | 10 | 0.0 % | 0.1598 | 32.1 % | 99.2 % | 0.0 % | 23.6 | 20.4 |
| sete | dense | clean | raft_small | cuda | 10 | 0.0 % | 0.1591 | 30.4 % | 99.3 % | 0.0 % | 31.1 | 20.4 |
| sete | dense | clean | raft_small_ft_r4 | cuda | 10 | 0.0 % | 0.1282 | 46.7 % | 99.7 % | 0.0 % | 16.9 | 20.0 |
| sete | dense | clean | raft_small_ft_r8 | cuda | 10 | 0.0 % | 0.1289 | 48.8 % | 99.5 % | 0.0 % | 24.1 | 20.0 |
| sete | dense | clean | raft_small_ft | cuda | 10 | 0.0 % | 0.1265 | 50.0 % | 99.6 % | 0.0 % | 31.0 | 20.0 |
| sete | dense | mild | raft_r4 | cuda | 10 | 5.0 % | 0.1016 | 59.0 % | 100.0 % | 0.0 % | 22.4 | 43.4 |
| sete | dense | mild | raft_r8 | cuda | 10 | 5.0 % | 0.1034 | 57.3 % | 100.0 % | 0.0 % | 34.2 | 43.4 |
| sete | dense | mild | raft | cuda | 10 | 5.0 % | 0.1033 | 58.4 % | 99.9 % | 0.0 % | 46.3 | 43.4 |
| sete | dense | mild | raft_ft_r4 | cuda | 10 | 5.0 % | 0.0955 | 65.3 % | 99.7 % | 0.0 % | 23.0 | 43.4 |
| sete | dense | mild | raft_ft_r8 | cuda | 10 | 5.0 % | 0.0864 | 70.5 % | 99.7 % | 0.0 % | 34.6 | 43.4 |
| sete | dense | mild | raft_ft | cuda | 10 | 5.0 % | 0.0854 | 71.6 % | 99.9 % | 0.0 % | 46.1 | 43.4 |
| sete | dense | mild | raft_small_r4 | cuda | 10 | 5.0 % | 0.2386 | 22.3 % | 94.2 % | 0.0 % | 16.6 | 20.4 |
| sete | dense | mild | raft_small_r8 | cuda | 10 | 5.0 % | 0.2084 | 28.8 % | 97.7 % | 0.0 % | 24.5 | 20.4 |
| sete | dense | mild | raft_small | cuda | 10 | 5.0 % | 0.2034 | 26.8 % | 97.9 % | 0.0 % | 30.7 | 20.4 |
| sete | dense | mild | raft_small_ft_r4 | cuda | 10 | 5.0 % | 0.1446 | 39.4 % | 99.1 % | 0.0 % | 16.6 | 20.0 |
| sete | dense | mild | raft_small_ft_r8 | cuda | 10 | 5.0 % | 0.1446 | 41.2 % | 99.0 % | 0.0 % | 23.6 | 20.0 |
| sete | dense | mild | raft_small_ft | cuda | 10 | 5.0 % | 0.1428 | 42.5 % | 99.0 % | 0.0 % | 30.0 | 20.0 |
| sete | dense | hard | raft_r4 | cuda | 10 | 30.0 % | 0.5437 | 13.7 % | 76.7 % | 50.0 % | 22.4 | 43.4 |
| sete | dense | hard | raft_r8 | cuda | 10 | 30.0 % | 0.3579 | 18.3 % | 90.6 % | 40.0 % | 34.5 | 43.4 |
| sete | dense | hard | raft | cuda | 10 | 30.0 % | 0.4448 | 16.2 % | 86.0 % | 30.0 % | 46.1 | 43.4 |
| sete | dense | hard | raft_ft_r4 | cuda | 10 | 30.0 % | 0.2558 | 17.9 % | 92.0 % | 0.0 % | 22.6 | 43.4 |
| sete | dense | hard | raft_ft_r8 | cuda | 10 | 30.0 % | 0.2634 | 17.1 % | 89.3 % | 0.0 % | 34.6 | 43.4 |
| sete | dense | hard | raft_ft | cuda | 10 | 30.0 % | 0.2628 | 17.8 % | 87.8 % | 0.0 % | 45.9 | 43.4 |
| sete | dense | hard | raft_small_r4 | cuda | 10 | 30.0 % | 0.5680 | 6.3 % | 60.0 % | 80.0 % | 16.3 | 20.4 |
| sete | dense | hard | raft_small_r8 | cuda | 10 | 30.0 % | 0.3724 | 7.3 % | 77.5 % | 60.0 % | 23.5 | 20.4 |
| sete | dense | hard | raft_small | cuda | 10 | 30.0 % | 0.3687 | 7.0 % | 78.0 % | 60.0 % | 30.3 | 20.4 |
| sete | dense | hard | raft_small_ft_r4 | cuda | 10 | 30.0 % | 0.3715 | 13.6 % | 73.5 % | 20.0 % | 16.8 | 20.0 |
| sete | dense | hard | raft_small_ft_r8 | cuda | 10 | 30.0 % | 0.4087 | 12.5 % | 67.0 % | 0.0 % | 23.4 | 20.0 |
| sete | dense | hard | raft_small_ft | cuda | 10 | 30.0 % | 0.4027 | 10.8 % | 68.8 % | 0.0 % | 30.3 | 20.0 |

Measured on Intel(R) Xeon(R) CPU @ 2.00GHz, 31 GiB, 4 CPUs, Linux-6.18.48+-x86_64-with-glibc2.35; GPU Tesla T4, 15 GiB, CUDA 12.8. Time is the median of 3 calls per pair, after 1 warm-up call(s) per method; memory is the peak held by CUDA tensors. Details in `context.json`.
