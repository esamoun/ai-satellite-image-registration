RAFT small fine-tuned (raft_small_ft_cross_date) with the pairs and the recipe of the retained RAFT large (raft_ft_cross_date), next to the pretrained RAFT small (raft_small) and to RAFT large, fine-tuned and pretrained (raft). Validation set of `outputs/small/validation`, real triplets of `outputs/small/validation-cycle`. What a gain, no gain and worse are is in docs/decisions.md, written before the training ran.

The two trainings:

| | raft_small_ft_cross_date | raft_ft_cross_date |
|---|---:|---:|
| run directory | `outputs/train/small-cross-date` | `outputs/train/large-cross-date` |
| cross-date share | 0.5 | 0.5 |
| seed | 0 | 0 |
| steps done / budget | 10000 / 10000 | 10000 / 10000 |
| sessions | 1 | 1 |
| commit | deb3d1b | 4429c35 |
| median s/step | 3.41 | 3.31 |
| training loss, last tenth of the steps | 0.8229 | 0.4915 |
| validations | 21 | 21 |
| selection score, pretrained (px) | 0.3224 | 0.1583 |
| selection score, kept (px) | 0.1424 | 0.0854 |
| kept step | 8000 | 8500 |
| SHA-256 of `best.pt` | `b666aaadf4188641` | `44bcc668d20a6334` |

Settings the two runs were not given alike: train.model. The device and the number of worker processes are not compared: a session may change them. With the same seed and the same pairs configuration, pair number i is the same pair in both runs.

**What the training changed.**

raft_small_ft_cross_date next to raft_small, on the validation set:

| scenario | degradation | pairs | raft_small: failed | raft_small_ft_cross_date: failed | neither fails | raft_small: EPE (px) | raft_small_ft_cross_date: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.1289 | 0.0634 | -0.0655 |
| translation | mild | 400 | 2 | 0 | 398 | 0.1656 | 0.0709 | -0.0947 |
| translation | hard | 400 | 109 | 1 | 291 | 0.4720 | 0.1476 | -0.3244 |
| affine | clean | 400 | 0 | 0 | 400 | 0.1304 | 0.0760 | -0.0544 |
| affine | mild | 400 | 1 | 0 | 399 | 0.1701 | 0.0857 | -0.0844 |
| affine | hard | 400 | 111 | 1 | 289 | 0.4777 | 0.1967 | -0.2810 |
| dense | clean | 400 | 0 | 0 | 400 | 0.1631 | 0.1320 | -0.0311 |
| dense | mild | 400 | 2 | 0 | 398 | 0.1919 | 0.1437 | -0.0482 |
| dense | hard | 400 | 103 | 1 | 297 | 0.4967 | 0.2442 | -0.2525 |
| all | all | 3600 | 328 | 3 | 3272 | 0.2451 | 0.1224 | -0.1227 |

raft_small_ft_cross_date beats raft_small on the validation set: it fails 3 pairs where raft_small fails 328, and over the 3272 pairs neither fails its mean error is 0.1224 px where raft_small's is 0.2451 px.

On the real triplets:

| chips | triplets | raft_small: failed | raft_small_ft_cross_date: failed | neither fails | raft_small: closure (px) | raft_small_ft_cross_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 102 | 0 | 139 | 0.2869 | 0.0925 | -0.1944 |
| training chips | 507 | 188 | 18 | 319 | 0.2037 | 0.0712 | -0.1324 |

Its closure is better than raft_small on the validation chips and better than it on the training chips.

**What is left to RAFT large, both fine-tuned.**

raft_small_ft_cross_date next to raft_ft_cross_date, on the validation set:

| scenario | degradation | pairs | raft_ft_cross_date: failed | raft_small_ft_cross_date: failed | neither fails | raft_ft_cross_date: EPE (px) | raft_small_ft_cross_date: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.0303 | 0.0634 | +0.0331 |
| translation | mild | 400 | 0 | 0 | 400 | 0.0350 | 0.0709 | +0.0359 |
| translation | hard | 400 | 0 | 1 | 399 | 0.1132 | 0.1725 | +0.0593 |
| affine | clean | 400 | 0 | 0 | 400 | 0.0364 | 0.0760 | +0.0396 |
| affine | mild | 400 | 0 | 0 | 400 | 0.0429 | 0.0857 | +0.0427 |
| affine | hard | 400 | 0 | 1 | 399 | 0.1464 | 0.2242 | +0.0778 |
| dense | clean | 400 | 0 | 0 | 400 | 0.0703 | 0.1320 | +0.0616 |
| dense | mild | 400 | 0 | 0 | 400 | 0.0818 | 0.1435 | +0.0617 |
| dense | hard | 400 | 0 | 1 | 399 | 0.2005 | 0.2708 | +0.0704 |
| all | all | 3600 | 0 | 3 | 3597 | 0.0840 | 0.1376 | +0.0536 |

raft_small_ft_cross_date does not beat raft_ft_cross_date on the validation set: it fails 3 pairs where raft_ft_cross_date fails 0, and over the 3597 pairs neither fails its mean error is 0.1376 px where raft_ft_cross_date's is 0.0840 px.

