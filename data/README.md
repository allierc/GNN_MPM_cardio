# Data

Two confluent sheets of human iPSC-derived cardiomyocytes on a 15 kPa gel, filmed at 24 frames per
second and tracked on a 137 x 137 lattice of points 15 px apart (18,769 points, flattened as
`n = y * 137 + x`). Only what the fit reads is here; the raw movies (2048 x 2048 px, 240 and 299
frames) and the tracker's full derivative stacks stay with the recording.

| specimen | folder | frames | cells |
|---|---|---|---|
| healthy | `healthy/` | 239 | 472 (331 inside the loss) |
| HCM | `hcm/` | 299 | 434 (298 inside the loss) |

## Files, per specimen

| file | content |
|---|---|
| `grid_flow.npz` | the tracked lattice positions over time, `[T, 18769, 2]` float32. Healthy: `pos`, already divided by the image width (2048 px), plus `vel` (frame-to-frame difference) and `ids`; HCM: `pos_px`, in image pixels as the tracker wrote them. `cardio/recording.py` maps both onto the sheet domain `[0.15, 0.85]` (world = 0.15 + 0.70 * x / 2048) and checks the array's sha256 before use. |
| `labels_nodes.npy` | `[18769]` int32, the cell label (1..C) of every tracking node, 0 = none |
| `labels_grid.npy` | the same as a `[137, 137]` image |
| `cells_2560.tif` | `[2560, 2560]` int32 label image for the engine's `label_image` field (row-flipped, nearest tracking node's label); the sheet fills rows/cols 384..2176 |
| `cell_centroids_world.npy` | `[C, 2]` cell centroids in world units |
| `nuclei.npy` | `[K, 3]` (row, col, sigma) of the detected nuclei that seeded the segmentation |
| `segmentation.json` | every detector setting tried and the one kept |
| `beats.json` (healthy) | speed-peak onsets `[2, 51, 101, 152, 204]` and the beat spans; the HCM onsets `[17, 61, 121, 181, 241]` are a constant in `recording.py` |
| `eval_mask.npy` (healthy) | `[18769]` bool, nodes inside the evaluated field (not used by the fit) |
| `noise_rest.npz` (healthy) | per-cell affine noise measured on the recording's own rest frames (`fit.py --noise rest`, planted-data tests only) |

The segmentation (`cardio/segmentation.py` + `cardio/seg/`) is deterministic and can be rebuilt
from the raw movie and its `.derivatives.npy`; the outputs shipped here are what the reference fits
used, and rebuilding is not needed to reproduce them.
