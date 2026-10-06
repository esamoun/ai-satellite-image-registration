Closure on real triplets, every triplet and window of a role's chips together:

| site | triplet | method | device | triplets | clouds | closure (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| validation chips | all | raft | mps | 241 | 0.0 % | 0.2093 | 57.7 % | 93.4 % | 32.4 % | 138.9 | n/a |
| validation chips | all | raft_ft_same_date | mps | 241 | 0.0 % | 0.1221 | 62.7 % | 97.1 % | 0.0 % | 139.9 | n/a |
| validation chips | all | raft_ft_cross_date | mps | 241 | 0.0 % | 0.1059 | 64.5 % | 98.5 % | 0.0 % | 139.9 | n/a |
| training chips | all | raft | mps | 507 | 0.0 % | 0.1354 | 75.0 % | 97.1 % | 28.2 % | 144.0 | n/a |
| training chips | all | raft_ft_same_date | mps | 507 | 0.0 % | 0.1092 | 71.6 % | 96.4 % | 3.4 % | 144.6 | n/a |
| training chips | all | raft_ft_cross_date | mps | 507 | 0.0 % | 0.0946 | 75.3 % | 97.4 % | 1.0 % | 145.0 | n/a |

Validation chips: santerre, lyon, morvan, sete. Training chips: champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava. Choices are made on the validation chips; the training chips are the ones a fine-tuned model has seen, and are reported, not chosen on. Each triplet of dates A < B < C is registered A to B, B to C and A to C on each 256 px window hidden at most 1 % on its three dates; the closure is the distance between A to B then B to C, and A to C, over pixels clear on all three. A triplet fails if a leg does, or if its mean closure exceeds 1.0 px; closure columns average the others. Time is the median of 1 call(s) per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O.

By chip and triplet:

| site | triplet | method | device | triplets | clouds | closure (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | days-anchor-season | raft | mps | 16 | 0.0 % | 0.9282 | 18.8 % | 72.9 % | 93.8 % | 137.3 | n/a |
| santerre | days-anchor-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.0765 | 73.3 % | 100.0 % | 0.0 % | 137.7 | n/a |
| santerre | days-anchor-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0729 | 77.8 % | 100.0 % | 0.0 % | 137.6 | n/a |
| santerre | days-anchor-year | raft | mps | 14 | 0.1 % | 0.8687 | 16.4 % | 71.9 % | 85.7 % | 141.1 | n/a |
| santerre | days-anchor-year | raft_ft_same_date | mps | 14 | 0.1 % | 0.0757 | 81.5 % | 100.0 % | 0.0 % | 141.4 | n/a |
| santerre | days-anchor-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.0600 | 89.8 % | 100.0 % | 0.0 % | 140.7 | n/a |
| santerre | days-season-year | raft | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 139.6 | n/a |
| santerre | days-season-year | raft_ft_same_date | mps | 14 | 0.1 % | 0.2574 | 16.9 % | 93.0 % | 0.0 % | 140.1 | n/a |
| santerre | days-season-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.1865 | 23.5 % | 96.6 % | 0.0 % | 140.0 | n/a |
| santerre | anchor-season-year | raft | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 138.6 | n/a |
| santerre | anchor-season-year | raft_ft_same_date | mps | 14 | 0.1 % | 0.2290 | 18.8 % | 96.1 % | 0.0 % | 138.6 | n/a |
| santerre | anchor-season-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.1627 | 36.9 % | 98.5 % | 0.0 % | 139.8 | n/a |
| lyon | anchor-days-season | raft | mps | 14 | 0.1 % | 0.0427 | 96.9 % | 99.7 % | 0.0 % | 139.5 | n/a |
| lyon | anchor-days-season | raft_ft_same_date | mps | 14 | 0.1 % | 0.0277 | 99.9 % | 100.0 % | 0.0 % | 142.3 | n/a |
| lyon | anchor-days-season | raft_ft_cross_date | mps | 14 | 0.1 % | 0.0259 | 99.4 % | 100.0 % | 0.0 % | 140.5 | n/a |
| lyon | anchor-days-year | raft | mps | 14 | 0.1 % | 0.0260 | 99.8 % | 100.0 % | 0.0 % | 138.8 | n/a |
| lyon | anchor-days-year | raft_ft_same_date | mps | 14 | 0.1 % | 0.0158 | 100.0 % | 100.0 % | 0.0 % | 140.1 | n/a |
| lyon | anchor-days-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.0163 | 100.0 % | 100.0 % | 0.0 % | 139.7 | n/a |
| lyon | anchor-season-year | raft | mps | 14 | 0.1 % | 0.2352 | 21.1 % | 98.5 % | 0.0 % | 138.9 | n/a |
| lyon | anchor-season-year | raft_ft_same_date | mps | 14 | 0.1 % | 0.0985 | 54.8 % | 100.0 % | 0.0 % | 139.6 | n/a |
| lyon | anchor-season-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.1117 | 49.8 % | 100.0 % | 0.0 % | 139.6 | n/a |
| lyon | days-season-year | raft | mps | 13 | 0.1 % | 0.2373 | 22.0 % | 97.2 % | 0.0 % | 137.5 | n/a |
| lyon | days-season-year | raft_ft_same_date | mps | 13 | 0.1 % | 0.0962 | 56.6 % | 100.0 % | 0.0 % | 139.6 | n/a |
| lyon | days-season-year | raft_ft_cross_date | mps | 13 | 0.1 % | 0.1176 | 45.7 % | 100.0 % | 0.0 % | 139.2 | n/a |
| morvan | anchor-days-season | raft | mps | 16 | 0.0 % | 0.3114 | 18.5 % | 92.2 % | 6.2 % | 137.8 | n/a |
| morvan | anchor-days-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.1474 | 35.9 % | 100.0 % | 0.0 % | 138.5 | n/a |
| morvan | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1205 | 41.0 % | 100.0 % | 0.0 % | 138.7 | n/a |
| morvan | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0616 | 91.9 % | 99.6 % | 0.0 % | 138.1 | n/a |
| morvan | anchor-days-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0338 | 99.3 % | 100.0 % | 0.0 % | 139.2 | n/a |
| morvan | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0338 | 99.2 % | 100.0 % | 0.0 % | 139.4 | n/a |
| morvan | anchor-season-year | raft | mps | 16 | 0.0 % | 0.4301 | 10.2 % | 79.9 % | 12.5 % | 140.8 | n/a |
| morvan | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.2641 | 5.6 % | 93.5 % | 0.0 % | 140.0 | n/a |
| morvan | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.2732 | 9.6 % | 91.6 % | 0.0 % | 140.1 | n/a |
| morvan | days-season-year | raft | mps | 16 | 0.0 % | 0.4623 | 7.2 % | 80.0 % | 18.8 % | 139.8 | n/a |
| morvan | days-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.2509 | 12.0 % | 95.4 % | 0.0 % | 139.6 | n/a |
| morvan | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.2419 | 12.1 % | 95.4 % | 0.0 % | 139.0 | n/a |
| sete | anchor-days-season | raft | mps | 16 | 0.0 % | 0.1413 | 83.3 % | 92.6 % | 18.8 % | 140.2 | n/a |
| sete | anchor-days-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.0916 | 88.8 % | 95.1 % | 0.0 % | 140.9 | n/a |
| sete | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0634 | 87.9 % | 99.8 % | 0.0 % | 140.5 | n/a |
| sete | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0513 | 95.3 % | 99.3 % | 37.5 % | 138.7 | n/a |
| sete | anchor-days-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0688 | 92.6 % | 94.4 % | 0.0 % | 140.2 | n/a |
| sete | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0365 | 92.9 % | 100.0 % | 0.0 % | 140.0 | n/a |
| sete | anchor-season-year | raft | mps | 16 | 0.0 % | 0.2246 | 75.9 % | 90.7 % | 12.5 % | 139.7 | n/a |
| sete | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0917 | 82.3 % | 95.0 % | 0.0 % | 140.3 | n/a |
| sete | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0796 | 81.1 % | 98.2 % | 0.0 % | 140.0 | n/a |
| sete | days-season-year | raft | mps | 16 | 0.0 % | 0.0926 | 93.8 % | 97.5 % | 37.5 % | 138.6 | n/a |
| sete | days-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.1209 | 82.4 % | 92.1 % | 0.0 % | 139.7 | n/a |
| sete | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0847 | 82.7 % | 97.0 % | 0.0 % | 140.0 | n/a |
| champagne | anchor-days-season | raft | mps | 16 | 0.0 % | 0.6166 | 17.1 % | 81.1 % | 68.8 % | 139.6 | n/a |
| champagne | anchor-days-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.1533 | 24.4 % | 100.0 % | 0.0 % | 140.1 | n/a |
| champagne | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0841 | 64.9 % | 100.0 % | 0.0 % | 140.2 | n/a |
| champagne | anchor-days-year | raft | mps | 16 | 0.0 % | 0.7324 | 14.8 % | 87.0 % | 93.8 % | 138.7 | n/a |
| champagne | anchor-days-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.1630 | 34.8 % | 95.8 % | 0.0 % | 139.5 | n/a |
| champagne | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1020 | 57.3 % | 100.0 % | 0.0 % | 139.5 | n/a |
| champagne | anchor-season-year | raft | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 139.0 | n/a |
| champagne | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.2744 | 15.3 % | 89.3 % | 0.0 % | 139.5 | n/a |
| champagne | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1690 | 28.1 % | 99.2 % | 0.0 % | 139.4 | n/a |
| champagne | days-season-year | raft | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 137.9 | n/a |
| champagne | days-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.2372 | 11.5 % | 95.7 % | 0.0 % | 138.5 | n/a |
| champagne | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1662 | 30.4 % | 99.9 % | 0.0 % | 139.3 | n/a |
| boerde | anchor-days-season | raft | mps | 15 | 0.0 % | 0.7586 | 4.6 % | 67.8 % | 60.0 % | 139.6 | n/a |
| boerde | anchor-days-season | raft_ft_same_date | mps | 15 | 0.0 % | 0.2187 | 20.9 % | 98.2 % | 0.0 % | 139.8 | n/a |
| boerde | anchor-days-season | raft_ft_cross_date | mps | 15 | 0.0 % | 0.1595 | 29.5 % | 100.0 % | 0.0 % | 139.6 | n/a |
| boerde | anchor-days-year | raft | mps | 15 | 0.0 % | 0.6146 | 31.9 % | 73.3 % | 60.0 % | 137.2 | n/a |
| boerde | anchor-days-year | raft_ft_same_date | mps | 15 | 0.0 % | 0.2091 | 36.0 % | 92.7 % | 0.0 % | 138.6 | n/a |
| boerde | anchor-days-year | raft_ft_cross_date | mps | 15 | 0.0 % | 0.1254 | 57.7 % | 97.1 % | 0.0 % | 138.2 | n/a |
| boerde | anchor-season-year | raft | mps | 16 | 0.0 % | 0.6110 | 0.3 % | 54.4 % | 93.8 % | 138.6 | n/a |
| boerde | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.4474 | 5.5 % | 65.4 % | 6.2 % | 139.1 | n/a |
| boerde | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.3780 | 5.7 % | 74.3 % | 0.0 % | 139.3 | n/a |
| boerde | days-season-year | raft | mps | 15 | 0.0 % | 0.9417 | 0.4 % | 50.6 % | 93.3 % | 137.9 | n/a |
| boerde | days-season-year | raft_ft_same_date | mps | 15 | 0.0 % | 0.3833 | 5.3 % | 74.4 % | 6.7 % | 138.6 | n/a |
| boerde | days-season-year | raft_ft_cross_date | mps | 15 | 0.0 % | 0.3359 | 4.9 % | 82.3 % | 0.0 % | 138.7 | n/a |
| bordeaux | anchor-days-season | raft | mps | 16 | 0.1 % | 0.0582 | 98.8 % | 99.9 % | 6.2 % | 141.3 | n/a |
| bordeaux | anchor-days-season | raft_ft_same_date | mps | 16 | 0.1 % | 0.0239 | 99.4 % | 100.0 % | 0.0 % | 142.8 | n/a |
| bordeaux | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0217 | 100.0 % | 100.0 % | 0.0 % | 144.0 | n/a |
| bordeaux | anchor-days-year | raft | mps | 16 | 0.1 % | 0.0653 | 98.2 % | 99.0 % | 6.2 % | 141.2 | n/a |
| bordeaux | anchor-days-year | raft_ft_same_date | mps | 16 | 0.1 % | 0.0196 | 100.0 % | 100.0 % | 0.0 % | 143.3 | n/a |
| bordeaux | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0239 | 100.0 % | 100.0 % | 0.0 % | 143.4 | n/a |
| bordeaux | anchor-season-year | raft | mps | 16 | 0.0 % | 0.1099 | 78.2 % | 99.8 % | 0.0 % | 142.3 | n/a |
| bordeaux | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0469 | 94.2 % | 100.0 % | 0.0 % | 143.6 | n/a |
| bordeaux | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0484 | 95.5 % | 100.0 % | 0.0 % | 143.6 | n/a |
| bordeaux | days-season-year | raft | mps | 16 | 0.1 % | 0.0956 | 72.1 % | 99.1 % | 0.0 % | 141.1 | n/a |
| bordeaux | days-season-year | raft_ft_same_date | mps | 16 | 0.1 % | 0.0461 | 95.4 % | 100.0 % | 0.0 % | 142.7 | n/a |
| bordeaux | days-season-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0475 | 97.2 % | 100.0 % | 0.0 % | 142.8 | n/a |
| milan | days-anchor-season | raft | mps | 16 | 0.1 % | 0.0777 | 76.4 % | 100.0 % | 0.0 % | 141.6 | n/a |
| milan | days-anchor-season | raft_ft_same_date | mps | 16 | 0.1 % | 0.0341 | 99.7 % | 100.0 % | 0.0 % | 142.1 | n/a |
| milan | days-anchor-season | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0390 | 99.3 % | 100.0 % | 0.0 % | 142.4 | n/a |
| milan | days-anchor-year | raft | mps | 16 | 0.0 % | 0.0570 | 95.7 % | 100.0 % | 0.0 % | 140.5 | n/a |
| milan | days-anchor-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0258 | 99.8 % | 100.0 % | 0.0 % | 141.7 | n/a |
| milan | days-anchor-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0239 | 100.0 % | 100.0 % | 0.0 % | 141.8 | n/a |
| milan | days-season-year | raft | mps | 16 | 0.1 % | 0.1297 | 43.6 % | 100.0 % | 0.0 % | 140.8 | n/a |
| milan | days-season-year | raft_ft_same_date | mps | 16 | 0.1 % | 0.0704 | 84.6 % | 100.0 % | 0.0 % | 141.3 | n/a |
| milan | days-season-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0680 | 82.8 % | 100.0 % | 0.0 % | 142.1 | n/a |
| milan | anchor-season-year | raft | mps | 16 | 0.1 % | 0.1051 | 55.1 % | 100.0 % | 0.0 % | 139.1 | n/a |
| milan | anchor-season-year | raft_ft_same_date | mps | 16 | 0.1 % | 0.0677 | 86.9 % | 100.0 % | 0.0 % | 140.9 | n/a |
| milan | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0560 | 92.1 % | 100.0 % | 0.0 % | 141.3 | n/a |
| landes | days-anchor-season | raft | mps | 16 | 0.0 % | 0.1132 | 92.0 % | 98.8 % | 6.2 % | 140.8 | n/a |
| landes | days-anchor-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.0323 | 98.2 % | 100.0 % | 0.0 % | 141.2 | n/a |
| landes | days-anchor-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0296 | 99.5 % | 100.0 % | 0.0 % | 141.8 | n/a |
| landes | days-anchor-year | raft | mps | 16 | 0.0 % | 0.0683 | 93.1 % | 98.3 % | 6.2 % | 154.4 | n/a |
| landes | days-anchor-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0239 | 99.3 % | 100.0 % | 0.0 % | 157.5 | n/a |
| landes | days-anchor-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0235 | 100.0 % | 100.0 % | 0.0 % | 159.0 | n/a |
| landes | days-season-year | raft | mps | 16 | 0.0 % | 0.3315 | 21.5 % | 95.5 % | 6.2 % | 150.1 | n/a |
| landes | days-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.1211 | 50.7 % | 99.8 % | 0.0 % | 151.9 | n/a |
| landes | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0988 | 57.9 % | 100.0 % | 0.0 % | 152.4 | n/a |
| landes | anchor-season-year | raft | mps | 16 | 0.0 % | 0.2922 | 16.6 % | 96.1 % | 12.5 % | 148.9 | n/a |
| landes | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.1067 | 55.9 % | 99.8 % | 0.0 % | 152.4 | n/a |
| landes | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0970 | 58.0 % | 100.0 % | 0.0 % | 151.6 | n/a |
| foret_noire | anchor-days-season | raft | mps | 16 | 0.0 % | 0.0393 | 98.3 % | 99.9 % | 0.0 % | 149.0 | n/a |
| foret_noire | anchor-days-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.0501 | 96.4 % | 100.0 % | 0.0 % | 150.8 | n/a |
| foret_noire | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0405 | 96.7 % | 100.0 % | 0.0 % | 150.7 | n/a |
| foret_noire | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0350 | 99.4 % | 99.9 % | 0.0 % | 159.5 | n/a |
| foret_noire | anchor-days-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0254 | 98.9 % | 100.0 % | 0.0 % | 161.9 | n/a |
| foret_noire | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0237 | 99.9 % | 100.0 % | 0.0 % | 161.7 | n/a |
| foret_noire | anchor-season-year | raft | mps | 16 | 0.0 % | 0.0631 | 86.5 % | 99.7 % | 0.0 % | 173.1 | n/a |
| foret_noire | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0503 | 95.3 % | 100.0 % | 0.0 % | 171.9 | n/a |
| foret_noire | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0472 | 95.7 % | 100.0 % | 0.0 % | 172.3 | n/a |
| foret_noire | days-season-year | raft | mps | 16 | 0.0 % | 0.0639 | 90.0 % | 99.8 % | 0.0 % | 170.5 | n/a |
| foret_noire | days-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0514 | 95.5 % | 100.0 % | 0.0 % | 173.1 | n/a |
| foret_noire | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0528 | 97.5 % | 100.0 % | 0.0 % | 172.1 | n/a |
| giens | anchor-days-season | raft | mps | 16 | 0.0 % | 0.1556 | 84.4 % | 93.6 % | 31.2 % | 192.3 | n/a |
| giens | anchor-days-season | raft_ft_same_date | mps | 16 | 0.0 % | 0.0551 | 90.2 % | 100.0 % | 18.8 % | 192.9 | n/a |
| giens | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1232 | 79.4 % | 93.3 % | 6.2 % | 208.9 | n/a |
| giens | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0599 | 90.0 % | 97.5 % | 37.5 % | 171.3 | n/a |
| giens | anchor-days-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0966 | 89.7 % | 93.0 % | 12.5 % | 170.2 | n/a |
| giens | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0937 | 80.1 % | 93.8 % | 0.0 % | 179.3 | n/a |
| giens | anchor-season-year | raft | mps | 16 | 0.0 % | 0.1524 | 75.6 % | 92.2 % | 31.2 % | 169.0 | n/a |
| giens | anchor-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0721 | 80.6 % | 100.0 % | 18.8 % | 172.9 | n/a |
| giens | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1521 | 72.2 % | 92.8 % | 6.2 % | 170.8 | n/a |
| giens | days-season-year | raft | mps | 16 | 0.0 % | 0.1952 | 73.8 % | 93.2 % | 31.2 % | 168.3 | n/a |
| giens | days-season-year | raft_ft_same_date | mps | 16 | 0.0 % | 0.0663 | 80.8 % | 100.0 % | 18.8 % | 170.8 | n/a |
| giens | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1387 | 70.0 % | 87.6 % | 6.2 % | 173.5 | n/a |
| costa_brava | anchor-days-season | raft | mps | 16 | 0.1 % | 0.0426 | 95.9 % | 99.9 % | 18.8 % | 155.8 | n/a |
| costa_brava | anchor-days-season | raft_ft_same_date | mps | 16 | 0.1 % | 0.0634 | 90.3 % | 97.5 % | 6.2 % | 158.3 | n/a |
| costa_brava | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0707 | 85.4 % | 99.1 % | 0.0 % | 156.3 | n/a |
| costa_brava | anchor-days-year | raft | mps | 16 | 0.1 % | 0.0502 | 95.0 % | 98.7 % | 18.8 % | 164.5 | n/a |
| costa_brava | anchor-days-year | raft_ft_same_date | mps | 16 | 0.1 % | 0.0925 | 90.4 % | 93.5 % | 6.2 % | 163.4 | n/a |
| costa_brava | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0736 | 87.3 % | 96.5 % | 0.0 % | 160.6 | n/a |
| costa_brava | anchor-season-year | raft | mps | 15 | 0.1 % | 0.0802 | 79.5 % | 99.1 % | 13.3 % | 167.9 | n/a |
| costa_brava | anchor-season-year | raft_ft_same_date | mps | 15 | 0.1 % | 0.0998 | 80.2 % | 93.9 % | 6.7 % | 170.1 | n/a |
| costa_brava | anchor-season-year | raft_ft_cross_date | mps | 15 | 0.1 % | 0.0650 | 88.8 % | 100.0 % | 6.7 % | 168.5 | n/a |
| costa_brava | days-season-year | raft | mps | 15 | 0.0 % | 0.0952 | 76.8 % | 98.3 % | 13.3 % | 167.6 | n/a |
| costa_brava | days-season-year | raft_ft_same_date | mps | 15 | 0.0 % | 0.1011 | 81.7 % | 92.9 % | 6.7 % | 168.7 | n/a |
| costa_brava | days-season-year | raft_ft_cross_date | mps | 15 | 0.0 % | 0.0710 | 89.3 % | 99.0 % | 6.7 % | 169.2 | n/a |

| pair | method | registrations | translation (px) | non-translation, p95 (px) |
|---|---|---:|---:|---:|
| anchor-days | raft | 190 | 0.117 (max 81.371) | 0.047 (max 46.924) |
| anchor-days | raft_ft_cross_date | 190 | 0.113 (max 1.052) | 0.038 (max 0.246) |
| anchor-days | raft_ft_same_date | 190 | 0.122 (max 2.630) | 0.028 (max 0.484) |
| anchor-season | raft | 191 | 0.191 (max 69.385) | 0.125 (max 119.983) |
| anchor-season | raft_ft_cross_date | 191 | 0.151 (max 1.493) | 0.083 (max 0.524) |
| anchor-season | raft_ft_same_date | 191 | 0.203 (max 2.624) | 0.077 (max 0.882) |
| anchor-year | raft | 189 | 0.168 (max 75.088) | 0.082 (max 114.378) |
| anchor-year | raft_ft_cross_date | 189 | 0.130 (max 1.540) | 0.065 (max 0.456) |
| anchor-year | raft_ft_same_date | 189 | 0.166 (max 2.240) | 0.047 (max 0.949) |
| days-season | raft | 189 | 0.204 (max 81.459) | 0.125 (max 70.504) |
| days-season | raft_ft_cross_date | 189 | 0.137 (max 1.356) | 0.085 (max 0.480) |
| days-season | raft_ft_same_date | 189 | 0.210 (max 2.336) | 0.074 (max 1.396) |
| days-year | raft | 187 | 0.130 (max 128.231) | 0.076 (max 130.481) |
| days-year | raft_ft_cross_date | 187 | 0.102 (max 0.632) | 0.060 (max 0.318) |
| days-year | raft_ft_same_date | 187 | 0.140 (max 2.566) | 0.046 (max 0.557) |
| season-year | raft | 187 | 0.195 (max 92.886) | 0.148 (max 93.574) |
| season-year | raft_ft_cross_date | 187 | 0.131 (max 1.423) | 0.077 (max 0.637) |
| season-year | raft_ft_same_date | 187 | 0.189 (max 2.807) | 0.065 (max 0.596) |

Displacements the methods find between real dates, across sites and windows. Translation is the median of the displacement over the window; the non-translation part is the 95th percentile of what is left. Median (max) over registrations.
