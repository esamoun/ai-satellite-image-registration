Closure on real triplets, every triplet and window of a role's chips together:

| site | triplet | method | device | triplets | clouds | closure (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| validation chips | all | raft | mps | 241 | 0.0 % | 0.2093 | 57.7 % | 93.4 % | 32.4 % | 142.4 | n/a |
| validation chips | all | raft_small | mps | 241 | 0.0 % | 0.2869 | 36.4 % | 87.5 % | 42.3 % | 56.3 | n/a |
| train chips | all | raft | mps | 507 | 0.0 % | 0.1354 | 75.0 % | 97.1 % | 28.2 % | 143.0 | n/a |
| train chips | all | raft_small | mps | 507 | 0.0 % | 0.2037 | 43.9 % | 94.9 % | 37.1 % | 57.0 | n/a |

Validation chips: santerre, lyon, morvan, sete. Train chips: champagne, boerde, bordeaux, milan, landes, foret_noire, giens, costa_brava. Choices are made on the validation chips; the training chips are the ones a fine-tuned model has seen, and are reported, not chosen on. Each triplet of dates A < B < C is registered A to B, B to C and A to C on each 256 px window hidden at most 1 % on its three dates; the closure is the distance between A to B then B to C, and A to C, over pixels clear on all three. A triplet fails if a leg does, or if its mean closure exceeds 1.0 px; closure columns average the others. Time is the median of 1 call(s) per pair, after 1 warm-up call(s) per method; memory is not measured, as no counter is available on the device. Measured on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O.

By chip and triplet:

| site | triplet | method | device | triplets | clouds | closure (px) | < 0.1 px | < 0.5 px | failures | time (ms) | memory (MiB) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| santerre | days-anchor-season | raft | mps | 16 | 0.0 % | 0.9282 | 18.8 % | 72.9 % | 93.8 % | 143.0 | n/a |
| santerre | days-anchor-season | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 55.7 | n/a |
| santerre | days-anchor-year | raft | mps | 14 | 0.1 % | 0.8687 | 16.4 % | 71.9 % | 85.7 % | 141.3 | n/a |
| santerre | days-anchor-year | raft_small | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 56.2 | n/a |
| santerre | days-season-year | raft | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 142.2 | n/a |
| santerre | days-season-year | raft_small | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 55.0 | n/a |
| santerre | anchor-season-year | raft | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 140.9 | n/a |
| santerre | anchor-season-year | raft_small | mps | 14 | 0.1 % | n/a | n/a | n/a | 100.0 % | 56.0 | n/a |
| lyon | anchor-days-season | raft | mps | 14 | 0.1 % | 0.0427 | 96.9 % | 99.7 % | 0.0 % | 143.9 | n/a |
| lyon | anchor-days-season | raft_small | mps | 14 | 0.1 % | 0.1445 | 50.4 % | 98.0 % | 0.0 % | 56.6 | n/a |
| lyon | anchor-days-year | raft | mps | 14 | 0.1 % | 0.0260 | 99.8 % | 100.0 % | 0.0 % | 142.5 | n/a |
| lyon | anchor-days-year | raft_small | mps | 14 | 0.1 % | 0.0624 | 86.2 % | 99.9 % | 0.0 % | 57.1 | n/a |
| lyon | anchor-season-year | raft | mps | 14 | 0.1 % | 0.2352 | 21.1 % | 98.5 % | 0.0 % | 142.8 | n/a |
| lyon | anchor-season-year | raft_small | mps | 14 | 0.1 % | 0.3589 | 9.4 % | 91.4 % | 0.0 % | 56.2 | n/a |
| lyon | days-season-year | raft | mps | 13 | 0.1 % | 0.2373 | 22.0 % | 97.2 % | 0.0 % | 141.3 | n/a |
| lyon | days-season-year | raft_small | mps | 13 | 0.1 % | 0.3666 | 9.5 % | 90.4 % | 0.0 % | 56.5 | n/a |
| morvan | anchor-days-season | raft | mps | 16 | 0.0 % | 0.3114 | 18.5 % | 92.2 % | 6.2 % | 143.1 | n/a |
| morvan | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.5636 | 3.1 % | 62.5 % | 25.0 % | 56.5 | n/a |
| morvan | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0616 | 91.9 % | 99.6 % | 0.0 % | 142.0 | n/a |
| morvan | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.1419 | 43.8 % | 98.5 % | 0.0 % | 56.5 | n/a |
| morvan | anchor-season-year | raft | mps | 16 | 0.0 % | 0.4301 | 10.2 % | 79.9 % | 12.5 % | 142.6 | n/a |
| morvan | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.6874 | 2.5 % | 38.9 % | 62.5 % | 55.6 | n/a |
| morvan | days-season-year | raft | mps | 16 | 0.0 % | 0.4623 | 7.2 % | 80.0 % | 18.8 % | 140.4 | n/a |
| morvan | days-season-year | raft_small | mps | 16 | 0.0 % | 0.6873 | 3.5 % | 41.7 % | 62.5 % | 56.0 | n/a |
| sete | anchor-days-season | raft | mps | 16 | 0.0 % | 0.1413 | 83.3 % | 92.6 % | 18.8 % | 144.1 | n/a |
| sete | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.2115 | 53.8 % | 91.5 % | 31.2 % | 56.5 | n/a |
| sete | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0513 | 95.3 % | 99.3 % | 37.5 % | 142.8 | n/a |
| sete | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.1798 | 61.0 % | 95.3 % | 31.2 % | 57.1 | n/a |
| sete | anchor-season-year | raft | mps | 16 | 0.0 % | 0.2246 | 75.9 % | 90.7 % | 12.5 % | 142.7 | n/a |
| sete | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.3247 | 34.2 % | 92.2 % | 25.0 % | 56.8 | n/a |
| sete | days-season-year | raft | mps | 16 | 0.0 % | 0.0926 | 93.8 % | 97.5 % | 37.5 % | 142.0 | n/a |
| sete | days-season-year | raft_small | mps | 16 | 0.0 % | 0.1714 | 44.8 % | 96.9 % | 37.5 % | 56.9 | n/a |
| champagne | anchor-days-season | raft | mps | 16 | 0.0 % | 0.6166 | 17.1 % | 81.1 % | 68.8 % | 143.7 | n/a |
| champagne | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.6931 | 2.3 % | 38.3 % | 93.8 % | 56.2 | n/a |
| champagne | anchor-days-year | raft | mps | 16 | 0.0 % | 0.7324 | 14.8 % | 87.0 % | 93.8 % | 142.2 | n/a |
| champagne | anchor-days-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.5 | n/a |
| champagne | anchor-season-year | raft | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 142.1 | n/a |
| champagne | anchor-season-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 55.9 | n/a |
| champagne | days-season-year | raft | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 141.4 | n/a |
| champagne | days-season-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 56.5 | n/a |
| boerde | anchor-days-season | raft | mps | 15 | 0.0 % | 0.7586 | 4.6 % | 67.8 % | 60.0 % | 143.8 | n/a |
| boerde | anchor-days-season | raft_small | mps | 15 | 0.0 % | 0.7146 | 4.1 % | 60.5 % | 80.0 % | 57.6 | n/a |
| boerde | anchor-days-year | raft | mps | 15 | 0.0 % | 0.6146 | 31.9 % | 73.3 % | 60.0 % | 142.5 | n/a |
| boerde | anchor-days-year | raft_small | mps | 15 | 0.0 % | 0.2226 | 15.1 % | 96.8 % | 86.7 % | 56.7 | n/a |
| boerde | anchor-season-year | raft | mps | 16 | 0.0 % | 0.6110 | 0.3 % | 54.4 % | 93.8 % | 142.6 | n/a |
| boerde | anchor-season-year | raft_small | mps | 16 | 0.0 % | n/a | n/a | n/a | 100.0 % | 56.9 | n/a |
| boerde | days-season-year | raft | mps | 15 | 0.0 % | 0.9417 | 0.4 % | 50.6 % | 93.3 % | 141.9 | n/a |
| boerde | days-season-year | raft_small | mps | 15 | 0.0 % | n/a | n/a | n/a | 100.0 % | 57.2 | n/a |
| bordeaux | anchor-days-season | raft | mps | 16 | 0.1 % | 0.0582 | 98.8 % | 99.9 % | 6.2 % | 144.1 | n/a |
| bordeaux | anchor-days-season | raft_small | mps | 16 | 0.1 % | 0.1432 | 77.8 % | 98.8 % | 12.5 % | 57.1 | n/a |
| bordeaux | anchor-days-year | raft | mps | 16 | 0.1 % | 0.0653 | 98.2 % | 99.0 % | 6.2 % | 142.4 | n/a |
| bordeaux | anchor-days-year | raft_small | mps | 16 | 0.1 % | 0.1680 | 72.1 % | 97.2 % | 6.2 % | 57.7 | n/a |
| bordeaux | anchor-season-year | raft | mps | 16 | 0.0 % | 0.1099 | 78.2 % | 99.8 % | 0.0 % | 143.7 | n/a |
| bordeaux | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.1587 | 38.9 % | 98.3 % | 12.5 % | 56.6 | n/a |
| bordeaux | days-season-year | raft | mps | 16 | 0.1 % | 0.0956 | 72.1 % | 99.1 % | 0.0 % | 142.8 | n/a |
| bordeaux | days-season-year | raft_small | mps | 16 | 0.1 % | 0.1720 | 34.7 % | 97.5 % | 6.2 % | 57.2 | n/a |
| milan | days-anchor-season | raft | mps | 16 | 0.1 % | 0.0777 | 76.4 % | 100.0 % | 0.0 % | 143.4 | n/a |
| milan | days-anchor-season | raft_small | mps | 16 | 0.1 % | 0.1565 | 51.0 % | 98.2 % | 6.2 % | 57.1 | n/a |
| milan | days-anchor-year | raft | mps | 16 | 0.0 % | 0.0570 | 95.7 % | 100.0 % | 0.0 % | 142.9 | n/a |
| milan | days-anchor-year | raft_small | mps | 16 | 0.0 % | 0.0848 | 76.4 % | 99.6 % | 0.0 % | 57.3 | n/a |
| milan | days-season-year | raft | mps | 16 | 0.1 % | 0.1297 | 43.6 % | 100.0 % | 0.0 % | 143.6 | n/a |
| milan | days-season-year | raft_small | mps | 16 | 0.1 % | 0.3179 | 17.1 % | 93.5 % | 6.2 % | 56.2 | n/a |
| milan | anchor-season-year | raft | mps | 16 | 0.1 % | 0.1051 | 55.1 % | 100.0 % | 0.0 % | 142.3 | n/a |
| milan | anchor-season-year | raft_small | mps | 16 | 0.1 % | 0.2896 | 15.8 % | 94.2 % | 6.2 % | 56.8 | n/a |
| landes | days-anchor-season | raft | mps | 16 | 0.0 % | 0.1132 | 92.0 % | 98.8 % | 6.2 % | 143.6 | n/a |
| landes | days-anchor-season | raft_small | mps | 16 | 0.0 % | 0.2172 | 39.5 % | 95.8 % | 12.5 % | 56.8 | n/a |
| landes | days-anchor-year | raft | mps | 16 | 0.0 % | 0.0683 | 93.1 % | 98.3 % | 6.2 % | 143.1 | n/a |
| landes | days-anchor-year | raft_small | mps | 16 | 0.0 % | 0.2764 | 49.6 % | 95.8 % | 18.8 % | 57.1 | n/a |
| landes | days-season-year | raft | mps | 16 | 0.0 % | 0.3315 | 21.5 % | 95.5 % | 6.2 % | 142.7 | n/a |
| landes | days-season-year | raft_small | mps | 16 | 0.0 % | 0.5668 | 11.4 % | 69.1 % | 25.0 % | 57.1 | n/a |
| landes | anchor-season-year | raft | mps | 16 | 0.0 % | 0.2922 | 16.6 % | 96.1 % | 12.5 % | 141.5 | n/a |
| landes | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.5307 | 9.2 % | 70.2 % | 43.8 % | 57.1 | n/a |
| foret_noire | anchor-days-season | raft | mps | 16 | 0.0 % | 0.0393 | 98.3 % | 99.9 % | 0.0 % | 143.6 | n/a |
| foret_noire | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.1332 | 43.8 % | 98.8 % | 0.0 % | 58.2 | n/a |
| foret_noire | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0350 | 99.4 % | 99.9 % | 0.0 % | 143.6 | n/a |
| foret_noire | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.0995 | 63.1 % | 99.4 % | 0.0 % | 57.3 | n/a |
| foret_noire | anchor-season-year | raft | mps | 16 | 0.0 % | 0.0631 | 86.5 % | 99.7 % | 0.0 % | 143.2 | n/a |
| foret_noire | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.1810 | 24.6 % | 97.4 % | 0.0 % | 57.5 | n/a |
| foret_noire | days-season-year | raft | mps | 16 | 0.0 % | 0.0639 | 90.0 % | 99.8 % | 0.0 % | 142.1 | n/a |
| foret_noire | days-season-year | raft_small | mps | 16 | 0.0 % | 0.1884 | 29.1 % | 96.6 % | 0.0 % | 57.1 | n/a |
| giens | anchor-days-season | raft | mps | 16 | 0.0 % | 0.1556 | 84.4 % | 93.6 % | 31.2 % | 144.1 | n/a |
| giens | anchor-days-season | raft_small | mps | 16 | 0.0 % | 0.0963 | 71.4 % | 98.5 % | 43.8 % | 57.1 | n/a |
| giens | anchor-days-year | raft | mps | 16 | 0.0 % | 0.0599 | 90.0 % | 97.5 % | 37.5 % | 142.9 | n/a |
| giens | anchor-days-year | raft_small | mps | 16 | 0.0 % | 0.0826 | 79.4 % | 98.9 % | 43.8 % | 57.0 | n/a |
| giens | anchor-season-year | raft | mps | 16 | 0.0 % | 0.1524 | 75.6 % | 92.2 % | 31.2 % | 143.0 | n/a |
| giens | anchor-season-year | raft_small | mps | 16 | 0.0 % | 0.2158 | 27.1 % | 93.5 % | 43.8 % | 56.8 | n/a |
| giens | days-season-year | raft | mps | 16 | 0.0 % | 0.1952 | 73.8 % | 93.2 % | 31.2 % | 142.1 | n/a |
| giens | days-season-year | raft_small | mps | 16 | 0.0 % | 0.2255 | 23.1 % | 92.5 % | 43.8 % | 56.6 | n/a |
| costa_brava | anchor-days-season | raft | mps | 16 | 0.1 % | 0.0426 | 95.9 % | 99.9 % | 18.8 % | 144.6 | n/a |
| costa_brava | anchor-days-season | raft_small | mps | 16 | 0.1 % | 0.1016 | 71.0 % | 98.6 % | 25.0 % | 57.0 | n/a |
| costa_brava | anchor-days-year | raft | mps | 16 | 0.1 % | 0.0502 | 95.0 % | 98.7 % | 18.8 % | 143.7 | n/a |
| costa_brava | anchor-days-year | raft_small | mps | 16 | 0.1 % | 0.0633 | 85.0 % | 100.0 % | 31.2 % | 57.4 | n/a |
| costa_brava | anchor-season-year | raft | mps | 15 | 0.1 % | 0.0802 | 79.5 % | 99.1 % | 13.3 % | 143.4 | n/a |
| costa_brava | anchor-season-year | raft_small | mps | 15 | 0.1 % | 0.1688 | 30.9 % | 97.7 % | 26.7 % | 56.7 | n/a |
| costa_brava | days-season-year | raft | mps | 15 | 0.0 % | 0.0952 | 76.8 % | 98.3 % | 13.3 % | 142.4 | n/a |
| costa_brava | days-season-year | raft_small | mps | 15 | 0.0 % | 0.1950 | 25.5 % | 96.3 % | 20.0 % | 56.8 | n/a |

| pair | method | registrations | translation (px) | non-translation, p95 (px) |
|---|---|---:|---:|---:|
| anchor-days | raft | 190 | 0.117 (max 81.371) | 0.047 (max 46.924) |
| anchor-days | raft_small | 190 | 0.141 (max 124.817) | 0.183 (max 117.217) |
| anchor-season | raft | 191 | 0.191 (max 69.385) | 0.125 (max 119.983) |
| anchor-season | raft_small | 191 | 0.287 (max 92.741) | 0.684 (max 96.199) |
| anchor-year | raft | 189 | 0.168 (max 75.088) | 0.082 (max 114.378) |
| anchor-year | raft_small | 189 | 0.225 (max 84.254) | 0.410 (max 90.320) |
| days-season | raft | 189 | 0.204 (max 81.459) | 0.125 (max 70.504) |
| days-season | raft_small | 189 | 0.304 (max 158.707) | 0.668 (max 100.035) |
| days-year | raft | 187 | 0.130 (max 128.231) | 0.076 (max 130.481) |
| days-year | raft_small | 187 | 0.203 (max 152.071) | 0.395 (max 152.666) |
| season-year | raft | 187 | 0.195 (max 92.886) | 0.148 (max 93.574) |
| season-year | raft_small | 187 | 0.275 (max 131.806) | 0.625 (max 132.213) |

Displacements the methods find between real dates, across sites and windows. Translation is the median of the displacement over the window; the non-translation part is the 95th percentile of what is left. Median (max) over registrations.
