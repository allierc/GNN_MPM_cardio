"""recording -- the healthy sheet, in world units, and its cells' affine motion.

One door to the data: the repository's `data/` folder (content-checked by sha256). This file
adds what the active-strain model needs:

    world position     x_w = 0.15 + 0.70 * x_img / 2048          (the recording fills [0.15, 0.85])
    per-node label     from data/<specimen>/labels_nodes.npy (segmentation.py)
    per-cell affine    for each cell j and frame t, the least-squares map
                           x_i(t) - x_i(0)  ~=  (A_j(t) - I) (X_i - Xbar_j) + u_j(t)
                       over the ~37 tracking nodes i inside cell j. A_j is the cell's deformation
                       gradient averaged over its area (2x2, dimensionless) and u_j its centroid
                       displacement (world units). Two trackings of one movie agree in the raw
                       nodal field only r ~ 0.27 at beat peak; averaging over a cell is where the
                       signal is (contraction-axis field split-half 0.9989), so the fit's
                       observable is A_j(t), u_j(t) -- not the nodes.

`cell_affine` is written in torch and is differentiable, because the same function is applied to
the MODEL's particles: one measurement, two subjects.
"""
from __future__ import annotations

import json
import os

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
DOM_LO, DOM_HI = 0.15, 0.85
DT_S = 0.0417                      # seconds per frame of the recording


ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data", "healthy")
DATA_HCM = os.path.join(ROOT, "data", "hcm")
# Content, not path, names the recording: sha256 of the grid-flow array as stored. A file that
# does not match is a different recording, whatever it is called, and load() refuses it.
HEALTHY_POS_SHA256 = "e5fb1774286545923e6dd97f62e9f64891686d8080c43fee09d9fc2ba8ecc725"   # grid_flow.npz['pos']
HCM_POS_SHA256 = "4a544cf8a813a93aa04398bc87157adad3edfe6a3866f6ded7c84eecc3f30f36"       # grid_flow.npz['pos_px']
HCM_ONSETS = [17, 61, 121, 181, 241]           # speed peaks of the HCM recording (299 frames)


def label_tif(specimen="healthy"):
    """The 2560x2560 label image of the specimen's cells, for Plexus' `label_image` field."""
    return os.path.join(DATA_HCM if specimen == "hcm" else DATA, "cells_2560.tif")


def _grid_flow(path, key, expect_sha256):
    """Open one grid-flow file and check the array's content against its declared identity."""
    import hashlib
    if not os.path.exists(path):
        raise RuntimeError(f"recording not found: {path} (see data/README.md)")
    z = np.load(path)
    if key not in z.files:
        raise RuntimeError(f"recording has no '{key}' array: {path} (has {z.files})")
    arr = z[key]
    got = hashlib.sha256(np.ascontiguousarray(arr).tobytes()).hexdigest()
    if got != expect_sha256:
        raise RuntimeError(f"recording content does not match its declared identity: {path}\n"
                           f"  expected sha256({key}) {expect_sha256}\n  got {got}")
    return arr


