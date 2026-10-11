Exported RAFT files copied to 8-bit integers, written next to them. A static copy computes every convolution on integers, with one scale per output channel, but the ones that read the flow or write its update and its upsampling weights; its scales are set by minmax on 36 pairs, pair 10 of every chip, scenario and preset of the validation set (santerre, lyon, morvan, sete). A dynamic copy stores the weights of its convolutions as integers and works out the other scales at each call. The correlation lookup, `GridSample`, has no integer version in ONNX Runtime and stays in float in both.

| file | from | kind | MB | float MB | int8 convolutions | float lookups | calibration pairs | SHA-256 |
|---|---|---|---:|---:|---:|---:|---:|---|
| `raft_large_ft_r12_int8.onnx` | `raft_large_ft_r12.onnx` | static | 7.1 | 21.5 | 165 of 190 | 48 | 36 | `97b6a8c7e0e66f008de4ffcc61030c03bc18a9587e236af8ef5173b12ccff609` |
| `raft_large_ft_r8_int8.onnx` | `raft_large_ft_r8.onnx` | static | 6.7 | 21.3 | 121 of 138 | 32 | 36 | `3d91f7b91ca04418de0f119c2d7738ed2272ace7b5548b290aa367dbb72e4dd3` |
| `raft_large_ft_r4_int8.onnx` | `raft_large_ft_r4.onnx` | static | 6.4 | 21.2 | 77 of 86 | 16 | 36 | `51b27700729010b0d2ecd67f8ebdb22619c8bcb3de1fbfd3ef81ecca63e05dd0` |
| `raft_small_ft_r12_int8.onnx` | `raft_small_ft_r12.onnx` | static | 2.0 | 4.3 | 128 of 152 | 48 | 36 | `32f8f2f851992dc01554495d6bac67612ba5dcbad5ea1bdd7687d5d9ab060f21` |
| `raft_large_ft_r12_int8_dynamic.onnx` | `raft_large_ft_r12.onnx` | dynamic | 6.3 | 21.5 | 190 of 190 | 48 |  | `94b9823eef594003e4676b4d8b32a3b5f68b4024ed2b763be5316f22d49d3e61` |
| `raft_small_ft_r12_int8_dynamic.onnx` | `raft_small_ft_r12.onnx` | dynamic | 1.9 | 4.3 | 152 of 152 | 48 |  | `93dc1bff0cd388dc5afd57e6e0af63bceb5a2a8b2ad613bdb5bacf2427729fa1` |
