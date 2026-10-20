---
name: mermaid-to-vsdx
description: Convert Mermaid flowchart syntax directly to Microsoft Visio VSDX files using standard BASFLO shapes
tags: [visio, vsdx, mermaid, flowchart, basflo]
---


> **Windows 环境**：技能目录为 C:\Users\Willian\.agents\skills\mermaid-to-vsdx，脚本请用绝对路径或先 cd 进技能目录；产物写到当前工作目录。本机没有 LibreOffice（soffice），依赖它做渲染、缩略图、接受修订、公式重算的步骤会失败，其余 Python 操作正常。
# Mermaid → Visio VSDX Converter

Convert Mermaid flowchart diagrams into real Microsoft Visio VSDX files with standard BASFLO symbols (Start/End, Process, Decision, dynamic connectors). Works without Visio installed — pure Python.

## When to Use

User says "convert to Visio", "export VSDX", "generate visio file", or needs a flowchart in Visio format.

## How It Works

Uses `templates/reference.vsdx` as a skeleton — a handwritten Visio file with BASFLO masters and theme. Only `visio/pages/page1.xml` is replaced; all other files (masters, themes, styles) are kept intact. The Python script parses Mermaid syntax, lays out shapes in columns, computes connector routes, and writes a valid VSDX.

## Usage

```bash
python scripts/gen_vsdx.py 'mermaid_text' output.vsdx
```

## Setup

Python 3 only (stdlib — no extra libraries needed).

## Procedure

1. Get Mermaid text from user (e.g. `graph TD; A[Start] --> B[Process]`)
2. Run: `python3 scripts/gen_vsdx.py 'flowchart_text' output.vsdx`
3. Send VSDX back to user

## ⚠️ Key Details

### Master ID Mapping (BASFLO_U.VSSX)
- Start/End (rounded rect) = Master 2
- Process (rect) = Master 5
- Decision (diamond) = Master 4
- Dynamic connector (line) = Master 6

### Must-Have: RecalcDocument=true
Without it in docProps/custom.xml, connectors pile up in Visio.

### Connector Strategy
- **Vertical**: `Begin=PAR(PNT(src!Connections.X3))`, `End=_WALKGLUE`, `ConFixedCode=5`
- **Horizontal**: `PAR(PNT(src!Connections.X2))` → `PAR(PNT(tgt!Connections.X1))`
- **L-shape**: `_WALKGLUE` begin, `PAR(PNT(...))` end. Geometry: first horizontal then vertical
- Connects always use `ToCell="PinX" ToPart="3"`
- All connectors need `BegTrigger`/`EndTrigger` with `_XFTRIGGER(Sheet.X!EventXFMod)`

### Shapes Must NOT Set Width/Height
Inherit from Master. Only PinX/PinY, LayerMember, LineWeight, LineColor, FillBkgnd, Character.

## Known Limitations
- TD layout only, no subgraph/swimlane
- BASFLO symbol set only (extensible)

## Author
Simon Chen — [szhzz.com](https://szhzz.com)
