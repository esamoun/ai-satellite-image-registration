The cost curve of RAFT: the large and the small model, pretrained and fine-tuned, with 4, 8, 12 refinements. Error, failures and time are read on the light validation set of `outputs/curve/onnx-light`, the same models under PyTorch on that of `outputs/curve/torch-light`, memory in `outputs/curve/footprint`, and the refinement counts on the full validation set of `outputs/curve/validation`. How each is measured is in docs/decisions.md.

ONNX Runtime on the CPU, 360 pairs:

| model | weights | refinements | method | EPE (px) | failures | time (ms) | memory added (MiB) | whole process (MiB) |
|---|---|---:|---|---:|---:|---:|---:|---:|
| RAFT large | pretrained | 4 | raft_r4_onnx | 0.1814 | 8.3 % | 445.6 | 81.4 | 269.0 |
| RAFT large | pretrained | 8 | raft_r8_onnx | 0.1251 | 4.7 % | 674.9 | 83.9 | 271.6 |
| RAFT large | pretrained | 12 | raft_onnx | 0.1243 | 3.9 % | 905.5 | 86.2 | 273.8 |
| RAFT large | fine-tuned | 4 | raft_ft_r4_onnx | 0.0963 | 0.0 % | 464.3 | 81.4 | 269.0 |
| RAFT large | fine-tuned | 8 | raft_ft_r8_onnx | 0.0878 | 0.0 % | 713.0 | 83.8 | 271.5 |
| RAFT large | fine-tuned | 12 | raft_ft_onnx | 0.0854 | 0.0 % | 963.7 | 86.2 | 273.8 |
| RAFT small | pretrained | 4 | raft_small_r4_onnx | 0.2294 | 31.9 % | 144.6 | 45.4 | 233.0 |
| RAFT small | pretrained | 8 | raft_small_r8_onnx | 0.2451 | 15.6 % | 260.9 | 47.5 | 235.0 |
| RAFT small | pretrained | 12 | raft_small_onnx | 0.2448 | 10.3 % | 374.8 | 49.6 | 237.3 |
| RAFT small | fine-tuned | 4 | raft_small_ft_r4_onnx | 0.1680 | 1.7 % | 141.3 | 45.2 | 232.9 |
| RAFT small | fine-tuned | 8 | raft_small_ft_r8_onnx | 0.1461 | 0.0 % | 252.8 | 47.5 | 235.1 |
| RAFT small | fine-tuned | 12 | raft_small_ft_onnx | 0.1424 | 0.0 % | 360.0 | 49.6 | 237.1 |

The same models under PyTorch on the same CPU and pairs:

| model | weights | refinements | method | EPE (px) | failures | time (ms) | memory added (MiB) | whole process (MiB) | memory of a call (MiB) | largest gap with ONNX Runtime (px) |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| RAFT large | pretrained | 4 | raft_r4 | 0.1814 | 8.3 % | 239.2 | 294.8 | 699.5 | 105.5 | 2.2e-03 |
| RAFT large | pretrained | 8 | raft_r8 | 0.1251 | 4.7 % | 304.9 | 295.1 | 699.9 | 105.5 | 4.3e-02 |
| RAFT large | pretrained | 12 | raft | 0.1243 | 3.9 % | 371.1 | 295.5 | 701.0 | 105.5 | 2.0e-01 |
| RAFT large | fine-tuned | 4 | raft_ft_r4 | 0.0963 | 0.0 % | 239.2 | 295.0 | 699.8 | 105.5 | 7.1e-07 |
| RAFT large | fine-tuned | 8 | raft_ft_r8 | 0.0878 | 0.0 % | 304.8 | 295.0 | 699.9 | 105.5 | 1.6e-06 |
| RAFT large | fine-tuned | 12 | raft_ft | 0.0854 | 0.0 % | 371.1 | 297.4 | 702.4 | 105.5 | 2.2e-06 |
| RAFT small | pretrained | 4 | raft_small_r4 | 0.2294 | 31.9 % | 52.6 | 79.9 | 484.7 | 23.9 | 7.4e-04 |
| RAFT small | pretrained | 8 | raft_small_r8 | 0.2451 | 15.6 % | 79.6 | 79.9 | 485.0 | 23.9 | 6.0e-02 |
| RAFT small | pretrained | 12 | raft_small | 0.2448 | 10.3 % | 106.5 | 83.8 | 489.4 | 25.0 | 1.0e+00 |
| RAFT small | fine-tuned | 4 | raft_small_ft_r4 | 0.1680 | 1.7 % | 52.5 | 79.9 | 485.0 | 23.9 | 1.2e-06 |
| RAFT small | fine-tuned | 8 | raft_small_ft_r8 | 0.1461 | 0.0 % | 79.4 | 83.7 | 489.0 | 23.9 | 1.1e-06 |
| RAFT small | fine-tuned | 12 | raft_small_ft | 0.1424 | 0.0 % | 106.2 | 83.7 | 488.2 | 25.0 | 1.4e-06 |

