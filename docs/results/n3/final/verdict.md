The final evaluation of N3: fine-tuned RAFT next to the pretrained model, on the simulated pairs of `outputs/n3` and the real triplets of `outputs/n3-cycle`. The criterion and the reading of the closure are in docs/decisions.md, written before any training ran, and the freeze before these tables were made.

**Yes**: on the 1,800 simulated pairs of the held-out sites (alps, libya4), raft_ft beats raft. It fails 0 pairs where raft fails 3, and over the 1,797 pairs neither fails its mean EPE is 0.0692 px where raft's is 0.0953 px, a difference of -0.0261 px (95 % interval -0.0275 to -0.0248 px by resampling the pairs, -0.0285 to -0.0238 px by resampling the 200 draws they come from). On the real triplets of every site, the closure of raft_ft is better than raft's: it fails 0 of 384 triplets where raft fails 89, and over the 295 neither fails its mean closure is 0.0721 px where raft's is 0.1441 px.

**The criterion: raft_ft next to raft, RAFT large.**

| sites | pairs | raft: failed | raft_ft: failed | neither fails | raft: EPE (px) | raft_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| held-out sites | 1800 | 3 | 0 | 1797 | 0.0953 | 0.0692 | -0.0261 | -0.0275 to -0.0248 | -0.0285 to -0.0238 | yes |
| alps | 900 | 0 | 0 | 900 | 0.1042 | 0.0739 | -0.0303 | -0.0326 to -0.0281 | -0.0342 to -0.0264 | yes |
| libya4 | 900 | 3 | 0 | 897 | 0.0864 | 0.0645 | -0.0220 | -0.0235 to -0.0204 | -0.0245 to -0.0194 | yes |
| seen sites | 3600 | 30 | 0 | 3570 | 0.1228 | 0.0787 | -0.0440 | -0.0467 to -0.0415 | -0.0480 to -0.0404 | yes |
| beauce | 900 | 15 | 0 | 885 | 0.1400 | 0.0871 | -0.0528 | -0.0600 to -0.0462 | -0.0640 to -0.0426 | yes |
| toulouse | 900 | 0 | 0 | 900 | 0.0966 | 0.0676 | -0.0291 | -0.0309 to -0.0273 | -0.0321 to -0.0260 | yes |
| vosges | 900 | 0 | 0 | 900 | 0.1305 | 0.0824 | -0.0481 | -0.0523 to -0.0441 | -0.0534 to -0.0430 | yes |
| marseille | 900 | 15 | 0 | 885 | 0.1242 | 0.0778 | -0.0464 | -0.0528 to -0.0406 | -0.0554 to -0.0381 | yes |

By cell, on the held-out sites:

| scenario | degradation | pairs | raft: failed | raft_ft: failed | neither fails | raft: EPE (px) | raft_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| translation | clean | 200 | 0 | 0 | 200 | 0.0482 | 0.0305 | -0.0177 | -0.0197 to -0.0157 | -0.0197 to -0.0157 | yes |
| translation | mild | 200 | 0 | 0 | 200 | 0.0520 | 0.0337 | -0.0183 | -0.0206 to -0.0161 | -0.0206 to -0.0161 | yes |
| translation | hard | 200 | 1 | 0 | 199 | 0.1167 | 0.0818 | -0.0349 | -0.0412 to -0.0289 | -0.0412 to -0.0289 | yes |
| affine | clean | 200 | 0 | 0 | 200 | 0.0551 | 0.0362 | -0.0189 | -0.0208 to -0.0170 | -0.0208 to -0.0170 | yes |
| affine | mild | 200 | 0 | 0 | 200 | 0.0609 | 0.0408 | -0.0201 | -0.0222 to -0.0181 | -0.0222 to -0.0181 | yes |
| affine | hard | 200 | 1 | 0 | 199 | 0.1420 | 0.1043 | -0.0377 | -0.0442 to -0.0315 | -0.0442 to -0.0315 | yes |
| dense | clean | 200 | 0 | 0 | 200 | 0.0929 | 0.0682 | -0.0248 | -0.0271 to -0.0225 | -0.0271 to -0.0225 | yes |
| dense | mild | 200 | 0 | 0 | 200 | 0.1025 | 0.0766 | -0.0259 | -0.0284 to -0.0235 | -0.0284 to -0.0235 | yes |
| dense | hard | 200 | 1 | 0 | 199 | 0.1885 | 0.1514 | -0.0371 | -0.0431 to -0.0316 | -0.0431 to -0.0316 | yes |

