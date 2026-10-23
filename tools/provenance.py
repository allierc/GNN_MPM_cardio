#!/usr/bin/env python
"""provenance -- regenerate PROVENANCE.md: every file here against its origin in the Plexus tree.

    python tools/provenance.py --plexus /path/to/Plexus
"""
import argparse, datetime, hashlib, os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plexus", required=True)
    a = ap.parse_args()
    P = a.plexus; S = f"{P}/prototype/cardio_mpm/strain"
    head = subprocess.run(["git", "-C", P, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", P, "status", "--short", "src/plexus", "prototype/cardio_mpm/strain"],
                           capture_output=True, text=True).stdout.strip().splitlines()
    pairs = [(f"src/plexus/{f}", f"src/plexus/{f}") for f in
             ["__init__.py", "engine.py", "schema.py", "paths.py", "units.py", "units_check.py", "geometry.py", "continuous_engine.py", "shapes.py"]]
    pairs += [(f"src/plexus/models/{f}", f"src/plexus/models/{f}") for f in
              ["__init__.py", "base.py", "registry.py", "state.py", "entities.py", "mesh.py", "topology.py", "hashgrid.py"]]
    pairs += [(f"src/plexus/operators/{f}", f"src/plexus/operators/{f}") for f in ["mpm_ops.py", "motion_ops.py", "__init__.py"]]
    pairs += [(f"cardio/{f}", f"prototype/cardio_mpm/strain/{f}") for f in
              ["fit.py", "model.py", "recording.py", "ops_percell.py", "s4_score.py", "s4_residual.py", "fd_check.py", "compare_sheets.py", "segmentation.py"]]
    pairs += [(f"cardio/seg/{f}", f"prototype/cardio_mpm/strain/seg/{f}") for f in ["README.md", "beat.py", "seeded.py", "segment.py", "strain.py", "validate.py"]]
    pairs += [("docs/SUMMARY.md", "prototype/cardio_mpm/strain/SUMMARY.md")]
    rows = []
    for here, there in pairs:
        x = sha(f"{ROOT}/{here}"); y = sha(f"{P}/{there}") if os.path.exists(f"{P}/{there}") else None
        rows.append((here, there, "identical" if x == y else ("MODIFIED" if y else "new"), x[:16]))
    data_rows = [
        ("data/healthy/grid_flow.npz", "prototype/cardio_mpm/cardio_real.npz", "re-saved: `pos`, `vel`, `ids`, `dt` byte-identical; the `source` string replaced"),
        ("data/healthy/beats.json", "discovery_cardio_mpm/_data/split.json", "the onsets and spans recording.load reads, extracted"),
        ("data/healthy/eval_mask.npy", "discovery_cardio_mpm/_data/eval_mask.npy", "identical"),
        ("data/hcm/grid_flow.npz", "the HCM recording's tracker derivatives file", "`pos_px` = channels 0:2 as float32, exactly the array recording.load built from the raw file")]
    for f in ["labels_grid.npy", "labels_nodes.npy", "cell_centroids_world.npy", "nuclei.npy", "cells_2560.tif", "noise_rest.npz", "segmentation.json"]:
        same = sha(f"{ROOT}/data/healthy/{f}") == sha(f"{S}/data/{f}")
        data_rows.append((f"data/healthy/{f}", f"prototype/cardio_mpm/strain/data/{f}", "identical" if same else ("`source` string replaced" if f.endswith(".json") else "DIFFER")))
    for f in ["labels_grid.npy", "labels_nodes.npy", "cell_centroids_world.npy", "nuclei.npy", "cells_2560.tif", "segmentation.json"]:
        same = sha(f"{ROOT}/data/hcm/{f}") == sha(f"{S}/data_hcm/{f}")
        data_rows.append((f"data/hcm/{f}", f"prototype/cardio_mpm/strain/data_hcm/{f}", "identical" if same else ("`source` string replaced" if f.endswith(".json") else "DIFFER")))
    ref_rows = []
    for tag, files in (("healthy_allbeats", ["fit.json", "params.npz", "s4_score.json", "residual.json"]), ("hcm_allbeats", ["fit.json", "params.npz", "s4_score.json"])):
        for f in files:
            same = sha(f"{ROOT}/reference/{tag}/{f}") == sha(f"{S}/out/fits/{tag}/{f}")
            ref_rows.append((f"reference/{tag}/{f}", f"prototype/cardio_mpm/strain/out/fits/{tag}/{f}", "identical" if same else "DIFFER"))
    md = ["# Provenance", "",
          f"Extracted from the private Plexus repository on {datetime.date.today().isoformat()}, working tree at commit `{head[:12]}`.",
          "The engine files are copied byte for byte; the prototype files are copied and then edited only where",
          "a path pointed into the Plexus tree (the data folder, the label image, the discovery loop's data door) or",
          "where a string named the recordings' source files. Every edit is listed by the `MODIFIED` flag below and",
          "can be diffed against the named origin.", "",
          "Uncommitted changes in the Plexus working tree at extraction time (copied as found):", ""]
    md += [f"    {l}" for l in dirty] or ["    (none)"]
    md += ["", "`src/plexus/engine.py` carried one uncommitted 11-line hunk (a per-tick cleanup of block-delta buffers for",
           "chemistry on MPM cell sets, 2026-10-21); it does not touch the MPM particle/grid path the cardio spec runs.", "",
           "## Code", "", "| file here | origin in Plexus | state | sha256 (first 16) |", "|---|---|---|---|"]
    md += [f"| `{h}` | `{t}` | {s} | `{x}` |" for h, t, s, x in rows]
    md += ["", "## Data", "", "| file here | origin | relation |", "|---|---|---|"]
    md += [f"| `{h}` | `{t}` | {s} |" for h, t, s in data_rows]
    md += ["", "Content identities checked by `cardio/recording.py` at load time:", "",
           "    sha256(data/healthy/grid_flow.npz['pos'])    e5fb1774286545923e6dd97f62e9f64891686d8080c43fee09d9fc2ba8ecc725",
           "    sha256(data/hcm/grid_flow.npz['pos_px'])     4a544cf8a813a93aa04398bc87157adad3edfe6a3866f6ded7c84eecc3f30f36", "",
           "## Reference fits", "", "Produced 2026-09-12 in the Plexus tree on one NVIDIA RTX A6000 (48 GB), Python 3.12.12,",
           "torch 2.9.0+cu128, numpy 2.2.6; `fit.json` records every flag, the per-iteration loss and the wall time.", "",
           "| file here | origin | relation |", "|---|---|---|"]
    md += [f"| `{h}` | `{t}` | {s} |" for h, t, s in ref_rows]
    md += ["", "## What was left behind", "",
           "- the rest of the Plexus operator library (vertex, membrane, chemistry, neural ... operators), its trainer, GUI, renderers and movie tools;",
           "- the discovery loop (`discovery_cardio_mpm/`) and its seal machinery: this repository reads two data files and checks their content hashes instead;",
           "- the strain prototype's figure and movie scripts (`figures.py`, `movie*.py`, `render_progress.sh`) and its intermediate fit directories;",
           "- the raw microscope movies and the tracker's full derivatives files; only the grid positions the fit reads are shipped.", ""]
    open(f"{ROOT}/PROVENANCE.md", "w").write("\n".join(md))
    print("\n".join(l for l in md if "MODIFIED" in l or "DIFFER" in l or "replaced" in l))


if __name__ == "__main__":
    main()
