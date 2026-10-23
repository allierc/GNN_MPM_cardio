"""figures_note -- the figures of docs/plexus_cardio_note.pdf, from the reference fits, white background.

    python cardio/figures_note.py            # writes docs/figures/fig_sheets.png, fig_axes.png, fig_training.png

Style: white background, no box (top and right spines hidden), panel letter above the frame, not bold;
healthy in blue, HCM in red (two sources). Everything is read from reference/<tag>/ and data/.
"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import recording as R  # noqa: E402

BLUE, RED, INK, MUTED, GREY = "#1f6fb8", "#c0522a", "0.15", "0.45", "0.72"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "text.color": INK, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False})
OUT = os.path.join(ROOT, "docs", "figures"); os.makedirs(OUT, exist_ok=True)
SOURCES = dict(reference={s: os.path.join(ROOT, "reference", f"{s}_allbeats") for s in ("healthy", "hcm")},
               parity={"healthy": os.path.join(ROOT, "parity", "runs", "full_repo_healthy"),
                       "hcm": os.path.join(ROOT, "parity", "runs", "full_repo_hcm")})
REF = dict(SOURCES["reference"])   # a copy; __main__ replaces its entries by the --source chosen
NAME = dict(healthy="healthy", hcm="HCM")


def letter(ax, s):
    ax.text(0.0, 1.04, s, transform=ax.transAxes, va="bottom", ha="left", fontsize=11)


def sheet(spec, beat=3):
    z = np.load(os.path.join(REF[spec], "params.npz"))
    inter = z["interior"].astype(bool)
    rec = R.load(specimen=spec); win = R.beat_window(rec, beat); A, u = R.window_affine(rec, win)
    sh = R.shortening(A).numpy()
    t0, tr, du, td = z["clock"][0], np.exp(z["clock"][1]), np.exp(z["clock"][2]), np.exp(z["clock"][3])
    t = np.arange(len(win["frames"]))
    s = 1 / (1 + np.exp(-(t - t0) / tr)) / (1 + np.exp(-(t0 + du - t) / td)); gam = (s - s[0]) / (1 - s[0])
    cen = np.load(os.path.join(R.DATA_HCM if spec == "hcm" else R.DATA, "cell_centroids_world.npy"))
    tree = cKDTree(cen); r = 3 * 0.7 / np.sqrt(len(cen)); local = np.full(len(cen), np.nan)
    for j in range(len(cen)):
        nb = [k for k in tree.query_ball_point(cen[j], r) if k != j and inter[k]]
        if len(nb) >= 3:
            local[j] = np.abs(np.mean(np.exp(2j * z["phi"][nb])))
    return dict(n=int(inter.sum()), inter=inter, g=z["g"], g2=z["g2"], phi=z["phi"], logE=z["logE"],
                delay_s=z["delay"] * R.DT_S, peak=sh.max(0), gamma=gam, t_s=t * R.DT_S,
                mean_curve=sh.mean(1), cen=cen, local=local,
                order=float(np.abs(np.mean(np.exp(2j * z["phi"][inter])))))


def fig_sheets(H, D):
    fig, ax = plt.subplots(2, 3, figsize=(11, 6.6), gridspec_kw=dict(wspace=0.32, hspace=0.42))
    ax = ax.ravel()
    keys = [("peak", "recorded peak shortening per cell (strain)"), ("g", "fitted g, active strain along the fibre"),
            ("delay_s", "fitted delay (s)"), ("logE", "fitted log E (E in spec units, 80 = init)"), ("g2", "fitted g2, active strain across the fibre")]
    for a, (k, xl) in zip(ax, keys):
        vh, vd = H[k][H["inter"]], D[k][D["inter"]]
        lo = min(vh.min(), vd.min()); hi = max(np.percentile(vh, 99), np.percentile(vd, 99))
        bins = np.linspace(lo, hi, 36)
        a.hist(vh, bins, histtype="step", lw=1.8, color=BLUE, density=True, label=f"healthy ({H['n']} cells)")
        a.hist(vd, bins, histtype="step", lw=1.8, color=RED, density=True, label=f"HCM ({D['n']} cells)")
        a.set_xlabel(xl); a.set_ylabel("density")
    ax[0].legend(loc="upper right", fontsize=9)
    a = ax[5]
    a.plot(H["t_s"], H["gamma"], color=BLUE, lw=1.8, label="healthy, fitted clock")
    a.plot(D["t_s"], D["gamma"], color=RED, lw=1.8, label="HCM, fitted clock")
    a.plot(H["t_s"], H["mean_curve"] / H["mean_curve"].max(), color=BLUE, lw=1, ls="--", label="healthy, recorded mean shortening")
    a.plot(D["t_s"], D["mean_curve"] / D["mean_curve"].max(), color=RED, lw=1, ls="--", label="HCM, recorded mean shortening")
    a.set_xlabel("time from the window start (s)"); a.set_ylabel("activation (normalised)")
    a.legend(loc="upper right", fontsize=8)
    for a, s in zip(ax, "abcdef"):
        letter(a, s)
    fig.savefig(os.path.join(OUT, "fig_sheets.png"), dpi=170, bbox_inches="tight"); plt.close(fig)


def fig_axes(H, D):
    fig, ax = plt.subplots(2, 2, figsize=(9.5, 9.2), gridspec_kw=dict(height_ratios=[1.5, 1], hspace=0.3, wspace=0.28))
    for a, S, col, name in ((ax[0, 0], H, BLUE, "healthy"), (ax[0, 1], D, RED, "HCM")):
        m = S["inter"]; c = S["cen"][m]; ph = S["phi"][m]; L = 0.012 * np.clip(S["g"][m] / 0.06, 0.15, 2.5)
        d = np.stack([np.cos(ph), np.sin(ph)], 1) * L[:, None]
        a.add_collection(LineCollection(np.stack([c - d, c + d], 1), colors=col, linewidths=1.5))
        a.scatter(S["cen"][~m, 0], S["cen"][~m, 1], s=4, c=GREY, lw=0)
        a.set_xlim(0.14, 0.87); a.set_ylim(0.14, 0.87); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
        for sp in ("left", "bottom"):
            a.spines[sp].set_visible(False)
        a.set_xlabel(f"{name}: fibre axis per cell (length ~ g), axis order {S['order']:.2f}", fontsize=9.5)
    a = ax[1, 0]; bins = np.linspace(0, 180, 25)
    for S, col, name in ((H, BLUE, "healthy"), (D, RED, "HCM")):
        a.hist(np.degrees(S["phi"][S["inter"]] % np.pi), bins, histtype="step", lw=1.8, color=col, density=True,
               label=f"{name} ({S['n']} cells)")
    a.set_xlabel("fibre axis angle (deg, mod 180)"); a.set_ylabel("density"); a.legend(loc="upper right", fontsize=9)
    a = ax[1, 1]; bins = np.linspace(0, 1, 21)
    for S, col, name in ((H, BLUE, "healthy"), (D, RED, "HCM")):
        v = S["local"][S["inter"]]; v = v[np.isfinite(v)]
        a.hist(v, bins, histtype="step", lw=1.8, color=col, density=True, label=f"{name}, median {np.median(v):.2f}")
    a.set_xlabel("local alignment, 3 cell radii (0 random, 1 parallel)"); a.set_ylabel("density")
    a.legend(loc="upper right", fontsize=9)
    for a, s in zip(ax.ravel(), "abcd"):
        letter(a, s)
    fig.savefig(os.path.join(OUT, "fig_axes.png"), dpi=170, bbox_inches="tight"); plt.close(fig)


def fig_training():
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6), gridspec_kw=dict(wspace=0.35))
    a = ax[0]
    for spec, col in (("healthy", BLUE), ("hcm", RED)):
        j = json.load(open(os.path.join(REF[spec], "fit.json")))
        loss = [r["loss"] for r in j["log"]]
        a.plot(loss, color=col, lw=1.6, label=f"{NAME[spec]} ({len(loss)} iterations, {j['seconds_total']/60:.0f} min)")
    a.set_xlabel("Adam iteration"); a.set_ylabel("loss (scaled affine mismatch)"); a.legend(fontsize=9, loc="upper right")
    for a, spec, col in ((ax[1], "healthy", BLUE), (ax[2], "hcm", RED)):
        s = json.load(open(os.path.join(REF[spec], "s4_score.json")))["results"]
        beats = sorted(s, key=int); x = np.arange(len(beats))
        rA = [s[b]["model"]["r2_A"] for b in beats]; ru = [s[b]["model"]["r2_u"] for b in beats]
        pA = [s[b]["replay"]["r2_A"] for b in beats]; pu = [s[b]["replay"]["r2_u"] for b in beats]
        a.plot(x - 0.08, rA, "o", color=col, ms=6, label="model, strain maps A")
        a.plot(x + 0.08, ru, "s", color=col, ms=6, mfc="white", label="model, displacements u")
        a.plot(x - 0.08, pA, "o", color=GREY, ms=6, label="replay of the fit beat, A")
        a.plot(x + 0.08, pu, "s", color=GREY, ms=6, mfc="white", label="replay, u")
        a.set_xticks(x); a.set_xticklabels([f"beat {b}" for b in beats]); a.set_ylim(0.8, 1.0)
        a.set_ylabel(r"$R^2$ against the recording"); a.set_xlabel(f"{NAME[spec]} sheet, every beat fitted")
    ax[1].legend(fontsize=8, loc="lower right")
    for a, s in zip(ax, "abc"):
        letter(a, s)
    fig.savefig(os.path.join(OUT, "fig_training.png"), dpi=170, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------------------------------------
# the data figure: the rest frame with the tracking lattice, and the segmentation on the lattice
# ------------------------------------------------------------------------------------------------
def fig_data(movies):
    """movies: {specimen: path to the raw .ome.tif} -- the raw frames are not shipped, so this panel
    set is rebuilt only where they are; the committed docs/figures/fig_data.png is its output."""
    import tifffile
    from matplotlib.colors import ListedColormap
    fig, ax = plt.subplots(2, 2, figsize=(10, 10.4), gridspec_kw=dict(wspace=0.08, hspace=0.16))
    rng = np.random.default_rng(3)
    for row, spec in enumerate(("healthy", "hcm")):
        dd = R.DATA_HCM if spec == "hcm" else R.DATA
        z = np.load(os.path.join(dd, "grid_flow.npz"))
        P0 = (z["pos_px"][0] if "pos_px" in z.files else z["pos"][0] * 2048.0).reshape(137, 137, 2)
        lab = np.load(os.path.join(dd, "labels_grid.npy")); nuc = np.load(os.path.join(dd, "nuclei.npy"))
        a = ax[row, 0]
        if movies.get(spec) and os.path.exists(movies[spec]):
            with tifffile.TiffFile(movies[spec]) as tf:
                img = tf.pages[0].asarray().astype(np.float32)
            lo, hi = np.percentile(img, (1, 99.5))
            a.imshow(np.clip((img - lo) / (hi - lo), 0, 1), cmap="gray", origin="upper", extent=(0, 2048, 2048, 0))
        a.scatter(P0[::4, ::4, 0], P0[::4, ::4, 1], s=2.5, c="#f2c94c", lw=0)
        a.set_xlim(0, 2048); a.set_ylim(2048, 0); a.set_xticks([]); a.set_yticks([])
        for sp in a.spines.values():
            sp.set_visible(False)
        a.set_xlabel(f"{NAME[spec]}: rest frame, every 4th tracking node")
        a = ax[row, 1]
        n = int(lab.max()); cmap = ListedColormap(np.vstack([[1, 1, 1, 1], plt.cm.tab20(rng.integers(0, 20, n))]))
        a.pcolormesh(P0[..., 0], P0[..., 1], lab, cmap=cmap, vmin=0, vmax=n, shading="nearest", rasterized=True)
        a.scatter(nuc[:, 1], nuc[:, 0], s=5, c="k", lw=0)
        a.set_xlim(0, 2048); a.set_ylim(2048, 0); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
        for sp in a.spines.values():
            sp.set_visible(False)
        cnt = np.bincount(lab.ravel())[1:]
        a.set_xlabel(f"{NAME[spec]}: {n} cells, {int(np.median(cnt))} nodes per cell (median)")
    for a, s in zip(ax.ravel(), "abcd"):
        letter(a, s)
    fig.savefig(os.path.join(OUT, "fig_data.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
    print("-> docs/figures/fig_data.png")


def fig_steps(movie, crop=(560, 760), size=300, name="fig_steps.png"):
    """The four steps of the segmentation on a detail of the healthy rest frame (a few cells).

    a  borders from the motion: the contraction axis of each tracking node (colour = angle, mod 180 deg) over the
       strength of the border map (the gradient of the smoothed axis field)
    b  nuclei: the detected dark nuclei, one circle each
    c  watershed: the tracking nodes coloured by their cell, the seeds in black
    d  label image: the engine's pixel map of the same cells, drawn as outlines
    `crop` = (x, y) of the top-left corner in image pixels, `size` its side in pixels."""
    import tifffile
    from matplotlib.colors import ListedColormap, hsv_to_rgb
    from matplotlib.patches import Circle
    sys.path.insert(0, os.path.join(HERE, "seg"))
    import beat as B, seeded as SD
    z = np.load(os.path.join(R.DATA, "grid_flow.npz"))
    P = (z["pos"].astype(np.float64) * 2048.0).reshape(-1, 137, 137, 2)
    uv = (P - P[0:1]).astype(np.float32)
    onsets = json.load(open(os.path.join(R.DATA, "beats.json")))["onsets"]
    b, _ = B.mean_beat(uv, onsets=onsets, n=49)
    ang, amp, aniso = B.axis_and_anisotropy(b)
    bd = SD.bnd_from(b); bn = bd / (np.percentile(bd, 99) + 1e-12)
    P0 = P[0]; lab = np.load(os.path.join(R.DATA, "labels_grid.npy")); nuc = np.load(os.path.join(R.DATA, "nuclei.npy"))
    canvas = tifffile.imread(os.path.join(R.DATA, "cells_2560.tif"))[::-1, :]          # rows = world y
    with tifffile.TiffFile(movie) as tf:
        img = tf.pages[0].asarray().astype(np.float32)
    lo_, hi_ = np.percentile(img, (1, 99.5)); img = np.clip((img - lo_) / (hi_ - lo_), 0, 1)
    x0, y0 = crop; x1, y1 = x0 + size, y0 + size
    rng = np.random.default_rng(3); n = int(lab.max())
    colours = plt.cm.tab20(rng.integers(0, 20, n + 1)); colours[0] = (1, 1, 1, 1)

    fig, ax = plt.subplots(1, 4, figsize=(11, 3.1), gridspec_kw=dict(wspace=0.04))
    for a in ax:
        a.imshow(img[y0:y1, x0:x1], cmap="gray", extent=(x0, x1, y1, y0), vmin=0, vmax=1, interpolation="bilinear")
        a.set_xlim(x0, x1); a.set_ylim(y1, y0); a.set_xticks([]); a.set_yticks([])
        for sp in a.spines.values():
            sp.set_visible(False)
    inside = (P0[..., 0] > x0 - 10) & (P0[..., 0] < x1 + 10) & (P0[..., 1] > y0 - 10) & (P0[..., 1] < y1 + 10)
    # a: borders from the motion
    a = ax[0]
    from scipy.interpolate import LinearNDInterpolator
    gx, gy = np.meshgrid(np.arange(x0, x1, 2.0) + 1.0, np.arange(y0, y1, 2.0) + 1.0)
    heat = LinearNDInterpolator(np.stack([P0[..., 0].ravel(), P0[..., 1].ravel()], 1), bn.ravel())(gx, gy)
    a.imshow(heat, cmap="magma", vmin=0, vmax=1, alpha=0.5, extent=(x0, x1, y1, y0), interpolation="bilinear")
    ii_, jj_ = np.indices(ang.shape)
    sel = inside & (ii_ % 2 == 0) & (jj_ % 2 == 0)
    X, Y, A = P0[..., 0][sel], P0[..., 1][sel], ang[sel]
    d = 7.0 * np.stack([np.cos(A), np.sin(A)], 1)
    from matplotlib.collections import LineCollection
    a.add_collection(LineCollection(np.stack([np.stack([X, Y], 1) - d, np.stack([X, Y], 1) + d], 1),
                                    colors=hsv_to_rgb(np.stack([(A % np.pi) / np.pi, np.full_like(A, 0.85), np.full_like(A, 1.0)], 1)),
                                    linewidths=1.4))
    # b: nuclei
    a = ax[1]
    for r, c, sg in nuc:
        if x0 - 60 < c < x1 + 60 and y0 - 60 < r < y1 + 60:
            a.add_patch(Circle((c, r), sg * np.sqrt(2), fill=False, ec="#f2c94c", lw=1.0))
            a.plot([c], [r], ".", color="#f2c94c", ms=3)
    # c: watershed on the lattice
    a = ax[2]
    a.scatter(P0[..., 0][inside], P0[..., 1][inside], s=14, c=colours[lab[inside]], lw=0)
    for r, c, sg in nuc:
        if x0 < c < x1 and y0 < r < y1:
            a.plot([c], [r], "o", color="k", ms=3.2)
    # d: the label image, as outlines
    a = ax[3]
    ii = np.arange(size) + x0; jj = np.arange(size) + y0
    ci = np.clip(((0.15 + 0.7 * (ii + 0.5) / 2048.0) * 2560).astype(int), 0, 2559)
    cj = np.clip(((0.15 + 0.7 * (jj + 0.5) / 2048.0) * 2560).astype(int), 0, 2559)
    L = canvas[np.ix_(cj, ci)]
    a.imshow(colours[L], extent=(x0, x1, y1, y0), alpha=0.28, interpolation="nearest")
    edge = np.zeros(L.shape, bool); edge[:, 1:] |= L[:, 1:] != L[:, :-1]; edge[1:, :] |= L[1:, :] != L[:-1, :]
    ov = np.zeros(L.shape + (4,)); ov[edge] = (0, 0, 0, 1)
    a.imshow(ov, extent=(x0, x1, y1, y0), interpolation="nearest")
    for a, s_ in zip(ax, "abcd"):
        letter(a, s_)
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight"); plt.close(fig)
    print("->", os.path.join("docs", "figures", name), "crop", crop, size)


def print_tables(H, D):
    """The values of Table 1 (reconstruction) and Table 2 (the two sheets), from the fits in REF."""
    print("Table 1 -- R^2 per beat, model (A, u), and the replay baseline of the fitted beat")
    for spec in ("healthy", "hcm"):
        r = json.load(open(os.path.join(REF[spec], "s4_score.json")))["results"]
        beats = sorted(r, key=int)
        rA = [r[b]["model"]["r2_A"] for b in beats]; ru = [r[b]["model"]["r2_u"] for b in beats]
        print(f"  {spec:8s} R2(A) " + " ".join(f"{v:.3f}" for v in rA) + f"   spread {max(rA) - min(rA):.4f}")
        print(f"  {spec:8s} R2(u) " + " ".join(f"{v:.3f}" for v in ru) + f"   spread {max(ru) - min(ru):.4f}")
        print(f"  {spec:8s} shortening corr {np.mean([r[b]['model']['shortening_corr'] for b in beats]):.3f}"
              f"   replay A/u (first beat) {r[beats[0]]['replay']['r2_A']:.3f} / {r[beats[0]]['replay']['r2_u']:.3f}")
        fj = json.load(open(os.path.join(REF[spec], "fit.json")))
        lg = [x["loss"] for x in fj["log"]]
        print(f"  {spec:8s} loss {lg[0]:.3f} -> {lg[-1]:.4f}, {fj['seconds_total'] / 60:.0f} min, peak mem {fj['peak_mem_gb']:.1f} GB")
    print("Table 2 -- medians over interior cells")
    def row(S):
        i = S["inter"]; act = i & (S["g"] > 0.01)
        return dict(peak=np.median(S["peak"][i]), g=np.median(S["g"][i]), g2=np.median(S["g2"][i]),
                    ratio=np.median(S["g2"][act] / S["g"][act]), silent=100 * (S["g"][i] < 0.01).mean(),
                    order=S["order"], local=np.nanmedian(S["local"][i]), E=np.exp(np.median(S["logE"][i])),
                    delay=S["delay_s"][i].std(), n=S["n"])
    h, d = row(H), row(D)
    for k, lab in (("n", "cells"), ("peak", "recorded peak shortening"), ("g", "g"), ("g2", "g2"), ("ratio", "g2/g active"),
                   ("silent", "silent %"), ("order", "axis order whole"), ("local", "axis order local"), ("E", "E"), ("delay", "delay sd s")):
        print(f"  {lab:26s} healthy {h[k]:9.4f}   HCM {d[k]:9.4f}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--movie-healthy", default="", help="raw .ome.tif of the healthy recording (optional; for fig_data)")
    ap.add_argument("--movie-hcm", default="", help="raw .ome.tif of the HCM recording (optional; for fig_data)")
    ap.add_argument("--crop", default="560,760", help="x,y of the top-left corner of the detail of fig_steps, image px")
    ap.add_argument("--crop-size", type=int, default=300)
    ap.add_argument("--only", default="", help="comma list among sheets,axes,training,data,steps,tables (default: sheets,axes,training,data)")
    ap.add_argument("--source", default="reference", choices=["reference", "parity"],
                    help="which fits to read: reference/ (the archived reporting fits) or parity/runs/ (the repository's own reruns)")
    args = ap.parse_args()
    REF.update(SOURCES[args.source])
    only = set(args.only.split(",")) if args.only else {"sheets", "axes", "training", "data"}
    H, D = sheet("healthy"), sheet("hcm")
    if "sheets" in only: fig_sheets(H, D)
    if "axes" in only: fig_axes(H, D)
    if "training" in only: fig_training()
    if "data" in only: fig_data(dict(healthy=args.movie_healthy, hcm=args.movie_hcm))
    if "steps" in only: fig_steps(args.movie_healthy, crop=tuple(int(v) for v in args.crop.split(",")), size=args.crop_size)
    if "tables" in only: print_tables(H, D)
