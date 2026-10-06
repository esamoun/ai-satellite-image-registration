Closure on real triplets, every triplet and window of a role's chips together:

| site | triplet | method | device | triplets | clouds | closure (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| validation chips | all | raft_small | mps | 241 | 0.0 % | 0.2869 | 36.4 % | 87.5 % | 42.3 % | 58.5 | n/a |
| validation chips | all | raft_small_ft_cross_date | mps | 241 | 0.0 % | 0.1522 | 50.2 % | 95.4 % | 0.0 % | 62.9 | n/a |
| validation chips | all | raft | mps | 241 | 0.0 % | 0.2093 | 57.7 % | 93.4 % | 32.4 % | 149.8 | n/a |
| validation chips | all | raft_ft_cross_date | mps | 241 | 0.0 % | 0.1059 | 64.5 % | 98.5 % | 0.0 % | 152.9 | n/a |
| training chips | all | raft_small | mps | 507 | 0.0 % | 0.2037 | 43.9 % | 94.9 % | 37.1 % | 57.9 | n/a |
| training chips | all | raft_small_ft_cross_date | mps | 507 | 0.0 % | 0.1403 | 58.7 % | 94.5 % | 3.6 % | 62.8 | n/a |
| training chips | all | raft | mps | 507 | 0.0 % | 0.1354 | 75.0 % | 97.1 % | 28.2 % | 147.9 | n/a |
| training chips | all | raft_ft_cross_date | mps | 507 | 0.0 % | 0.0946 | 75.3 % | 97.4 % | 1.0 % | 151.6 | n/a |

Validation chips: santerre, lyon, morvan, sete. Training chips: champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava. Choices are made on the validation chips; the training chips are the ones a fine-tuned model has seen, and are reported, not chosen on. Each triplet of dates A < B < C is registered A to B, B to C and A to C on each 256 px window hidden at most 1 % on its three dates; the closure is the distance between A to B then B to C, and A to C, over pixels clear on all three. A triplet fails if a leg does, or if its mean closure exceeds 1.0 px; closure columns average the others. Time is the median of 1 call(s) per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O.

By chip and triplet:

| site | triplet | method | device | triplets | clouds | closure (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | days-anchor-season | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 63.3 | n/a |
| santerre | days-anchor-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1037 | 54.9 % | 100.0 % | 0.0 % | 63.7 | n/a |
| santerre | days-anchor-season | raft | mps | 16 | 0.0 % | 0.9282 | 18.8 % | 72.9 % | 93.8 % | 160.1 | n/a |
| santerre | days-anchor-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0729 | 77.8 % | 100.0 % | 0.0 % | 165.8 | n/a |
| santerre | days-anchor-year | raft_small | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 62.4 | n/a |
| santerre | days-anchor-year | raft_small_ft_cross_date | mps | 14 | 0.1 % | 0.1118 | 44.5 % | 100.0 % | 0.0 % | 66.4 | n/a |
| santerre | days-anchor-year | raft | mps | 14 | 0.1 % | 0.8687 | 16.4 % | 71.9 % | 85.7 % | 159.8 | n/a |
| santerre | days-anchor-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.0600 | 89.8 % | 100.0 % | 0.0 % | 162.0 | n/a |
| santerre | days-season-year | raft_small | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 61.4 | n/a |
| santerre | days-season-year | raft_small_ft_cross_date | mps | 14 | 0.1 % | 0.3610 | 3.7 % | 75.7 % | 0.0 % | 63.7 | n/a |
| santerre | days-season-year | raft | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 158.4 | n/a |
| santerre | days-season-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.1865 | 23.5 % | 96.6 % | 0.0 % | 161.7 | n/a |
| santerre | anchor-season-year | raft_small | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 61.2 | n/a |
| santerre | anchor-season-year | raft_small_ft_cross_date | mps | 14 | 0.1 % | 0.3151 | 6.8 % | 81.8 % | 0.0 % | 62.4 | n/a |
| santerre | anchor-season-year | raft | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 156.8 | n/a |
| santerre | anchor-season-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.1627 | 36.9 % | 98.5 % | 0.0 % | 160.5 | n/a |
| lyon | anchor-days-season | raft_small | mps | 14 | 0.1 % | 0.1445 | 50.4 % | 98.0 % | 0.0 % | 59.4 | n/a |
| lyon | anchor-days-season | raft_small_ft_cross_date | mps | 14 | 0.1 % | 0.0534 | 93.0 % | 100.0 % | 0.0 % | 64.5 | n/a |
| lyon | anchor-days-season | raft | mps | 14 | 0.1 % | 0.0427 | 96.9 % | 99.7 % | 0.0 % | 151.3 | n/a |
| lyon | anchor-days-season | raft_ft_cross_date | mps | 14 | 0.1 % | 0.0259 | 99.4 % | 100.0 % | 0.0 % | 154.5 | n/a |
| lyon | anchor-days-year | raft_small | mps | 14 | 0.1 % | 0.0624 | 86.2 % | 99.9 % | 0.0 % | 58.2 | n/a |
| lyon | anchor-days-year | raft_small_ft_cross_date | mps | 14 | 0.1 % | 0.0294 | 99.6 % | 100.0 % | 0.0 % | 64.5 | n/a |
| lyon | anchor-days-year | raft | mps | 14 | 0.1 % | 0.0260 | 99.8 % | 100.0 % | 0.0 % | 150.4 | n/a |
| lyon | anchor-days-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.0163 | 100.0 % | 100.0 % | 0.0 % | 152.5 | n/a |
| lyon | anchor-season-year | raft_small | mps | 14 | 0.1 % | 0.3589 | 9.4 % | 91.4 % | 0.0 % | 57.9 | n/a |
| lyon | anchor-season-year | raft_small_ft_cross_date | mps | 14 | 0.1 % | 0.1150 | 46.0 % | 100.0 % | 0.0 % | 63.3 | n/a |
| lyon | anchor-season-year | raft | mps | 14 | 0.1 % | 0.2352 | 21.1 % | 98.5 % | 0.0 % | 150.5 | n/a |
| lyon | anchor-season-year | raft_ft_cross_date | mps | 14 | 0.1 % | 0.1117 | 49.8 % | 100.0 % | 0.0 % | 154.2 | n/a |
| lyon | days-season-year | raft_small | mps | 13 | 0.1 % | 0.3666 | 9.5 % | 90.4 % | 0.0 % | 57.9 | n/a |
| lyon | days-season-year | raft_small_ft_cross_date | mps | 13 | 0.1 % | 0.1142 | 43.4 % | 100.0 % | 0.0 % | 61.7 | n/a |
| lyon | days-season-year | raft | mps | 13 | 0.1 % | 0.2373 | 22.0 % | 97.2 % | 0.0 % | 149.2 | n/a |
| lyon | days-season-year | raft_ft_cross_date | mps | 13 | 0.1 % | 0.1176 | 45.7 % | 100.0 % | 0.0 % | 152.4 | n/a |
| morvan | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.5636 | 3.1 % | 62.5 % | 25.0 % | 58.1 | n/a |
| morvan | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1582 | 26.7 % | 100.0 % | 0.0 % | 65.2 | n/a |
| morvan | anchor-days-season | raft | mps | 16 | 0.0 % | 0.3114 | 18.5 % | 92.2 % | 6.2 % | 147.5 | n/a |
| morvan | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1205 | 41.0 % | 100.0 % | 0.0 % | 152.2 | n/a |
| morvan | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.1419 | 43.8 % | 98.5 % | 0.0 % | 57.7 | n/a |
| morvan | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0617 | 84.9 % | 100.0 % | 0.0 % | 65.5 | n/a |
| morvan | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0616 | 91.9 % | 99.6 % | 0.0 % | 146.7 | n/a |
| morvan | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0338 | 99.2 % | 100.0 % | 0.0 % | 149.7 | n/a |
| morvan | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.6874 | 2.5 % | 38.9 % | 62.5 % | 57.5 | n/a |
| morvan | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.2739 | 14.3 % | 91.5 % | 0.0 % | 61.5 | n/a |
| morvan | anchor-season-year | raft | mps | 16 | 0.0 % | 0.4301 | 10.2 % | 79.9 % | 12.5 % | 148.1 | n/a |
| morvan | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.2732 | 9.6 % | 91.6 % | 0.0 % | 151.5 | n/a |
| morvan | days-season-year | raft_small | mps | 16 | 0.0 % | 0.6873 | 3.5 % | 41.7 % | 62.5 % | 57.7 | n/a |
| morvan | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.3112 | 8.8 % | 86.0 % | 0.0 % | 60.2 | n/a |
| morvan | days-season-year | raft | mps | 16 | 0.0 % | 0.4623 | 7.2 % | 80.0 % | 18.8 % | 147.1 | n/a |
| morvan | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.2419 | 12.1 % | 95.4 % | 0.0 % | 150.0 | n/a |
| sete | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.2115 | 53.8 % | 91.5 % | 31.2 % | 58.4 | n/a |
| sete | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1136 | 70.4 % | 96.6 % | 0.0 % | 63.4 | n/a |
| sete | anchor-days-season | raft | mps | 16 | 0.0 % | 0.1413 | 83.3 % | 92.6 % | 18.8 % | 148.8 | n/a |
| sete | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0634 | 87.9 % | 99.8 % | 0.0 % | 152.2 | n/a |
| sete | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.1798 | 61.0 % | 95.3 % | 31.2 % | 58.0 | n/a |
| sete | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0773 | 75.0 % | 99.9 % | 0.0 % | 63.1 | n/a |
| sete | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0513 | 95.3 % | 99.3 % | 37.5 % | 147.5 | n/a |
| sete | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0365 | 92.9 % | 100.0 % | 0.0 % | 151.2 | n/a |
| sete | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.3247 | 34.2 % | 92.2 % | 25.0 % | 58.3 | n/a |
| sete | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1054 | 65.8 % | 99.6 % | 0.0 % | 60.5 | n/a |
| sete | anchor-season-year | raft | mps | 16 | 0.0 % | 0.2246 | 75.9 % | 90.7 % | 12.5 % | 150.6 | n/a |
| sete | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0796 | 81.1 % | 98.2 % | 0.0 % | 153.3 | n/a |
| sete | days-season-year | raft_small | mps | 16 | 0.0 % | 0.1714 | 44.8 % | 96.9 % | 37.5 % | 58.2 | n/a |
| sete | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1326 | 63.7 % | 94.2 % | 0.0 % | 60.2 | n/a |
| sete | days-season-year | raft | mps | 16 | 0.0 % | 0.0926 | 93.8 % | 97.5 % | 37.5 % | 148.8 | n/a |
| sete | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0847 | 82.7 % | 97.0 % | 0.0 % | 152.0 | n/a |
| champagne | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.6931 | 2.3 % | 38.3 % | 93.8 % | 57.6 | n/a |
| champagne | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1788 | 19.7 % | 99.9 % | 0.0 % | 66.8 | n/a |
| champagne | anchor-days-season | raft | mps | 16 | 0.0 % | 0.6166 | 17.1 % | 81.1 % | 68.8 % | 146.8 | n/a |
| champagne | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0841 | 64.9 % | 100.0 % | 0.0 % | 151.3 | n/a |
| champagne | anchor-days-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.8 | n/a |
| champagne | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.2092 | 14.6 % | 98.1 % | 0.0 % | 61.2 | n/a |
| champagne | anchor-days-year | raft | mps | 16 | 0.0 % | 0.7324 | 14.8 % | 87.0 % | 93.8 % | 149.0 | n/a |
| champagne | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1020 | 57.3 % | 100.0 % | 0.0 % | 150.8 | n/a |
| champagne | anchor-season-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.5 | n/a |
| champagne | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.2904 | 11.8 % | 83.7 % | 0.0 % | 61.3 | n/a |
| champagne | anchor-season-year | raft | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 149.0 | n/a |
| champagne | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1690 | 28.1 % | 99.2 % | 0.0 % | 153.0 | n/a |
| champagne | days-season-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.7 | n/a |
| champagne | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.2807 | 5.1 % | 91.1 % | 0.0 % | 58.4 | n/a |
| champagne | days-season-year | raft | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 147.6 | n/a |
| champagne | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1662 | 30.4 % | 99.9 % | 0.0 % | 151.4 | n/a |
| boerde | anchor-days-season | raft_small | mps | 15 | 0.0 % | 0.7146 | 4.1 % | 60.5 % | 80.0 % | 58.4 | n/a |
| boerde | anchor-days-season | raft_small_ft_cross_date | mps | 15 | 0.0 % | 0.3014 | 6.1 % | 86.3 % | 0.0 % | 63.8 | n/a |
| boerde | anchor-days-season | raft | mps | 15 | 0.0 % | 0.7586 | 4.6 % | 67.8 % | 60.0 % | 147.0 | n/a |
| boerde | anchor-days-season | raft_ft_cross_date | mps | 15 | 0.0 % | 0.1595 | 29.5 % | 100.0 % | 0.0 % | 151.6 | n/a |
| boerde | anchor-days-year | raft_small | mps | 15 | 0.0 % | 0.2226 | 15.1 % | 96.8 % | 86.7 % | 57.7 | n/a |
| boerde | anchor-days-year | raft_small_ft_cross_date | mps | 15 | 0.0 % | 0.1864 | 34.0 % | 96.0 % | 0.0 % | 63.4 | n/a |
| boerde | anchor-days-year | raft | mps | 15 | 0.0 % | 0.6146 | 31.9 % | 73.3 % | 60.0 % | 148.5 | n/a |
| boerde | anchor-days-year | raft_ft_cross_date | mps | 15 | 0.0 % | 0.1254 | 57.7 % | 97.1 % | 0.0 % | 151.9 | n/a |
| boerde | anchor-season-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.4 | n/a |
| boerde | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.6014 | 0.3 % | 28.4 % | 18.8 % | 61.3 | n/a |
| boerde | anchor-season-year | raft | mps | 16 | 0.0 % | 0.6110 | 0.3 % | 54.4 % | 93.8 % | 149.3 | n/a |
| boerde | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.3780 | 5.7 % | 74.3 % | 0.0 % | 152.3 | n/a |
| boerde | days-season-year | raft_small | mps | 15 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.9 | n/a |
| boerde | days-season-year | raft_small_ft_cross_date | mps | 15 | 0.0 % | 0.5302 | 1.2 % | 48.4 % | 20.0 % | 60.0 | n/a |
| boerde | days-season-year | raft | mps | 15 | 0.0 % | 0.9417 | 0.4 % | 50.6 % | 93.3 % | 147.4 | n/a |
| boerde | days-season-year | raft_ft_cross_date | mps | 15 | 0.0 % | 0.3359 | 4.9 % | 82.3 % | 0.0 % | 151.3 | n/a |
| bordeaux | anchor-days-season | raft_small | mps | 16 | 0.1 % | 0.1432 | 77.8 % | 98.8 % | 12.5 % | 58.1 | n/a |
| bordeaux | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0353 | 98.6 % | 100.0 % | 0.0 % | 65.7 | n/a |
| bordeaux | anchor-days-season | raft | mps | 16 | 0.1 % | 0.0582 | 98.8 % | 99.9 % | 6.2 % | 147.5 | n/a |
| bordeaux | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0217 | 100.0 % | 100.0 % | 0.0 % | 152.0 | n/a |
| bordeaux | anchor-days-year | raft_small | mps | 16 | 0.1 % | 0.1680 | 72.1 % | 97.2 % | 6.2 % | 58.1 | n/a |
| bordeaux | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0376 | 98.2 % | 100.0 % | 0.0 % | 64.8 | n/a |
| bordeaux | anchor-days-year | raft | mps | 16 | 0.1 % | 0.0653 | 98.2 % | 99.0 % | 6.2 % | 147.4 | n/a |
| bordeaux | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0239 | 100.0 % | 100.0 % | 0.0 % | 150.6 | n/a |
| bordeaux | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.1587 | 38.9 % | 98.3 % | 12.5 % | 57.7 | n/a |
| bordeaux | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0650 | 85.6 % | 100.0 % | 0.0 % | 61.8 | n/a |
| bordeaux | anchor-season-year | raft | mps | 16 | 0.0 % | 0.1099 | 78.2 % | 99.8 % | 0.0 % | 148.7 | n/a |
| bordeaux | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0484 | 95.5 % | 100.0 % | 0.0 % | 152.9 | n/a |
| bordeaux | days-season-year | raft_small | mps | 16 | 0.1 % | 0.1720 | 34.7 % | 97.5 % | 6.2 % | 58.2 | n/a |
| bordeaux | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0682 | 81.6 % | 100.0 % | 0.0 % | 61.8 | n/a |
| bordeaux | days-season-year | raft | mps | 16 | 0.1 % | 0.0956 | 72.1 % | 99.1 % | 0.0 % | 147.8 | n/a |
| bordeaux | days-season-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0475 | 97.2 % | 100.0 % | 0.0 % | 151.4 | n/a |
| milan | days-anchor-season | raft_small | mps | 16 | 0.1 % | 0.1565 | 51.0 % | 98.2 % | 6.2 % | 58.5 | n/a |
| milan | days-anchor-season | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0635 | 83.4 % | 100.0 % | 0.0 % | 66.2 | n/a |
| milan | days-anchor-season | raft | mps | 16 | 0.1 % | 0.0777 | 76.4 % | 100.0 % | 0.0 % | 147.7 | n/a |
| milan | days-anchor-season | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0390 | 99.3 % | 100.0 % | 0.0 % | 152.0 | n/a |
| milan | days-anchor-year | raft_small | mps | 16 | 0.0 % | 0.0848 | 76.4 % | 99.6 % | 0.0 % | 58.4 | n/a |
| milan | days-anchor-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0446 | 96.2 % | 100.0 % | 0.0 % | 66.2 | n/a |
| milan | days-anchor-year | raft | mps | 16 | 0.0 % | 0.0570 | 95.7 % | 100.0 % | 0.0 % | 147.7 | n/a |
| milan | days-anchor-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0239 | 100.0 % | 100.0 % | 0.0 % | 149.6 | n/a |
| milan | days-season-year | raft_small | mps | 16 | 0.1 % | 0.3179 | 17.1 % | 93.5 % | 6.2 % | 57.8 | n/a |
| milan | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0956 | 58.7 % | 100.0 % | 0.0 % | 62.7 | n/a |
| milan | days-season-year | raft | mps | 16 | 0.1 % | 0.1297 | 43.6 % | 100.0 % | 0.0 % | 149.6 | n/a |
| milan | days-season-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0680 | 82.8 % | 100.0 % | 0.0 % | 152.5 | n/a |
| milan | anchor-season-year | raft_small | mps | 16 | 0.1 % | 0.2896 | 15.8 % | 94.2 % | 6.2 % | 58.0 | n/a |
| milan | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0952 | 61.6 % | 100.0 % | 0.0 % | 62.5 | n/a |
| milan | anchor-season-year | raft | mps | 16 | 0.1 % | 0.1051 | 55.1 % | 100.0 % | 0.0 % | 147.9 | n/a |
| milan | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0560 | 92.1 % | 100.0 % | 0.0 % | 150.8 | n/a |
| landes | days-anchor-season | raft_small | mps | 16 | 0.0 % | 0.2172 | 39.5 % | 95.8 % | 12.5 % | 59.3 | n/a |
| landes | days-anchor-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0596 | 89.6 % | 100.0 % | 0.0 % | 68.2 | n/a |
| landes | days-anchor-season | raft | mps | 16 | 0.0 % | 0.1132 | 92.0 % | 98.8 % | 6.2 % | 144.7 | n/a |
| landes | days-anchor-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0296 | 99.5 % | 100.0 % | 0.0 % | 150.4 | n/a |
| landes | days-anchor-year | raft_small | mps | 16 | 0.0 % | 0.2764 | 49.6 % | 95.8 % | 18.8 % | 57.3 | n/a |
| landes | days-anchor-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0507 | 92.5 % | 100.0 % | 0.0 % | 63.6 | n/a |
| landes | days-anchor-year | raft | mps | 16 | 0.0 % | 0.0683 | 93.1 % | 98.3 % | 6.2 % | 145.8 | n/a |
| landes | days-anchor-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0235 | 100.0 % | 100.0 % | 0.0 % | 148.8 | n/a |
| landes | days-season-year | raft_small | mps | 16 | 0.0 % | 0.5668 | 11.4 % | 69.1 % | 25.0 % | 58.1 | n/a |
| landes | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1545 | 23.1 % | 100.0 % | 0.0 % | 61.7 | n/a |
| landes | days-season-year | raft | mps | 16 | 0.0 % | 0.3315 | 21.5 % | 95.5 % | 6.2 % | 147.2 | n/a |
| landes | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0988 | 57.9 % | 100.0 % | 0.0 % | 150.2 | n/a |
| landes | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.5307 | 9.2 % | 70.2 % | 43.8 % | 57.4 | n/a |
| landes | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1621 | 18.4 % | 100.0 % | 0.0 % | 63.4 | n/a |
| landes | anchor-season-year | raft | mps | 16 | 0.0 % | 0.2922 | 16.6 % | 96.1 % | 12.5 % | 145.7 | n/a |
| landes | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0970 | 58.0 % | 100.0 % | 0.0 % | 148.7 | n/a |
| foret_noire | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.1332 | 43.8 % | 98.8 % | 0.0 % | 58.0 | n/a |
| foret_noire | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0743 | 74.0 % | 100.0 % | 0.0 % | 66.3 | n/a |
| foret_noire | anchor-days-season | raft | mps | 16 | 0.0 % | 0.0393 | 98.3 % | 99.9 % | 0.0 % | 144.7 | n/a |
| foret_noire | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0405 | 96.7 % | 100.0 % | 0.0 % | 150.5 | n/a |
| foret_noire | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.0995 | 63.1 % | 99.4 % | 0.0 % | 58.0 | n/a |
| foret_noire | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0462 | 96.0 % | 100.0 % | 0.0 % | 64.0 | n/a |
| foret_noire | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0350 | 99.4 % | 99.9 % | 0.0 % | 146.7 | n/a |
| foret_noire | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0237 | 99.9 % | 100.0 % | 0.0 % | 149.9 | n/a |
| foret_noire | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.1810 | 24.6 % | 97.4 % | 0.0 % | 58.9 | n/a |
| foret_noire | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0739 | 77.8 % | 100.0 % | 0.0 % | 66.0 | n/a |
| foret_noire | anchor-season-year | raft | mps | 16 | 0.0 % | 0.0631 | 86.5 % | 99.7 % | 0.0 % | 154.2 | n/a |
| foret_noire | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0472 | 95.7 % | 100.0 % | 0.0 % | 158.2 | n/a |
| foret_noire | days-season-year | raft_small | mps | 16 | 0.0 % | 0.1884 | 29.1 % | 96.6 % | 0.0 % | 59.0 | n/a |
| foret_noire | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.0903 | 65.1 % | 100.0 % | 0.0 % | 64.5 | n/a |
| foret_noire | days-season-year | raft | mps | 16 | 0.0 % | 0.0639 | 90.0 % | 99.8 % | 0.0 % | 151.8 | n/a |
| foret_noire | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0528 | 97.5 % | 100.0 % | 0.0 % | 156.1 | n/a |
| giens | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.0963 | 71.4 % | 98.5 % | 43.8 % | 58.9 | n/a |
| giens | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1185 | 72.3 % | 93.6 % | 12.5 % | 67.5 | n/a |
| giens | anchor-days-season | raft | mps | 16 | 0.0 % | 0.1556 | 84.4 % | 93.6 % | 31.2 % | 147.1 | n/a |
| giens | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1232 | 79.4 % | 93.3 % | 6.2 % | 152.5 | n/a |
| giens | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.0826 | 79.4 % | 98.9 % | 43.8 % | 58.0 | n/a |
| giens | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1556 | 73.4 % | 87.0 % | 6.2 % | 64.4 | n/a |
| giens | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0599 | 90.0 % | 97.5 % | 37.5 % | 147.7 | n/a |
| giens | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.0937 | 80.1 % | 93.8 % | 0.0 % | 150.3 | n/a |
| giens | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.2158 | 27.1 % | 93.5 % | 43.8 % | 58.1 | n/a |
| giens | anchor-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1400 | 50.3 % | 96.0 % | 12.5 % | 62.1 | n/a |
| giens | anchor-season-year | raft | mps | 16 | 0.0 % | 0.1524 | 75.6 % | 92.2 % | 31.2 % | 150.3 | n/a |
| giens | anchor-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1521 | 72.2 % | 92.8 % | 6.2 % | 152.6 | n/a |
| giens | days-season-year | raft_small | mps | 16 | 0.0 % | 0.2255 | 23.1 % | 92.5 % | 43.8 % | 58.1 | n/a |
| giens | days-season-year | raft_small_ft_cross_date | mps | 16 | 0.0 % | 0.1084 | 56.7 % | 100.0 % | 18.8 % | 61.3 | n/a |
| giens | days-season-year | raft | mps | 16 | 0.0 % | 0.1952 | 73.8 % | 93.2 % | 31.2 % | 148.8 | n/a |
| giens | days-season-year | raft_ft_cross_date | mps | 16 | 0.0 % | 0.1387 | 70.0 % | 87.6 % | 6.2 % | 151.4 | n/a |
| costa_brava | anchor-days-season | raft_small | mps | 16 | 0.1 % | 0.1016 | 71.0 % | 98.6 % | 25.0 % | 59.4 | n/a |
| costa_brava | anchor-days-season | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0714 | 83.9 % | 99.8 % | 6.2 % | 65.6 | n/a |
| costa_brava | anchor-days-season | raft | mps | 16 | 0.1 % | 0.0426 | 95.9 % | 99.9 % | 18.8 % | 152.8 | n/a |
| costa_brava | anchor-days-season | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0707 | 85.4 % | 99.1 % | 0.0 % | 155.2 | n/a |
| costa_brava | anchor-days-year | raft_small | mps | 16 | 0.1 % | 0.0633 | 85.0 % | 100.0 % | 31.2 % | 57.9 | n/a |
| costa_brava | anchor-days-year | raft_small_ft_cross_date | mps | 16 | 0.1 % | 0.0831 | 86.6 % | 94.3 % | 6.2 % | 61.3 | n/a |
| costa_brava | anchor-days-year | raft | mps | 16 | 0.1 % | 0.0502 | 95.0 % | 98.7 % | 18.8 % | 149.6 | n/a |
| costa_brava | anchor-days-year | raft_ft_cross_date | mps | 16 | 0.1 % | 0.0736 | 87.3 % | 96.5 % | 0.0 % | 152.9 | n/a |
| costa_brava | anchor-season-year | raft_small | mps | 15 | 0.1 % | 0.1688 | 30.9 % | 97.7 % | 26.7 % | 57.7 | n/a |
| costa_brava | anchor-season-year | raft_small_ft_cross_date | mps | 15 | 0.1 % | 0.0846 | 71.6 % | 100.0 % | 6.7 % | 60.9 | n/a |
| costa_brava | anchor-season-year | raft | mps | 15 | 0.1 % | 0.0802 | 79.5 % | 99.1 % | 13.3 % | 149.4 | n/a |
| costa_brava | anchor-season-year | raft_ft_cross_date | mps | 15 | 0.1 % | 0.0650 | 88.8 % | 100.0 % | 6.7 % | 152.7 | n/a |
| costa_brava | days-season-year | raft_small | mps | 15 | 0.0 % | 0.1950 | 25.5 % | 96.3 % | 20.0 % | 57.7 | n/a |
| costa_brava | days-season-year | raft_small_ft_cross_date | mps | 15 | 0.0 % | 0.1010 | 67.3 % | 99.1 % | 6.7 % | 59.3 | n/a |
| costa_brava | days-season-year | raft | mps | 15 | 0.0 % | 0.0952 | 76.8 % | 98.3 % | 13.3 % | 147.9 | n/a |
| costa_brava | days-season-year | raft_ft_cross_date | mps | 15 | 0.0 % | 0.0710 | 89.3 % | 99.0 % | 6.7 % | 150.6 | n/a |

| pair | method | registrations | translation (px) | non-translation, p95 (px) |
|---|---|---:|---:|---:|
| anchor-days | raft | 190 | 0.117 (max 81.371) | 0.047 (max 46.924) |
| anchor-days | raft_ft_cross_date | 190 | 0.113 (max 1.052) | 0.038 (max 0.246) |
| anchor-days | raft_small | 190 | 0.141 (max 124.817) | 0.183 (max 117.217) |
| anchor-days | raft_small_ft_cross_date | 190 | 0.136 (max 1.280) | 0.078 (max 0.235) |
| anchor-season | raft | 191 | 0.191 (max 69.385) | 0.125 (max 119.983) |
| anchor-season | raft_ft_cross_date | 191 | 0.151 (max 1.493) | 0.083 (max 0.524) |
| anchor-season | raft_small | 191 | 0.287 (max 92.741) | 0.684 (max 96.199) |
| anchor-season | raft_small_ft_cross_date | 191 | 0.198 (max 1.900) | 0.140 (max 0.752) |
| anchor-year | raft | 189 | 0.168 (max 75.088) | 0.082 (max 114.378) |
| anchor-year | raft_ft_cross_date | 189 | 0.130 (max 1.540) | 0.065 (max 0.456) |
| anchor-year | raft_small | 189 | 0.225 (max 84.254) | 0.410 (max 90.320) |
| anchor-year | raft_small_ft_cross_date | 189 | 0.187 (max 1.178) | 0.119 (max 0.464) |
| days-season | raft | 189 | 0.204 (max 81.459) | 0.125 (max 70.504) |
| days-season | raft_ft_cross_date | 189 | 0.137 (max 1.356) | 0.085 (max 0.480) |
| days-season | raft_small | 189 | 0.304 (max 158.707) | 0.668 (max 100.035) |
| days-season | raft_small_ft_cross_date | 189 | 0.206 (max 1.926) | 0.133 (max 0.395) |
| days-year | raft | 187 | 0.130 (max 128.231) | 0.076 (max 130.481) |
| days-year | raft_ft_cross_date | 187 | 0.102 (max 0.632) | 0.060 (max 0.318) |
| days-year | raft_small | 187 | 0.203 (max 152.071) | 0.395 (max 152.666) |
| days-year | raft_small_ft_cross_date | 187 | 0.173 (max 1.390) | 0.119 (max 0.315) |
| season-year | raft | 187 | 0.195 (max 92.886) | 0.148 (max 93.574) |
| season-year | raft_ft_cross_date | 187 | 0.131 (max 1.423) | 0.077 (max 0.637) |
| season-year | raft_small | 187 | 0.275 (max 131.806) | 0.625 (max 132.213) |
| season-year | raft_small_ft_cross_date | 187 | 0.212 (max 1.285) | 0.137 (max 0.355) |

Displacements the methods find between real dates, across sites and windows. Translation is the median of the displacement over the window; the non-translation part is the 95th percentile of what is left. Median (max) over registrations.
