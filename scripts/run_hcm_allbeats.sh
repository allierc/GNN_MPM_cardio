#!/bin/bash
# hcm_allbeats: the reporting fit of the HCM sheet, every flag as recorded in reference/hcm_allbeats/fit.json.
# About 150 min and 38 GB of GPU memory on an RTX A6000 (250 iterations, one rollout per beat).
# Usage: scripts/run_hcm_allbeats.sh [--device cuda:0] [--tag <name>] [--iters N]    (later flags override)
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONPATH=$HERE/src${PYTHONPATH:+:$PYTHONPATH}
cd $HERE/cardio
python -u fit.py --target recording --specimen hcm --beats 1,2,3,4 --beat 3 --per-parent 120 --n-grid 128 --anchor 10000 --drag 150 --band 0.03 --nu 0.3 --youngs 80 --iters 250 --kappa-shrink 0.1 --u-weight 1 --n-modes 2 --mode-shrink 0.01 --fit-frames 0 --free g,g2,phi,logE,clock,delay,logtau,logtr,logdur,psi,amode,logkappa --lr g=2e-3,phi=0.03,logE=0.06,clock=0.05,delay=0.1,g2=2e-3,logtau=0.05,logtr=0.05,logdur=0.05,psi=0.01,amode=0.02,logkappa=0.05 --cell-clock-shrink 0.05 --delay-shrink 0 --seed 0 --noise none --clock-mode sigmoid --clock-smooth 0.01 --E-shrink 0.3 --save-every 25 --checkpoints '' --anchor-percell --mask-band --tag hcm_allbeats "$@"
# score the fit on every beat (per-beat R^2 of the per-cell strain maps A and displacements u, next to the replay baseline)
TAG=hcm_allbeats; for a in "$@"; do if [ "$prev" = "--tag" ]; then TAG=$a; fi; prev=$a; done
python -u s4_score.py --params out/fits/$TAG/params.npz --specimen hcm --per-parent 120 --n-grid 128 \
    --anchor 10000 --anchor-percell --drag 150 --band 0.03 --nu 0.3 --fit-beat 3 --fit-beats 1,2,3,4 --beats 1,2,3,4
