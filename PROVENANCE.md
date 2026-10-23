# Provenance

Extracted from the private Plexus repository on 2026-10-22, working tree at commit `7ebdd4af3b8d`.
The engine files are copied byte for byte; the prototype files are copied and then edited only where
a path pointed into the Plexus tree (the data folder, the label image, the discovery loop's data door) or
where a string named the recordings' source files. Every edit is listed by the `MODIFIED` flag below and
can be diffed against the named origin.

Uncommitted changes in the Plexus working tree at extraction time (copied as found):

    M src/plexus/engine.py
     M src/plexus/operators/contact_ops.py
     M src/plexus/operators/diffusion_reaction.py
     M src/plexus/operators/gastrulation_ops.py
     M src/plexus/operators/vertex_ops.py
     M src/plexus/tasks/trace_recording.py
     M src/plexus/trainer.py
    ?? prototype/cardio_mpm/strain/out/fits/full_plexus_hcm/
    ?? prototype/cardio_mpm/strain/out/fits/full_plexus_healthy/
    ?? prototype/cardio_mpm/strain/out/fits/full_plexus_healthy_2/
    ?? prototype/cardio_mpm/strain/out/fits/gate_plexus_healthy/

`src/plexus/engine.py` carried one uncommitted 11-line hunk (a per-tick cleanup of block-delta buffers for
chemistry on MPM cell sets, 2026-10-21); it does not touch the MPM particle/grid path the cardio spec runs.

## Code

| file here | origin in Plexus | state | sha256 (first 16) |
|---|---|---|---|
| `src/plexus/__init__.py` | `src/plexus/__init__.py` | identical | `93fd22bff64e6224` |
| `src/plexus/engine.py` | `src/plexus/engine.py` | identical | `15091b041463c9d0` |
| `src/plexus/schema.py` | `src/plexus/schema.py` | identical | `39fc2817aa18a089` |
| `src/plexus/paths.py` | `src/plexus/paths.py` | identical | `31861fa290086ae9` |
| `src/plexus/units.py` | `src/plexus/units.py` | identical | `e8edc2628b6de373` |
| `src/plexus/units_check.py` | `src/plexus/units_check.py` | identical | `f6bdfbb26332c668` |
| `src/plexus/geometry.py` | `src/plexus/geometry.py` | identical | `5d013892396c3da9` |
| `src/plexus/continuous_engine.py` | `src/plexus/continuous_engine.py` | identical | `f5da358a3e56f49f` |
| `src/plexus/shapes.py` | `src/plexus/shapes.py` | identical | `2c88377026f00b7b` |
| `src/plexus/models/__init__.py` | `src/plexus/models/__init__.py` | identical | `ece2acfb293329d9` |
| `src/plexus/models/base.py` | `src/plexus/models/base.py` | identical | `7c7abe98380fe1c4` |
| `src/plexus/models/registry.py` | `src/plexus/models/registry.py` | identical | `0c2d5aa0abb7d832` |
| `src/plexus/models/state.py` | `src/plexus/models/state.py` | identical | `c7060442f1608766` |
| `src/plexus/models/entities.py` | `src/plexus/models/entities.py` | identical | `4fc177a8cd94f84a` |
| `src/plexus/models/mesh.py` | `src/plexus/models/mesh.py` | identical | `56c524ab3bde50e3` |
| `src/plexus/models/topology.py` | `src/plexus/models/topology.py` | identical | `7035624c065cb432` |
| `src/plexus/models/hashgrid.py` | `src/plexus/models/hashgrid.py` | identical | `c9763d07c090836a` |
| `src/plexus/operators/mpm_ops.py` | `src/plexus/operators/mpm_ops.py` | identical | `7385f1caed4078c1` |
| `src/plexus/operators/motion_ops.py` | `src/plexus/operators/motion_ops.py` | identical | `9f0d78a535109aa7` |
| `src/plexus/operators/__init__.py` | `src/plexus/operators/__init__.py` | MODIFIED | `4d042059640f5527` |
| `cardio/fit.py` | `prototype/cardio_mpm/strain/fit.py` | MODIFIED | `2f798ad900c1c4e4` |
| `cardio/model.py` | `prototype/cardio_mpm/strain/model.py` | MODIFIED | `8e45bfd54fd0b757` |
| `cardio/recording.py` | `prototype/cardio_mpm/strain/recording.py` | MODIFIED | `fc361d7bfa98b08f` |
| `cardio/ops_percell.py` | `prototype/cardio_mpm/strain/ops_percell.py` | identical | `096cd687e5a4a78b` |
| `cardio/s4_score.py` | `prototype/cardio_mpm/strain/s4_score.py` | MODIFIED | `baa37c74c47a1adf` |
| `cardio/s4_residual.py` | `prototype/cardio_mpm/strain/s4_residual.py` | MODIFIED | `05d5a79414b83d84` |
| `cardio/fd_check.py` | `prototype/cardio_mpm/strain/fd_check.py` | MODIFIED | `d53d4ff6ae3a95d3` |
| `cardio/compare_sheets.py` | `prototype/cardio_mpm/strain/compare_sheets.py` | identical | `a618afb8b2b73f0c` |
| `cardio/segmentation.py` | `prototype/cardio_mpm/strain/segmentation.py` | MODIFIED | `9c5f40eddffce7ba` |
| `cardio/seg/README.md` | `prototype/cardio_mpm/strain/seg/README.md` | identical | `93830250d57efeae` |
| `cardio/seg/beat.py` | `prototype/cardio_mpm/strain/seg/beat.py` | identical | `58b1051dc5f767af` |
| `cardio/seg/seeded.py` | `prototype/cardio_mpm/strain/seg/seeded.py` | MODIFIED | `72b2175efecdbefa` |
| `cardio/seg/segment.py` | `prototype/cardio_mpm/strain/seg/segment.py` | identical | `a65f134a5d8ac08b` |
| `cardio/seg/strain.py` | `prototype/cardio_mpm/strain/seg/strain.py` | identical | `451cd2f4d6211bdb` |
| `cardio/seg/validate.py` | `prototype/cardio_mpm/strain/seg/validate.py` | identical | `2319178efde71685` |
| `docs/SUMMARY.md` | `prototype/cardio_mpm/strain/SUMMARY.md` | MODIFIED | `bafad5c480ccf5d9` |

## Data

| file here | origin | relation |
|---|---|---|
| `data/healthy/grid_flow.npz` | `prototype/cardio_mpm/cardio_real.npz` | re-saved: `pos`, `vel`, `ids`, `dt` byte-identical; the `source` string replaced |
| `data/healthy/beats.json` | `discovery_cardio_mpm/_data/split.json` | the onsets and spans recording.load reads, extracted |
| `data/healthy/eval_mask.npy` | `discovery_cardio_mpm/_data/eval_mask.npy` | identical |
| `data/hcm/grid_flow.npz` | `the HCM recording's tracker derivatives file` | `pos_px` = channels 0:2 as float32, exactly the array recording.load built from the raw file |
| `data/healthy/labels_grid.npy` | `prototype/cardio_mpm/strain/data/labels_grid.npy` | identical |
| `data/healthy/labels_nodes.npy` | `prototype/cardio_mpm/strain/data/labels_nodes.npy` | identical |
| `data/healthy/cell_centroids_world.npy` | `prototype/cardio_mpm/strain/data/cell_centroids_world.npy` | identical |
| `data/healthy/nuclei.npy` | `prototype/cardio_mpm/strain/data/nuclei.npy` | identical |
| `data/healthy/cells_2560.tif` | `prototype/cardio_mpm/strain/data/cells_2560.tif` | identical |
| `data/healthy/noise_rest.npz` | `prototype/cardio_mpm/strain/data/noise_rest.npz` | identical |
| `data/healthy/segmentation.json` | `prototype/cardio_mpm/strain/data/segmentation.json` | `source` string replaced |
| `data/hcm/labels_grid.npy` | `prototype/cardio_mpm/strain/data_hcm/labels_grid.npy` | identical |
| `data/hcm/labels_nodes.npy` | `prototype/cardio_mpm/strain/data_hcm/labels_nodes.npy` | identical |
| `data/hcm/cell_centroids_world.npy` | `prototype/cardio_mpm/strain/data_hcm/cell_centroids_world.npy` | identical |
| `data/hcm/nuclei.npy` | `prototype/cardio_mpm/strain/data_hcm/nuclei.npy` | identical |
| `data/hcm/cells_2560.tif` | `prototype/cardio_mpm/strain/data_hcm/cells_2560.tif` | identical |
| `data/hcm/segmentation.json` | `prototype/cardio_mpm/strain/data_hcm/segmentation.json` | `source` string replaced |

Content identities checked by `cardio/recording.py` at load time:

    sha256(data/healthy/grid_flow.npz['pos'])    e5fb1774286545923e6dd97f62e9f64891686d8080c43fee09d9fc2ba8ecc725
    sha256(data/hcm/grid_flow.npz['pos_px'])     4a544cf8a813a93aa04398bc87157adad3edfe6a3866f6ded7c84eecc3f30f36

## Reference fits

Produced 2026-09-12 in the Plexus tree on one NVIDIA RTX A6000 (48 GB), Python 3.12.12,
torch 2.9.0+cu128, numpy 2.2.6; `fit.json` records every flag, the per-iteration loss and the wall time.

| file here | origin | relation |
|---|---|---|
| `reference/healthy_allbeats/fit.json` | `prototype/cardio_mpm/strain/out/fits/healthy_allbeats/fit.json` | identical |
| `reference/healthy_allbeats/params.npz` | `prototype/cardio_mpm/strain/out/fits/healthy_allbeats/params.npz` | identical |
| `reference/healthy_allbeats/s4_score.json` | `prototype/cardio_mpm/strain/out/fits/healthy_allbeats/s4_score.json` | identical |
| `reference/healthy_allbeats/residual.json` | `prototype/cardio_mpm/strain/out/fits/healthy_allbeats/residual.json` | identical |
| `reference/hcm_allbeats/fit.json` | `prototype/cardio_mpm/strain/out/fits/hcm_allbeats/fit.json` | identical |
| `reference/hcm_allbeats/params.npz` | `prototype/cardio_mpm/strain/out/fits/hcm_allbeats/params.npz` | identical |
| `reference/hcm_allbeats/s4_score.json` | `prototype/cardio_mpm/strain/out/fits/hcm_allbeats/s4_score.json` | identical |

## What was left behind

- the rest of the Plexus operator library (vertex, membrane, chemistry, neural ... operators), its trainer, GUI, renderers and movie tools;
- the discovery loop (`discovery_cardio_mpm/`) and its seal machinery: this repository reads two data files and checks their content hashes instead;
- the strain prototype's figure and movie scripts (`figures.py`, `movie*.py`, `render_progress.sh`) and its intermediate fit directories;
- the raw microscope movies and the tracker's full derivatives files; only the grid positions the fit reads are shipped.
