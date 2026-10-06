The ablation: RAFT large fine-tuned on same-date pairs only (raft_ft_same_date) and on same-date and cross-date pairs (raft_ft_cross_date), next to the pretrained model (raft). Validation set of `outputs/ablation/validation`, real triplets of `outputs/ablation/validation-cycle`. The rule that chooses is in docs/decisions.md, written before either training ran.

The two trainings:

| | raft_ft_same_date | raft_ft_cross_date |
|---|---:|---:|
| run directory | `outputs/train/large-same-date` | `outputs/train/large-cross-date` |
| cross-date share | 0 | 0.5 |
| seed | 0 | 0 |
| steps done / budget | 10000 / 10000 | 10000 / 10000 |
| sessions | 1 | 1 |
| commit | 4429c35 | 4429c35 |
| median s/step | 3.05 | 3.31 |
| training loss, last tenth of the steps | 0.2070 | 0.4915 |
| validations | 21 | 21 |
| selection score, pretrained (px) | 0.1583 | 0.1583 |
| selection score, kept (px) | 0.0731 | 0.0854 |
| kept step | 10000 | 8500 |
| SHA-256 of `best.pt` | `3b722e8e77397ce4` | `44bcc668d20a6334` |

Settings the two runs were not given alike: pairs.cross_date. The device and the number of worker processes are not compared: a session may change them. The two training losses are not on the same pairs (a cross-date pair has a truth off by what its two dates are misregistered by), so they are not compared; the selection scores are, both being on the light validation set.

raft_ft_same_date next to raft, on the validation set:

| scenario | degradation | pairs | raft: failed | raft_ft_same_date: failed | neither fails | raft: EPE (px) | raft_ft_same_date: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.0447 | 0.0215 | -0.0232 |
| translation | mild | 400 | 0 | 0 | 400 | 0.0613 | 0.0248 | -0.0365 |
| translation | hard | 400 | 24 | 0 | 376 | 0.2118 | 0.0837 | -0.1281 |
| affine | clean | 400 | 0 | 0 | 400 | 0.0522 | 0.0289 | -0.0233 |
| affine | mild | 400 | 0 | 0 | 400 | 0.0702 | 0.0341 | -0.0361 |
| affine | hard | 400 | 23 | 0 | 377 | 0.2389 | 0.1218 | -0.1171 |
| dense | clean | 400 | 0 | 0 | 400 | 0.0923 | 0.0599 | -0.0324 |
| dense | mild | 400 | 0 | 0 | 400 | 0.1124 | 0.0712 | -0.0412 |
| dense | hard | 400 | 23 | 0 | 377 | 0.2751 | 0.1753 | -0.0998 |
| all | all | 3600 | 70 | 0 | 3530 | 0.1265 | 0.0679 | -0.0587 |

raft_ft_same_date beats raft on the validation set: it fails 0 pairs where raft fails 70, and over the 3530 pairs neither fails its mean error is 0.0679 px where raft's is 0.1265 px.

On the real triplets:

| chips | triplets | raft: failed | raft_ft_same_date: failed | neither fails | raft: closure (px) | raft_ft_same_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 78 | 0 | 163 | 0.2093 | 0.0939 | -0.1154 |
| training chips | 507 | 143 | 17 | 364 | 0.1354 | 0.0545 | -0.0809 |

Its closure is better than raft on the validation chips and better than it on the training chips.

raft_ft_cross_date next to raft, on the validation set:

| scenario | degradation | pairs | raft: failed | raft_ft_cross_date: failed | neither fails | raft: EPE (px) | raft_ft_cross_date: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.0447 | 0.0303 | -0.0144 |
| translation | mild | 400 | 0 | 0 | 400 | 0.0613 | 0.0350 | -0.0263 |
| translation | hard | 400 | 24 | 0 | 376 | 0.2118 | 0.1072 | -0.1045 |
| affine | clean | 400 | 0 | 0 | 400 | 0.0522 | 0.0364 | -0.0158 |
| affine | mild | 400 | 0 | 0 | 400 | 0.0702 | 0.0429 | -0.0273 |
| affine | hard | 400 | 23 | 0 | 377 | 0.2389 | 0.1378 | -0.1011 |
| dense | clean | 400 | 0 | 0 | 400 | 0.0923 | 0.0703 | -0.0220 |
| dense | mild | 400 | 0 | 0 | 400 | 0.1124 | 0.0818 | -0.0306 |
| dense | hard | 400 | 23 | 0 | 377 | 0.2751 | 0.1911 | -0.0840 |
| all | all | 3600 | 70 | 0 | 3530 | 0.1265 | 0.0802 | -0.0464 |