On the real triplets:

| chips | triplets | raft_ft_cross_date: failed | raft_small_ft_cross_date: failed | neither fails | raft_ft_cross_date: closure (px) | raft_small_ft_cross_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 0 | 0 | 241 | 0.1059 | 0.1522 | +0.0463 |
| training chips | 507 | 5 | 18 | 488 | 0.0811 | 0.1395 | +0.0584 |

Its closure is worse than raft_ft_cross_date on the validation chips and worse than it on the training chips.

**Next to RAFT large as it was before any training.**

raft_small_ft_cross_date next to raft, on the validation set:

| scenario | degradation | pairs | raft: failed | raft_small_ft_cross_date: failed | neither fails | raft: EPE (px) | raft_small_ft_cross_date: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.0447 | 0.0634 | +0.0187 |
| translation | mild | 400 | 0 | 0 | 400 | 0.0613 | 0.0709 | +0.0096 |
| translation | hard | 400 | 24 | 1 | 376 | 0.2118 | 0.1603 | -0.0515 |
| affine | clean | 400 | 0 | 0 | 400 | 0.0522 | 0.0760 | +0.0238 |
| affine | mild | 400 | 0 | 0 | 400 | 0.0702 | 0.0857 | +0.0154 |
| affine | hard | 400 | 23 | 1 | 377 | 0.2389 | 0.2154 | -0.0235 |
| dense | clean | 400 | 0 | 0 | 400 | 0.0923 | 0.1320 | +0.0396 |
| dense | mild | 400 | 0 | 0 | 400 | 0.1124 | 0.1435 | +0.0311 |
| dense | hard | 400 | 23 | 1 | 377 | 0.2751 | 0.2585 | -0.0166 |
| all | all | 3600 | 70 | 3 | 3530 | 0.1265 | 0.1324 | +0.0059 |

raft_small_ft_cross_date does not beat raft on the validation set: it fails 3 pairs where raft fails 70, and over the 3530 pairs neither fails its mean error is 0.1324 px where raft's is 0.1265 px.

On the real triplets:

| chips | triplets | raft: failed | raft_small_ft_cross_date: failed | neither fails | raft: closure (px) | raft_small_ft_cross_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 78 | 0 | 163 | 0.2093 | 0.1188 | -0.0905 |
| training chips | 507 | 143 | 18 | 364 | 0.1354 | 0.0792 | -0.0562 |

Its closure is better than raft on the validation chips and better than it on the training chips.

**The gap before any training.**

raft_small next to raft, on the validation set:

| scenario | degradation | pairs | raft: failed | raft_small: failed | neither fails | raft: EPE (px) | raft_small: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.0447 | 0.1289 | +0.0842 |
| translation | mild | 400 | 0 | 2 | 398 | 0.0613 | 0.1656 | +0.1043 |
| translation | hard | 400 | 24 | 109 | 286 | 0.1780 | 0.4717 | +0.2937 |
| affine | clean | 400 | 0 | 0 | 400 | 0.0522 | 0.1304 | +0.0782 |
| affine | mild | 400 | 0 | 1 | 399 | 0.0702 | 0.1701 | +0.0999 |
| affine | hard | 400 | 23 | 111 | 285 | 0.2032 | 0.4790 | +0.2758 |
| dense | clean | 400 | 0 | 0 | 400 | 0.0923 | 0.1631 | +0.0708 |
| dense | mild | 400 | 0 | 2 | 398 | 0.1124 | 0.1919 | +0.0794 |
| dense | hard | 400 | 23 | 103 | 293 | 0.2466 | 0.4961 | +0.2495 |
| all | all | 3600 | 70 | 328 | 3259 | 0.1086 | 0.2442 | +0.1356 |

raft_small does not beat raft on the validation set: it fails 328 pairs where raft fails 70, and over the 3259 pairs neither fails its mean error is 0.2442 px where raft's is 0.1086 px.

On the real triplets:

| chips | triplets | raft: failed | raft_small: failed | neither fails | raft: closure (px) | raft_small: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 78 | 102 | 134 | 0.1502 | 0.2764 | +0.1262 |
| training chips | 507 | 143 | 188 | 314 | 0.0884 | 0.1981 | +0.1097 |

Its closure is worse than raft on the validation chips and worse than it on the training chips.

A model trained on cross-date pairs has seen the dates of the training chips, so its closure there is a training score: it is reported, and the verdict is read on the validation set.

An EPE or a closure is a mean over the pairs or triplets neither of the two methods of a table fails, so a method's figure changes with the method it is read next to. A difference is the method read minus the one it is read next to: negative is better. A closure is worse with more failed triplets, or with as many and a higher mean.

**Verdict: gain.** On the validation set, raft_small_ft_cross_date fails 3 pairs where raft_small fails 328, and over the 3272 pairs neither fails its mean error is 0.1224 px where raft_small's is 0.2451 px: it beats raft_small.
