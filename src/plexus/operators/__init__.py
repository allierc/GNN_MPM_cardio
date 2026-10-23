"""The operator library, trimmed to what the cardiomyocyte sheet instantiates.

Plexus proper ships twenty-odd mechanism modules; the cardio spec (`cardio/model.py: build_spec`)
resolves to exactly two of them, and importing this package self-registers both:

    mpm_ops      MLS-MPM: the `mpm_grid` and `label_image` fields, `seed_from_segmentation`,
                 `mpm_anchor`, and the four-step cycle `mpm_strain` / `mpm_scatter` /
                 `mpm_grid_update` / `mpm_gather` in their `implementation: differentiable` bodies
    motion_ops   `drag`, the Stokes drag on every material point

Both files are byte-identical to the Plexus originals (see PROVENANCE.md); the per-cell substrate
spring `anchor_percell` is the prototype's own and registers from `cardio/ops_percell.py`.
"""
from __future__ import annotations

from . import motion_ops   # noqa: F401  drag
from . import mpm_ops      # noqa: F401  mpm_grid, label_image, seed_from_segmentation, mpm_anchor, mpm_*

__all__ = ["motion_ops", "mpm_ops"]