By cell, on alps:

| scenario | degradation | pairs | raft: failed | raft_ft: failed | neither fails | raft: EPE (px) | raft_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| translation | clean | 100 | 0 | 0 | 100 | 0.0500 | 0.0293 | -0.0207 | -0.0237 to -0.0178 | -0.0237 to -0.0178 | yes |
| translation | mild | 100 | 0 | 0 | 100 | 0.0540 | 0.0325 | -0.0215 | -0.0247 to -0.0182 | -0.0247 to -0.0182 | yes |
| translation | hard | 100 | 0 | 0 | 100 | 0.1361 | 0.0928 | -0.0433 | -0.0536 to -0.0327 | -0.0536 to -0.0327 | yes |
| affine | clean | 100 | 0 | 0 | 100 | 0.0566 | 0.0353 | -0.0213 | -0.0240 to -0.0185 | -0.0240 to -0.0185 | yes |
| affine | mild | 100 | 0 | 0 | 100 | 0.0626 | 0.0403 | -0.0223 | -0.0254 to -0.0192 | -0.0254 to -0.0192 | yes |
| affine | hard | 100 | 0 | 0 | 100 | 0.1643 | 0.1183 | -0.0460 | -0.0569 to -0.0351 | -0.0569 to -0.0351 | yes |
| dense | clean | 100 | 0 | 0 | 100 | 0.0950 | 0.0688 | -0.0261 | -0.0293 to -0.0230 | -0.0293 to -0.0230 | yes |
| dense | mild | 100 | 0 | 0 | 100 | 0.1057 | 0.0778 | -0.0280 | -0.0314 to -0.0246 | -0.0314 to -0.0246 | yes |
| dense | hard | 100 | 0 | 0 | 100 | 0.2137 | 0.1701 | -0.0436 | -0.0538 to -0.0336 | -0.0538 to -0.0336 | yes |

By cell, on libya4:

| scenario | degradation | pairs | raft: failed | raft_ft: failed | neither fails | raft: EPE (px) | raft_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| translation | clean | 100 | 0 | 0 | 100 | 0.0463 | 0.0317 | -0.0146 | -0.0173 to -0.0120 | -0.0173 to -0.0120 | yes |
| translation | mild | 100 | 0 | 0 | 100 | 0.0500 | 0.0348 | -0.0152 | -0.0182 to -0.0123 | -0.0182 to -0.0123 | yes |
| translation | hard | 100 | 1 | 0 | 99 | 0.0971 | 0.0706 | -0.0265 | -0.0330 to -0.0199 | -0.0330 to -0.0199 | yes |
| affine | clean | 100 | 0 | 0 | 100 | 0.0537 | 0.0371 | -0.0166 | -0.0192 to -0.0140 | -0.0192 to -0.0140 | yes |
| affine | mild | 100 | 0 | 0 | 100 | 0.0593 | 0.0413 | -0.0180 | -0.0207 to -0.0153 | -0.0207 to -0.0153 | yes |
| affine | hard | 100 | 1 | 0 | 99 | 0.1194 | 0.0902 | -0.0293 | -0.0360 to -0.0226 | -0.0360 to -0.0226 | yes |
| dense | clean | 100 | 0 | 0 | 100 | 0.0909 | 0.0675 | -0.0234 | -0.0268 to -0.0200 | -0.0268 to -0.0200 | yes |
| dense | mild | 100 | 0 | 0 | 100 | 0.0994 | 0.0754 | -0.0239 | -0.0276 to -0.0204 | -0.0276 to -0.0204 | yes |
| dense | hard | 100 | 1 | 0 | 99 | 0.1630 | 0.1325 | -0.0305 | -0.0365 to -0.0247 | -0.0365 to -0.0247 | yes |