raft_ft_cross_date beats raft on the validation set: it fails 0 pairs where raft fails 70, and over the 3530 pairs neither fails its mean error is 0.0802 px where raft's is 0.1265 px.

On the real triplets:

| chips | triplets | raft: failed | raft_ft_cross_date: failed | neither fails | raft: closure (px) | raft_ft_cross_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 78 | 0 | 163 | 0.2093 | 0.0900 | -0.1193 |
| training chips | 507 | 143 | 5 | 364 | 0.1354 | 0.0483 | -0.0872 |

Its closure is better than raft on the validation chips and better than it on the training chips.

raft_ft_cross_date next to raft_ft_same_date, on the validation set:

| scenario | degradation | pairs | raft_ft_same_date: failed | raft_ft_cross_date: failed | neither fails | raft_ft_same_date: EPE (px) | raft_ft_cross_date: EPE (px) | difference (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| translation | clean | 400 | 0 | 0 | 400 | 0.0215 | 0.0303 | +0.0088 |
| translation | mild | 400 | 0 | 0 | 400 | 0.0248 | 0.0350 | +0.0102 |
| translation | hard | 400 | 0 | 0 | 400 | 0.0891 | 0.1139 | +0.0248 |
| affine | clean | 400 | 0 | 0 | 400 | 0.0289 | 0.0364 | +0.0075 |
| affine | mild | 400 | 0 | 0 | 400 | 0.0341 | 0.0429 | +0.0088 |
| affine | hard | 400 | 0 | 0 | 400 | 0.1300 | 0.1469 | +0.0168 |
| dense | clean | 400 | 0 | 0 | 400 | 0.0599 | 0.0703 | +0.0104 |
| dense | mild | 400 | 0 | 0 | 400 | 0.0712 | 0.0818 | +0.0106 |
| dense | hard | 400 | 0 | 0 | 400 | 0.1835 | 0.2013 | +0.0177 |
| all | all | 3600 | 0 | 0 | 3600 | 0.0714 | 0.0843 | +0.0129 |

On the real triplets:

| chips | triplets | raft_ft_same_date: failed | raft_ft_cross_date: failed | neither fails | raft_ft_same_date: closure (px) | raft_ft_cross_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| validation chips | 241 | 0 | 0 | 241 | 0.1221 | 0.1059 | -0.0163 |
| training chips | 507 | 17 | 5 | 490 | 0.1092 | 0.0827 | -0.0264 |

The closure of raft_ft_cross_date is better than raft_ft_same_date on the validation chips and better than it on the training chips. The validation chips decide. A model trained on cross-date pairs has seen the dates of the training chips, so its closure there is a training score: it is reported and decides nothing.

The same closure, one validation chip at a time:

| validation chip | triplets | raft_ft_same_date: failed | raft_ft_cross_date: failed | neither fails | raft_ft_same_date: closure (px) | raft_ft_cross_date: closure (px) | difference (px) |
|---|---:|---:|---:|---:|---:|---:|---:|
| santerre | 58 | 0 | 0 | 58 | 0.1568 | 0.1189 | -0.0379 |
| lyon | 55 | 0 | 0 | 55 | 0.0589 | 0.0670 | +0.0081 |
| morvan | 64 | 0 | 0 | 64 | 0.1740 | 0.1674 | -0.0067 |
| sete | 64 | 0 | 0 | 64 | 0.0933 | 0.0661 | -0.0272 |

An EPE or a closure is a mean over the pairs or triplets neither of the two methods of a table fails, so a method's figure changes with the method it is read next to. A difference is the method read minus the one it is read next to: negative is better. A closure is worse with more failed triplets, or with as many and a higher mean.

**What the rule gives.** Both variants beat the pretrained model on the validation set. On the real triplets of the validation chips, raft_ft_cross_date closes better than raft_ft_same_date: it is retained.