def load(device="cpu", specimen="healthy"):
    """The recording in world units and the per-node cell labels.

    `healthy`: data/healthy/grid_flow.npz['pos'] is the 137x137 tracking lattice of the healthy
    sheet, 239 frames, already normalised by the image width (2048 px); its beat onsets come from
    data/healthy/beats.json. `hcm`: data/hcm/grid_flow.npz['pos_px'] is the same lattice of the
    HCM sheet, 299 frames, in image pixels (channels 0:2 of the tracker's derivatives file,
    exactly as stored). Both are mapped onto the sheet domain [DOM_LO, DOM_HI]."""
    if specimen == "hcm":
        pos_px = _grid_flow(os.path.join(DATA_HCM, "grid_flow.npz"), "pos_px", HCM_POS_SHA256)
        pos = DOM_LO + (DOM_HI - DOM_LO) * pos_px / 2048.0
        lab = np.load(os.path.join(DATA_HCM, "labels_nodes.npy")).astype(np.int64)
        assert lab.shape[0] == pos.shape[1], (lab.shape, pos.shape)
        return dict(pos=torch.as_tensor(pos, device=device), labels=torch.as_tensor(lab, device=device),
                    n_cells=int(lab.max()), onsets=list(HCM_ONSETS), specimen="hcm", dt_s=DT_S,
                    fit_span=None, heldout_spans=None, eval_mask=None)
    P = _grid_flow(os.path.join(DATA, "grid_flow.npz"), "pos", HEALTHY_POS_SHA256)
    pos = DOM_LO + (DOM_HI - DOM_LO) * P.astype(np.float32)          # [T,N,2] world
    beats = json.load(open(os.path.join(DATA, "beats.json")))
    eval_mask = np.load(os.path.join(DATA, "eval_mask.npy"))
    lab = np.load(os.path.join(DATA, "labels_nodes.npy")).astype(np.int64)  # [N], 1..C
    assert lab.shape[0] == pos.shape[1], (lab.shape, pos.shape)
    return dict(pos=torch.as_tensor(pos, device=device),
                labels=torch.as_tensor(lab, device=device),
                n_cells=int(lab.max()), specimen="healthy",
                fit_span=tuple(beats["fit_span"]),
                heldout_spans=[tuple(s) for s in beats["heldout_spans"]],
                onsets=list(beats["onsets"]),
                eval_mask=torch.as_tensor(eval_mask, device=device),
                dt_s=DT_S)


def cell_affine(x, X0, cid, n_cells, eps=1e-12):
    """Per-cell least-squares affine map, differentiable.

    x    [N,2] current positions        X0 [N,2] rest positions        cid [N] labels in 1..C
    Returns A [C,2,2] (the cell's mean deformation gradient) and u [C,2] (its centroid
    displacement). Cells with fewer than 3 points get A = I, u = 0.
    Solves  S_xX A^T = S_XX A^T  ->  A = S_xX S_XX^{-1}  with centred sums per cell.
    """
    C = n_cells
    idx = cid - 1
    ones = torch.ones(x.shape[0], device=x.device, dtype=x.dtype)
    cnt = torch.zeros(C, device=x.device, dtype=x.dtype).index_add(0, idx, ones)
    sx = torch.zeros(C, 2, device=x.device, dtype=x.dtype).index_add(0, idx, x)
    sX = torch.zeros(C, 2, device=x.device, dtype=x.dtype).index_add(0, idx, X0)
    xbar = sx / cnt.clamp(min=1)[:, None]
    Xbar = sX / cnt.clamp(min=1)[:, None]
    dx = x - xbar[idx]
    dX = X0 - Xbar[idx]
    SXX = torch.zeros(C, 2, 2, device=x.device, dtype=x.dtype).index_add(
        0, idx, dX[:, :, None] * dX[:, None, :])
    SxX = torch.zeros(C, 2, 2, device=x.device, dtype=x.dtype).index_add(
        0, idx, dx[:, :, None] * dX[:, None, :])
    ok = (cnt >= 3) & (torch.linalg.det(SXX).abs() > eps)
    eye = torch.eye(2, device=x.device, dtype=x.dtype).expand(C, 2, 2)
    SXX_safe = torch.where(ok[:, None, None], SXX, eye)
    A = torch.where(ok[:, None, None], SxX @ torch.linalg.inv(SXX_safe), eye)
    u = torch.where(ok[:, None], xbar - Xbar, torch.zeros_like(xbar))
    return A, u


def recording_affine(rec, frames, ref_frame):
    """A_rec [T,C,2,2], u_rec [T,C,2] over `frames`, rest = the recording at `ref_frame`."""
    pos, lab, C = rec["pos"], rec["labels"], rec["n_cells"]
    X0 = pos[ref_frame]
    As, us = [], []
    for t in frames:
        A, u = cell_affine(pos[t], X0, lab, C)
        As.append(A); us.append(u)
    return torch.stack(As), torch.stack(us)


REST_TAIL = 18                 # frames of the plateau before the next beat that define rest
PRE, POST = 8, 4               # a window opens 8 frames before an onset, closes 4 before the next


