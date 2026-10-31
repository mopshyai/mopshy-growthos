#!/usr/bin/env bash
# Re-download the free-license media the reels use. Pexels and Pixabay allow
# commercial use, but not re-hosting the raw files, so they are not in git.
set -euo pipefail
cd "$(dirname "$0")/assets"
mkdir -p broll music screens
UA="Mozilla/5.0"
clips=(
  pizza:7362641 packages:7362808 envelopes:7362636 office-evening:8347238 truck:33870727
  phone-call:7686682 typing:8472307 sticky-note:7581334 owner-laptop:12896411
  frustrated-laptop:12908960 watch-concerned:13801280 phone-notification:7822022
  smiling-call:8037831 thumbs-up:10373958 thinking:8731297 crumpled-paper:7581228
  receptionist:8467633 clock:11267667 irritated-look:8724356 excited:8724462
  team-celebrate:6395992 man-office-phone:7262260 woman-typing:7605074
  # Agency Rescue cast: one cottonbro studio shoot (Dana, Raj, Maria) + the landscaper customer
  dana-raj:8467629 dana-night-phone:8468759 dana-night-tired:8468761 dana-maria:8467948
  landscaper-mower:12694264 landscaper-field:12694116
)
for pair in "${clips[@]}"; do
  name=${pair%%:*}; id=${pair##*:}; out="broll/$name-$id.mp4"
  [ -s "$out" ] && continue
  url=$(curl -sIL -A "$UA" "https://www.pexels.com/download/video/$id/?h=1920&w=1080" | grep -i '^location' | tail -1 | tr -d '\r' | cut -d' ' -f2)
  curl -sL -A "$UA" -o "$out" "$url" && echo "got $out"
done
m="music/urban-hip-hop-beat-prettyjohn1-523746.mp3"
[ -s "$m" ] || curl -sL -A "$UA" -e "https://pixabay.com/music/old-school-hip-hop-urban-hip-hop-beat-523746/" \
  -o "$m" "https://cdn.pixabay.com/download/audio/2026/04/23/audio_8593d985e3.mp3"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for p in case-studies/all-capital-insurance pricing; do
  n=$(basename "$p"); out="screens/$n-desktop.png"
  [ -s "$out" ] || "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,3000 --screenshot="$out" "https://mopshy.com/$p" 2>/dev/null
done
echo "assets ready"