raft_ft beats raft in every cell of the held-out sites.

**RAFT small, raft_small_ft next to raft_small: read the same way and reported, not the criterion.**

| sites | pairs | raft_small: failed | raft_small_ft: failed | neither fails | raft_small: EPE (px) | raft_small_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| held-out sites | 1800 | 39 | 0 | 1761 | 0.2116 | 0.1249 | -0.0868 | -0.0916 to -0.0822 | -0.0942 to -0.0796 | yes |
| alps | 900 | 30 | 0 | 870 | 0.2327 | 0.1276 | -0.1052 | -0.1131 to -0.0974 | -0.1163 to -0.0944 | yes |
| libya4 | 900 | 9 | 0 | 891 | 0.1911 | 0.1222 | -0.0688 | -0.0739 to -0.0640 | -0.0769 to -0.0610 | yes |
| seen sites | 3600 | 263 | 0 | 3337 | 0.2345 | 0.1261 | -0.1085 | -0.1129 to -0.1041 | -0.1147 to -0.1023 | yes |
| beauce | 900 | 47 | 0 | 853 | 0.2547 | 0.1352 | -0.1195 | -0.1300 to -0.1093 | -0.1326 to -0.1066 | yes |
| toulouse | 900 | 2 | 0 | 898 | 0.2197 | 0.1232 | -0.0965 | -0.1023 to -0.0909 | -0.1047 to -0.0882 | yes |
| vosges | 900 | 139 | 0 | 761 | 0.2407 | 0.1173 | -0.1234 | -0.1349 to -0.1124 | -0.1394 to -0.1075 | yes |
| marseille | 900 | 75 | 0 | 825 | 0.2242 | 0.1277 | -0.0965 | -0.1049 to -0.0887 | -0.1076 to -0.0859 | yes |

By cell, on the held-out sites:

| scenario | degradation | pairs | raft_small: failed | raft_small_ft: failed | neither fails | raft_small: EPE (px) | raft_small_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| translation | clean | 200 | 0 | 0 | 200 | 0.1360 | 0.0687 | -0.0674 | -0.0730 to -0.0620 | -0.0730 to -0.0620 | yes |
| translation | mild | 200 | 1 | 0 | 199 | 0.1475 | 0.0713 | -0.0762 | -0.0876 to -0.0673 | -0.0876 to -0.0673 | yes |
| translation | hard | 200 | 14 | 0 | 186 | 0.3199 | 0.1453 | -0.1746 | -0.1940 to -0.1563 | -0.1940 to -0.1563 | yes |
| affine | clean | 200 | 0 | 0 | 200 | 0.1379 | 0.0810 | -0.0569 | -0.0627 to -0.0512 | -0.0627 to -0.0512 | yes |
| affine | mild | 200 | 1 | 0 | 199 | 0.1503 | 0.0871 | -0.0632 | -0.0750 to -0.0541 | -0.0750 to -0.0541 | yes |
| affine | hard | 200 | 12 | 0 | 188 | 0.3323 | 0.1827 | -0.1497 | -0.1698 to -0.1307 | -0.1698 to -0.1307 | yes |
| dense | clean | 200 | 0 | 0 | 200 | 0.1706 | 0.1325 | -0.0381 | -0.0434 to -0.0332 | -0.0434 to -0.0332 | yes |
| dense | mild | 200 | 0 | 0 | 200 | 0.1816 | 0.1401 | -0.0415 | -0.0504 to -0.0344 | -0.0504 to -0.0344 | yes |
| dense | hard | 200 | 11 | 0 | 189 | 0.3505 | 0.2254 | -0.1251 | -0.1444 to -0.1066 | -0.1444 to -0.1066 | yes |

By cell, on alps:

| scenario | degradation | pairs | raft_small: failed | raft_small_ft: failed | neither fails | raft_small: EPE (px) | raft_small_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| translation | clean | 100 | 0 | 0 | 100 | 0.1394 | 0.0666 | -0.0728 | -0.0808 to -0.0645 | -0.0808 to -0.0645 | yes |
| translation | mild | 100 | 1 | 0 | 99 | 0.1583 | 0.0682 | -0.0901 | -0.1114 to -0.0741 | -0.1114 to -0.0741 | yes |
| translation | hard | 100 | 11 | 0 | 89 | 0.3692 | 0.1600 | -0.2092 | -0.2377 to -0.1826 | -0.2377 to -0.1826 | yes |
| affine | clean | 100 | 0 | 0 | 100 | 0.1411 | 0.0783 | -0.0628 | -0.0710 to -0.0545 | -0.0710 to -0.0545 | yes |
| affine | mild | 100 | 1 | 0 | 99 | 0.1619 | 0.0841 | -0.0778 | -0.1003 to -0.0613 | -0.1003 to -0.0613 | yes |
| affine | hard | 100 | 9 | 0 | 91 | 0.3883 | 0.1968 | -0.1915 | -0.2234 to -0.1620 | -0.2234 to -0.1620 | yes |
| dense | clean | 100 | 0 | 0 | 100 | 0.1739 | 0.1306 | -0.0433 | -0.0509 to -0.0358 | -0.0509 to -0.0358 | yes |
| dense | mild | 100 | 0 | 0 | 100 | 0.1909 | 0.1388 | -0.0520 | -0.0683 to -0.0393 | -0.0683 to -0.0393 | yes |
| dense | hard | 100 | 8 | 0 | 92 | 0.4137 | 0.2428 | -0.1709 | -0.2036 to -0.1406 | -0.2036 to -0.1406 | yes |

By cell, on libya4:

| scenario | degradation | pairs | raft_small: failed | raft_small_ft: failed | neither fails | raft_small: EPE (px) | raft_small_ft: EPE (px) | difference (px) | 95 % interval, pairs (px) | 95 % interval, draws (px) | beats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| translation | clean | 100 | 0 | 0 | 100 | 0.1326 | 0.0707 | -0.0620 | -0.0690 to -0.0550 | -0.0690 to -0.0550 | yes |
| translation | mild | 100 | 0 | 0 | 100 | 0.1368 | 0.0743 | -0.0625 | -0.0692 to -0.0558 | -0.0692 to -0.0558 | yes |
| translation | hard | 100 | 3 | 0 | 97 | 0.2747 | 0.1318 | -0.1429 | -0.1674 to -0.1208 | -0.1674 to -0.1208 | yes |
| affine | clean | 100 | 0 | 0 | 100 | 0.1348 | 0.0838 | -0.0510 | -0.0587 to -0.0433 | -0.0587 to -0.0433 | yes |
| affine | mild | 100 | 0 | 0 | 100 | 0.1388 | 0.0900 | -0.0488 | -0.0559 to -0.0417 | -0.0559 to -0.0417 | yes |
| affine | hard | 100 | 3 | 0 | 97 | 0.2798 | 0.1694 | -0.1104 | -0.1322 to -0.0904 | -0.1322 to -0.0904 | yes |
| dense | clean | 100 | 0 | 0 | 100 | 0.1674 | 0.1344 | -0.0330 | -0.0396 to -0.0264 | -0.0396 to -0.0264 | yes |
| dense | mild | 100 | 0 | 0 | 100 | 0.1723 | 0.1413 | -0.0310 | -0.0372 to -0.0248 | -0.0372 to -0.0248 | yes |
| dense | hard | 100 | 3 | 0 | 97 | 0.2905 | 0.2090 | -0.0816 | -0.1001 to -0.0647 | -0.1001 to -0.0647 | yes |

raft_small_ft beats raft_small in every cell of the held-out sites.

**Closure of the real triplets, raft_ft next to raft.**

