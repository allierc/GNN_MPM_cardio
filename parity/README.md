# Parity with the Plexus tree

The nominal fits rerun from this repository and from the Plexus tree on the same day, same GPU model (NVIDIA RTX PRO 6000 Blackwell (97 GB)),
same environment (Python 3.12.12, torch 2.9.0+cu128), same seed and flags (`configs/*.json`). Every number below is
`tools/compare_fits.py` on the two fit directories; the full output of each comparison is the `.txt` beside this file,
and the compared fits themselves are under `runs/` (`fit.json`, `params.npz`, `s4_score.json`).

| comparison | max relative loss difference over the log | worst claimed map, max difference / map spread | largest R² difference | file |
|---|---|---|---|---|
| 3 iterations, repo vs Plexus | 1.1e-06 | 6.3e-03 (delay) | - | `healthy_gate_repo_vs_plexus.txt` |
| 250 iterations, repo vs Plexus | 1.9e-05 | 7.3e-03 (delay) | 2.0e-06 | `healthy_repo_vs_plexus.txt` |
| 250 iterations, Plexus vs Plexus (floor) | 2.2e-05 | 3.2e-02 (delay) | 3.9e-06 | `healthy_plexus_vs_plexus.txt` |
| 250 iterations, repo vs the archived fit (RTX A6000, 2026-09-12) | 1.6e-05 | 2.3e-02 (delay) | 2.1e-06 | `healthy_repo_vs_reference.txt` |
| 250 iterations, repo vs Plexus | 1.3e-04 | 1.0e-01 (g) | 2.7e-05 | `hcm_repo_vs_plexus.txt` |
| 250 iterations, repo vs the archived fit (RTX A6000, 2026-09-12) | 1.0e-04 | 9.8e-02 (g2) | 1.7e-05 | `hcm_repo_vs_reference.txt` |

Reading the table: the `Plexus vs Plexus` row is the floor set by float32 atomic adds in the MPM scatter
(two runs of the SAME code on the same GPU); a `repo vs Plexus` row at that floor means the extraction changed
nothing. Plexus's strict mode (`PLEXUS_STRICT_DETERMINISM=1`, `torch.use_deterministic_algorithms(True)`) cannot
be used to remove the floor on this path: the segmentation seed calls `torch.bincount` on CUDA, which has no
deterministic kernel, and the engine refuses to run with `warn_only`. The `vs the archived fit` rows compare
against a different GPU generation and date, so they measure the fit's reproducibility as a whole, not the extraction.
