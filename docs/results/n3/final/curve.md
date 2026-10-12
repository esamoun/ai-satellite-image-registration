The cost curve of RAFT: the large and the small model, pretrained and fine-tuned, with 4, 8, 12 refinements. Error, failures and time are read on the benchmark's pairs of alps, libya4, under ONNX Runtime in `outputs/n3-curve/onnx` and the same models under PyTorch on the same pairs in `outputs/n3-curve/torch`, and memory in `outputs/n3-curve/footprint`. How each is measured is in docs/decisions.md.

ONNX Runtime on the CPU, 1800 pairs:

| model | weights | refinements | method | EPE (px) | failures | time (ms) | memory added (MiB) | whole process (MiB) |
|---|---|---:|---|---:|---:|---:|---:|---:|
| RAFT large | pretrained | 4 | raft_r4_onnx | 0.1299 | 0.2 % | 435.9 | 81.5 | 270.3 |
| RAFT large | pretrained | 8 | raft_r8_onnx | 0.0987 | 0.2 % | 680.1 | 83.9 | 272.7 |
| RAFT large | pretrained | 12 | raft_onnx | 0.0953 | 0.2 % | 911.7 | 86.1 | 275.0 |
| RAFT large | fine-tuned | 4 | raft_ft_r4_onnx | 0.0806 | 0.0 % | 458.3 | 81.5 | 270.3 |
| RAFT large | fine-tuned | 8 | raft_ft_r8_onnx | 0.0712 | 0.0 % | 685.6 | 83.8 | 272.5 |
| RAFT large | fine-tuned | 12 | raft_ft_onnx | 0.0692 | 0.0 % | 915.6 | 86.4 | 275.2 |
| RAFT small | pretrained | 4 | raft_small_r4_onnx | 0.2681 | 23.2 % | 144.6 | 45.3 | 234.1 |
| RAFT small | pretrained | 8 | raft_small_r8_onnx | 0.2356 | 4.5 % | 256.8 | 47.3 | 236.2 |
| RAFT small | pretrained | 12 | raft_small_onnx | 0.2116 | 2.2 % | 368.4 | 49.5 | 238.4 |
| RAFT small | fine-tuned | 4 | raft_small_ft_r4_onnx | 0.1509 | 0.0 % | 144.2 | 45.4 | 234.2 |
| RAFT small | fine-tuned | 8 | raft_small_ft_r8_onnx | 0.1317 | 0.0 % | 256.4 | 47.4 | 236.3 |
| RAFT small | fine-tuned | 12 | raft_small_ft_onnx | 0.1266 | 0.0 % | 367.0 | 49.7 | 238.4 |

The same models under PyTorch on the same CPU and pairs:

| model | weights | refinements | method | EPE (px) | failures | time (ms) | memory added (MiB) | whole process (MiB) | memory of a call (MiB) | largest gap with ONNX Runtime (px) | time on cuda (ms) |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RAFT large | pretrained | 4 | raft_r4 | 0.1299 | 0.2 % | 232.2 | 294.6 | 700.7 | 105.5 | 9.2e-05 | 21.6 |
| RAFT large | pretrained | 8 | raft_r8 | 0.0987 | 0.2 % | 294.7 | 294.9 | 701.6 | 105.5 | 1.7e-04 | 34.6 |
| RAFT large | pretrained | 12 | raft | 0.0953 | 0.2 % | 355.6 | 294.9 | 701.0 | 105.5 | 1.4e-04 | 46.2 |
| RAFT large | fine-tuned | 4 | raft_ft_r4 | 0.0806 | 0.0 % | 233.1 | 294.8 | 700.8 | 105.5 | 7.5e-07 | 22.9 |
| RAFT large | fine-tuned | 8 | raft_ft_r8 | 0.0712 | 0.0 % | 294.3 | 294.8 | 700.9 | 105.5 | 1.4e-06 | 34.4 |
| RAFT large | fine-tuned | 12 | raft_ft | 0.0692 | 0.0 % | 355.8 | 296.9 | 703.3 | 105.5 | 2.3e-06 | 46.0 |
| RAFT small | pretrained | 4 | raft_small_r4 | 0.2681 | 23.2 % | 50.0 | 79.7 | 486.0 | 23.9 | 2.3e-04 | 15.8 |
| RAFT small | pretrained | 8 | raft_small_r8 | 0.2356 | 4.5 % | 75.1 | 79.6 | 485.7 | 23.9 | 2.8e-03 | 22.4 |
| RAFT small | pretrained | 12 | raft_small | 0.2116 | 2.2 % | 100.4 | 83.6 | 490.1 | 25.0 | 6.5e-03 | 29.0 |
| RAFT small | fine-tuned | 4 | raft_small_ft_r4 | 0.1509 | 0.0 % | 49.9 | 79.7 | 485.7 | 23.9 | 6.9e-07 | 15.7 |
| RAFT small | fine-tuned | 8 | raft_small_ft_r8 | 0.1317 | 0.0 % | 75.0 | 83.7 | 489.9 | 23.9 | 1.3e-06 | 22.4 |
| RAFT small | fine-tuned | 12 | raft_small_ft | 0.1266 | 0.0 % | 100.2 | 83.6 | 489.7 | 25.0 | 9.1e-07 | 29.0 |

