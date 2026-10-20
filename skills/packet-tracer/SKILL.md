---
name: packet-tracer
description: Build, modify, inspect and test Cisco Packet Tracer .pkt/.pka files programmatically (decrypt/encrypt, generate topologies with routers/switches/PCs/printers, copper + fiber links, IPs, hostnames, notes) and verify them in the real PT 8.2.2 GUI. Use when the user asks to build/rebuild a network "in Packet Tracer", convert a diagram/floor plan into a .pkt, change cabling (Glasfaser/Twisted Pair), add devices or configs to an existing .pkt, or read what is inside a .pkt.
---

# Packet Tracer (.pkt) skill

Packet Tracer has no scripting API, so this skill **writes the .pkt file directly**: XML built from
verified device templates, then encrypted with the PT container format. Everything here was verified
against Cisco Packet Tracer 8.2.2 (Linux, `/opt/pt`, launcher `/usr/local/bin/packettracer`, no login needed).

## Files
- `scripts/ptlib.py` – topology builder (`Network`: `add`, `link`, `fiber`, `set_ip`, `note`, `save`, `router_config`)
- `scripts/ptcrypto.py` – `-d file.pkt out.xml` / `-e in.xml out.pkt` / `-logs pt_*.log`
- `scripts/extract_template.py` – pull a `<DEVICE>` of model X out of any .pkt (`--list` shows models)
- `scripts/pttest.sh file.pkt [shot.png] [wait-s]` – opens the file in PT on `DISPLAY=:0`, prints `OK`/`FAIL`, optional screenshot, kills PT
- `scripts/xin.py` – XTest mouse/keyboard driver for the PT GUI (`click x y`, `drag x1 y1 x2 y2`, `key End`, `ctrl s`, `type text`, `sleep n`)
- `scripts/example_tebstarts.py` – full worked example (2 buildings, fiber backbone, 21 devices)
- `templates/` – `base.xml` (empty 8.2 workspace) + device XML: `router-1941`, `switch-3650-24PS`, `switch-2960-24TT`, `switch-3560-24PS`, `pc-PT`, `server-PT`
- `reference/pkt-format.md` – XML structure, link/port/fiber/printer details, pitfalls

## Setup (once)
`scripts/setup.sh` creates `scripts/venv` with `twofish` (patched for Python 3.12) and `python-xlib`.
Always run the Python scripts with `scripts/venv/bin/python`.

## Workflow: build a network
1. Read the source (floor plans, photos, diagram). Zoom into hand-written labels with PIL crops if needed;
   list every device per room/floor and the intended cabling. State assumptions the source leaves open
   (building interconnect, unlabeled devices) in the final answer.
2. Write a short build script using `ptlib` (copy `example_tebstarts.py`). Layout rule of thumb in the
   logical workspace: router top (y≈40), core y≈190, floor switches y≈350, end devices y≥540, x spacing ≈115.
   Name devices with hostnames-safe names (no spaces): `SW-HG-EG`, `PC3-EG`, `Printer1-NG-EG`.
3. Give end devices static IPs (`ip='192.168.10.11/24', gw=...`) and the router a `router_config(...)`
   plus `set_ip` on its port, so the file works immediately (pings succeed).
4. `net.save(out.pkt)` → then **always** `scripts/pttest.sh out.pkt shot.png 90` and look at the screenshot:
   `OK` + green link triangles = done. Fiber = red lines; links still orange after 90 s are not up.
5. Deliver the .pkt into the user's folder and summarize devices/ports/IPs and assumptions.

## Device / port cheat sheet
| kind | model | ports |
|---|---|---|
| `router` | 1941 | GigabitEthernet0/0, 0/1 |
| `switch` | 3650-24PS | GigabitEthernet1/0/1-24 (copper), GigabitEthernet1/1/1-4 (SFP → **fiber**) |
| `switch2960` | 2960-24TT | FastEthernet0/1-24, GigabitEthernet0/1-2 (copper only) |
| `switch3560` | 3560-24PS | FastEthernet0/1-24, GigabitEthernet0/1-2 (copper only) |
| `pc` / `server` / `printer` | PC-PT / Server-PT / Printer-PT | FastEthernet0 |

Copper sub-type is chosen automatically (switch↔switch crossover, everything else straight-through).
`net.fiber(...)` inserts GLC-LH-SMD SFPs and only works on `switch` (3650) — PT rejects fiber on copper
ports and silently drops such links, so "Glasfaser zwischen Switches" means: use 3650s for those switches.
Need another model (2911, IE-2000, Laptop, WLC…)? `extract_template.py` from a sample in `/opt/pt/saves`
(decrypt first; prefer files with VERSION 8.x), add it to `KINDS` in `ptlib.py`, then load-test.

## Modify an existing .pkt
`ptcrypto.py -d in.pkt in.xml`, edit the XML (ElementTree is fine; `<X />` vs `<X/>` doesn't matter),
`ptcrypto.py -e in.xml out.pkt`, `pttest.sh out.pkt`. Keep `VERSION` ≤ installed version. Devices copied
between files need new MACs, a `SAVE_REF_ID`, a matching NODE in `PHYSICALWORKSPACE` — `ptlib.add` does
all of that, so prefer re-adding through `ptlib` over hand-copying.

## Verifying / GUI automation
- `pttest.sh` derives the verdict from the window title (`wmctrl`); "Incompatible File" is PT's generic
  parse-failure dialog — the version number in it is a red herring when VERSION is already low enough.
  Bisect by rebuilding with parts left out.
- Launch PT only via an absolute path computed **before** `cd /opt/pt/bin`, wait ≥3 s after killing a
  previous instance (else the file is handed to the dying instance and PT opens empty).
- `pkill -x PacketTracer` — never `pkill -f`, that matches the calling shell.
- To learn how PT serializes something new: open a file, do it in the GUI with `xin.py`, `ctrl s`,
  decrypt, diff against your XML. Device dialog: click device with select tool (18,115); Physical tab has
  the MODULES list; port menus for cables support `End`/`Up` keys. Close dialogs with `wmctrl -c <name>`.
- Full-screen screenshots: `DISPLAY=:0 import -window root shot.png`; crop with PIL before viewing.

## Known limits
- No Printer-PT/Laptop/IP-phone templates shipped with PT samples; printer is derived from PC-PT (works).
- Switch/router configs are plain `RUNNINGCONFIG` lines; PT applies them on load. VLAN membership etc.
  also lives in per-port XML fields — for anything beyond hostnames/IPs, do it in the GUI or verify.
- `~/pt/logs` are encrypted and contain nothing useful about load failures.
