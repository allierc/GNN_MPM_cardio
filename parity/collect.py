#!/usr/bin/env python
"""collect -- gather the parity runs into parity/runs/ and write parity/README.md.

    python parity/collect.py --repo-fits cardio/out/fits --plexus-fits <Plexus>/prototype/cardio_mpm/strain/out/fits

Pairs compared (tools/compare_fits.py, full output kept per pair under parity/):
    repo vs Plexus, same GPU model, same run day     -- is the extraction the same code?
    Plexus vs Plexus (a second run of the same tree) -- the run-to-run floor of float32 atomics
    repo vs the archived reference fit (RTX A6000)   -- the number a reader will compare to
"""
import argparse, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
KEEP = ("fit.json", "params.npz", "s4_score.json")


def stage(src, name):
    dst = os.path.join(HERE, "runs", name)
    if not os.path.isdir(src):
        return None
    os.makedirs(dst, exist_ok=True)
    for f in KEEP:
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), dst)
    return dst


def compare(a, b, label):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "compare_fits.py"), a, b], capture_output=True, text=True)
    open(os.path.join(HERE, f"{label}.txt"), "w").write(r.stdout)
    return r.stdout


def summarise(txt):
    """max |dL|/L, the worst relative difference among the claimed maps, and the largest R^2 difference."""
    loss = leaf = r2 = None; worst_leaf = ("", 0.0)
    for line in txt.splitlines():
        if line.startswith("  max |dL|/L"):
            loss = float(line.split(":")[1].split()[0])
        if line.startswith("  ") and " rel " in line and line.split()[0] in ("g", "g2", "phi", "delay", "logE", "logkappa", "amode", "psi", "logtr", "logdur", "logtau", "clock"):
            k = line.split()[0]; v = float(line.split("rel")[1])
            if k in ("g", "g2", "phi", "delay") and v > worst_leaf[1]:
                worst_leaf = (k, v)
        if line.startswith("  beat"):
            ds = [float(s.split(")")[0]) for s in line.split("(d ")[1:]]
            r2 = max([r2 or 0.0] + ds)
    return loss, worst_leaf, r2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-fits", default=os.path.join(ROOT, "cardio", "out", "fits"))
    ap.add_argument("--plexus-fits", required=True)
    ap.add_argument("--gpu", default="NVIDIA RTX PRO 6000 Blackwell (97 GB)")
    args = ap.parse_args()
    runs = {}
    for tag in ("gate_repo_healthy", "full_repo_healthy", "full_repo_hcm"):
        runs[tag] = stage(os.path.join(args.repo_fits, tag), tag)
    for tag in ("gate_plexus_healthy", "full_plexus_healthy", "full_plexus_healthy_2", "full_plexus_hcm"):
        runs[tag] = stage(os.path.join(args.plexus_fits, tag), tag)
    ref = {s: os.path.join(ROOT, "reference", f"{s}_allbeats") for s in ("healthy", "hcm")}
    pairs = [("healthy_gate_repo_vs_plexus", "gate_repo_healthy", "gate_plexus_healthy", "3 iterations, repo vs Plexus"),
             ("healthy_repo_vs_plexus", "full_repo_healthy", "full_plexus_healthy", "250 iterations, repo vs Plexus"),
             ("healthy_plexus_vs_plexus", "full_plexus_healthy", "full_plexus_healthy_2", "250 iterations, Plexus vs Plexus (floor)"),
             ("healthy_repo_vs_reference", "full_repo_healthy", ref["healthy"], "250 iterations, repo vs the archived fit (RTX A6000, 2026-09-12)"),
             ("hcm_repo_vs_plexus", "full_repo_hcm", "full_plexus_hcm", "250 iterations, repo vs Plexus"),
             ("hcm_repo_vs_reference", "full_repo_hcm", ref["hcm"], "250 iterations, repo vs the archived fit (RTX A6000, 2026-09-12)")]
    rows = []
    for label, a, b, what in pairs:
        pa = runs.get(a) or a; pb = runs.get(b) if b in runs else b
        if not (pa and pb and os.path.isdir(pa) and os.path.isdir(pb)):
            rows.append((what, "not run", "", "", label)); continue
        txt = compare(pa, pb, label)
        loss, (lk, lv), r2 = summarise(txt)
        rows.append((what, f"{loss:.1e}" if loss is not None else "-", f"{lv:.1e} ({lk})" if lk else "-", f"{r2:.1e}" if r2 is not None else "-", label))
    md = ["# Parity with the Plexus tree", "",
          f"The nominal fits rerun from this repository and from the Plexus tree on the same day, same GPU model ({args.gpu}),",
          "same environment (Python 3.12.12, torch 2.9.0+cu128), same seed and flags (`configs/*.json`). Every number below is",
          "`tools/compare_fits.py` on the two fit directories; the full output of each comparison is the `.txt` beside this file,",
          "and the compared fits themselves are under `runs/` (`fit.json`, `params.npz`, `s4_score.json`).", "",
          "| comparison | max relative loss difference over the log | worst claimed map, max difference / map spread | largest R² difference | file |",
          "|---|---|---|---|---|"]
    md += [f"| {w} | {l} | {k} | {r} | `{f}.txt` |" for w, l, k, r, f in rows]
    md += ["", "Reading the table: the `Plexus vs Plexus` row is the floor set by float32 atomic adds in the MPM scatter",
           "(two runs of the SAME code on the same GPU); a `repo vs Plexus` row at that floor means the extraction changed",
           "nothing. Plexus's strict mode (`PLEXUS_STRICT_DETERMINISM=1`, `torch.use_deterministic_algorithms(True)`) cannot",
           "be used to remove the floor on this path: the segmentation seed calls `torch.bincount` on CUDA, which has no",
           "deterministic kernel, and the engine refuses to run with `warn_only`. The `vs the archived fit` rows compare",
           "against a different GPU generation and date, so they measure the fit's reproducibility as a whole, not the extraction.", ""]
    open(os.path.join(HERE, "README.md"), "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
