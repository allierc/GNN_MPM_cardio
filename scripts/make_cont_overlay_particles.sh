#!/bin/bash
# cont_overlay_particles.mp4 -- the fitted model over beats 1-3 in ONE rollout that is never reset, two views side by
# side: the raw frames (green = recording, magenta = the rest frame warped by the fitted motion, drawn x4) and the points
# (green = the 18,769 tracking nodes, blue = the material points, displacement x10). Needs the raw microscope movie.
#
#   scripts/make_cont_overlay_particles.sh <movie.ome.tif> [fit dir, default cardio/out/fits/healthy_allbeats] [--device cuda:0]
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONPATH=$HERE/src${PYTHONPATH:+:$PYTHONPATH}
MOVIE=$1; FIT=${2:-$HERE/cardio/out/fits/healthy_allbeats}; shift; shift || true
[ -f "$MOVIE" ] || { echo "usage: $0 <movie.ome.tif> [fit dir] [--device cuda:0]"; exit 1; }
A="--per-parent 120 --drag 150 --anchor-percell --continuous --overlay --seconds 6 --tag cont"
cd $HERE/cardio
python -u movie_image.py     $A --movie "$MOVIE" --params "$FIT/params.npz" --amplify 4 "$@"
python -u movie_particles.py $A --params "$FIT/params.npz" "$@"
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
cd out/movies
$FF -loglevel error -y -i progress_overlay_cont.mp4 -i progress_particles_cont.mp4 -filter_complex \
  "[0:v]scale=-2:1000[a];[1:v]scale=-2:1000[b];[a][b]hstack=inputs=2[v]" -map "[v]" -r 26 \
  -c:v libx264 -crf 20 -pix_fmt yuv420p cont_overlay_particles.mp4
rm -f progress_overlay_cont.mp4 progress_particles_cont.mp4
ls -la cont_overlay_particles.mp4
