#!/usr/bin/env bash
# Generate animated GIF variations of the MishMash bubble logo.
# Requires: ImageMagick (convert, identify), awk
#
# Usage: ./scripts/generate_bubble_gifs.sh
#
# Outputs (in assets/images/bubbles/):
#   mishmash_bubbles_notext_overlap_center.gif  — circles overlap fully at center
#   mishmash_bubbles_notext_sides_back.gif      — circles move apart and return
#   mishmash_bubbles_notext_right_down_wrap.gif — right circle drops and wraps from top
#   mishmash_bubbles_notext_left_down_wrap.gif  — left circle drops and wraps from top
#   mishmash_bubbles_notext_combined.gif        — all animations in one loop
#
# The blink GIF (mishmash_bubbles_notext_blink.gif) is retimed from its
# existing frames — it is not regenerated from scratch.

set -euo pipefail

BASE_DIR="assets/images/bubbles"
TMP="$BASE_DIR/.tmp_gen"
rm -rf "$TMP"
mkdir -p "$TMP"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

make_svg() {
  local out="$1" cx1="$2" cy1="$3" cx2="$4" cy2="$5"
  cat > "$out" <<EOF
<svg width="1000" height="762" viewBox="0 0 420 320" xmlns="http://www.w3.org/2000/svg">
  <circle cx="$cx1" cy="$cy1" r="110" fill="#A7A1F4" stroke="#777" stroke-width="1"/>
  <circle cx="$cx2" cy="$cy2" r="110" fill="#C1F7AE" stroke="#777" stroke-width="1"/>
  <defs>
    <clipPath id="clip-left-gpt" clipPathUnits="userSpaceOnUse">
      <circle cx="$cx1" cy="$cy1" r="110" />
    </clipPath>
  </defs>
  <circle cx="$cx2" cy="$cy2" r="110" fill="#363644" clip-path="url(#clip-left-gpt)" />
</svg>
EOF
}