The other methods, on the same CPU and pairs:

| method | EPE (px) | failures | time (ms) | memory added (MiB) | whole process (MiB) |
|---|---:|---:|---:|---:|---:|
| phase_correlation | 0.2165 | 1.7 % | 5.3 | 0.0 | 172.1 |
| sift_ransac | 0.1257 | 16.9 % | 21.0 | 12.2 | 184.4 |
| arosics | 0.2138 | 19.7 % | 19.4 | 8.3 | 301.9 |

EPE is the mean error over non-failed pairs; time is the median over pairs of a call's time. Memory added is the rise of the resident high-water mark of a process that does nothing but call the method, above its mark with the method's runtime imported: the weights, what the runtime keeps and the working memory of a call, on one pair. The whole process is the mark itself. Both are lower bounds, and neither is the memory of a call that PyTorch's profiler reads. Each method was read in 3 processes and the median reading is given; from one process to another the memory added moves by up to 2.0 MiB (raft_r4_onnx).

Memory had not settled for sift_ransac: the last call still raised the mark.

Fewer refinements, under PyTorch on the full validation set, 3600 pairs:

| model | weights | refinements | all: EPE (px) | failures | against 12 (px) | clean: EPE (px) | failures | against 12 (px) | mild: EPE (px) | failures | against 12 (px) | hard: EPE (px) | failures | against 12 (px) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RAFT large | pretrained | 4 | 0.1777 | 6.9 % | +0.0660 | 0.0717 | 0.0 % | +0.0086 | 0.0929 | 0.0 % | +0.0116 | 0.4185 | 20.8 % | +0.2074 |
| RAFT large | pretrained | 8 | 0.1312 | 2.9 % | +0.0102 | 0.0648 | 0.0 % | +0.0017 | 0.0831 | 0.0 % | +0.0018 | 0.2566 | 8.7 % | +0.0286 |
| RAFT large | pretrained | 12 | 0.1265 | 1.9 % | n/a | 0.0631 | 0.0 % | n/a | 0.0813 | 0.0 % | n/a | 0.2420 | 5.8 % | n/a |
| RAFT large | fine-tuned | 4 | 0.0974 | 0.0 % | +0.0130 | 0.0561 | 0.0 % | +0.0104 | 0.0645 | 0.0 % | +0.0113 | 0.1715 | 0.0 % | +0.0174 |
| RAFT large | fine-tuned | 8 | 0.0861 | 0.0 % | +0.0018 | 0.0473 | 0.0 % | +0.0016 | 0.0550 | 0.0 % | +0.0018 | 0.1559 | 0.0 % | +0.0019 |
| RAFT large | fine-tuned | 12 | 0.0843 | 0.0 % | n/a | 0.0457 | 0.0 % | n/a | 0.0532 | 0.0 % | n/a | 0.1540 | 0.0 % | n/a |
| RAFT small | pretrained | 4 | 0.2247 | 32.3 % | +0.0629 | 0.1820 | 0.0 % | +0.0412 | 0.2474 | 0.4 % | +0.0708 | 0.7986 | 96.5 % | +0.4575 |
| RAFT small | pretrained | 8 | 0.2531 | 15.3 % | +0.0383 | 0.1481 | 0.0 % | +0.0073 | 0.1871 | 0.3 % | +0.0109 | 0.5667 | 45.6 % | +0.1454 |
| RAFT small | pretrained | 12 | 0.2451 | 9.1 % | n/a | 0.1408 | 0.0 % | n/a | 0.1759 | 0.4 % | n/a | 0.4823 | 26.9 % | n/a |
| RAFT small | fine-tuned | 4 | 0.1707 | 1.1 % | +0.0371 | 0.1035 | 0.0 % | +0.0131 | 0.1153 | 0.0 % | +0.0152 | 0.2975 | 3.2 % | +0.0844 |
| RAFT small | fine-tuned | 8 | 0.1417 | 0.2 % | +0.0048 | 0.0936 | 0.0 % | +0.0031 | 0.1036 | 0.0 % | +0.0035 | 0.2285 | 0.7 % | +0.0078 |
| RAFT small | fine-tuned | 12 | 0.1376 | 0.1 % | n/a | 0.0905 | 0.0 % | n/a | 0.1000 | 0.0 % | n/a | 0.2225 | 0.2 % | n/a |

Against 12 is the mean error minus that of the same model with 12 refinements, the count it was trained with, over the pairs neither fails: positive is worse. No model was retrained.
