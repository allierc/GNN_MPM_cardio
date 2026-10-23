# GNN_MPM_cardio

Per-cell active-strain model of a beating cardiomyocyte sheet, fitted by gradient descent through a
differentiable material-point (MPM) simulation to the tracked motion of two recordings:
one healthy sheet and one carrying a hypertrophic cardiomyopathy (HCM) mutation. This repository
is the part of the Plexus code base that those two fits run on, with the data they read and the
fitted results they produced, so that the fits can be rerun and checked outside Plexus.

`docs/SUMMARY.md` says what the model is, what each learnable means, what was measured and what
may be claimed. `PROVENANCE.md` lists every file against its origin.

## Layout

| path | what |
|---|---|
| `src/plexus/` | the engine: `engine.py` (the tick loop, autograd-safe), `schema.py` (spec loading), the set/level data model in `models/`, and the two operator modules the spec uses (`operators/mpm_ops.py`: grid, label-image field, segmentation seed, substrate anchor, the differentiable MLS-MPM cycle; `operators/motion_ops.py`: drag) |
| `cardio/model.py` | the spec (`build_spec`), the learnables (`Params`), the rollout that injects the active strain once per frame, the per-cell affine loss |
| `cardio/recording.py` | the recordings in world units, the per-cell least-squares affine map (the observable, same function for model and data), beat windows |
| `cardio/fit.py` | the optimiser (Adam, one rollout per beat, gradients accumulated) |
| `cardio/s4_score.py` | per-beat R² of the strain maps and displacements next to the replay and do-nothing baselines |
| `cardio/ops_percell.py` | the per-cell substrate spring, registered from here (not part of the engine) |
| `cardio/fd_check.py`, `s4_residual.py`, `compare_sheets.py` | gradient check against central differences; residual by component and time; healthy-vs-HCM table |
| `cardio/segmentation.py`, `cardio/seg/` | how the cell labels were made from the raw movie (needs the movie; outputs are shipped under `data/`) |
| `data/healthy/`, `data/hcm/` | the tracked grid positions ("grid flow"), cell labels, label image, beat onsets; see `data/README.md` |
| `specs/` | the engine spec each beat's rollout runs, rendered to YAML (`build_spec` writes the same dict at run time) |
| `configs/` | every flag of the two reporting fits, as recorded by `fit.py` |
| `scripts/run_healthy_allbeats.sh`, `scripts/run_hcm_allbeats.sh` | the two reporting fits, flags as recorded, followed by the scorer |
| `reference/` | the reporting fits as produced in Plexus: `fit.json` (config + per-iteration loss), `params.npz` (every learnable), `s4_score.json` |
| `tools/compare_fits.py` | loss log, parameters and scores of two fit directories side by side, with a tolerance verdict |
| `parity/` | the record of rerunning both fits from this repository against the Plexus tree |
| `docs/` | the note `plexus_cardio_note.pdf` with its source and figures; `cont_overlay_particles.mp4`, the healthy fit against the recording over beats 1-3 in one rollout (made by `scripts/make_cont_overlay_particles.sh`) |

## Install

Python >= 3.10 with a CUDA build of PyTorch. The reference fits used Python 3.12.12, torch 2.9.0+cu128,
numpy 2.2.6, scipy 1.16.2, tifffile 2025.10.16, pyyaml 6.0.3.

    pip install -e .                 # torch, numpy, scipy, pyyaml, tifffile
    pip install -e .[figures]        # + matplotlib, for compare_sheets.py

`warp-lang` is optional: the MPM module imports it if present for its GPU kernels, but the cardio
spec names `implementation: differentiable`, the pure-torch bodies, and never calls them.

## Run

    scripts/run_healthy_allbeats.sh --device cuda:0        # ~110 min, 36 GB GPU memory
    scripts/run_hcm_allbeats.sh --device cuda:0            # ~150 min, 38 GB GPU memory

Each script runs `cardio/fit.py` with the recorded flags (250 iterations of Adam over 120
material points per cell on a 128² grid, one rollout per beat: 3 beats healthy, 4 HCM), then
`cardio/s4_score.py` on the result. Any flag after the script name is passed through and overrides
(`--tag`, `--iters`, `--per-parent`, ...). Output: `cardio/out/fits/<tag>/fit.json`, `params.npz`,
`params_p20.npz`, `params_p50.npz` (checkpoints at 20% and 50% of the run), `s4_score.json`.

A cheap end-to-end check (two iterations, 8 points per cell, 48² grid, first 10 frames; a few
minutes, under 4 GB):

    scripts/run_healthy_allbeats.sh --tag smoke --iters 2 --per-parent 8 --n-grid 48 --fit-frames 10 --checkpoints ''

Compare any two fit directories:

    python tools/compare_fits.py cardio/out/fits/healthy_allbeats reference/healthy_allbeats

## What the reporting fits returned

Per beat, R² of the per-cell strain maps (A) and of the per-cell displacements (u) against the
recording, cells touching the prescribed edge band excluded (`reference/*/s4_score.json`):

| | beat 1 | beat 2 | beat 3 | beat 4 | replay baseline |
|---|---|---|---|---|---|
| healthy, R²(A) | 0.870 | 0.872 | 0.871 | | 0.98 |
| healthy, R²(u) | 0.935 | 0.937 | 0.935 | | 0.96 |
| HCM, R²(A) | 0.894 | 0.900 | 0.898 | 0.898 | |
| HCM, R²(u) | 0.949 | 0.958 | 0.958 | 0.958 | |

Every beat is fitted (this is parameter estimation, not a learning task), so these are consistency
numbers; the spread across beats (0.002 healthy, 0.006 HCM) is the point. Final loss 0.1939
(healthy) and 0.1536 (HCM), from 1.778 and 1.566 at iteration 0.

## Reproducibility

The MPM scatter accumulates with `index_add`, whose CUDA kernel is atomic and reorders run to run;
in float32 the same fit differs from itself at about 1e-6 of the loss per rollout (Plexus
`fd_check`, float64: 1e-15). Two runs agree in their loss log to that order and in their
parameters to a small fraction of each map's spread; `parity/` records what was measured for the
runs from this repository against the Plexus tree on the same GPU model. The GPU model matters for
the last digits; the fitted maps do not depend on it (two seeds and two layouts agree per cell at
r = 0.9, `docs/SUMMARY.md` section 4).

## The model in one paragraph

Every particle belongs to one measured cell j. Once a frame the deformation gradient of its
particles is multiplied on the left by `I + c_j(t) (g_j f_j f_jᵀ + g2_j f⊥_j f⊥_jᵀ)`, sized so the
accumulated active part is exactly `I + γ_j(t) (g_j f_j f_jᵀ + g2_j f⊥_j f⊥_jᵀ)`: g_j the active
shortening along the fibre axis f_j = (cos φ_j, sin φ_j) at full activation (a strain), g2_j the
active strain across it (negative = thickening), γ_j(t) in [0, 1] the cell's activation, a shared
four-number clock shifted by a per-cell delay δ_j and scaled per cell, plus two shared temporal
modes with per-cell weights. Each cell has a Young's modulus E_j (shrunk toward uniform, reported
but not claimed) and a substrate spring κ_j. The sheet sits on a substrate spring κ = 10⁴ with
drag 150; the outer 0.03 of the domain is driven by the recording because the field is a crop of a
larger monolayer. The observable is the per-cell least-squares affine map (A_j(t), u_j(t)) over the
cell's tracking nodes or particles; the loss is the mean squared mismatch of A and u, each scaled by
the recording's own spread, over the ~330 cells away from the edge band.
