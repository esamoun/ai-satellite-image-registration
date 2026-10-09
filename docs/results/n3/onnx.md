RAFT exported to ONNX (opset 17), one file per model, weights and refinement count, the image size left free. Parity is the largest difference between the file's flow under ONNX Runtime and PyTorch's on one 256 px pair, on the CPU; a file over 0.001 px is refused.

| file | model | weights | refinements | MB | parity with PyTorch (px) | SHA-256 |
|---|---|---|---:|---:|---:|---|
| `raft_large_r4.onnx` | RAFT large | `raft_large_C_T_SKHT_V2-ff5fadd5.pth` | 4 | 21.2 | 1.3e-05 | `9423fb88287f9cac25e81e3e2a8c66a1648bedaffb216f77db3aafd1bb137a89` |
| `raft_large_r8.onnx` | RAFT large | `raft_large_C_T_SKHT_V2-ff5fadd5.pth` | 8 | 21.3 | 1.7e-05 | `4f676bd522d6fbdad0888f241fb621740cf48cbd0dbd674e3a0ab2bacab5a85a` |
| `raft_large_r12.onnx` | RAFT large | `raft_large_C_T_SKHT_V2-ff5fadd5.pth` | 12 | 21.5 | 3.0e-05 | `9b94acd758745fa7498d44988e3e94a5e911fd88edb28a509bfead804d065d4f` |
| `raft_small_r4.onnx` | RAFT small | `raft_small_C_T_V2-01064c6d.pth` | 4 | 4.1 | 1.5e-05 | `631803dddd730f657a91a551af8dedfd5204714946676042a2c6e562525381c8` |
| `raft_small_r8.onnx` | RAFT small | `raft_small_C_T_V2-01064c6d.pth` | 8 | 4.2 | 2.9e-05 | `d8e6b62ba3e5dac15407533b1cf5ac0b34ff49270e7b701f079b1e0257c9eae6` |
| `raft_small_r12.onnx` | RAFT small | `raft_small_C_T_V2-01064c6d.pth` | 12 | 4.3 | 3.0e-05 | `23d2500b220d9bb713c855eab7648aaa1ace25226a35a51132bea7153eb164be` |
| `raft_large_ft_r4.onnx` | RAFT large | `raft_large_ft-44bcc668.pth` | 4 | 21.2 | 1.7e-05 | `c8ee13ca706020957af22b3f0b1a686e6bc562e010cfbc83c8ebbb6fa39b1ede` |
| `raft_large_ft_r8.onnx` | RAFT large | `raft_large_ft-44bcc668.pth` | 8 | 21.3 | 3.2e-05 | `813662803b0cca223bcde6a9c1be0f7d6c1e7e515301961624c2ebf8213afe2c` |
| `raft_large_ft_r12.onnx` | RAFT large | `raft_large_ft-44bcc668.pth` | 12 | 21.5 | 5.1e-05 | `da410478e79cb32343b6f8c2c0f88e53d0b93d192a1152d8b3e088aef242fcfe` |
| `raft_small_ft_r4.onnx` | RAFT small | `raft_small_ft-b666aaad.pth` | 4 | 4.1 | 1.5e-05 | `72fa35ab2a2c537a6f3dda9aacc057498cbd69a7ac676c6eee0352b189f17361` |
| `raft_small_ft_r8.onnx` | RAFT small | `raft_small_ft-b666aaad.pth` | 8 | 4.2 | 1.6e-05 | `7cac15615efd9ec3771421f6eab8daa3b19da78f21e86b2aba6a238fcbec6359` |
| `raft_small_ft_r12.onnx` | RAFT small | `raft_small_ft-b666aaad.pth` | 12 | 4.3 | 3.0e-05 | `c7671f015621fa28434bd9f39b61632ebec45650791fd6611ce2cecbddf4ed76` |