def beat_window(rec, k):
    """Beat k (0-based over the recording's onsets), as the physics defines it, not the speed peak.

    The split's onsets are peaks of mean nodal speed, i.e. MID-upstroke; referenced to them a beat
    looks strained for 45 of its 52 frames (measured: 1.5% offset from frame 4 to 48). The tissue
    rests for the last ~25 frames before the next onset, so REST is the median position over the
    `REST_TAIL` frames ending `POST` before the next onset, and the window runs from `PRE` frames
    before the onset (rest) to `POST` before the next (rest). Windows of consecutive beats overlap
    only in rest frames; each contains exactly one contraction.
    Returns dict(frames [T], ref [N,2] rest positions, onset, k).
    """
    on = rec["onsets"]
    o = on[k]
    nxt = on[k + 1] if k + 1 < len(on) else rec["pos"].shape[0] - 1
    lo, hi = max(o - PRE, 0), nxt - POST
    ref = rec["pos"][hi - REST_TAIL:hi].median(0).values
    return dict(frames=list(range(lo, hi + 1)), ref=ref, onset=o, k=k, span=(lo, hi))


def continuous_window(rec, beats=(1, 2, 3), rest_head=8):
    """ONE window spanning several beats, for a rollout that is never reset.

    `beat_window` gives each beat its own window and its own rest, which is what a fit wants (one
    contraction, starting and ending at rest). A movie of three beats built from three such windows
    restarts the model at every beat -- three rollouts stitched together. This window instead opens
    `PRE` frames before the first onset, closes `POST` before the beat after the last, and takes its
    rest from the `rest_head` frames at its OWN start, which precede any contraction here.
    `segments` are the frame offsets at which each beat's clock fires, so the model's single clock
    can be replayed once per beat inside one continuous rollout (`model.Params.segments`).
    """
    on = rec["onsets"]
    start = max(on[beats[0]] - PRE, 0)
    nxt = on[beats[-1] + 1] if beats[-1] + 1 < len(on) else rec["pos"].shape[0] - 1
    hi = nxt - POST
    ref = rec["pos"][start:start + rest_head].median(0).values
    return dict(frames=list(range(start, hi + 1)), ref=ref, span=(start, hi), onset=on[beats[0]],
                k=beats[0], segments=[int(on[k] - PRE - start) for k in beats], beats=list(beats))


def window_affine(rec, win):
    """A_rec [T,C,2,2], u_rec [T,C,2] over the window, relative to its REST configuration."""
    pos, lab, C = rec["pos"], rec["labels"], rec["n_cells"]
    As, us = [], []
    for t in win["frames"]:
        A, u = cell_affine(pos[t], win["ref"], lab, C)
        As.append(A); us.append(u)
    return torch.stack(As), torch.stack(us)


def shortening(A):
    """Per-cell shortening strain: minus the smallest eigenvalue of sym(A - I). [T,C] or [C].

    In CLOSED FORM, not through `eigvalsh`: for a symmetric 2x2 the eigenvalues are
    (a + c)/2 -+ sqrt(((a - c)/2)^2 + b^2), exact and differentiable, while cuSOLVER's batched
    path raises CUSOLVER_STATUS_INVALID_VALUE above ~70k matrices (a three-beat window is
    158 x 472 of them) on perfectly finite input.
    """
    eye = torch.eye(2, device=A.device, dtype=A.dtype)
    E = A - eye
    a, c = E[..., 0, 0], E[..., 1, 1]
    b = 0.5 * (E[..., 0, 1] + E[..., 1, 0])
    half, disc = 0.5 * (a + c), torch.sqrt((0.5 * (a - c)) ** 2 + b ** 2)
    return -(half - disc)