The other methods, on the same CPU and pairs:

| method | EPE (px) | failures | time (ms) | memory added (MiB) | whole process (MiB) |
|---|---:|---:|---:|---:|---:|
| raft_ft_r4_onnx_int8 | 0.0831 | 0.0 % | 232.1 | 77.6 | 266.5 |
| raft_ft_r8_onnx_int8 | 0.0733 | 0.0 % | 399.1 | 82.6 | 271.5 |
| raft_ft_onnx_int8 | 0.0712 | 0.0 % | 564.2 | 99.8 | 288.7 |
| phase_correlation | 0.2026 | 0.0 % | 5.0 | 0.0 | 173.5 |
| sift_ransac | 0.1278 | 3.9 % | 28.3 | 12.0 | 185.4 |
| arosics | 0.2286 | 12.1 % | 21.7 | 8.4 | 303.4 |

EPE is the mean error over non-failed pairs; time is the median over pairs of a call's time. Memory added is the rise of the resident high-water mark of a process that does nothing but call the method, above its mark with the method's runtime imported: the weights, what the runtime keeps and the working memory of a call, on one pair. The whole process is the mark itself. Both are lower bounds, and neither is the memory of a call that PyTorch's profiler reads. Each method was read in 3 processes and the median reading is given; from one process to another the memory added moves by up to 6.6 MiB (raft_ft_onnx).

Memory had not settled for sift_ransac, arosics: the last call still raised the mark.

Fewer refinements, under PyTorch on the same pairs, 1800 pairs:

| model | weights | refinements | all: EPE (px) | failures | against 12 (px) | clean: EPE (px) | failures | against 12 (px) | mild: EPE (px) | failures | against 12 (px) | hard: EPE (px) | failures | against 12 (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RAFT large | pretrained | 4 | 0.1299 | 0.2 % | +0.0346 | 0.0716 | 0.0 % | +0.0062 | 0.0805 | 0.0 % | +0.0087 | 0.2382 | 0.5 % | +0.0891 |
| RAFT large | pretrained | 8 | 0.0987 | 0.2 % | +0.0033 | 0.0669 | 0.0 % | +0.0015 | 0.0735 | 0.0 % | +0.0016 | 0.1559 | 0.5 % | +0.0069 |
| RAFT large | pretrained | 12 | 0.0953 | 0.2 % | n/a | 0.0654 | 0.0 % | n/a | 0.0718 | 0.0 % | n/a | 0.1491 | 0.5 % | n/a |
| RAFT large | fine-tuned | 4 | 0.0806 | 0.0 % | +0.0114 | 0.0546 | 0.0 % | +0.0096 | 0.0613 | 0.0 % | +0.0110 | 0.1259 | 0.0 % | +0.0135 |
| RAFT large | fine-tuned | 8 | 0.0712 | 0.0 % | +0.0020 | 0.0467 | 0.0 % | +0.0018 | 0.0520 | 0.0 % | +0.0017 | 0.1149 | 0.0 % | +0.0025 |
| RAFT large | fine-tuned | 12 | 0.0692 | 0.0 % | n/a | 0.0450 | 0.0 % | n/a | 0.0503 | 0.0 % | n/a | 0.1124 | 0.0 % | n/a |
| RAFT small | pretrained | 4 | 0.2681 | 23.2 % | +0.0968 | 0.1888 | 0.0 % | +0.0406 | 0.2199 | 0.0 % | +0.0578 | 0.6886 | 69.7 % | +0.4158 |
| RAFT small | pretrained | 8 | 0.2356 | 4.5 % | +0.0349 | 0.1556 | 0.0 % | +0.0074 | 0.1703 | 0.3 % | +0.0105 | 0.4025 | 13.2 % | +0.0945 |
| RAFT small | pretrained | 12 | 0.2116 | 2.2 % | n/a | 0.1482 | 0.0 % | n/a | 0.1598 | 0.3 % | n/a | 0.3343 | 6.2 % | n/a |
| RAFT small | fine-tuned | 4 | 0.1509 | 0.0 % | +0.0243 | 0.1073 | 0.0 % | +0.0132 | 0.1134 | 0.0 % | +0.0141 | 0.2321 | 0.0 % | +0.0456 |
| RAFT small | fine-tuned | 8 | 0.1317 | 0.0 % | +0.0051 | 0.0989 | 0.0 % | +0.0049 | 0.1049 | 0.0 % | +0.0055 | 0.1913 | 0.0 % | +0.0048 |
| RAFT small | fine-tuned | 12 | 0.1266 | 0.0 % | n/a | 0.0941 | 0.0 % | n/a | 0.0994 | 0.0 % | n/a | 0.1865 | 0.0 % | n/a |

Against 12 is the mean error minus that of the same model with 12 refinements, the count it was trained with, over the pairs neither fails: positive is worse. No model was retrained.

Held-out sites in this table: alps, libya4. They are kept for the final evaluation: no threshold, preset or variant may be chosen on their rows.