| sites | triplets | raft: failed | raft_ft: failed | neither fails | raft: closure (px) | raft_ft: closure (px) | difference (px) | raft_ft is |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| every site | 384 | 89 | 0 | 295 | 0.1441 | 0.0721 | -0.0720 | better |
| held-out sites | 128 | 2 | 0 | 126 | 0.1176 | 0.0721 | -0.0455 | better |
| alps | 64 | 2 | 0 | 62 | 0.1453 | 0.0799 | -0.0655 | better |
| libya4 | 64 | 0 | 0 | 64 | 0.0907 | 0.0646 | -0.0261 | better |
| seen sites | 256 | 87 | 0 | 169 | 0.1639 | 0.0721 | -0.0918 | better |
| beauce | 64 | 61 | 0 | 3 | 0.6778 | 0.0541 | -0.6237 | better |
| toulouse | 64 | 2 | 0 | 62 | 0.0880 | 0.0456 | -0.0424 | better |
| vosges | 64 | 8 | 0 | 56 | 0.3266 | 0.1384 | -0.1882 | better |
| marseille | 64 | 16 | 0 | 48 | 0.0401 | 0.0302 | -0.0099 | better |

**Closure of the real triplets, raft_small_ft next to raft_small.**

| sites | triplets | raft_small: failed | raft_small_ft: failed | neither fails | raft_small: closure (px) | raft_small_ft: closure (px) | difference (px) | raft_small_ft is |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| every site | 384 | 143 | 7 | 241 | 0.1899 | 0.0745 | -0.1154 | better |
| held-out sites | 128 | 15 | 2 | 113 | 0.2247 | 0.0883 | -0.1364 | better |
| alps | 64 | 15 | 2 | 49 | 0.3791 | 0.1177 | -0.2614 | better |
| libya4 | 64 | 0 | 0 | 64 | 0.1064 | 0.0658 | -0.0406 | better |
| seen sites | 256 | 128 | 5 | 128 | 0.1592 | 0.0623 | -0.0969 | better |
| beauce | 64 | 64 | 3 | 0 | n/a | n/a | n/a | better |
| toulouse | 64 | 2 | 0 | 62 | 0.1904 | 0.0721 | -0.1182 | better |
| vosges | 64 | 46 | 0 | 18 | 0.2183 | 0.0675 | -0.1508 | better |
| marseille | 64 | 16 | 2 | 48 | 0.0968 | 0.0475 | -0.0492 | better |

An EPE or a closure is a mean over the pairs or triplets neither of the two models fails. A difference is the fine-tuned model minus the pretrained one: negative is better. A model beats the other if it fails at most as many pairs and its mean EPE is lower, with no margin. A closure is worse with more failed triplets, or with as many and a higher mean.

The intervals are percentile bootstraps of the difference, 10,000 resamples with seed 0, the pairs neither model fails found again in each resample. The first resamples the pairs, as the criterion registered. The second resamples the draws: pair number i of a site is one window and one draw of its motion, seen under every scenario and preset, and is drawn with all its pairs. In a cell a draw has one pair, and the two are the same. Both cover the draw of the pairs, not the seed of the training: each model was trained once.

The pairs of the four RAFT methods were scored on Intel(R) Xeon(R) CPU @ 2.00GHz, 31 GiB, 4 CPUs, Linux-6.18.48+-x86_64-with-glibc2.35; GPU Tesla T4, 15 GiB, CUDA 12.8 (cuda), and the triplets on Apple M1, 8 GiB, 8 CPUs, macOS-26.6.2-arm64-arm-64bit-Mach-O. The fine-tuned weights are the published ones: raft_ft is `raft_large_ft-44bcc668.pth` of release `weights-n3`, SHA-256 `44bcc668d20a633410259e43de2c56a4712c4e23860fb8f456cc5bb6a8589d13`; raft_small_ft is `raft_small_ft-b666aaad.pth` of release `weights-n3`, SHA-256 `b666aaadf41886411bc53665aa6c3e30ab699d211cbe4ae97025c41e0a10e137`.

Held-out sites in this table: alps, libya4. They are kept for the final evaluation: no threshold, preset or variant may be chosen on their rows.