def clock_init(A_rec):
    """Fit the four clock numbers to the recording's MEAN shortening curve (over cells), so the
    model's clock starts where the tissue's is. Least squares on the normalised curve; the
    amplitude goes to g, not to the clock. Returns (t0, tau_r, dur, tau_d) in frames."""
    from scipy.optimize import minimize
    y = shortening(A_rec).mean(1).cpu().numpy()
    y = np.clip(y - np.median(y[-REST_TAIL:]), 0, None)
    y = y / y.max()
    t = np.arange(len(y), dtype=float)

    def s(p):
        t0, ltr, ld, ltd = p
        v = 1 / (1 + np.exp(-(t - t0) / np.exp(ltr))) * 1 / (1 + np.exp(-(t0 + np.exp(ld) - t) / np.exp(ltd)))
        v = (v - v[0]) / (1 - v[0] + 1e-9)
        return v / max(v.max(), 1e-9)

    best = None
    for t0 in (4.0, 6.0, 8.0, 10.0):
        r = minimize(lambda p: ((s(p) - y) ** 2).sum(), x0=[t0, np.log(1.5), np.log(10.0), np.log(3.0)],
                     method="Nelder-Mead", options=dict(maxiter=4000, xatol=1e-4, fatol=1e-8))
        if best is None or r.fun < best.fun:
            best = r
    t0, ltr, ld, ltd = best.x
    return dict(t0=float(t0), tau_r=float(np.exp(ltr)), dur=float(np.exp(ld)), tau_d=float(np.exp(ltd)),
                residual=float(best.fun), curve=y.tolist(), fit=s(best.x).tolist())


def fibre_init(A_rec):
    """Per-cell contraction axis and amplitude from the fit beat alone.

    For each cell, the frame of largest |A - I| (Frobenius) is its peak; the eigenvector of the
    most negative eigenvalue of sym(A - I) at that frame is the direction it shortened along,
    and minus that eigenvalue is how much (dimensionless strain). Returns phi [C] (angle of the
    axis, radians, mod pi) and amp [C] (peak shortening strain, >= 0).
    """
    T, C = A_rec.shape[:2]
    eye = torch.eye(2, device=A_rec.device, dtype=A_rec.dtype)
    E = 0.5 * ((A_rec - eye) + (A_rec - eye).transpose(-1, -2))         # [T,C,2,2] symmetric
    mag = torch.linalg.norm((A_rec - eye).reshape(T, C, 4), dim=-1)      # [T,C]
    tpk = mag.argmax(0)                                                  # [C]
    Epk = E[tpk, torch.arange(C)]                                        # [C,2,2]
    w, v = torch.linalg.eigh(Epk)                                        # ascending eigenvalues
    axis = v[:, :, 0]                                                    # most negative -> shortening
    phi = torch.atan2(axis[:, 1], axis[:, 0]) % np.pi
    amp = (-w[:, 0]).clamp(min=0)
    return phi, amp, tpk


if __name__ == "__main__":
    rec = load()
    for k in range(4):
        w = beat_window(rec, k)
        print(f"beat {k}: onset {w['onset']}  window {w['span']}  ({len(w['frames'])} frames)")
    win = beat_window(rec, 3)
    A, u = window_affine(rec, win)
    ck = clock_init(A)
    print(f"clock from the mean shortening curve: t0 {ck['t0']:.2f}  tau_r {ck['tau_r']:.2f}  "
          f"dur {ck['dur']:.2f}  tau_d {ck['tau_d']:.2f}  (residual {ck['residual']:.4f})")
    sh = shortening(A).mean(1)
    print("mean shortening per frame:", " ".join(f"{v:.4f}" for v in sh.tolist()))
    phi, amp, tpk = fibre_init(A)
    lo, hi = win["span"]
    print(f"cells {rec['n_cells']}  fit beat [{lo},{hi}]  nodes {rec['pos'].shape[1]}")
    print(f"peak shortening strain per cell: median {amp.median():.4f}  p10 {amp.quantile(0.1):.4f}  "
          f"p90 {amp.quantile(0.9):.4f}  max {amp.max():.4f}")
    print(f"peak frame (rel. to onset): median {tpk.float().median():.0f}  range {tpk.min()}-{tpk.max()}")
    print(f"centroid displacement at peak (world): median "
          f"{u.norm(dim=-1).max(0).values.median():.5f}")