# Render SVG frames to PNG, then assemble into a GIF with a 10s hold on frame 0.
assemble_gif() {
  local frame_dir="$1" out="$2"
  local frames=("$frame_dir"/frame_*.png)
  local n=${#frames[@]}
  local args=()
  for ((i=0; i<n; i++)); do
    if [[ $i -eq 0 ]]; then
      args+=( \( "${frames[$i]}" -set delay 1000 \) )
    else
      args+=( \( "${frames[$i]}" -set delay 4 \) )
    fi
  done
  convert -dispose previous "${args[@]}" -loop 0 "$out"
}

pad2() { printf "%02d" "$1"; }
pad3() { printf "%03d" "$1"; }

# ---------------------------------------------------------------------------
# 1. Overlap center — circles converge to cx=210 (full overlap) and return
# ---------------------------------------------------------------------------
echo "Generating overlap center..."
DIR="$TMP/overlap_center"
mkdir -p "$DIR"
for i in $(seq 0 11); do
  m=$(awk -v i="$i" 'BEGIN{pi=atan2(0,-1); print (1-cos(2*pi*i/12))/2 }')
  cx1=$(awk -v m="$m" 'BEGIN{printf "%.3f", 150 + 60*m}')
  cx2=$(awk -v m="$m" 'BEGIN{printf "%.3f", 270 - 60*m}')
  s="$DIR/frame_$(pad2 "$i").svg"
  p="$DIR/frame_$(pad2 "$i").png"
  make_svg "$s" "$cx1" 160 "$cx2" 160
  convert -background none "$s" "$p"
done
assemble_gif "$DIR" "$BASE_DIR/mishmash_bubbles_notext_overlap_center.gif"

# ---------------------------------------------------------------------------
# 2. Sides and back — circles move apart and return
# ---------------------------------------------------------------------------
echo "Generating sides and back..."
DIR="$TMP/sides_back"
mkdir -p "$DIR"
for i in $(seq 0 11); do
  m=$(awk -v i="$i" 'BEGIN{pi=atan2(0,-1); print (1-cos(2*pi*i/12))/2 }')
  cx1=$(awk -v m="$m" 'BEGIN{printf "%.3f", 150 - 55*m}')
  cx2=$(awk -v m="$m" 'BEGIN{printf "%.3f", 270 + 55*m}')
  s="$DIR/frame_$(pad2 "$i").svg"
  p="$DIR/frame_$(pad2 "$i").png"
  make_svg "$s" "$cx1" 160 "$cx2" 160
  convert -background none "$s" "$p"
done
assemble_gif "$DIR" "$BASE_DIR/mishmash_bubbles_notext_sides_back.gif"

# ---------------------------------------------------------------------------
# 3 & 4. Vertical wrap — one circle drops out of frame and re-enters from top
# ---------------------------------------------------------------------------
Y_VALUES=(160 200 240 280 320 360 400 440 -120 -80 -40 0 40 80 120 160)

echo "Generating right down wrap..."
DIR="$TMP/right_down_wrap"
mkdir -p "$DIR"
for i in "${!Y_VALUES[@]}"; do
  idx=$(pad2 "$i")
  y="${Y_VALUES[$i]}"
  s="$DIR/frame_${idx}.svg"; p="$DIR/frame_${idx}.png"
  make_svg "$s" 150 160 270 "$y"
  convert -background none "$s" "$p"
done
assemble_gif "$DIR" "$BASE_DIR/mishmash_bubbles_notext_right_down_wrap.gif"

echo "Generating left down wrap..."
DIR="$TMP/left_down_wrap"
mkdir -p "$DIR"
for i in "${!Y_VALUES[@]}"; do
  idx=$(pad2 "$i")
  y="${Y_VALUES[$i]}"
  s="$DIR/frame_${idx}.svg"; p="$DIR/frame_${idx}.png"
  make_svg "$s" 150 "$y" 270 160
  convert -background none "$s" "$p"
done
assemble_gif "$DIR" "$BASE_DIR/mishmash_bubbles_notext_left_down_wrap.gif"

# ---------------------------------------------------------------------------
# 5. Retime the blink GIF (preserve original frames, change first-frame delay)
# ---------------------------------------------------------------------------
echo "Retiming blink..."
BLINK="$BASE_DIR/mishmash_bubbles_notext_blink.gif"
BLINK_ORIG_DELAYS=(1000 8 6 8 220)
BLINK_COUNT=$(identify -format '%n\n' "$BLINK" | head -1)
BLINK_ARGS=()
for ((i=0; i<BLINK_COUNT; i++)); do
  BLINK_ARGS+=( \( "${BLINK}[$i]" -set delay "${BLINK_ORIG_DELAYS[$i]}" \) )
done
BLINK_TMP="$TMP/blink_retimed.gif"
convert -dispose previous "${BLINK_ARGS[@]}" -loop 0 "$BLINK_TMP"
mv "$BLINK_TMP" "$BLINK"

# ---------------------------------------------------------------------------
# 6. Combined GIF — all animations in sequence, 30s hold between each
# ---------------------------------------------------------------------------
echo "Generating combined..."
COMB_DIR="$TMP/combined"
mkdir -p "$COMB_DIR"
cidx=0
> "$COMB_DIR/delays.txt"

add_cframe() {
  local src="$1" delay="$2"
  cp "$src" "$COMB_DIR/frame_$(pad3 $cidx).png"
  echo "$delay" >> "$COMB_DIR/delays.txt"
  cidx=$((cidx + 1))
}

extract_frames() {
  local gif="$1" prefix="$2"
  local count
  count=$(identify -format '%n\n' "$gif" | head -1)
  for ((i=0; i<count; i++)); do
    convert "${gif}[$i]" "$COMB_DIR/${prefix}_$(pad3 $i).png"
  done
  echo "$count"
}

# Use blink frame 0 as the hold frame (normal bubbles, eyes open)
convert "${BLINK}[0]" "$COMB_DIR/hold.png"
HOLD="$COMB_DIR/hold.png"

# Blink
BLINK_N=$(extract_frames "$BLINK" "blink")
BLINK_MOTION_DELAYS=(8 6 8)
add_cframe "$HOLD" 3000
for ((i=1; i<BLINK_N-1; i++)); do
  add_cframe "$COMB_DIR/blink_$(pad3 $i).png" "${BLINK_MOTION_DELAYS[$((i-1))]}"
done

# Overlap center
OC_N=$(extract_frames "$BASE_DIR/mishmash_bubbles_notext_overlap_center.gif" "oc")
add_cframe "$HOLD" 3000
for ((i=1; i<OC_N; i++)); do
  add_cframe "$COMB_DIR/oc_$(pad3 $i).png" 4
done

# Sides back
SB_N=$(extract_frames "$BASE_DIR/mishmash_bubbles_notext_sides_back.gif" "sb")
add_cframe "$HOLD" 3000
for ((i=1; i<SB_N; i++)); do
  add_cframe "$COMB_DIR/sb_$(pad3 $i).png" 4
done

# Right down wrap
RW_N=$(extract_frames "$BASE_DIR/mishmash_bubbles_notext_right_down_wrap.gif" "rw")
add_cframe "$HOLD" 3000
for ((i=1; i<RW_N; i++)); do
  add_cframe "$COMB_DIR/rw_$(pad3 $i).png" 4
done

# Left down wrap
LW_N=$(extract_frames "$BASE_DIR/mishmash_bubbles_notext_left_down_wrap.gif" "lw")
add_cframe "$HOLD" 3000
for ((i=1; i<LW_N; i++)); do
  add_cframe "$COMB_DIR/lw_$(pad3 $i).png" 4
done

# Assemble
CARGS=()
ci=0
while IFS= read -r d; do
  CARGS+=( \( "$COMB_DIR/frame_$(pad3 $ci).png" -set delay "$d" \) )
  ci=$((ci + 1))
done < "$COMB_DIR/delays.txt"
convert -dispose previous "${CARGS[@]}" -loop 0 "$BASE_DIR/mishmash_bubbles_notext_combined.gif"

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
rm -rf "$TMP"

echo ""
echo "Done. Generated GIFs:"
for f in \
  mishmash_bubbles_notext_blink.gif \
  mishmash_bubbles_notext_overlap_center.gif \
  mishmash_bubbles_notext_sides_back.gif \
  mishmash_bubbles_notext_right_down_wrap.gif \
  mishmash_bubbles_notext_left_down_wrap.gif \
  mishmash_bubbles_notext_combined.gif; do
  echo "  $BASE_DIR/$f"
done
