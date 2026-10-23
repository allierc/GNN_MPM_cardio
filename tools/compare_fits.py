#!/usr/bin/env python
"""compare_fits -- are two fits the same fit?  Loss log, parameters and scores, side by side.

    python tools/compare_fits.py <fit_dir_A> <fit_dir_B> [--tol 1e-5]

A fit directory is what cardio/fit.py writes: fit.json (the per-iteration loss log and the config),
params.npz (every learnable), and s4_score.json if the scorer ran. The comparison reports, per
quantity, the largest absolute difference and that difference relative to the quantity's own scale:

    loss      |L_A - L_B| / |L_A|            at every logged iteration
    leaf      max |p_A - p_B| / spread(p_A)  where spread = std over cells (the map's own range);
              for the 4-number clock, the value itself
    scores    |R2_A - R2_B|                  per beat, for the strain maps (A) and displacements (u)

The verdict line applies `--tol` to the relative loss difference and the relative leaf differences.
Float32 MPM scatter accumulates with atomic adds whose order changes run to run, so two runs of the
SAME code differ at the 1e-6 level per rollout; run the same tree twice to know that floor before
reading a difference between two trees as a difference between the trees.
"""
import argparse, json, os, sys
import numpy as np


def load_dir(d):
    out = {}
    fj = os.path.join(d, "fit.json")
    if os.path.exists(fj):
        j = json.load(open(fj)); out["log"] = np.array([r["loss"] for r in j["log"]]); out["config"] = j["config"]
    pz = os.path.join(d, "params.npz")
    if os.path.exists(pz):
        z = np.load(pz); out["params"] = {k: z[k] for k in z.files if z[k].dtype.kind in "fiu" and z[k].ndim >= 1}
    sj = os.path.join(d, "s4_score.json")
    if os.path.exists(sj):
        out["scores"] = json.load(open(sj))["results"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--tol", type=float, default=1e-5, help="relative tolerance for the verdict")
    args = ap.parse_args()
    A, B = load_dir(args.a), load_dir(args.b)
    worst = 0.0
    if "log" in A and "log" in B:
        n = min(len(A["log"]), len(B["log"]))
        la, lb = A["log"][:n], B["log"][:n]
        rel = np.abs(la - lb) / np.maximum(np.abs(la), 1e-30)
        print(f"loss log: {n} common iterations (A has {len(A['log'])}, B {len(B['log'])})")
        print(f"  it 0      A {la[0]:.9f}  B {lb[0]:.9f}  |dL|/L {rel[0]:.2e}")
        print(f"  it {n-1:<5} A {la[-1]:.9f}  B {lb[-1]:.9f}  |dL|/L {rel[-1]:.2e}")
        print(f"  max |dL|/L over the log: {rel.max():.2e} at iteration {int(rel.argmax())}")
        worst = max(worst, float(rel.max()))
        for k in ("device", "seed", "iters", "per_parent", "specimen", "beats"):
            if A.get("config", {}).get(k) != B.get("config", {}).get(k):
                print(f"  config differs: {k}: {A['config'].get(k)} vs {B['config'].get(k)}")
    if "params" in A and "params" in B:
        print("parameters (max |dp| / spread of A's map):")
        for k in sorted(set(A["params"]) & set(B["params"])):
            pa, pb = A["params"][k].astype(np.float64), B["params"][k].astype(np.float64)
            if pa.shape != pb.shape:
                print(f"  {k:10} shape {pa.shape} vs {pb.shape}"); continue
            if pa.dtype.kind in "iub":
                print(f"  {k:10} {'identical' if np.array_equal(pa, pb) else 'DIFFER'}"); continue
            d = np.abs(pa - pb); sp = pa.std() if pa.size > 1 and pa.std() > 0 else np.abs(pa).max()
            r = d.max() / max(sp, 1e-30)
            print(f"  {k:10} max|dp| {d.max():.3e}  rms {np.sqrt((d**2).mean()):.3e}  spread(A) {sp:.3e}  rel {r:.2e}")
            worst = max(worst, float(r))
    if "scores" in A and "scores" in B:
        print("scores (model R^2, A = strain maps, u = displacements):")
        for beat in sorted(set(A["scores"]) & set(B["scores"]), key=int):
            ma, mb = A["scores"][beat]["model"], B["scores"][beat]["model"]
            print(f"  beat {beat}: R2(A) {ma['r2_A']:.6f} vs {mb['r2_A']:.6f} (d {abs(ma['r2_A']-mb['r2_A']):.1e})"
                  f"   R2(u) {ma['r2_u']:.6f} vs {mb['r2_u']:.6f} (d {abs(ma['r2_u']-mb['r2_u']):.1e})")
    print(f"verdict: worst relative difference {worst:.2e} {'<=' if worst <= args.tol else '>'} tol {args.tol:g} -> "
          f"{'SAME within tolerance' if worst <= args.tol else 'DIFFERENT beyond tolerance'}")
    sys.exit(0 if worst <= args.tol else 1)


if __name__ == "__main__":
    main()
