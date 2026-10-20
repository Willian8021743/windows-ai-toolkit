# packet-tracer — Claude Code skill

Build, modify, inspect and test Cisco Packet Tracer `.pkt` files programmatically.
Packet Tracer has no scripting API, so this skill writes the (encrypted) `.pkt` container
directly from XML device templates and verifies the result in the real PT 8.2.2 GUI.

See [SKILL.md](SKILL.md) for the full workflow, device/port cheat sheet and known limits.

## Install

```bash
git clone https://github.com/ghulqdev/packet-tracer-skill ~/.claude/skills/packet-tracer
~/.claude/skills/packet-tracer/scripts/setup.sh   # creates scripts/venv (twofish, python-xlib)
```

Requirements: Linux, Packet Tracer 8.2.2 installed under `/opt/pt`, Python 3.12+,
`wmctrl` and ImageMagick (`import`) for the GUI test/screenshot helper.

## Layout

| path | purpose |
|---|---|
| `scripts/ptlib.py` | topology builder (`Network`: `add`, `link`, `fiber`, `set_ip`, `note`, `save`) |
| `scripts/ptcrypto.py` | decrypt / encrypt `.pkt` files |
| `scripts/extract_template.py` | pull a device template out of any `.pkt` |
| `scripts/pttest.sh` | open a `.pkt` in PT, report OK/FAIL, take a screenshot |
| `scripts/xin.py` | XTest mouse/keyboard driver for GUI automation |
| `scripts/example_tebstarts.py` | worked example: 2 buildings, fiber backbone, 21 devices |
| `templates/` | empty workspace + device XML (1941, 3650, 2960, 3560, PC-PT, Server-PT) |
| `reference/pkt-format.md` | notes on the `.pkt` XML structure and pitfalls |
