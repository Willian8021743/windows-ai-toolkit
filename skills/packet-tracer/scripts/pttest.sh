#!/bin/bash
# Load-test a .pkt in the real Packet Tracer GUI (needs an X display, wmctrl, ImageMagick `import`).
# usage: pttest.sh file.pkt [screenshot.png] [seconds-to-wait-before-screenshot]
# prints OK / FAIL (Incompatible-File dialog) / TIMEOUT. PT is killed afterwards.
F="$(realpath "$1")"
export DISPLAY="${DISPLAY:-:0}"
PTBIN="${PTBIN:-/opt/pt/bin}"
(cd "$PTBIN" && LD_LIBRARY_PATH="$PTBIN" nohup ./PacketTracer "$F" > /dev/null 2>&1 &)
for i in $(seq 1 60); do
  sleep 1
  T=$(wmctrl -l 2>/dev/null | grep -i "Packet Tracer")
  if echo "$T" | grep -qi "Incompatible\|Invalid File"; then echo "FAIL $1"; break; fi
  if echo "$T" | grep -q -- "- $F"; then echo "OK $1"; break; fi
  if [ $i = 60 ]; then echo "TIMEOUT $1: $T"; fi
done
[ -n "$3" ] && sleep "$3"
[ -n "$2" ] && import -window root "$2"
pkill -x PacketTracer; sleep 3     # -x! `pkill -f PacketTracer` would kill the calling shell too
